from enum import IntEnum
import wiringpi as wpi
from wiringpi import GPIO


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

    def __init__(self, left_f: int = 3, left_b: int = 0, right_f: int = 2, right_b: int = 1):
        self._motion_table = ((left_f, left_b), (right_f, right_b))

        wpi.wiringPiSetup()

        for i in [left_f, left_b, right_f, right_b]:
            wpi.pinMode(i, GPIO.OUTPUT)
            wpi.digitalWrite(i, 0)

    def start_caterpillars(self, sides: [Side], directions: [Direction]):
        assert len(sides) == len(directions)
        for side in sides:
            pins = self._motion_table[side]

            # Low output to other pin.
            wpi.digitalWrite(pins[1 - directions[side]], 0)
            # High output to destination pin.
            wpi.digitalWrite(pins[directions[side]], 1)

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
        self._cat_controller.start_caterpillars([Side.LEFT, Side.RIGHT], [direction, direction])

    def rotate(self, side: Side):
        self._cat_controller.start_caterpillars([Side.LEFT, Side.RIGHT], [Direction(1 - side), Direction(side)])

    def stop(self):
        self._cat_controller.stop_caterpillars([Side.LEFT, Side.RIGHT])

