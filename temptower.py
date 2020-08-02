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

EXTRA_Z_HOP = 0
SLOW_E_MM = -1 # disable for now
SLOW_XY_RATE = 2*60 # in mm per minute for some reason
SLOW_BEFORE = 'retract' # retract or any

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

class LineAnalysis:
    def __init__(self, position):
        self.start = list(position)
        self.delta = [0, 0, 0, 0]
        self.end = list(position)

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
        z = self.position[2]
        if z not in self.layers:
            #print(f"Layer @ z={z}")
            self.layers.append(z)
        self.retracted = False
        self.z_up = False
        if self.has_retracted:
            self.retracting = True
    
    def retract(self):
        self.has_retracted = True
        self.retracted = True
        steps_back = 1
        extrusion_back = 0
        while self.line_number - steps_back >= 0:
            history_number = self.line_number - steps_back
            history = self.new_analysis[history_number]
            if (not hasattr(history, 'retract')) or history.retract:
                #print(f"rewound {steps_back}")
                break
            history.steps_to_retract = steps_back
            history.e_to_retract = extrusion_back
            extrusion_back += history.delta[3]
            steps_back += 1
        self.extruder_pause()
    
    def z_hop(self):
        self.z_up = True
    
    def z_lift(self):
        if self.retracted:
            self.z_hop()
    
    def detect_retract(self):
        if self.position[3] is None:
            self.line_analysis.retract = False
            return
        if not hasattr(self, 'prev_e') or self.prev_e is None:
            self.prev_e = self.position[3]
        if self.position[3] < self.prev_e:
            self.line_analysis.retract = True
            self.retract()
        else:
            self.line_analysis.retract = False
        self.prev_e = self.position[3]
    
    def move_axis(self, axis, number):
        if self.position[axis] is None:
            self.position[axis] = 0
            self.line_analysis.start[axis] = 0
        if self.is_relative:
            self.position[axis] += number
            self.line_analysis.delta[axis] = number
            self.line_analysis.end = list(self.position)
        else:
            self.line_analysis.start = list(self.position)
            self.position[axis] = self.offset[axis] + number
            self.line_analysis.end = list(self.position)
            self.line_analysis.delta[axis] = (
                self.line_analysis.end[axis]
                - self.line_analysis.start[axis]
                )
        if self.max[axis] == None or self.position[axis] > self.max[axis]:
            self.max[axis] = self.position[axis]
            if axis == self.E_AXIS:
                self.materialized()
            if axis == 2:
                self.z_lift()
        if self.min[axis] == None or self.position[axis] < self.min[axis]:
            self.min[axis] = self.position[axis]
        if axis == 2 and number < 0:
            self.z_up = False
            self.z_hopping = True
    
    def extruder_pause(self):
        steps_back = 1
        extrusion_back = 0
        while self.line_number - steps_back >= 0:
            history_number = self.line_number - steps_back
            history = self.new_analysis[history_number]
            if history.delta[3] == 0:
                break
            history.steps_to_e_pause = steps_back
            history.e_to_pause = extrusion_back
            extrusion_back += history.delta[3]
            steps_back += 1
    
    def check_extruder_pause(self):
        if self.line_analysis.delta[3] == 0:
            self.extruder_pause()
    
    def move(self, command, args, comment=''):
        for arg in args:
            if arg[0] == 'F':
                self.feedrate = float(arg[1:])
            else:
                try:
                    axis = self.AXES.index(arg[0])
                except ValueError: # ignore unknown axis
                    return
                else:
                    self.move_axis(axis, float(arg[1:]))
        if hasattr(self, 'feedrate'):
            self.line_analysis.feedrate = self.feedrate
        self.detect_retract()
    
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
    
    def reset(self):
        self.is_relative = False
        self.max = [0, 0, 0, 0]
        self.min = [0, 0, 0, 0]
        self.material_max = [0, 0, 0]
        self.material_min = [0, 0, 0]
        self.position = [None, None, None, None]
        self.offset = [0, 0, 0, 0]
        self.layers = []
        self.has_retracted = False
        self.retracted = False
        self.z_up = False
        self.next_line = 0
        self.prev_e = None
        self.new_analysis = []
    
    def __init__(self, gcode):
        self.gcode = list(gcode)
        self.commands = {
            k: getattr(self, v.__name__) for k, v in self.commands.items()
            }
        self.reset()
        self.ran_once = False
    
    def run_line(self, line):
        if len(self.new_analysis) <= self.line_number:
            self.new_analysis.append(LineAnalysis(
                self.position
                ))
        self.line_analysis = self.new_analysis[self.line_number]
        if ';' in line:
            (code, comment) = line.split(';', 1)
        else:
            code = line
            comment = ''
        args = code.split()
        if len(args) == 0:
            self.comment(line)
        else:
            command = args.pop(0)
            if command in self.commands:
                self.commands[command](command, args, comment)
            else:
                self.unimplemented(command, args, comment)
        self.check_extruder_pause()
    
    def step(self):
        self.line_number = self.next_line
        line = self.gcode[self.line_number]
        self.run_line(line)
        del self.line_number
        self.next_line += 1
        
    def end_default(self, attr, value):
        if not hasattr(self, attr):
            setattr(self, attr, value)

    def end(self):
        self.end_default('z_hopping', False)
        self.end_default('retracting', False)
        self.bounding_max = self.material_max
        self.bounding_min = self.material_min
        self.ran_once = True
        self.analysis = self.new_analysis
        
    def run(self):
        self.next_line = 0
        while self.next_line < len(self.gcode):
            self.step()
        self.end()

