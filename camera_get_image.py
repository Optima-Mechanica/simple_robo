#!/usr/bin/env python3

import asyncio
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
from contextlib import asynccontextmanager
import uvicorn
from typing import Optional, Union
import logging
from fastapi.templating import Jinja2Templates

import os
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).parent
STATIC_DIR = SCRIPT_DIR / 'pkg' / 'static'
TP_DIR = SCRIPT_DIR / 'third_party'

sys.path.extend([(TP_DIR / 'cameractrls').absolute(), TP_DIR.absolute()])

from pkg.capturers.opencv2 import CV2Capturer as CameraCapturer
#from pkg.capturers.v4l_cameractrls import V4LCapturer as CameraCapturer
#from pkg.capturers.ffmpeg import FFMPEGCapturer as CameraCapturer

from pkg.camera_motion_controller import CameraMotionController
from pkg.api_data_structures import PTZRecord, Focus, Direction


async def gen_frames() -> AsyncGenerator[bytes, None]:
    """
    An asynchronous generator function that yields camera frames.

    :yield: JPEG encoded image bytes.
    """
    try:
        while True:
            frame = capturer.capture_image()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                break
            await asyncio.sleep(0)
    except (asyncio.CancelledError, GeneratorExit):
        print('Frame generation cancelled.')
    finally:
        print('Frame generator exited.')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    try:
        yield
    except asyncio.exceptions.CancelledError as error:
        print(error.args)
    finally:
        capturer.stop_capturing()
        print('Camera resource released.')

app = FastAPI(lifespan=lifespan)
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
templates = Jinja2Templates(directory=(STATIC_DIR /'templates'))
motion_controller = CameraMotionController(4)


@app.get('/video_feed')
async def video_feed() -> StreamingResponse:
    """
    Video streaming route.

    :return: StreamingResponse with multipart JPEG frames.
    """
    return StreamingResponse(
        gen_frames(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


@app.get('/')
def entrypoint(request: Request):
    # logger.debug('Requested /')
    return templates.TemplateResponse('index.html', {'request': request, 'name': 'World'})

@app.post('/api/motion/direction')
async def direction_set(direction: Direction):
    return {'message': 'Direction submitted successfully!', 'data': direction.model_dump_json() }


@app.get('/api/camera/controls')
async def controls_get():
    return { 'data': motion_controller.get_controls()  }


@app.post('/api/camera/ptz')
async def camera_ptz(ptz_record: PTZRecord, background_tasks: BackgroundTasks):
    background_tasks.add_task(motion_controller.set_ptz, ptz_record.pan, ptz_record.tilt, ptz_record.zoom)
    return {'message': 'PTZ submitted successfully!', 'data': ptz_record.model_dump_json() }


@app.post('/api/camera/focus')
async def camera_focus(focus: Focus):
    motion_controller.focus(focus.auto, focus.value)
    return {'message': 'Focus submitted successfully!', 'data': focus.model_dump_json() }


@app.post('/api/camera/reset')
async def camera_reset():
    errors = motion_controller.reset()
    return {'message': 'Camera was reset successfully!' }

#@app.get('/{path:path}')
#async def html_landing():
#    return Response(prebuilt_html(title='FastUI Button Example'))


async def main():
    """
    Main entry point to run the Uvicorn server.
    """
    config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(config)

    # Run the server
    await server.serve()


if '__main__' == __name__:
    # Usage example: Streaming default camera for local webcam:
    capturer = CameraCapturer(4)

    # Usage example: Streaming the camera for a specific camera index:
    # camera = Camera(0)

    # Usage example 3: Streaming an IP camera:
    # camera = Camera('rtsp://user:password@ip_address:port/')

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Server stopped by user.')
