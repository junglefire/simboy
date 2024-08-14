# -*- coding: utf-8 -*- 
#!/usr/bin/env python
import logging as logger
import click

from pyboy import PyBoy

# parse command line
@click.command()
@click.option('--rom-file', type=str, required=True, default='rom/s_mario.gbc', help='rom file')
@click.option('--debug', type=bool, required=False, is_flag=True, help='print debug log information')
def main(rom_file: str, debug: bool) -> None:
	if debug:
		logger.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logger.DEBUG)
	else:
		logger.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logger.INFO)
	# Application
	pyboy = PyBoy(rom_file, sound=True)
	while pyboy.tick():
		pass
	pyboy.stop()	

if __name__ == "__main__":
	main()
