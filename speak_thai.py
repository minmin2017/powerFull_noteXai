import asyncio
import sys
import os
import edge_tts
import subprocess

async def speak(text):
    voice = "th-TH-NiwatNeural"
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_tts.mp3")
    if os.path.exists(output_file):
        try: os.remove(output_file)
        except: pass
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    
    ps_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "play_audio.ps1")
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script, output_file])

if __name__ == "__main__":
    txt = sys.argv[1] if len(sys.argv) > 1 else "สวัสดีครับ ตอนนี้ทดสอบระบบเสียงภาษาไทยแล้วครับ"
    asyncio.run(speak(txt))
