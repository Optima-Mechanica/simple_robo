import ctypes
from fcntl import ioctl
import io
import logging
import select
import struct
import sys


from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_YUYV, V4L2_PIX_FMT_YVYU, V4L2_PIX_FMT_UYVY, V4L2_PIX_FMT_YU12, V4L2_PIX_FMT_YV12
from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_NV12, V4L2_PIX_FMT_NV21  #, V4L2_PIX_FMT_GREY
from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_RGB565, V4L2_PIX_FMT_RGB24, V4L2_PIX_FMT_BGR24, V4L2_PIX_FMT_RX24

from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_MJPEG, V4L2_PIX_FMT_JPEG
from third_party.cameractrls.cameraview import V4L2Camera, tj_init_decompress, tj_decompress, TJPF_RGB, SDL_PALS
from third_party.cameractrls.cameractrls import VIDIOC_QUERYCAP, VIDIOC_G_FMT, VIDIOC_G_PARM, VIDIOC_S_PARM
from third_party.cameractrls.cameractrls import VIDIOC_REQBUFS, VIDIOC_QUERYBUF, VIDIOC_QBUF, VIDIOC_DQBUF, VIDIOC_STREAMON, VIDIOC_STREAMOFF
from third_party.cameractrls.cameractrls import V4L2_CAP_VIDEO_CAPTURE, V4L2_CAP_STREAMING, V4L2_MEMORY_MMAP, V4L2_BUF_TYPE_VIDEO_CAPTURE
from third_party.cameractrls.cameractrls import v4l2_capability, v4l2_format, v4l2_streamparm, v4l2_requestbuffers, v4l2_buffer


from PIL import Image

from .capturer import CameraCapturer


class V4LCapturer(CameraCapturer):
    """
    V4L capturer, uses cameractrls library.
    """

    def __init__(self, camera_device: int):
        super().__init__(camera_device)

        self._camera = V4L2Camera(self.camera_device)
        self._camera.pipe = self

        width = self._camera.width
        height = self._camera.height

        self._outbuffer = None
        self._bytesperline = self._camera.bytesperline

        if self._camera.pixelformat in [V4L2_PIX_FMT_MJPEG, V4L2_PIX_FMT_JPEG]:
            self._tj = tj_init_decompress()
            # Create rgb buffer.
            self._outbuffer = (ctypes.c_uint8 * (width * height * 3))()
            self._bytesperline = width * 3

        self._qbuf = None
        self._image = None

    def start_capturing(self):
        # self._camera.start()
        try:
            ioctl(self._camera.fd, VIDIOC_STREAMON, struct.pack('I', V4L2_BUF_TYPE_VIDEO_CAPTURE))
        except Exception as e:
            logging.error('VIDIOC_STREAMON failed %s: %s', self.device, e)
            return

        for buf in self._camera.cap_bufs:
            ioctl(self._camera.fd, VIDIOC_QBUF, buf)

        self._qbuf = v4l2_buffer()
        self._qbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE
        self._qbuf.memory = self._camera.cap_bufs[0].memory

    def stop_capturing(self):
        self._camera.stop()

        try:
            ioctl(self._camera.fd, VIDIOC_STREAMOFF, struct.pack('I', V4L2_BUF_TYPE_VIDEO_CAPTURE))
        except Exception as e:
            logging.error('VIDIOC_STREAMOFF failed %s: %s', self._camera.device, e)

    def _capture(self):
        if self._qbuf is None:
            self.start_capturing()

        poll = select.poll()
        poll.register(self._camera.fd, select.POLLIN)

        timeout = 0

        # DQBUF can block forever, so poll with 1000 ms timeout before
        # quit after 5s
        if len(poll.poll(1000)) == 0:
           logging.warning('%s: timeout occured', self._camera.device)
           timeout += 1
           if timeout == 5:
                self.write_buf(None)
                return
        try:
            ioctl(self._camera.fd, VIDIOC_DQBUF, self._qbuf)
        except Exception as e:
            logging.error('VIDIOC_DQBUF failed %s: %s', self._camera.device, e)
            # self.pipe.write_buf(None)
            return

        buf = self._camera.cap_bufs[self._qbuf.index]
        buf.bytesused = self._qbuf.bytesused
        # buf.timestamp = qbuf.timestamp

        self.write_buf(buf)

        ioctl(self._camera.fd, VIDIOC_QBUF, buf)

    def write_buf(self, buf):
        """
        Special method, which will be called by V4L2camera object during capture cycle.
        """
        if buf is None:
            logging.debug('write_buf() buffer is None')
            return

        logging.debug('write_buf() called, buffer size = %d', buf.bytesused)
        ptr = (ctypes.c_uint8 * buf.bytesused).from_buffer(buf.buffer)

        if self._camera.pixelformat == V4L2_PIX_FMT_MJPEG or self._camera.pixelformat == V4L2_PIX_FMT_JPEG:
            tj_decompress(self._tj, ptr, buf.bytesused, self._outbuffer, self._camera.width,
                          self._bytesperline, self._camera.height, TJPF_RGB, 0)
            # Ignore decode errors, some cameras only send imperfect frames.
            ptr = self._outbuffer

        img_byte_arr = io.BytesIO()
        Image.frombytes('RGB', (self._camera.width, self._camera.height), ptr, 'raw').save(img_byte_arr, format='jpeg')

        self._image = img_byte_arr.getvalue()

    def capture_image(self):
        self._capture()
        return self._image
