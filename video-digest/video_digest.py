#!/usr/bin/env python3
"""Powerfull Note — LOCAL video-comprehension worker (zero API cost).

Pipeline (all local):
  1. If --source is a http(s)/YouTube URL, download it with yt-dlp (height <= 480).
  2. Keyframes via ffmpeg scene detection (threshold 0.3), cap 20, saved as
     frame_<seconds>.jpg. If scene detection yields < 3 frames, fall back to one
     frame every 60 s (still capped at 20).
  3. Transcript via faster-whisper "small" (device auto, int8, cpu fallback),
     language auto (Thai + English both occur).
  4. Write digest.json continuously so pollers see progress:
       status: "processing" -> "done"  (or "error: ...").

Usage:
  python3 video_digest.py --source <path|url> --out <dir> [--id <id>]
                          [--section <id>] [--notify-url <url>] [--model small]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

FFMPEG = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/usr/bin/ffprobe"


def find_ytdlp():
    return shutil.which("yt-dlp") or os.path.expanduser("~/.local/bin/yt-dlp")


def is_url(s):
    return bool(re.match(r"^https?://", s or "", re.I))


class Digest:
    """Incrementally-written digest.json so HTTP pollers see live progress."""

    def __init__(self, out_dir, video_id, source):
        self.path = os.path.join(out_dir, "digest.json")
        self.data = {
            "id": video_id,
            "source": source,
            "title": None,
            "duration_s": None,
            "frames": [],
            "transcript": [],
            "status": "processing",
        }
        self.write()

    def set(self, **kw):
        self.data.update(kw)
        self.write()

    def write(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)


def probe_duration(path):
    try:
        out = subprocess.check_output(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            stderr=subprocess.STDOUT, text=True,
        ).strip()
        return float(out)
    except Exception:
        return None


def download(url, out_dir, digest):
    """Download a URL to <=480p mp4 via yt-dlp. Returns local path or raises."""
    ytdlp = find_ytdlp()
    tmpl = os.path.join(out_dir, "source.%(ext)s")
    # Grab the title for the digest (best-effort, non-fatal).
    try:
        title = subprocess.check_output(
            [ytdlp, "--no-warnings", "--print", "title", "--skip-download", url],
            stderr=subprocess.DEVNULL, text=True, timeout=120,
        ).strip().splitlines()
        if title:
            digest.set(title=title[0])
    except Exception:
        pass
    cmd = [
        ytdlp, "--no-warnings", "--no-playlist",
        "-f", "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
        "--merge-output-format", "mp4",
        "-o", tmpl, url,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=1800)
    # yt-dlp picked an extension; find the produced file.
    for name in sorted(os.listdir(out_dir)):
        if name.startswith("source."):
            return os.path.join(out_dir, name)
    raise RuntimeError("yt-dlp finished but no source file was produced")


def fmt_t(t):
    # 3.20 -> "3.2", 60.0 -> "60", 12.53 -> "12.53"
    return f"{round(float(t), 2):g}"


def detect_scene_times(path, threshold=0.3):
    """Return a sorted list of scene-cut timestamps (seconds) via ffmpeg showinfo."""
    cmd = [
        FFMPEG, "-hide_banner", "-i", path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-vsync", "vfr", "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                          text=True, timeout=1800)
    times = []
    for m in re.finditer(r"pts_time:([0-9.]+)", proc.stderr):
        try:
            times.append(float(m.group(1)))
        except ValueError:
            pass
    return sorted(set(times))


def extract_frame(path, t, out_dir, prefix="frame"):
    """Extract a single JPEG at time t. Returns basename or None."""
    name = f"{prefix}_{fmt_t(t)}.jpg"
    dest = os.path.join(out_dir, name)
    cmd = [
        FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
        "-ss", str(max(0.0, float(t))), "-i", path,
        "-frames:v", "1", "-q:v", "3", dest,
    ]
    try:
        subprocess.run(cmd, check=True, timeout=120)
        return name if os.path.exists(dest) else None
    except Exception:
        return None


def build_frames(path, out_dir, video_id, digest, duration):
    times = []
    try:
        times = detect_scene_times(path)
    except Exception as e:
        print(f"[frames] scene detection failed: {e}", file=sys.stderr)
    mode = "scene"
    if len(times) < 3:
        # Fallback: 1 frame per 60 s across the clip.
        mode = "interval"
        dur = duration or probe_duration(path) or 0
        times = [0.0]
        t = 60.0
        while t < dur:
            times.append(t)
            t += 60.0
        if not times:
            times = [0.0]
    times = sorted(set(round(x, 2) for x in times))[:20]  # cap 20
    url_prefix = f"/uploads/videodigest/{video_id}/"
    frames = []
    for t in times:
        name = extract_frame(path, t, out_dir)
        if name:
            frames.append({"t": t, "file": url_prefix + name})
            digest.set(frames=frames)  # progressive
    print(f"[frames] mode={mode} produced={len(frames)}", file=sys.stderr)
    return frames


def build_transcript(path, out_dir, digest, model_name="small"):
    # Extract mono 16k wav (robust; empty transcript if there is no audio track).
    wav = os.path.join(out_dir, "audio.wav")
    try:
        subprocess.run(
            [FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
             "-i", path, "-vn", "-ac", "1", "-ar", "16000", wav],
            check=True, timeout=1800,
        )
    except Exception as e:
        print(f"[transcript] no audio / extraction failed: {e}", file=sys.stderr)
        return []
    if not os.path.exists(wav) or os.path.getsize(wav) < 1000:
        print("[transcript] audio track empty", file=sys.stderr)
        return []

    from faster_whisper import WhisperModel
    model = None
    for device in ("auto", "cpu"):
        try:
            model = WhisperModel(model_name, device=device, compute_type="int8")
            print(f"[transcript] model={model_name} device={device}", file=sys.stderr)
            break
        except Exception as e:
            print(f"[transcript] WhisperModel({device}) failed: {e}", file=sys.stderr)
    if model is None:
        return []

    segments, info = model.transcribe(wav, language=None, beam_size=5,
                                      vad_filter=True,
                                      vad_parameters={"min_silence_duration_ms": 500})
    transcript = []
    for seg in segments:
        text = (seg.text or "").strip()
        if not text:
            continue
        transcript.append({"start": round(seg.start, 2),
                           "end": round(seg.end, 2), "text": text})
        digest.set(transcript=transcript)  # progressive
    try:
        os.remove(wav)
    except OSError:
        pass
    print(f"[transcript] lang={getattr(info, 'language', '?')} segments={len(transcript)}",
          file=sys.stderr)
    return transcript


def notify(url, video_id, section, status, error=None):
    if not url:
        return
    try:
        payload = json.dumps({"id": video_id, "section": section,
                             "status": status, "error": error}).encode("utf-8")
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10).read()
    except Exception as e:
        print(f"[notify] failed: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--id", default=None)
    ap.add_argument("--section", default=None)
    ap.add_argument("--notify-url", default=None)
    ap.add_argument("--model", default="small")
    args = ap.parse_args()

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    video_id = args.id or os.path.basename(os.path.normpath(out_dir))
    digest = Digest(out_dir, video_id, args.source)

    try:
        t0 = time.time()
        if is_url(args.source):
            print(f"[main] downloading {args.source}", file=sys.stderr)
            media = download(args.source, out_dir, digest)
        else:
            media = args.source
            if not os.path.exists(media):
                raise FileNotFoundError(f"source not found: {media}")
        duration = probe_duration(media)
        digest.set(duration_s=round(duration, 2) if duration else None)

        build_frames(media, out_dir, video_id, digest, duration)
        build_transcript(media, out_dir, digest, args.model)

        digest.set(status="done")
        print(f"[main] done in {time.time() - t0:.1f}s", file=sys.stderr)
        notify(args.notify_url, video_id, args.section, "done")
    except Exception as e:
        msg = f"error: {e}"
        try:
            digest.set(status=msg)
        except Exception:
            pass
        print(f"[main] {msg}", file=sys.stderr)
        notify(args.notify_url, video_id, args.section, msg, error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
