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
steps = int(sys.argv[4])

gcode = None

with open(input_file, 'r') as fh:
    gcode = list(fh)

gcode = list(map(str.rstrip, gcode))

SET_TEMP = 'M109'
PREHEAT = 'M104'
MOVE = 'G1'
VERTICAL_AXIS = 'Z'
DWELL = 'G4 P' + str(1000 * 5) # in ms

output_file = '.temptower.'.join(
    input_file.rsplit('.', 1)
    )

print(f"Saving output to {output_file}")

fh = open(output_file, 'w')

comment = re.compile(r';.*')

def nocomment(line):
    r = comment.sub('', line)
    return r

height = 0

for line in gcode:
    args = nocomment(line).split()
    if len(args) == 0:
        continue
    command = args.pop(0)
    if command == MOVE:
        for arg in args:
            if arg.startswith(VERTICAL_AXIS):
                height = max(height, float(arg.replace(VERTICAL_AXIS, '')))

step_size = height / steps

print(f"Height: {height}")
print(f"Step size: {step_size}")

cur_step = 0
cur_height = 0
temp_range = float(end_temp - start_temp)
temp_step = temp_range/(steps-1)

print(f"Temperature step: {temp_step}")

def cur_temp():
    return int(
        start_temp + temp_step * (
            max(min(cur_step, steps), 0)
            )
        )

def cur_step_limit():
    return (cur_step + 1) * step_size

def output(command):
    print(command, file=fh)

def override(old, new):
    output(f"; overriden by temptower.py: {old}")
    output(f"{new} ; override")

def insert(new):
    output(f"{new} ; added by temptower.py")

def set_temp_command():
    return f"{SET_TEMP} S{cur_temp()}"

def dwell():
    insert(DWELL)

def set_temp():
    insert(set_temp_command())
    dwell()
    
def maybe_insert_temp():
    global cur_step
    if cur_height > cur_step_limit():
        cur_step += 1
        print(f"Step {cur_step} at height {cur_height} temp {cur_temp()}")
        output(f"; temptower.py: height {cur_height}")
        output(f"; temptower.py: step {cur_step}")
        output(f"; temptower.py: temp {cur_temp()}")
        set_temp()
    
for line in gcode:
    args = nocomment(line).split()
    if len(args) == 0:
        output(line)
        continue
    command = args.pop(0)
    if command == MOVE:
        output(line)
        for arg in args:
            if arg.startswith(VERTICAL_AXIS):
                cur_height = max(cur_height, float(arg.replace(VERTICAL_AXIS, '')))
                #print(f"Height: {cur_height}")
                maybe_insert_temp()
    elif command == PREHEAT:
        print(f"Temp: {cur_temp()}")
        override(line, f"{PREHEAT} S{cur_temp()}")
    elif command == SET_TEMP:
        print(f"Temp: {cur_temp()}")
        override(line, f"{SET_TEMP} S{cur_temp()}")
    else:
        output(line)

fh.close()
del fh

print(f"{output_file} is ready to be printed.")

assert cur_step == steps - 1
