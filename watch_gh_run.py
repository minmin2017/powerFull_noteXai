import subprocess
import json
import time
import sys
import os
import shutil
import urllib.request

def notify_chat(msg):
    try:
        req = urllib.request.Request(
            'http://127.0.0.1:4321/api/chat',
            data=json.dumps({'role': 'gemini', 'text': msg, 'section': 'main'}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
        print("Chat notified:", msg[:60])
    except Exception as e:
        print("Error notifying chat:", e)

def watch_run(run_id):
    print(f"Starting auto-watcher for GitHub Actions Run #{run_id}...")
    start_time = time.time()
    
    while True:
        try:
            res = subprocess.run(
                ['gh', 'run', 'view', str(run_id), '--json', 'status,conclusion,name,jobs'],
                capture_output=True,
                text=True
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                status = data.get('status')
                conclusion = data.get('conclusion')
                
                print(f"Status: {status}, Conclusion: {conclusion}")
                
                if status == 'completed':
                    elapsed = int(time.time() - start_time)
                    if conclusion == 'success':
                        out_dir = r"C:\Users\wicha\Desktop\powerfull_note\media\cloud_matrix_rendered"
                        os.makedirs(out_dir, exist_ok=True)
                        subprocess.run(['gh', 'run', 'download', str(run_id), '--dir', out_dir])
                        
                        msg_success = f"🎉 **Cloud Run #{run_id} เรนเดอร์และรวมไฟล์เสร็จสมบูรณ์ 100%!**\n\n"
                        
                        merged_file = None
                        for root, dirs, files in os.walk(out_dir):
                            for f in files:
                                if f.endswith('.mp4'):
                                    merged_file = os.path.join(root, f)
                                    break
                            if merged_file:
                                break
                                
                        if merged_file:
                            dst = r"C:\Users\wicha\Desktop\Full_Chapter6_Manim_Lesson.mp4"
                            shutil.copy2(merged_file, dst)
                            try:
                                os.startfile(dst)
                            except Exception:
                                pass
                            msg_success += f"📺 **เปิดวิดีโอ Full Lesson ให้ดูบนหน้าจอ Windows เรียบร้อยแล้วครับ!** (`{dst}`)"
                        
                        notify_chat(msg_success)
                        break
                    else:
                        log_res = subprocess.run(
                            ['gh', 'run', 'view', str(run_id), '--log-failed'],
                            capture_output=True,
                            text=True
                        )
                        err_snippet = log_res.stdout[-600:] if log_res.stdout else "Unknown error"
                        msg_fail = f"⚠️ **Cloud Run #{run_id} พบข้อผิดพลาด (Failed):**\n```\n{err_snippet}\n```"
                        notify_chat(msg_fail)
                        break
        except Exception as e:
            print("Watcher error:", e)
            
        time.sleep(25)

if __name__ == '__main__':
    run_id = sys.argv[1] if len(sys.argv) > 1 else '33311896065'
    watch_run(run_id)
