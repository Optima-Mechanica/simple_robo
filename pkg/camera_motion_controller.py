import logging
import os
import sys

from third_party.cameractrls.cameractrls import CameraCtrls, PTZController, V4L2Ctrl, \
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
        #self._listener = self._ctrls.subscribe_events(
        #    self._update_params,
        #    lambda errs: logging.error('Error event: %s', '\n'.join(errs)),
        #)

        self._position_parameters = dict()

    @property
    def has_ptz(self) -> bool:
        return self._ctrls.has_ptz()

    @property
    def ptz(self) -> (int, int, int):
        if self._ptz is None:
            return 0, 0, 0

        pan = 0 if self._ptz.pan_absolute is None else self._ptz.pan_absolute.value
        tilt = 0 if self._ptz.tilt_absolute is None else self._ptz.tilt_absolute.value
        zoom = 0 if self._ptz.zoom_absolute is None else self._ptz.zoom_absolute.value

        return pan, tilt, zoom

    @ptz.setter
    def ptz(self, value: (int, int, int)):
        self.set_ptz(*value)

    @property
    def focus(self) -> (bool, int):
        return False if self._focus_auto is None else bool(self._focus_auto.value), \
            False if self._focus_absolute is None else int(self._focus_absolute.value)

    @focus.setter
    def focus(self, value: (bool, int)):
        self.set_focus(*value)

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
        #if self._ptz.do_zoom_step(value - self._prev_zoom, errors) != 0:
        if self._ptz.do_zoom_step(value - self._prev_zoom, errors) != 0:
            errors.append(f'zoom new value {value} can''t be set!')
        # Potential bug.
        self._prev_zoom = value
        return errors

    def set_focus(self, auto: bool, value: int | None = None):
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

    def get_controls(self, hierarchy: bool = False):
        necessary_params = ['name', 'tooltip', 'type', 'value', 'min', 'max', 'default', 'step', 'inactive',
                            'readonly', 'unrestorable']

        return self._ctrls.get_ctrl_pages() if hierarchy else {
            ctrl.text_id: {
                param_name: getattr(ctrl, param_name) for param_name in necessary_params
            } for ctrl in self._ctrls.get_ctrls()
        }

    def _get_control_values(self):
        return {ctrl.text_id: ctrl.value for ctrl in self._ctrls.get_ctrls()}

    def _update_params(self, event: V4L2Ctrl):
        logging.debug(f'V4LEvent: %s %s %s', event.text_id, event.name, event.value)
        {
            self._ptz.pan_absolute.text_id: lambda: logging.debug('PAN'),
            self._ptz.tilt_absolute.text_id: lambda: logging.debug('TILT'),
            self._ptz.zoom_absolute.text_id: lambda: logging.debug('ZOOM'),
            self._focus_absolute.text_id: lambda: logging.debug('FOCUS_FLAG'),
            self._focus_auto.text_id: lambda: logging.debug('FOCUS_VALUE')
        }[event.text_id]()

        print()

    def __del__(self):
        pass
        # self._ctrls.terminate_all()
