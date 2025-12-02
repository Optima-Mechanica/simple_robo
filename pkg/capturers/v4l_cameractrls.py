from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_YUYV, V4L2_PIX_FMT_YVYU, V4L2_PIX_FMT_UYVY, V4L2_PIX_FMT_YU12, V4L2_PIX_FMT_YV12
from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_NV12, V4L2_PIX_FMT_NV21, V4L2_PIX_FMT_GREY
from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_RGB565, V4L2_PIX_FMT_RGB24, V4L2_PIX_FMT_BGR24, V4L2_PIX_FMT_RX24

from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_MJPEG, V4L2_PIX_FMT_JPEG
from third_party.cameractrls.cameraview import V4L2Camera, tj_init_decompress, tj_decompress, TJPF_RGB, SDL_PALS
import ctypes

import sys

from .capturer import CameraCapturer


class V4LCapturer(CameraCapturer):
    """
    V4L capturer, uses cameractrls library.
    """

    def __init__(self, camera_device: int):
        super().__init__(camera_device)

        self._camera = V4L2Camera(self.camera_device)

        width = self._camera.width
        height = self._camera.height

        self._outbuffer = None
        self._bytesperline = self._camera.bytesperline

        if self._camera.pixelformat in [V4L2_PIX_FMT_MJPEG, V4L2_PIX_FMT_JPEG]:
            self._tj = tj_init_decompress()
            # Create rgb buffer.
            self._outbuffer = (ctypes.c_uint8 * (width * height * 3))()
            self._bytesperline = width * 3

    def start_capturing(self):
        self._camera.start()

    def stop_capturing(self):
        self._camera.stop()

    def capture_image(self):
        ptr = (ctypes.c_uint8 * self._outbuffer.bytesused).from_buffer(self._outbuffer)

        if self._camera.pixelformat == V4L2_PIX_FMT_MJPEG or self._camera.pixelformat == V4L2_PIX_FMT_JPEG:
            tj_decompress(self._tj, ptr, self._outbuffer.bytesused, self._outbuffer, self._camera.width,
                          self._bytesperline, self._camera.height, TJPF_RGB, 0)
            # Ignore decode errors, some cameras only send imperfect frames.
            ptr = self._outbuffer

            # result = Image.frombytes(V4L2Format2PIL(self._camera.pixelformat), (self._camera.width, self._camera.height), ptr, 'raw')
        bpc = self._camera.width * self._camera.height

        # Make a Numpy array for each channel's pixels
        #R = np.frombuffer(ptr, dtype=np.uint8, count=bpc).reshape((h,w))
        #G = np.frombuffer(ptr, dtype=np.uint8, count=bpc, offset=bpc).reshape((h,w))
        #B = np.frombuffer(ptr, dtype=np.uint8, count=bpc, offset=2 * bpc).reshape((h,w))

        # Interleave the pixels from RRRRRRGGGGGGBBBBBB to RGBRGBRGBRGBRGB
        #RGB = np.dstack((R,G,B))

        # Make PIL Image from Numpy array
        #result = Image.fromarray(RGB)
        # result = Image.frombytes('L', (self._camera.width, self._camera.height), ptr, 'raw')

        # result.save(, 'PNG')
