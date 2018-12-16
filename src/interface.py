import os
import os.path
import subprocess
import sys
import time
from multiprocessing import Process
from . import SAVES, DUMP


# Help message.
HELP = """\
Usage:  [OPTIONS]  frequency

Option        Meaning
 -h, --help    Show this message
 -c <channel>  HDFM channel, for stations with subchannels (default = 1)
 -p <ppm>      PPM error correction (default = 0)
 -s <dir>      Directory to do_save weather and traffic images to (default = none)
 -l <1-3>      Log level output from nrsc5 (default = 3, only debug info)
 -a <null>     Display album/station art
"""


# NRSC5 management.
class NRSC5(Process):
    def __init__(self):
        super().__init__()
        # NRSC5 arguments.
        self.channel = 0
        self.ppm = 0
        self.log = 3
        self.freq = None
        self.dump_dir = DUMP
        # Command/arg list.
        self.cmd_args = None

    # Format command/argument list.
    def format_cmd(self):
        self.cmd_args = [
            'nrsc5',
            '-l',
            str(self.log),
            '-p',
            str(self.ppm),
            '--dump-aas-files',
            self.dump_dir,
            str(self.freq),
            str(self.channel)
        ]

    # Format command and run.
    def run(self):
        self.format_cmd()
        subprocess.call(self.cmd_args)


# User interface management (CLI).
class UserInterface:
    nrsc5: NRSC5
    # Halt program status code.
    HALT = 1
    # Success code.
    SUCCESS = 0

    def __init__(self, nrsc5):
        # NRSC5 management object.
        self.nrsc5 = nrsc5
        # Operations for each command line option.
        self.option_map = {
            '-c': self.channel,
            '-p': self.ppm,
            '-l': self.log,
            '-a': self.art_set,
            '-s': self.save_dir_set
        }
        # Whether album art should be displayed.
        self.art = False
        # Directory where weather/traffic maps should be saved.
        self.save_dir = SAVES
        self.do_save = False

    # Print help.
    @staticmethod
    def help():
        print(HELP)

    # Determine whether a string represents an integer.
    @staticmethod
    def repr_int(val):
        try:
            int(val)
            return True
        except ValueError:
            return False

    # Determine whether a string represents a float.
    @staticmethod
    def repr_float(val):
        try:
            float(val)
            return True
        except ValueError:
            return False

    # Add channel argument to NRSC5 args.
    def channel(self, arg):
        # Validate channel.
        if not UserInterface.repr_int(arg):
            print('Error: Invalid channel (0 - 3)')
            return False
        channel = int(arg)
        if channel < 0 or channel > 3:
            print('Error: Invalid channel (0 - 3)')
            return False
        # Set NRSC5 arg.
        self.nrsc5.channel = channel
        return True

    # Process frequency.
    def frequency(self, arg):
        # Validate.
        if not UserInterface.repr_float(arg):
            print('Error: Invalid frequency')
            return False
        freq = float(arg)
        if freq < 88 or freq > 108:
            print('Error: Frequency out of range (88.0 - 108.0)')
            return False
        self.nrsc5.freq = freq
        return True

    # Handle ppm argument.
    def ppm(self, arg):
        # Validate.
        if not UserInterface.repr_int(arg):
            print('Error: Invalid PPM argument')
            return False
        self.nrsc5.ppm = int(arg)
        return True

    # Handle log level arg.
    def log(self, arg):
        # Validate input.
        if not UserInterface.repr_int(arg):
            print('Error: Invalid log level (1 - 3)')
            return False
        level = int(arg)
        if level < 1 or level > 3:
            print('Error: Invalid log level (1 - 3)')
            return False
        self.nrsc5.log = level
        return True

    # Set save directory.
    def save_dir_set(self, arg):
        # Validate directory.
        if not os.path.isdir(arg):
            print('Error: Invalid directory')
            return False
        self.save_dir = arg
        self.do_save = True
        return True

    # Set whether or not album art should be saved.
    def art_set(self, arg):
        # Handle the arg.
        self.art = True
        return True

    # Process arguments inputted to the main script.
    def process(self, args):
        # Print help and exit if in args.
        if '-h' in args or '--help' in args:
            self.help()
            return self.HALT
        # Handle no args.
        if len(args) == 1:
            print('Error: No frequency specified')
            return self.HALT
        # Process last argument, which should be the frequency, exiting if there is an error.
        rc = self.frequency(args[-1])
        if not rc:
            return self.HALT
        # Process all args other.
        length = len(args)
        for i in range(length):
            if args[i][0] != '-':
                continue
            # Do not process a flag at the end (should be frequency).
            if i < length - 1:
                rc = self.option_map[args[i]](args[i + 1])
                if not rc:
                    return self.HALT
        return self.SUCCESS


if __name__ == '__main__':
    nrsc5 = NRSC5()
    ui = UserInterface(nrsc5)
    ui.process(sys.argv)

    nrsc5_args = 'NRSC5: {0}, {1}, {2}, {3}; {4}'.format(
        nrsc5.channel,
        nrsc5.ppm,
        nrsc5.log,
        nrsc5.freq,
        nrsc5.cmd_args
    )
    ui_args = 'UI: {0}, {1}, {2}'.format(
        ui.art,
        ui.save_dir,
        ui.do_save
    )
    print(nrsc5_args)
    print(ui_args)

    nrsc5.format_cmd()
    nrsc5.start()
    time.sleep(100)
