#!/usr/bin/env python3

# temptower.py -- Add temperature changes to temperature tower gcode
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

"""
Usage: ./temptower.py <input.gcode> <start_temp> <end_temp> <sections>
Usage: ./temptower.py Temp_Tower.gcode 180 230 8
"""

import sys
import os
import re

assert os.path.exists(sys.argv[1])
input_file = sys.argv[1]
start_temp = int(sys.argv[2])
end_temp = int(sys.argv[3])
assert start_temp < end_temp
floors = int(sys.argv[4])

gcode = None

with open(input_file, 'r') as fh:
    gcode = list(fh)

gcode = list(map(str.rstrip, gcode))

DWELL_TIME_MS = 1000 * 5


output_file = '.temptower.'.join(
    input_file.rsplit('.', 1)
    )


comment = re.compile(r';.*')

def nocomment(line):
    r = comment.sub('', line)
    return r

height = 0

class Machine:
    def set_temp(self, command, args, comment=''):
        pass
    
    def preheat(self, command, args, comment=''):
        pass
    
    def materialized(self):
        #print(f"E={self.position[3]} Z={self.position[2]}")
        for axis in range(3):
            if (
                self.material_max[axis] is None
                or self.position[axis] > self.material_max[axis]
                ):
                self.material_max[axis] = self.position[axis]
            if (
                self.material_min[axis] is None
                or self.position[axis] < self.material_min[axis]
                ):
                self.material_min[axis] = self.position[axis]
    
    def move_axis(self, axis, number):
        if self.is_relative:
            if self.position[axis] is None:
                self.position[axis] = 0
            self.position[axis] += number
        else:
            self.position[axis] = self.offset[axis] + number
        if self.max[axis] == None or self.position[axis] > self.max[axis]:
            self.max[axis] = self.position[axis]
            if axis == self.E_AXIS:
                self.materialized()
        if self.min[axis] == None or self.position[axis] < self.min[axis]:
            self.min[axis] = self.position[axis]
    
    def move(self, command, args, comment=''):
        for arg in args:
            try:
                axis = self.AXES.index(arg[0])
            except ValueError: # ignore unknown axis
                return
            else:
                self.move_axis(axis, float(arg[1:]))
    
    def offset_axis(self, axis, where):
        if self.position[axis] is None:
            self.offset[axis] = 0 - where
        else:
            self.offset[axis] = self.position[axis] - where
    
    def setoff(self, command, args, comment=''):
        for arg in args:
            try:
                axis = self.AXES.index(arg[0])
            except ValueError: # ignore unknown axis
                return
            else:
                self.offset_axis(axis, float(arg[1:]))
    
    def dwell(self, command, args, comment=''):
        pass
    
    def comment(self, line):
        pass
    
    def unimplemented(self, command, args, comment=''):
        return
        raise NotImplementedError(f"gcode command {command} hasn't been implemented")
    
    def absolute(self, command, args, comment=''):
        self.is_relative = False
    
    def relative(self, command, args, comment=''):
        self.is_relative = True

    commands = {
        'M109': set_temp,
        'M104': preheat,
        'G1': move,
        'G0': move,
        'G5': unimplemented,
        'G6': unimplemented,
        'G90': absolute,
        'G91': relative,
        'G4': dwell,
        'G92': setoff,
        }
    
    AXES = ['X', 'Y', 'Z', 'E']
    E_AXIS = AXES.index('E')

    def __init__(self, gcode):
        self.gcode = list(gcode)
        self.is_relative = False
        self.max = [0, 0, 0, 0]
        self.min = [0, 0, 0, 0]
        self.material_max = [0, 0, 0]
        self.material_min = [0, 0, 0]
        self.position = [None, None, None, None]
        self.offset = [0, 0, 0, 0]
        self.commands = {
            k: getattr(self, v.__name__) for k, v in self.commands.items()
            }
    
    def run_line(self, line):
        if ';' in line:
            (code, comment) = line.split(';', 1)
        else:
            code = line
            comment = ''
        args = code.split()
        if len(args) == 0:
            self.comment(line)
            return
        command = args.pop(0)
        if command in self.commands:
            self.commands[command](command, args, comment)
        else:
            self.unimplemented(command, args, comment)
        
    def run(self):
        for line in self.gcode:
            self.run_line(line)

