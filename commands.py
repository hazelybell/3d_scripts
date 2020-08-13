#!/usr/bin/env python3

# commands.py -- Model G-code commands
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
from command import Control
from command import NoOp

# These are in the order I added them

class Move(Control):
    code = 'G0'
    def _evolve(self):
        for axis, value in self.aargs.items():
            if axis == 'F':
                self.before.feedrate = value/60.0 # mm/s not mm/m as in gcode!
                self.after.feedrate = value/60.0 # mm/s not mm/m as in gcode!
            else:
                getattr(self.after, axis.lower()).move(value)
        if self.before.feedrate is not None:
            if self.head_dist > 0:
                self.after.time = (
                    self.before.time 
                    + (self.head_dist / self.before.feedrate)
                    )
            else:
                self.after.time = (
                    self.before.time 
                    + (self.head_dist_e / self.before.feedrate)
                    )
        if (
            self.head_dist_z == 0.0
            and self.head_dist_xy is not None
            and self.head_dist_xy > 0
            and self.head_dist_e is not None
            and self.head_dist_e > 0
            ):
            e_xy = self.head_dist_e / self.head_dist_xy
            if (
                self.after.min_e_xy is None
                or self.after.min_e_xy > e_xy
                ):
                self.after.min_e_xy = e_xy
            if (
                self.after.max_e_xy is None
                or self.after.max_e_xy < e_xy
                ):
                self.after.max_e_xy = e_xy

class MoveAlt(Move):
    code = 'G1'

class SetHeadTemp(Control):
    code = 'M109'
    waits = True
    
    def _evolve(self):
        self.after.head_temp = self.S

class PreheatHeadTemp(SetHeadTemp):
    code = 'M104'
    waits = False

class SetBedTemp(Control):
    code = 'M190'
    waits = True
    def _evolve(self):
        self.after.bed_temp = self.S

class PreheatBedTemp(SetBedTemp):
    code = 'M140'
    waits = False

class SetOffset(Control):
    code = 'G92'
    def _evolve(self):
        for axis, value in self.aargs.items():
            getattr(self.after, axis.lower()).set_offset(value)
            

class Informational(NoOp):
    pass

class Ignored(Control):
    def _evolve(self):
        pass

class ReportTemps(Informational):
    code = 'M105'

class AbsoluteE(Control):
    code = 'M82'
    def _evolve(self):
        self.after.e.relative = False

class SetFeedrateMult(Control):
    code = 'M220'
    def _evolve(self):
        self.after.feedrate_mult = self.S/100

class SetFlowMult(Control):
    code = 'M221'
    def _evolve(self):
        self.after.flowrate_mult = self.S/100

class Home(Control):
    code = 'G28'
    def _evolve(self):
        self.after.x.position = 0.0
        self.after.y.position = 0.0
        self.after.z.position = 0.0

class AutoBedLevel(Home):
    code = 'G29'

class Park(Control):
    code = 'G27'
    def _evolve(self):
        self.after.x.position = None
        self.after.y.position = None
        self.after.z.position = None

class BedLevelingState(Ignored):
    code = 'M420'

class LinearAdvanceFactor(Control):
    code = 'M900'
    def _evolve(self):
        self.after.la_k = self.K

class FanOff(Control):
    code = 'M107'
    def _evolve(self):
        self.after.fan_speed = 0.0

class SetTypeAccel(Control):
    code = 'M204'
    def _evolve(self):
        for axis, value in self.aargs.items():
            if axis == 'S':
                self.after.print_accel = value
                self.after.retract_accel = value
                self.after.travel_accel = value
            elif axis == 'P':
                self.after.print_accel = value
            elif axis == 'R':
                self.after.retract_accel = value
            elif axis == 'T':
                self.after.travel_accel = value
            else:
                raise ParseError()

class SetJerk(Control):
    code = 'M205'
    def _evolve(self):
        for axis, value in self.aargs.items():
            getattr(self.after, axis.lower()).jerk = value

class SetAxisAccel(Control):
    code = 'M201'
    def _evolve(self):
        for axis, value in self.aargs.items():
            if axis == 'F':
                self.after.frequency_limit = value
            else:
                getattr(self.after, axis.lower()).accel_limit = value

class SetFan(Control):
    code = 'M106'
    def _evolve(self):
        self.after.fan_speed = self.S/255

class Relative(Control):
    code = 'G91'
    def _evolve(self):
        for axis in self.after.axes:
            axis.relative = True

class Absolute(Control):
    code = 'G90'
    def _evolve(self):
        for axis in self.after.axes:
            axis.relative = True

class DisableSteppers(Control):
    code = 'M84'
    def _evolve(self):
        self.after.steppers = False
        self.after.homed = False

class SetAxisFeedrateLimit(Control):
    code = 'M203'
    def _evolve(self):
        for axis, value in self.aargs.items():
            getattr(self.after, axis.lower()).speed_limit = value
