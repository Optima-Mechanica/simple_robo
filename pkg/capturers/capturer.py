from abc import ABC, abstractmethod


class CameraCapturer(ABC):
    """
    Abstract interface for camera capturers.
    """

    def __init__(self, camera_device: int):
        self._camera_device = f'/dev/video{camera_device}'

    @abstractmethod
    def start_capturing(self):
        pass

    @abstractmethod
    def stop_capturing(self):
        pass

    @abstractmethod
    def capture_image(self):
        pass

    @property
    def camera_device(self) -> str:
        return self._camera_device