class Mutator(Machine):
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

    def move(self, command, args, comment=''):
        self.echo(command, args, comment)
        super().move(command, args, comment)
    
    def setoff(self, command, args, comment=''):
        super().setoff(command, args, comment)
        self.echo(command, args, comment)

    def dwell(self, command, args, comment=''):
        super().dwell(command, args, comment)
        self.echo(command, args, comment)
    
    def comment(self, line):
        super().comment(line)
        if self.outputting:
            self.output(line)

    def unimplemented(self, command, args, comment=''):
        super().unimplemented(command, args, comment)
        self.echo(command, args, comment)

    def absolute(self, command, args, comment=''):
        super().absolute(command, args, comment)
        self.echo(command, args, comment)

    def relative(self, command, args, comment=''):
        super().relative(command, args, comment)
        self.echo(command, args, comment)

    def insert(self, new):
        self.output(f"{new} ; added by temptower.py")
    
    @property
    def outputting(self):
        return hasattr(self, 'fh')
    
    def generate(self, output_file):
        print(f"Saving output to {output_file}")
        self.fh = open(output_file, 'w')
        self.run()
        self.fh.close()
        del self.fh
        print(f"{output_file} is ready to be printed.")

    def output(self, command):
        print(command, file=self.fh)
    
class ExtrusionDecelerator(Mutator):
    def modify_move(self, command, args, comment, feedrate):
        found_f = False
        new_args = list()
        for argi in range(len(args)):
            arg = args[argi]
            if arg[0] == 'F':
                found_f = True
                arg = f"F{feedrate:0.5}"
            new_args.append(arg)
        if not found_f:
            new_args.append(f"F{feedrate:0.5}")
        super().move(command, new_args, comment)

    def maybe_modify_move(self, command, args, comment):
        line_analysis = self.analysis[self.line_number]
        if hasattr(line_analysis, 'feedrate'):
            self.old_feedrate = line_analysis.feedrate
        modifies_feedrate = False
        moves_head = False
        extrudes = False
        for arg in args:
            if arg[0] == 'F':
                modifies_feedrate = True
            elif arg[0] == 'X' or arg[0] == 'Y' or arg[0] == 'Z':
                moves_head = True
            elif arg[0] == 'E':
                extrudes = True
        if (
            SLOW_BEFORE == 'any'
            and line_analysis.delta[3] > 0
            and hasattr(line_analysis, 'e_to_pause')
            and line_analysis.e_to_pause <= SLOW_E_MM
            and hasattr(line_analysis, 'feedrate')
            and line_analysis.feedrate is not None
            and line_analysis.feedrate > SLOW_XY_RATE
            and moves_head
            ):
            new_feedrate = (
                self.old_feedrate * line_analysis.e_to_pause
                + SLOW_XY_RATE * (SLOW_E_MM - line_analysis.e_to_pause)
                ) / SLOW_E_MM
            if self.outputting:
                self.output(f"; feedrate: old: {self.old_feedrate/60} mm/s new: {new_feedrate/60} mm/s")
            self.modify_move(command, args, comment, new_feedrate)
        elif (
            SLOW_BEFORE == 'retract'
            and line_analysis.delta[3] > 0
            and hasattr(line_analysis, 'e_to_retract')
            and line_analysis.e_to_retract <= SLOW_E_MM
            and hasattr(line_analysis, 'feedrate')
            and line_analysis.feedrate is not None
            and line_analysis.feedrate > SLOW_XY_RATE
            and moves_head
            ):
            new_feedrate = (
                self.old_feedrate * line_analysis.e_to_retract
                + SLOW_XY_RATE * (SLOW_E_MM - line_analysis.e_to_retract)
                ) / SLOW_E_MM
            if self.outputting:
                self.output(f"; feedrate: old: {self.old_feedrate/60} mm/s new: {new_feedrate/60} mm/s")
            self.modify_move(command, args, comment, new_feedrate)
        elif (
            hasattr(self, 'old_feedrate')
            and self.old_feedrate != self.feedrate
            and not modifies_feedrate
            and moves_head
            ):
            self.modify_move(command, args, comment, self.old_feedrate)
        else:
            super().move(command, args, comment)
    
    def move(self, command, args, comment=''):
        if hasattr(self, 'analysis') and self.outputting:
            self.maybe_modify_move(command, args, comment)
        else:
            super().move(command, args, comment='')

