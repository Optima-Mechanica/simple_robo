import logging
import os
import sys

from third_party.cameractrls.cameractrls import CameraCtrls, PTZController


class CameraMotionController:
    """
    Camera PTZ and focus controller.
    """

    def __init__(self, camera_device: int):
        self._device = f'/dev/video{camera_device}'
        try:
            self._camera_fd = os.open(self._device, os.O_RDWR, 0)
        except Exception as e:
            logging.error(f'os.open: {e}')
            sys.exit(3)

        self._ctrls = CameraCtrls(self._device, self._camera_fd)
        self._ptz = PTZController(self._ctrls)
        self._prev_zoom = 0

    def lift(self, value: int):
        errors = []
        if self._ptz.do_tilt_step(value, errors) != 0:
            errors.append(f'tilt new value {value} can''t be set!')
        return errors

    def rotate(self, value: int):
        errors = []
        if self._ptz.do_pan_step(value, errors) != 0:
            errors.append(f'pan new value {value} can''t be set!')
        return errors

    def zoom(self, value: int):
        errors = []
        if self._ptz.do_zoom_step(value - self._prev_zoom, errors) != 0:
            errors.append(f'zoom new value {value} can''t be set!')
        # Potential bug.
        self._prev_zoom = value
        return errors

    def focus(self, auto: bool, value: int | None = None):
        errs = []
        #self._ptz.get_ctrls()

        self._ptz.ctrls.setup_ctrls({'focus_automatic_continuous': auto}, errs)

        if value is not None:
            self._ptz.ctrls.setup_ctrls({'focus_absolute': value}, errs)

        return errs

    def set_ptz(self, pan: int, tilt: int, zoom: int):
        errors = []
        errors.extend(self.rotate(pan))
        errors.extend(self.lift(tilt))
        errors.extend(self.zoom(zoom))

        return errors

    def reset(self):
        errors = []
        self._ptz.do_reset(errs=errors)

        return errors

    def get_controls(self):
        return self._ctrls.get_ctrl_pages()


#self.ptz_controllers.terminate_all()

