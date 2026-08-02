"""Persistent edge-tts worker — streams MP3 audio chunks as they're generated
instead of waiting for the whole clip (that wait was the main source of the
"laggy" TTS playback: the old /api/tts spawned a fresh edge-tts CLI process
per request and only responded after the full file was written to disk).

Protocol (line-based control on stdin/stderr, raw audio bytes on stdout):
  stdin  <- "<voice>|<text>\n"           one job per line
  stdout -> raw MP3 bytes for that job, streamed as edge-tts yields them
  stderr -> "READY" once at startup, then "DONE" / "ERROR: ..." per job

Only one job is in flight at a time — matches this app's single active
conversation, keeps the framing simple (no interleaving needed)."""
import asyncio
import sys

import edge_tts

DEFAULT_VOICE = "th-TH-PremwadeeNeural"


async def synth_job(voice: str, text: str):
    communicate = edge_tts.Communicate(text, voice or DEFAULT_VOICE)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            sys.stdout.buffer.write(chunk["data"])
            sys.stdout.buffer.flush()


def main():
    print("READY", file=sys.stderr, flush=True)
    for line in sys.stdin:
        line = line.rstrip("\n")
        if not line:
            continue
        voice, _, text = line.partition("|")
        if not text:
            text, voice = voice, DEFAULT_VOICE
        try:
            asyncio.run(synth_job(voice, text))
            print("DONE", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