class TemperatureTower(ExtrusionDecelerator):
    def set_temp(self, command, args, comment = ''):
        if len(self.layers) > 1:
            self.overriden(command, args, comment)
            if hasattr(self, 'fh'):
                self.insert_set_temp()
        else:
            self.echo(command, args, comment)
    
    def preheat(self, command, args, comment = ''):
        if len(self.layers) > 1:
            self.overriden(command, args, comment)
            if hasattr(self, 'fh'):
                self.insert_set_temp()
        else:
            self.echo(command, args, comment)
    
    def z_lift(self):
        if self.ran_once and not self.retracting and not self.z_hopping:
            self.maybe_insert_temp()
    
    def retract(self):
        super().retract()
        self.echo('', [], f"Retract {self.prev_e}-{self.position[3]}")
        if self.ran_once and self.retracting and not self.z_hopping:
            self.maybe_insert_temp()
    
    def z_hop(self):
        super().z_hop()
        self.echo('', [], "Z-hop")
        if self.ran_once and self.z_hopping:
            assert self.retracted
            assert self.z_up
            self.maybe_insert_temp()
    
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
        self.reset()
        if self.retracting:
            print(f"Filament retracting: {self.retracting}")
        if self.z_hopping:
            print(f"Z-hopping (Z-lift): {self.z_hopping}")
        assert hasattr(self, 'retracting')
        assert hasattr(self, 'bounding_max')
        self.tower_height = self.bounding_max[2]
        self.floor_size = self.tower_height / floors
        print(f"Height: {self.tower_height}")
        print(f"Floor height: {self.floor_size}")
        assert self.tower_height > 0
        self.cur_floor = 0
        self.start_temp = start_temp
        self.end_temp = end_temp
        self.floors = floors
        self.temp_has_been_overriden = False
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

    def set_temp_command(self,):
        return f"M104 S{self.cur_temp}"
        # Using R instead of S here in case of cooling direction
        # return f"M109 R{self.cur_temp}"

    def insert_dwell(self):
        self.insert('G4 P5000')

    def insert_set_temp(self):
        if EXTRA_Z_HOP:
            assert not self.is_relative
            self.echo(
                'G1',
                [f"Z{self.position[2] + EXTRA_Z_HOP}"],
                "Extra z-lift (z-hop) to prevent pooling"
                )
        self.insert(self.set_temp_command())
        #self.insert_dwell()
        if EXTRA_Z_HOP:
            assert not self.is_relative
            self.echo(
                'G1',
                [f"Z{self.position[2]}"],
                "Undo extra nozzle lift"
                )
        self.temp_has_been_overriden = True
    
    def maybe_insert_temp(self):
        if not self.outputting:
            return
        if self.cur_height > self.cur_floor_limit or (
            len(self.layers) > 1 and not self.temp_has_been_overriden
            ):
            if self.cur_height > self.cur_floor_limit:
                self.cur_floor += 1
            print(f"Step {self.cur_floor} at height {self.cur_height} temp {self.cur_temp}")
            self.output(f"; temptower.py: height {self.cur_height}")
            self.output(f"; temptower.py: step {self.cur_floor}")
            self.output(f"; temptower.py: temp {self.cur_temp}")
            self.insert_set_temp()
            self.insert(f"M117 Tower Floor {self.cur_floor+1}/{self.floors}")
    
    def generate(self, output_file):
        super().generate(output_file)
        print(f"{self.cur_floor} {self.floors}")
        assert self.cur_floor == self.floors - 1

temp_tower = TemperatureTower(gcode, start_temp, end_temp, floors)
temp_tower.generate(output_file)

