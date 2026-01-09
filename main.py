#!/usr/bin/env python3

import asyncio
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse
import json

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).parent
STATIC_DIR = SCRIPT_DIR / 'pkg' / 'static'
TP_DIR = SCRIPT_DIR / 'third_party'

sys.path.extend([str(sp) for sp in [(TP_DIR / 'cameractrls').absolute(), TP_DIR.absolute()]])

from pkg.capturers.opencv2 import CV2Capturer as CameraCapturer
#from pkg.capturers.v4l_cameractrls import V4LCapturer as CameraCapturer
#from pkg.capturers.ffmpeg import FFMPEGCapturer as CameraCapturer

from pkg.camera_motion_controller import CameraMotionController
from pkg.robot_motion_controller import RobotMotionController, Direction as RobotDirection, Side
from pkg.api_data_structures import PTZRecord, Focus, Direction, ServerEvent, ServerEventData, ConnectionInfo
from pkg.frame_generator import FrameGenerator
from pkg.wifi_monitor import get_wifi_signal_strength
from pkg.camera_list import list_cameras


cameras = list_cameras()

if not cameras:
    logging.warning('PTZ cameras were not found!')
    cameras = list_cameras(ptz_only=False)

if not cameras:
    logging.error('Cameras were not found!')
    sys.exit(3)


CAMERA_PATH = cameras[0].real_path

logging.info('Selected camera: %s', cameras[0].path)

capturer = CameraCapturer(CAMERA_PATH)
frame_generator = FrameGenerator(capturer)
templates = Jinja2Templates(directory=(STATIC_DIR / 'templates'))
camera_motion_controller = CameraMotionController(CAMERA_PATH)
robot_motion_controller = RobotMotionController()
message_queue: asyncio.Queue[ServerEvent] = asyncio.Queue()

app = FastAPI()
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    try:
        logging.info('Video capturing starting...')
        capturer.start_capturing()
        logging.info('Capturing started.')
        yield
    except asyncio.exceptions.CancelledError as error:
        logging.error(error.args)
    finally:
        capturer.stop_capturing()
        logging.info('Camera resource released.')


app.router.lifespan_context = lifespan


async def ev_gen(request: Request):
    while not await request.is_disconnected():
        message = await message_queue.get()
        prepared_message = json.loads(message.model_dump_json())
        prepared_message['data'] = json.dumps(prepared_message['data'])
        logging.debug('Server event: %s', prepared_message)

        yield prepared_message


@app.get('/video_feed')
async def video_feed() -> StreamingResponse:
    """
    Video streaming route.

    :return: StreamingResponse with multipart JPEG frames.
    """
    return StreamingResponse(
        frame_generator(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )


@app.get('/')
def entrypoint(request: Request):
    logging.debug('Requested /')
    return templates.TemplateResponse('index.html', {'request': request})


@app.post('/api/motion/direction')
async def direction_set(direction: Direction):
    # loop = asyncio.get_running_loop()
    # loop.call_later(2, lambda: asyncio.create_task(my_callback_function("Hello from the timer!")))

    geo_direction = {
        'N': lambda: robot_motion_controller.shift(RobotDirection.FORWARD),
        'S': lambda: robot_motion_controller.shift(RobotDirection.BACK),
        'E': lambda: robot_motion_controller.rotate(Side.RIGHT),
        'W': lambda: robot_motion_controller.rotate(Side.LEFT),
        'NE': None, # 'Lf',
        'NW': None, # 'Rf',
        'SE': None, # 'Lb',
        'SW': None, # 'Rb',
        'C': robot_motion_controller.stop
    }

    if (m_dir := geo_direction.get(direction.direction)) is not None:
        m_dir()

    return {'message': 'Direction submitted successfully!', 'data': direction.model_dump_json() }


@app.get('/api/camera/controls')
async def controls_get():
    return { 'data': camera_motion_controller.get_controls()  }


@app.post('/api/camera/ptz')
async def set_camera_ptz(ptz_record: PTZRecord, background_tasks: BackgroundTasks):
    # background_tasks.add_task(camera_motion_controller.set_ptz, ptz_record.pan, ptz_record.tilt, ptz_record.zoom)
    camera_motion_controller.ptz = (ptz_record.pan, ptz_record.tilt, ptz_record.zoom)
    await message_queue.put(ServerEvent(data=ServerEventData(payload=ptz_record)))
    return {'message': 'PTZ submitted successfully!', 'data': ptz_record.model_dump_json() }


@app.get('/api/camera/ptz')
async def get_camera_ptz():
    return PTZRecord.from_tuple(camera_motion_controller.ptz).model_dump_json()


@app.post('/api/camera/focus')
async def set_camera_focus(focus: Focus):
    camera_motion_controller.set_focus(focus.auto, focus.value)
    await message_queue.put(ServerEvent(data=ServerEventData(payload=focus)))
    return {'message': 'Focus submitted successfully!', 'data': focus.model_dump_json() }


@app.get('/api/camera/focus')
async def get_camera_focus():
    return Focus.from_tuple(camera_motion_controller.focus).model_dump_json()


@app.post('/api/camera/reset')
async def camera_reset():
    errors = camera_motion_controller.reset()
    await message_queue.put(ServerEvent(data=ServerEventData(payload='reset')))
    return {'message': 'Camera was reset successfully!' }


@app.get('/api/connection')
async def wifi_info():
    level = get_wifi_signal_strength()

    if level is not None:
        return ConnectionInfo.from_tuple(('wifi', level)).model_dump_json()

    return ConnectionInfo.from_tuple((None, None)).model_dump_json()


#@app.get('/{path:path}')
#async def html_landing():
#    return Response(prebuilt_html(title='FastUI Button Example'))


@app.get('/event_stream')
async def event_stream(request: Request):
    # return StreamingResponse(ev_gen(request), media_type='text/event-stream')
    return EventSourceResponse(ev_gen(request))


async def main(host: str = '0.0.0.0', port: int = 8000):
    """
    Main entry point to run the Uvicorn server.
    """

    config = uvicorn.Config(app, host=host, port=port, reload_dirs=['pkg'], reload_excludes=['pkg/static'],
                            use_colors=True, timeout_graceful_shutdown=3)
    server = uvicorn.Server(config)

    # Run the server
    await server.serve()


if '__main__' == __name__:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Server stopped by user.')
