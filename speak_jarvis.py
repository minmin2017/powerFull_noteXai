import asyncio
import sys
import os
import edge_tts
import subprocess

async def speak_jarvis(text, lang="auto"):
    # Safety: Kill any lingering powershell play_audio processes to prevent overlapping voices
    try:
        subprocess.run(["powershell", "-Command", "Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like '*play_audio.ps1*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"], capture_output=True)
    except:
        pass

    # Detect language or default to JARVIS British voice for English
    has_thai = any('\u0e00' <= char <= '\u0e7f' for char in text)
    
    if has_thai:
        voice = "th-TH-NiwatNeural"  # Professional Thai Male Voice
        rate = "+0%"
        pitch = "+0Hz"
    else:
        voice = "en-GB-RyanNeural"   # JARVIS British AI Butler Voice
        rate = "+5%"
        pitch = "-5Hz"              # Slightly deeper, sophisticated tone
    
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_tts.mp3")
    if os.path.exists(output_file):
        try: os.remove(output_file)
        except: pass
    
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_file)
    
    ps_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "play_audio.ps1")
    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script, output_file])

if __name__ == "__main__":
    txt = sys.argv[1] if len(sys.argv) > 1 else "At your service, sir. I am JARVIS, your AI assistant."
    asyncio.run(speak_jarvis(txt))
