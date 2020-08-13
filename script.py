#!/usr/bin/env python3

# script.py -- G-code script model
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

import logging
logger = logging.getLogger(__name__)
DEBUG = logger.debug
INFO = logger.info
WARNING = logger.warning
ERROR = logger.error
CRITICAL = logger.critical

from machine_state import MachineState
from command import parse

class Script:
    def __init__(self, script=None):
        if script is None:
            self.commands = None
            self.file_name = None
        else:
            self.commands = list(script.commands)
            self.file_name = script.file_name
    
    @classmethod
    def from_file(cls, file_name):
        INFO(f"Parsing {file_name}")
        with open(file_name, 'r') as fh:
            commands = list(map(parse, map(str.rstrip, fh)))
        for i in range(len(commands)):
            assert commands[i].oln is None
            commands[i].oln = i+1
            commands[i].ln = i+1
        INFO(f"Parsed {commands[-1].ln} commands")
        new = cls()
        new.commands = commands
        new.file_name = file_name
        return new
    
    def analyze_one(self, command):
        try:
            self.state = command.evolve(self.state)
        except:
            CRITICAL(f"Analysis error: {self.file_name}:{self.ci+1}")
            CRITICAL(f"    {command.g_code}")
            raise
    
    def analyze(self):
        INFO(f"Analyzing {self.file_name}")
        self.state = MachineState()
        for ci in range(len(self.commands)):
            self.ci = ci
            command = self.commands[ci]
            self.analyze_one(command)
            if ci > 0:
                assert self.commands[ci-1].after is self.commands[ci].before
        del self.ci
