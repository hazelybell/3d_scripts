#!/usr/bin/env python3

# mutator.py -- G-code script post-processor base class
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

from command import parse
from machine_state import MachineState
from script import Script

class Mutator(Script):
    def keep(self, ci, old):
        assert self.original[old.ln-1] is old
        new = old.copy()
        new.oln = old.oln
        self.commands.append(new)
        self.analyze_one(new)
        
    def replace(self, ci, old, replacements):
        for cj in range(len(replacements)):
            replacements[cj].oln = old.oln
            self.analyze_one(replacements[cj])
        self.commands.extend(replacements)
    
    def process(self):
        INFO(f"Processing: {self.__class__.__name__}")
        for ci in range(len(self.original)):
            self.process_command(ci, self.original[ci])
        for ci in range(len(self.commands)):
            self.commands[ci].ln = ci + 1
        INFO(f"Processed {self.commands[-1].ln} commands")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.analyze()
        self.original = self.commands
        self.commands = []
        self.process()


