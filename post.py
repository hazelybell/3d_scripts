#!/usr/bin/env python3

# post.py -- G-code post-processor
# Copyright (C) 2020 Hazel Victoria Campbell

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import logging
logger = logging.getLogger(__name__)
DEBUG = logger.debug
INFO = logger.info
WARNING = logger.warning
ERROR = logger.error
CRITICAL = logger.critical

import argparse

from script import Script
from smooth import Smooth

def main():
    arguments = argparse.ArgumentParser(
        description='Post-process g-code script file'
        )
    arguments.add_argument(
        'input', 
        metavar='input.gcode',
        type=str,
        help="Input gcode filename"
        )
    arguments.add_argument(
        '--reorder-retract',
        action='store_true',
        help="Move retracts to before non-printing moves (Cura)"
        )
    arguments.add_argument(
        '--wipe-speed',
        type=float,
        help="(mm/s)",
        default=1
        )
    arguments.add_argument(
        '--max-command-rate',
        type=float,
        help='(commands/s)',
        default=100,
        )
    arguments.add_argument(
        '--smooth-corners',
        type=float,
        metavar='JUNCTION_DEVIATION',
        help='(mm) (0 disables) (default: 0)',
        default=0,
        )
    args = arguments.parse_args()
    logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)
    script = Script.from_file(args.input)
    if args.reorder_retract:
        raise NotImplementedError()
        script = ReorderRetract(script, args.wipe_speed)
    if args.smooth_corners > 0:
        script = Smooth(script,
                        args.smooth_corners,
                        args.max_command_rate,
                        )

if __name__ == '__main__':
    main()

