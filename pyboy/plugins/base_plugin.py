#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

__pdoc__ = {
    "PyBoyPlugin": False,
    "PyBoyWindowPlugin": False,
    "PyBoyGameWrapper.post_tick": False,
    "PyBoyGameWrapper.enabled": False,
    "PyBoyGameWrapper.argv": False,
}
import logging as logger
import io
import random
from array import array

import numpy as np

import pyboy


ROWS, COLS = 144, 160


class PyBoyPlugin:
    argv = []

    def __init__(self, pyboy, mb, pyboy_argv):
        self.pyboy = pyboy
        self.mb = mb
        self.pyboy_argv = pyboy_argv

    def handle_events(self, events):
        return events

    def post_tick(self):
        pass

    def window_title(self):
        return ""

    def stop(self):
        pass

    def enabled(self):
        return True


class PyBoyWindowPlugin(PyBoyPlugin):
    def __init__(self, pyboy, mb, pyboy_argv, *args, **kwargs):
        super().__init__(pyboy, mb, pyboy_argv, *args, **kwargs)

        if not self.enabled():
            return

        scale = pyboy_argv.get("scale")
        self.scale = scale
        logger.debug("%s initialization" % self.__class__.__name__)

        self._scaledresolution = (scale * COLS, scale * ROWS)
        logger.debug("Scale: x%d (%d, %d)", self.scale, self._scaledresolution[0], self._scaledresolution[1])

        self.enable_title = True
        self.renderer = mb.lcd.renderer

    def frame_limiter(self, speed):
        return False

    def set_title(self, title):
        pass

