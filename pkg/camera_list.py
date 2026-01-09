import logging
import os
from pathlib import Path
from third_party.cameractrls.cameractrls import get_devices, v4ldirs, CameraCtrls, PTZController


def list_cameras(dirs: list[Path | str] = v4ldirs, ptz_only: bool = True):
    """
    List camera devices and check device for the PTZ support.
    """

    devices = []

    for device in get_devices(dirs):
        try:
            camera_fd = os.open(device.real_path, os.O_RDONLY, 0)
            ctrls = CameraCtrls(device.real_path, camera_fd)
            device.has_ptz = ctrls.has_ptz()

            if not ptz_only:
                logging.info('Appending device "%s" [PTZ = %d]', device.real_path, device.has_ptz)
                devices.append(device)
            elif device.has_ptz:
                logging.info('Appending PTZ device "%s"', device.real_path)
                devices.append(device)
        except Exception as e:
            logging.error(f'os.open: {e}')
            raise
        finally:
            os.close(camera_fd)

    return devices
