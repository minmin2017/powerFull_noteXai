"""
Robot Arm Camera — Shape Detection Streaming Server
Run with: python3 shape_cam_server.py [--device 0] [--port 8090]
"""
import cv2
import numpy as np
import time
import threading
import argparse
import math
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Global shared state
latest_jpeg = b''
lock = threading.Lock()

def camera_thread(device_id):
    global latest_jpeg
    while True:
        cap = cv2.VideoCapture(device_id)
        if not cap.isOpened():
            print(f"Error: Could not open camera {device_id}. Retrying in 2 seconds...")
            time.sleep(2)
            continue
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)

        prev_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to read frame from camera. Retrying...")
                cap.release()
                time.sleep(2)
                break
            
            # FPS Calculation
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time

            # Shape detection preprocessing
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blur, 50, 150)
            dilated = cv2.dilate(edges, None, iterations=1)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            shapes_count = {"Triangle": 0, "Square": 0, "Rectangle": 0, "Circle": 0}

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 1500:
                    continue
                
                perimeter = cv2.arcLength(cnt, True)
                if perimeter == 0:
                    continue
                
                approx = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
                vertices = len(approx)

                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                else:
                    cX, cY = 0, 0

                shape_name = ""
                color = (255, 255, 255)

                if vertices == 3:
                    shape_name = "Triangle"
                    color = (0, 255, 0) # Green
                elif vertices == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    aspect_ratio = w / float(h)
                    if 0.9 <= aspect_ratio <= 1.1:
                        shape_name = "Square"
                        color = (255, 0, 0) # Blue in BGR
                    else:
                        shape_name = "Rectangle"
                        color = (255, 0, 0) # Blue
                elif vertices > 4:
                    circularity = 4 * math.pi * area / (perimeter * perimeter)
                    if circularity > 0.8:
                        shape_name = "Circle"
                        color = (0, 255, 255) # Yellow
                
                if shape_name:
                    shapes_count[shape_name] += 1
                    cv2.drawContours(frame, [cnt], -1, color, 2)
                    cv2.putText(frame, shape_name, (cX - 20, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Draw top bar
            summary_text = f"Circle: {shapes_count['Circle']} | Square: {shapes_count['Square']} | Triangle: {shapes_count['Triangle']} | FPS: {int(fps)}"
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 30), (0, 0, 0), -1)
            cv2.putText(frame, summary_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Encode frame to JPEG
            ret_encode, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret_encode:
                with lock:
                    latest_jpeg = buffer.tobytes()

            # Small sleep to yield
            time.sleep(0.01)

class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            content = '''<html>
<head>
    <title>Robot Arm Camera</title>
    <style>
        body { background-color: #121212; color: white; text-align: center; font-family: sans-serif; }
        img { max-width: 100%; border: 2px solid #333; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>🦾 Robot Arm Camera &mdash; Shape Detection</h1>
    <img src="/stream">
</body>
</html>'''.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    with lock:
                        frame = latest_jpeg
                    if frame:
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-Type', 'image/jpeg')
                        self.send_header('Content-Length', str(len(frame)))
                        self.end_headers()
                        self.wfile.write(frame)
                        self.wfile.write(b'\r\n')
                    time.sleep(0.06) # ~15 fps
            except Exception as e:
                pass
        else:
            self.send_error(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress logging
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Shape Detection Camera Server")
    parser.add_argument("--device", type=int, default=0, help="Camera device index")
    parser.add_argument("--port", type=int, default=8090, help="HTTP Server port")
    args = parser.parse_args()

    t = threading.Thread(target=camera_thread, args=(args.device,))
    t.daemon = True
    t.start()

    server = ThreadingHTTPServer(('0.0.0.0', args.port), StreamingHandler)
    print(f"Serving on http://localhost:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()
