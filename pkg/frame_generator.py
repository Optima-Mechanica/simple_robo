import asyncio
from typing import AsyncGenerator

from .capturers.capturer import CameraCapturer


class FrameGenerator:
    def __init__(self, capturer: CameraCapturer):
        self._capturer = capturer

    async def __call__(self) -> AsyncGenerator[bytes, None]:
        """
        An asynchronous generator function that yields camera frames.

        :yield: JPEG encoded image bytes.
        """

        try:
            while True:
                frame = self._capturer.capture_image()
                if frame:
                    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    break
                await asyncio.sleep(0)

        except (asyncio.CancelledError, GeneratorExit):
            print('Frame generation cancelled.')
        finally:
            print('Frame generator exited.')
