#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

from pyboy.plugins.window_sdl2 import WindowSDL2 

class PluginManager:
	def __init__(self, pyboy, mb, pyboy_argv):
		self.pyboy = pyboy
		self.window_sdl2 = WindowSDL2(pyboy, mb, pyboy_argv)
		self.window_sdl2_enabled = self.window_sdl2.enabled()

	def gamewrapper(self):
		return None 

	def handle_events(self, events):
		if self.window_sdl2_enabled:
			events = self.window_sdl2.handle_events(events)
		return events

	def post_tick(self):
		# foreach plugins [].post_tick()
		self._post_tick_windows()

	def _set_title(self):
		if self.window_sdl2_enabled:
			self.window_sdl2.set_title(self.pyboy.window_title)
		pass

	def _post_tick_windows(self):
		if self.window_sdl2_enabled:
			self.window_sdl2.post_tick()
		pass

	def frame_limiter(self, speed):
		if speed <= 0:
			return
		if self.window_sdl2_enabled:
			done = self.window_sdl2.frame_limiter(speed)
			if done: return

	def window_title(self):
		title = ""
		if self.window_sdl2_enabled:
			title += self.window_sdl2.window_title()
		return title

	def stop(self):
		if self.window_sdl2_enabled:
			self.window_sdl2.stop()

	def handle_breakpoint(self):
		if self.debug_prompt_enabled:
			self.debug_prompt.handle_breakpoint()
