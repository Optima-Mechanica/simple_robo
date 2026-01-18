from enum import IntEnum
import logging

try:
    import wiringpi as wpi
    from wiringpi import GPIO
except ModuleNotFoundError:
    logging.warning('WiringPi module can\'t be imported! Probably it\'s a testing environment?')

    class GPIO(IntEnum):
        OUTPUT = 0
        INPUT = 1

    class wpi:
        _msg = 'WiringPi stub: module was not imported!'

        @classmethod
        def wiringPiSetup(cls):
            logging.warning(cls._msg)

        @classmethod
        def pinMode(cls, a, b):
            logging.warning(cls._msg)

        @classmethod
        def digitalWrite(cls, a, b):
            logging.warning(cls._msg)


class Direction(IntEnum):
    """
    Motion direction.
    """

    FORWARD = 0
    BACK = 1


class Side(IntEnum):
    """
    Side where is the caterpillar will enabled.
    """

    LEFT = 0
    RIGHT = 1


class CaterpillarController:
    """
    Controller for enabling or disabling caterpillars.
    """

    def __init__(self, left_f: int = 2, left_b: int = 1, right_f: int = 0, right_b: int = 3):
        self._motion_table = ((left_f, left_b), (right_f, right_b))

        wpi.wiringPiSetup()

        for i in [left_f, left_b, right_f, right_b]:
            wpi.pinMode(i, GPIO.OUTPUT)
            wpi.digitalWrite(i, 0)

    def start_caterpillars(self, sides: {Side: Direction}):
        for side, direction in sides.items():
            pins = self._motion_table[side]
            # Low output to other pin.
            wpi.digitalWrite(pins[1 - direction], 0)
            # High output to destination pin.
            wpi.digitalWrite(pins[direction], 1)

    def stop_caterpillars(self, sides: [Side]):
        for side in sides:
            for pin in self._motion_table[side]:
                wpi.digitalWrite(pin, 0)


class RobotMotionController:
    """
    Robot motion controller.
    """

    def __init__(self, cat_controller: CaterpillarController = CaterpillarController()):
        self._cat_controller = cat_controller

    def shift(self, direction: Direction):
        self._cat_controller.start_caterpillars(
                {Side.LEFT: direction, Side.RIGHT: direction})

    def rotate(self, side: Side):
        self._cat_controller.start_caterpillars({Side.LEFT: Direction(1 - side), Side.RIGHT: Direction(side)})

    def stop(self):
        self._cat_controller.stop_caterpillars([Side.LEFT, Side.RIGHT])

