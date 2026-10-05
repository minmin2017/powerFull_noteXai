import os
import json
import base64
from faster_whisper import WhisperModel

def format_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

os.makedirs("output_transcripts", exist_ok=True)

with open("audio_payload.json", "r") as f:
    payload = json.load(f)

with open("audio1.mp3", "wb") as f:
    f.write(base64.b64decode(payload["audio1"]))

with open("audio2.mp3", "wb") as f:
    f.write(base64.b64decode(payload["audio2"]))

files = [
    ("audio1.mp3", "real_hook_01_fresh_print_handheld"),
    ("audio2.mp3", "real_hook_02_break_test_flat_vs_upright")
]

print("Loading Whisper model (medium) on Ubuntu Cloud...")
model = WhisperModel("medium", device="cpu", compute_type="int8")

for audio_file, base_name in files:
    print(f"Transcribing {audio_file} -> {base_name}...")
    segments, info = model.transcribe(
        audio_file,
        language="th",
        word_timestamps=True,
        vad_filter=True,
        beam_size=5
    )

    segment_list = []
    srt_lines = []
    idx = 1
    for seg in segments:
        text = seg.text.strip()
        is_uncertain = seg.avg_logprob < -0.8 or seg.no_speech_prob > 0.4
        flagged_text = f"[?] {text}" if is_uncertain else text

        words = []
        if seg.words:
            for w in seg.words:
                words.append({
                    "word": w.word,
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "probability": round(w.probability, 3)
                })

        seg_data = {
            "id": idx,
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": text,
            "flagged_text": flagged_text,
            "avg_logprob": round(seg.avg_logprob, 3),
            "no_speech_prob": round(seg.no_speech_prob, 3),
            "words": words
        }
        segment_list.append(seg_data)

        start_str = format_timestamp(seg.start)
        end_str = format_timestamp(seg.end)
        srt_lines.append(f"{idx}\n{start_str} --> {end_str}\n{flagged_text}\n")
        idx += 1

    srt_path = os.path.join("output_transcripts", f"{base_name}.srt")
    json_path = os.path.join("output_transcripts", f"{base_name}.json")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "clip": base_name,
            "language": info.language,
            "duration": round(info.duration, 2),
            "segments": segment_list
        }, f, ensure_ascii=False, indent=2)

    print(f"Finished {base_name} ({len(segment_list)} segments)")

print("Cloud transcription complete.")
