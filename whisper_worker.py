"""Persistent faster-whisper worker. Loads model once, then reads jobs from stdin.
Each job line: <audio_file>|<language>
Outputs: segment lines, then "DONE" (or "ERROR: ..." then "DONE")."""
import sys
from faster_whisper import WhisperModel

model_name = sys.argv[1] if len(sys.argv) > 1 else "large-v3-turbo"
print("LOADING", flush=True)
model = WhisperModel(model_name, device="auto", compute_type="auto")
print("READY", flush=True)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    parts = line.split("|", 1)
    audio_file = parts[0]
    language = parts[1] if len(parts) > 1 and parts[1] else None
    try:
        segments, _ = model.transcribe(audio_file, language=language, beam_size=5,
                                        vad_filter=True, vad_parameters={"min_silence_duration_ms": 500})
        for segment in segments:
            text = segment.text.strip()
            if text:
                print(text, flush=True)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
    print("DONE", flush=True)
