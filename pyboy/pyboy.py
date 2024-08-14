#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#
"""
The core module of the emulator
"""
import logging as logger
import numpy as np
import heapq
import time
import os
import re


from pyboy.utils import IntIOWrapper, WindowEvent
from pyboy.plugins.manager import PluginManager
from .core.mb import Motherboard

SPF = 1 / 60. # inverse FPS (frame-per-second)

defaults = {
	"color_palette": (0xFFFFFF, 0x999999, 0x555555, 0x000000),
	"cgb_color_palette": (
		(0xFFFFFF, 0x7BFF31, 0x0063C5, 0x000000), (0xFFFFFF, 0xFF8484, 0x943A3A, 0x000000),
		(0xFFFFFF, 0xFF8484, 0x943A3A, 0x000000)
	),
	"scale": 3,
	"window": "SDL2",
	"log_level": "ERROR",
}

class PyBoy:
	# gamerom: Filepath to a game-ROM for Game Boy or Game Boy Color.
	# scale: Window scale factor. Doesn't apply to API.
	# bootrom: Filepath to a boot-ROM to use. If unsure, specify `None`.
	# sound: Enable sound emulation and output.
	# sound_emulated: Enable sound emulation without any output. Used for compatibility.
	# cgb: Forcing Game Boy Color mode.
	# log_level: "CRITICAL", "ERROR", "WARNING", "INFO" or "DEBUG"
	# color_palette: Specify the color palette to use for rendering.
	# cgb_color_palette: Specify the color palette to use for rendering in CGB-mode for non-color games	
	def __init__( self, gamerom, *, scale=defaults["scale"], bootrom=None, sound=False, sound_emulated=False, cgb=None, **kwargs):
		self.initialized = False
		kwargs["window"] = defaults["window"]
		kwargs["scale"] = scale
		randomize = kwargs.pop("randomize", False) # Undocumented feature
		# get default parameters
		for k, v in defaults.items():
			if k not in kwargs:
				kwargs[k] = v
		# rom file
		if gamerom is None:
			raise FileNotFoundError(f"None is not a ROM file!")
		if not os.path.isfile(gamerom):
			raise FileNotFoundError(f"ROM file {gamerom} was not found!")
		self.gamerom = gamerom
		# create Motherboard instance
		self.mb = Motherboard(
			gamerom,
			bootrom,
			kwargs["color_palette"],
			kwargs["cgb_color_palette"],
			sound,
			sound_emulated,
			cgb,
			randomize=randomize,
		)

		# Performance measures
		self.avg_pre = 0
		self.avg_tick = 0
		self.avg_post = 0

		# Absolute frame count of the emulation
		self.frame_count = 0

		self.set_emulation_speed(1)
		self.paused = False
		self.events = []
		self.queued_input = []
		self.quitting = False
		self.stopped = False
		self.window_title = "PyBoy"
		self._hooks = {}
		self._plugin_manager = PluginManager(self, self.mb, kwargs)
		self.initialized = True

	def _tick(self, render):
		if self.stopped:
			return False
		t_start = time.perf_counter_ns()
		self._handle_events(self.events)
		t_pre = time.perf_counter_ns()
		if not self.paused:
			self.__rendering(render)
			# Reenter mb.tick until we eventually get a clean exit without breakpoints
			while self.mb.tick():
				pass
			self.frame_count += 1
		t_tick = time.perf_counter_ns()
		self._post_tick()
		t_post = time.perf_counter_ns()
		nsecs = t_pre - t_start
		self.avg_pre = 0.9 * self.avg_pre + (0.1*nsecs/1_000_000_000)
		nsecs = t_tick - t_pre
		self.avg_tick = 0.9 * self.avg_tick + (0.1*nsecs/1_000_000_000)
		nsecs = t_post - t_tick
		self.avg_post = 0.9 * self.avg_post + (0.1*nsecs/1_000_000_000)
		return not self.quitting

	def tick(self, count=1, render=True):
		running = False
		while count != 0:
			_render = render and count == 1 # Only render on last tick to improve performance
			running = self._tick(_render)
			count -= 1
		return running

	def _handle_events(self, events):
		# This feeds events into the tick-loop from the window. There might already be events in the list from the API.
		events = self._plugin_manager.handle_events(events)
		for event in events:
			if event == WindowEvent.QUIT:
				self.quitting = True
			elif event == WindowEvent.RELEASE_SPEED_UP:
				# Switch between unlimited and 1x real-time emulation speed
				self.target_emulationspeed = int(bool(self.target_emulationspeed) ^ True)
				logger.debug("Speed limit: %d", self.target_emulationspeed)
			elif event == WindowEvent.STATE_SAVE:
				with open(self.gamerom + ".state", "wb") as f:
					self.mb.save_state(IntIOWrapper(f))
			elif event == WindowEvent.STATE_LOAD:
				state_path = self.gamerom + ".state"
				if not os.path.isfile(state_path):
					logger.error("State file not found: %s", state_path)
					continue
				with open(state_path, "rb") as f:
					self.mb.load_state(IntIOWrapper(f))
			elif event == WindowEvent.PASS:
				pass # Used in place of None in Cython, when key isn't mapped to anything
			elif event == WindowEvent.PAUSE_TOGGLE:
				if self.paused:
					self._unpause()
				else:
					self._pause()
			elif event == WindowEvent.PAUSE:
				self._pause()
			elif event == WindowEvent.UNPAUSE:
				self._unpause()
			elif event == WindowEvent._INTERNAL_RENDERER_FLUSH:
				self._plugin_manager._post_tick_windows()
			else:
				self.mb.buttonevent(event)

	def _pause(self):
		if self.paused:
			return
		self.paused = True
		self.save_target_emulationspeed = self.target_emulationspeed
		self.target_emulationspeed = 1
		logger.info("Emulation paused!")
		self._update_window_title()

	def _unpause(self):
		if not self.paused:
			return
		self.paused = False
		self.target_emulationspeed = self.save_target_emulationspeed
		logger.info("Emulation unpaused!")
		self._update_window_title()

	def _post_tick(self):
		if self.frame_count % 60 == 0:
			self._update_window_title()
		self._plugin_manager.post_tick()
		self._plugin_manager.frame_limiter(self.target_emulationspeed)

		# Prepare an empty list, as the API might be used to send in events between ticks
		self.events = []
		while self.queued_input and self.frame_count == self.queued_input[0][0]:
			_, _event = heapq.heappop(self.queued_input)
			self.events.append(WindowEvent(_event))

	def _update_window_title(self):
		avg_emu = self.avg_pre + self.avg_tick + self.avg_post
		self.window_title = f"CPU/frame: {(self.avg_pre + self.avg_tick) / SPF * 100:0.2f}%"
		self.window_title += f' Emulation: x{(round(SPF / avg_emu) if avg_emu > 0 else "INF")}'
		if self.paused:
			self.window_title += "[PAUSED]"
		self.window_title += self._plugin_manager.window_title()
		self._plugin_manager._set_title()

	def __rendering(self, value):
		self.mb.lcd.disable_renderer = not value

	def __del__(self):
		self.stop(save=False)

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.stop()

	def stop(self, save=True):
		if self.initialized and not self.stopped:
			logger.info("###########################")
			logger.info("# Emulator is turning off #")
			logger.info("###########################")
			self._plugin_manager.stop()
			self.mb.stop(save)
			self.stopped = True

	def save_state(self, file_like_object):
		if isinstance(file_like_object, str):
			raise Exception("String not allowed. Did you specify a filepath instead of a file-like object?")
		if file_like_object.__class__.__name__ == "TextIOWrapper":
			raise Exception("Text file not allowed. Did you specify open(..., 'wb')?")
		self.mb.save_state(IntIOWrapper(file_like_object))

	def load_state(self, file_like_object):
		if isinstance(file_like_object, str):
			raise Exception("String not allowed. Did you specify a filepath instead of a file-like object?")
		if file_like_object.__class__.__name__ == "TextIOWrapper":
			raise Exception("Text file not allowed. Did you specify open(..., 'rb')?")
		self.mb.load_state(IntIOWrapper(file_like_object))

	def set_emulation_speed(self, target_speed):
		if target_speed > 5:
			logger.warning("The emulation speed might not be accurate when speed-target is higher than 5")
		self.target_emulationspeed = target_speed