class TemperatureTower(Machine):
    def deparse(self, command, args, comment = ''):
        words = [command]
        words.extend(args)
        if len(comment) > 0:
            words.append(';')
            words.append(comment)
        return ' '.join(words)
        
    
    def echo(self, command, args, comment = ''):
        if hasattr(self, 'fh'):
            self.output(self.deparse(command, args, comment))
    
    def overriden(self, command, args, comment):
        self.echo('', [], 
                  'overriden by temptower.py: '
                  + self.deparse(command, args, comment)
                  )
    
    def set_temp(self, command, args, comment = ''):
        self.overriden(command, args, comment)
        if hasattr(self, 'fh'):
            self.insert_set_temp()
    
    def preheat(self, command, args, comment = ''):
        self.overriden(command, args, comment)
        if hasattr(self, 'fh'):
            self.insert_set_temp()
    
    def materialized(self):
        super().materialized()
        if hasattr(self, 'fh'):
            self.maybe_insert_temp()
    
    def move(self, command, args, comment=''):
        super().move(command, args, comment)
        self.echo(command, args, comment)
    
    def setoff(self, command, args, comment=''):
        super().setoff(command, args, comment)
        self.echo(command, args, comment)

    def dwell(self, command, args, comment=''):
        super().dwell(command, args, comment)
        self.echo(command, args, comment)
    
    def comment(self, line):
        super().comment(line)
        line = line.replace(';', '', 1)
        line = line.lstrip()
        self.echo('', [], line)

    def unimplemented(self, command, args, comment=''):
        super().unimplemented(command, args, comment)
        self.echo(command, args, comment)

    def absolute(self, command, args, comment=''):
        super().absolute(command, args, comment)
        self.echo(command, args, comment)

    def relative(self, command, args, comment=''):
        super().relative(command, args, comment)
        self.echo(command, args, comment)

    @property
    def cur_height(self):
        return self.material_max[2]
    
    @property
    def temp_range(self):
        return float(self.end_temp - self.start_temp)
    
    @property
    def temp_inc(self):
        return self.temp_range/(self.floors-1)
        
    def __init__(self, gcode, start_temp, end_temp, floors):
        super().__init__(gcode)
        super().run()
        self.bounding_max = self.material_max
        self.bounding_min = self.material_min
        super().__init__(gcode)
        self.tower_height = self.bounding_max[2]
        self.floor_size = self.tower_height / floors
        print(f"Height: {self.tower_height}")
        print(f"Floor height: {self.floor_size}")
        assert self.tower_height > 0
        self.cur_floor = 0
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.floors = floors
        print(f"Temperature change each floor: {self.temp_inc}")

    @property
    def cur_temp(self):
        return int(
            self.start_temp + self.temp_inc * (
                max(min(self.cur_floor, self.floors), 0)
                )
            )
    
    @property
    def cur_floor_limit(self):
        #print(f"{self.cur_floor} {self.floor_size}")
        return (self.cur_floor + 1) * self.floor_size
    
    def output(self, command):
        print(command, file=self.fh)
    
    def insert(self, new):
        self.output(f"{new} ; added by temptower.py")
    
    def set_temp_command(self,):
        # Using R instead of S here in case of cooling direction
        return f"M109 R{self.cur_temp}"

    def insert_dwell(self):
        self.insert('G4 P5000')

    def insert_set_temp(self):
        self.insert(self.set_temp_command())
        self.insert_dwell()
    
    def maybe_insert_temp(self):
        if self.cur_height > self.cur_floor_limit:
            self.cur_floor += 1
            print(f"Step {self.cur_floor} at height {self.cur_height} temp {self.cur_temp}")
            self.output(f"; temptower.py: height {self.cur_height}")
            self.output(f"; temptower.py: step {self.cur_floor}")
            self.output(f"; temptower.py: temp {self.cur_temp}")
            self.insert_set_temp()
            self.insert(f"M117 Tower Floor {self.cur_floor+1}/{self.floors}")
    
    def generate(self, output_file):
        print(f"Saving output to {output_file}")
        self.fh = open(output_file, 'w')
        self.run()
        self.fh.close()
        del self.fh
        print(f"{output_file} is ready to be printed.")
        print(f"{self.cur_floor} {self.floors}")
        assert self.cur_floor == self.floors - 1

temp_tower = TemperatureTower(gcode, start_temp, end_temp, floors)
temp_tower.generate(output_file)

