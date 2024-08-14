#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

from pyboy.plugins.base_plugin import PyBoyGameWrapper

# imports
from pyboy.plugins.window_sdl2 import WindowSDL2 # isort:skip
from pyboy.plugins.window_open_gl import WindowOpenGL # isort:skip
from pyboy.plugins.window_null import WindowNull # isort:skip
from pyboy.plugins.debug import Debug # isort:skip
from pyboy.plugins.disable_input import DisableInput # isort:skip
from pyboy.plugins.auto_pause import AutoPause # isort:skip
from pyboy.plugins.record_replay import RecordReplay # isort:skip
from pyboy.plugins.rewind import Rewind # isort:skip
from pyboy.plugins.screen_recorder import ScreenRecorder # isort:skip
from pyboy.plugins.screenshot_recorder import ScreenshotRecorder # isort:skip
from pyboy.plugins.debug_prompt import DebugPrompt # isort:skip
from pyboy.plugins.game_wrapper_super_mario_land import GameWrapperSuperMarioLand # isort:skip
from pyboy.plugins.game_wrapper_tetris import GameWrapperTetris # isort:skip
from pyboy.plugins.game_wrapper_kirby_dream_land import GameWrapperKirbyDreamLand # isort:skip
from pyboy.plugins.game_wrapper_pokemon_gen1 import GameWrapperPokemonGen1 # isort:skip
from pyboy.plugins.game_wrapper_pokemon_pinball import GameWrapperPokemonPinball # isort:skip
# imports end


def parser_arguments():
	# yield_plugins
	yield WindowSDL2.argv
	# yield_plugins end
	pass


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
