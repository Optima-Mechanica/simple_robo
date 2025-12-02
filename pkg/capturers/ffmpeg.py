#!/usr/bin/env python3

import logging

from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_YUYV, V4L2_PIX_FMT_YVYU, V4L2_PIX_FMT_UYVY, V4L2_PIX_FMT_YU12, V4L2_PIX_FMT_YV12
from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_NV12, V4L2_PIX_FMT_NV21
from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_RGB565, V4L2_PIX_FMT_RGB24, V4L2_PIX_FMT_BGR24, V4L2_PIX_FMT_RX24
from third_party.cameractrls.cameractrls import V4L2_PIX_FMT_MJPEG, V4L2_PIX_FMT_JPEG
import ffmpeg

import sys

from .capturer import CameraCapturer


def v4l2_format2_ffmpeg(fmt) -> str:
    f_map = {
        V4L2_PIX_FMT_YUYV: 'yuyv', V4L2_PIX_FMT_YVYU: 'yvyu', V4L2_PIX_FMT_UYVY: 'uyvy', V4L2_PIX_FMT_NV12: 'nv12',
        V4L2_PIX_FMT_NV21: 'nv21', V4L2_PIX_FMT_YU12: 'iyuv', V4L2_PIX_FMT_YV12: 'yv12', V4L2_PIX_FMT_RGB565: 'rgb565',
        V4L2_PIX_FMT_RGB24: 'rgb24', V4L2_PIX_FMT_BGR24: 'bgr24', V4L2_PIX_FMT_RX24: 'bgr888',
        V4L2_PIX_FMT_MJPEG: 'rgb24', V4L2_PIX_FMT_JPEG: 'rgb24'
    }

    if (result := f_map.get(fmt)) is not None:
        return result

    formats = 'Sorry, only YUYV, YVYU, UYVY, NV12, NV21, YU12, RGBP, RGB3, BGR3, RX24, MJPG, JPEG, GREY ' \
              'are supported yet.'
    logging.error('Invalid pixel format: %s (%s)', fmt, formats)

    raise RuntimeError(f'Invalid pixel format: {fmt}')


class FFMPEGCapturer(CameraCapturer):
    """
    Image capturer, uses ffmpeg.
    """
    def __init__(self, camera_device: int):
        super().__init__(0)
        self._ffmpeg_process = None

    def start_capturing(self):
        pass

    def stop_capturing(self):
        if self._ffmpeg_process is not None:
            self._ffmpeg_process.interrupt()

    def capture_image(self):
        try:
            self._ffmpeg_process = (
                ffmpeg
                .input(self._camera_device, format='v4l2', framerate=30)
                .output('pipe:', format='image2pipe', pix_fmt='bgr24', preset='veryfast', v=1)
                #.output('pipe:', format='webm', vcodec='libvpx-vp9', acodec='libvorbis', preset='fast', crf=20)
                #.output('pipe:', format='mpegts', vcodec='libx264', acodec='aac', preset='fast') #, crf=23)
                #.output('pipe:', format='mpeg', vcodec='libx264', acodec='aac', preset='veryfast') #, crf=23)
                .run_async(pipe_stdout=True)
            )

            return self._ffmpeg_process.stdout.read()
        except ffmpeg.Error as e:
            logging.error(e.stderr.decode(), file=sys.stderr)
