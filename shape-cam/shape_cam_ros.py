"""
Robot Arm Sim Camera — Shape Detection Streaming Server (ROS 2 version)

Subscribes to a sensor_msgs/msg/Image topic published by the sim (default
/overhead_camera/image_raw), runs the same shape-detection pipeline as
shape_cam_server.py, and serves the annotated stream as MJPEG over HTTP.

Run with:
    source /opt/ros/humble/setup.bash
    # source your workspace too if the topic comes from a custom package, e.g.:
    # source ~/ros2_ws/install/setup.bash
    python3 shape_cam_ros.py [--topic /overhead_camera/image_raw] [--port 8090]

Then open http://localhost:8090 in a browser.
"""
import cv2
import numpy as np
import time
import threading
import argparse
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from sensor_msgs.msg import Image

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

# Global shared state
latest_jpeg = b''
lock = threading.Lock()
last_frame_time = 0.0
current_topic = ''


class ShapeCamPanel(Node):
    def __init__(self, topic):
        super().__init__('shape_cam_panel')
        self.topic = topic
        self._warned_encoding = False
        self._prev_time = time.time()
        # Calibrated table (wood) color in LAB a/b — learned from the first
        # frame's center crop, then only nudged when the new sample agrees
        # (so the arm passing over the table can't hijack the calibration).
        self._wood_ab = None

        qos = QoSProfile(depth=10)
        self.subscription = self.create_subscription(
            Image,
            topic,
            self.image_callback,
            qos,
        )
        self.get_logger().info(f"Subscribed to {topic}")

    def image_callback(self, msg):
        global latest_jpeg, last_frame_time

        # Convert Image msg to numpy without cv_bridge
        arr = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.width, -1)

        if msg.encoding == "rgb8":
            frame = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        elif msg.encoding == "bgr8":
            frame = arr
        else:
            if not self._warned_encoding:
                self.get_logger().warn(
                    f"Unhandled image encoding '{msg.encoding}', using raw buffer as-is"
                )
                self._warned_encoding = True
            frame = arr

        # Make sure we have a writable 3-channel BGR frame for drawing
        frame = np.ascontiguousarray(frame)
        if frame.ndim == 2 or frame.shape[2] == 1:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        # FPS calculation
        curr_time = time.time()
        fps = 1 / (curr_time - self._prev_time) if (curr_time - self._prev_time) > 0 else 0
        self._prev_time = curr_time

        # ---- Shape detection: LAB color segmentation ----
        # Canny alone merges each object with its shadow on the wood table,
        # so instead: find the table by its wood color, then objects are the
        # pixels *on* the table whose a/b chroma differs from the wood.
        # Shadows keep the wood's a/b (only L drops), so they are ignored.
        h_img, w_img = frame.shape[:2]
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.int16)
        L, ach, bch = lab[:, :, 0], lab[:, :, 1], lab[:, :, 2]

        crop = lab[h_img // 3:2 * h_img // 3, w_img // 3:2 * w_img // 3]
        sample = (float(np.median(crop[:, :, 1])), float(np.median(crop[:, :, 2])))
        if self._wood_ab is None:
            self._wood_ab = sample
        elif abs(sample[0] - self._wood_ab[0]) < 10 and abs(sample[1] - self._wood_ab[1]) < 10:
            self._wood_ab = (0.9 * self._wood_ab[0] + 0.1 * sample[0],
                             0.9 * self._wood_ab[1] + 0.1 * sample[1])
        wa, wb = self._wood_ab

        shapes_count = {"Triangle": 0, "Square": 0, "Rectangle": 0, "Circle": 0, "Cylinder": 0}

        wood = ((np.abs(ach - wa) < 12) & (np.abs(bch - wb) < 12)).astype(np.uint8) * 255
        table_cnts, _ = cv2.findContours(wood, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if table_cnts:
            table = max(table_cnts, key=cv2.contourArea)
            if cv2.contourArea(table) > 0.05 * h_img * w_img:
                hull = cv2.convexHull(table)
                tmask = np.zeros((h_img, w_img), np.uint8)
                cv2.drawContours(tmask, [hull], -1, 255, -1)
                tmask = cv2.erode(tmask, np.ones((9, 9), np.uint8))
                cv2.polylines(frame, [hull], True, (80, 80, 80), 1)

                wood_L = np.median(L[tmask > 0])
                dist = np.sqrt((ach - wa) ** 2 + (bch - wb) ** 2)
                glare = L > wood_L + 40  # specular highlight on the table
                obj = ((dist > 18) & (tmask > 0) & (~glare)).astype(np.uint8) * 255
                obj = cv2.morphologyEx(obj, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
                obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

                contours, _ = cv2.findContours(obj, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area < 200:
                        continue
                    perimeter = cv2.arcLength(cnt, True)
                    if perimeter == 0:
                        continue
                    approx = cv2.approxPolyDP(cnt, 0.04 * perimeter, True)
                    vertices = len(approx)
                    circularity = 4 * math.pi * area / (perimeter * perimeter)
                    x, y, w, h = cv2.boundingRect(cnt)
                    (rw, rh) = cv2.minAreaRect(cnt)[1]
                    rect_fill = area / (rw * rh) if rw * rh > 0 else 0
                    rect_aspect = max(rw, rh) / min(rw, rh) if min(rw, rh) > 0 else 1

                    shape_name = ""
                    color = (255, 255, 255)
                    if vertices == 3:
                        shape_name, color = "Triangle", (0, 255, 0)      # green
                    elif vertices == 4 and circularity < 0.85:
                        aspect_ratio = w / float(h)
                        shape_name = "Square" if 0.9 <= aspect_ratio <= 1.1 else "Rectangle"
                        color = (255, 0, 0)                              # blue
                    elif circularity > 0.72:
                        shape_name, color = "Circle", (0, 255, 255)      # yellow
                    elif rect_fill > 0.7 and rect_aspect > 1.3:
                        # cylinder seen from a slight angle: rounded upright slab
                        shape_name, color = "Cylinder", (0, 140, 255)    # orange

                    if shape_name:
                        shapes_count[shape_name] += 1
                        cv2.drawContours(frame, [cnt], -1, color, 2)
                        cv2.putText(frame, shape_name, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Draw top bar
        summary_text = (
            f"Cir: {shapes_count['Circle']} | Sq: {shapes_count['Square'] + shapes_count['Rectangle']} | "
            f"Tri: {shapes_count['Triangle']} | Cyl: {shapes_count['Cylinder']} | "
            f"FPS: {int(fps)} | {self.topic}"
        )
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 30), (0, 0, 0), -1)
        cv2.putText(frame, summary_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Encode frame to JPEG
        ret_encode, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if ret_encode:
            with lock:
                latest_jpeg = buffer.tobytes()
                last_frame_time = curr_time


def make_placeholder_jpeg(topic):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    text = f"waiting for ROS images on {topic}..."
    cv2.putText(frame, text, (20, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    ret_encode, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    return buffer.tobytes() if ret_encode else b''


def placeholder_thread(topic):
    """Keep latest_jpeg populated with a placeholder until real frames arrive."""
    global latest_jpeg
    while True:
        with lock:
            have_real_frame = bool(latest_jpeg) and (time.time() - last_frame_time) < 2.0
        if not have_real_frame:
            placeholder = make_placeholder_jpeg(topic)
            with lock:
                # Don't clobber a real frame that just arrived
                if not latest_jpeg or (time.time() - last_frame_time) >= 2.0:
                    latest_jpeg = placeholder
        time.sleep(1.0)


class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            content = f'''<html>
<head>
    <title>Robot Arm Sim Camera</title>
    <style>
        body {{ background-color: #121212; color: white; text-align: center; font-family: sans-serif; }}
        img {{ max-width: 100%; border: 2px solid #333; margin-top: 20px; }}
    </style>
</head>
<body>
    <h1>🦾 Robot Arm Sim Camera &mdash; Shape Detection</h1>
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
                    time.sleep(0.06)  # ~15 fps
            except Exception:
                pass
        else:
            self.send_error(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress logging
        pass


def main():
    global current_topic

    parser = argparse.ArgumentParser(description="Shape Detection Camera Server (ROS 2)")
    parser.add_argument("--topic", type=str, default="/overhead_camera/image_raw",
                         help="sensor_msgs/msg/Image topic to subscribe to")
    parser.add_argument("--port", type=int, default=8090, help="HTTP Server port")
    args = parser.parse_args()

    current_topic = args.topic

    rclpy.init()
    node = ShapeCamPanel(args.topic)

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,))
    spin_thread.daemon = True
    spin_thread.start()

    ph_thread = threading.Thread(target=placeholder_thread, args=(args.topic,))
    ph_thread.daemon = True
    ph_thread.start()

    server = ThreadingHTTPServer(('0.0.0.0', args.port), StreamingHandler)
    print(f"Serving on http://localhost:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
