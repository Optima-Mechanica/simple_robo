import logging
import os
import sys

from third_party.cameractrls.cameractrls import CameraCtrls, PTZController, \
    V4L2_CID_FOCUS_ABSOLUTE, V4L2_CID_FOCUS_AUTO


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
        self._focus_absolute = self._ctrls.v4l_ctrls.find_by_v4l2_id(V4L2_CID_FOCUS_ABSOLUTE)
        self._focus_auto = self._ctrls.v4l_ctrls.find_by_v4l2_id(V4L2_CID_FOCUS_AUTO)

    @property
    def has_ptz(self) -> bool:
        return self._ctrls.has_ptz()

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

        self._ptz.ctrls.setup_ctrls({self._focus_auto.text_id: auto}, errs)

        if value is not None:
            self._ptz.ctrls.setup_ctrls({self._focus_absolute.text_id: value}, errs)

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

    def get_controls(self, hierarchy: bool = True):
        return self._ctrls.get_ctrl_pages() if hierarchy else self._ptz.get_ctrls()

    def __del__(self):
        self._ctrls.terminate_all()
