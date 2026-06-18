"""Local transcription via faster-whisper large-v3. Streams one segment per line to stdout."""
import sys
from faster_whisper import WhisperModel

audio_file = sys.argv[1]
language = sys.argv[2] if len(sys.argv) > 2 else None

model = WhisperModel("large-v3", device="auto", compute_type="auto")
segments, _ = model.transcribe(audio_file, language=language, beam_size=5)
for segment in segments:
    print(segment.text.strip(), flush=True)
