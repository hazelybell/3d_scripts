#!/usr/bin/env python3

# machine_state.py -- State of 3-D printer
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

import numpy

class Axis:
    def reset(self):
        self.relative = None
        self.position = None
        self.offset = 0.0
        self.min = None
        self.max = None
        self.accel_limit = None
        self.speed_limit = None
    
    def __init__(self, other=None):
        if other is None:
            self.reset()
        else:
            self.__dict__.update(other.__dict__)
    
    def set_offset(self, off):
        if self.position is None:
            self.offset = 0.0 - off
        else:
            self.offset = self.position - off
    
    def relative_move(self, amount):
        self.position += amount
    
    def absolute_move(self, amount):
        self.position = self.offset + amount
    
    def move(self, amount):
        if self.relative:
            self.relative_move(amount)
        else:
            self.absolute_move(amount)
        if self.min is None or self.position < self.min:
            self.min = self.position
        if self.max is None or self.position > self.max:
            self.max = self.position
        assert self.max >= self.min
    
class MachineState:
    def reset(self):
        self.x = Axis()
        self.y = Axis()
        self.z = Axis()
        self.e = Axis()
        self.time = 0.0 # seconds
        self.layer = None
        self.retracted = False
        self.lifted = False
        self.bed_temp = None
        self.head_temp = None
        self.feedrate_mult = 1.0
        self.flowrate_mult = 1.0
        self.la_k = None
        self.feedrate = None # mm/s not mm/m as in gcode!
        self.fan_speed = None
        self.print_accel = None
        self.retract_accel = None
        self.travel_accel = None
        self.steppers = True
        self.homed = False
        self.max_e_xy = None
        self.min_e_xy = None
        self.frequency_limit = None

    def __init__(self, other=None):
        if other is None:
            self.reset()
        else:
            self.__dict__.update(other.__dict__)
            self.x = Axis(other.x)
            self.y = Axis(other.y)
            self.z = Axis(other.z)
            self.e = Axis(other.e)

    @property
    def axes(self):
        return [self.x, self.y, self.z, self.e]
    
    @property
    def position(self):
        return [
            self.x.position,
            self.y.position,
            self.z.position,
            self.e.position
            ]
    
    @property
    def pos_vec(self):
        if (
            self.x.position is None
            or self.y.position is None
            or self.z.position is None
            or self.e.position is None
            ):
            return None
        return numpy.array((
            self.x.position,
            self.y.position,
            self.z.position,
            self.e.position,
            ))

    @property
    def pos_vec_xyz(self):
        if (
            self.x.position is None
            or self.y.position is None
            or self.z.position is None
            ):
            return None
        return numpy.array((
            self.x.position,
            self.y.position,
            self.z.position,
            ))

    @property
    def pos_vec_xy(self):
        if (
            self.x.position is None
            or self.y.position is None
            ):
            return None
        return numpy.array((
            self.x.position,
            self.y.position,
            ))

    @property
    def loc_vec(self):
        if (
            self.x.position is None
            or self.y.position is None
            or self.z.position is None
            or self.e.position is None
            or self.time is None
            ):
            return None
        return numpy.array((
            self.x.position,
            self.y.position,
            self.z.position,
            self.e.position,
            self.time
            ))
