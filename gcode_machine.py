#!/usr/bin/env python3

# gcode_machine.py -- GCode Interpreter that doesn't understand many cmds
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

#@state_machine
#class PrintPhase:
    #@unique
    #class States(Enum):
        #BEGIN = 'BEGIN'
        #PRINTING = 'PRINTING'
        #END = 'END'
    
    #def reset(self):
        #self.state = self.BEGIN
        #self.last_command = '; no last command (top of file)'
    
    #def __init__(self):
        #self.reset()
    
    #@transition()
    #def begin_or_end(self, command):
        #if self.state == self.BEGIN:
            #self.state = self.BEGIN
            #self.last_command = command
        #elif self.state == self.PRINTING:
            #self.state = self.END
            #self.last_command = command
        #elif self.state == self.END:
            #self.state = self.END
            #self.last_command = command
        #else:
            #raise RuntimeError("Logic error?")
    
    #def begin(self, command):
        #if self.state == self.BEGIN:
            #self.state = self.BEGIN
            #self.last_command = command
        #elif self.state == self.PRINTING or self.state == self.END:
            #raise ValueError(
                #f"Setup command after command only allowed at"
                #f"beginning of gcode.\n"
                #f"Last {self.state} command: {self.last_command}\n"
                #f"Setup command: {command}"
                #)
        #else:
            #raise RuntimeError("Logic error?")
    
    #def end(self, command):
        #if self.state == self.END or self.state == self.PRINTING:
            #self.state = self.END
            #self.last_command = command
        #elif self.state == self.BEGIN:
            #raise ValueError(
                #f"Finish command after command only allowed at"
                #f"end of gcode. Didn't print anything?'\n"
                #f"Last {self.state} command: {self.last_command}\n"
                #f"Finish command: {command}"
                #)
        #else:
            #raise RuntimeError("Logic error?")

    #def materialized(self, command):
        #if self.state == self.BEGIN or self.state == self.END:
            #self.state = self.PRINTING
            #self.last_command = command
        #elif self.state == self.END:
            #raise ValueError(
                #f"Printing command after command only allowed at"
                #f"beginning or end of gcode.\n"
                #f"Last {self.state} command: {self.last_command}\n"
                #f"Print command: {command}"
                #)
        #else:
            #raise RuntimeError("Logic error?")

from enum import Enum
from enum import unique

from state_machine import state_machine
from state_machine import transition
from java_envy import globalize
from gcode import top

