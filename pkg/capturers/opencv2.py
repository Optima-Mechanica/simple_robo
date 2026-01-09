import cv2
from pathlib import Path
import threading
from .capturer import CameraCapturer


class CV2Capturer(CameraCapturer):
    """
    OpenCV camera capturer.
    """

    def __init__(self, camera_device: int | str | Path):
        super().__init__(camera_device)
        self._cv2_camera = cv2.VideoCapture(camera_device)
        self._lock = threading.Lock()

    def start_capturing(self):
        pass

    def stop_capturing(self):
        with self._lock:
            if self._cv2_camera.isOpened():
                self._cv2_camera.release()

    def capture_image(self):
        with self._lock:
            ret, frame = self._cv2_camera.read()
            if not ret:
                return b''

            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                return b''

            return jpeg.tobytes()
