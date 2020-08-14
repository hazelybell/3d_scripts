#!/usr/bin/env python3

# index.html - sin color animation
# Copyright &copy; 2020 Hazel Victoria Campbell

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

from math import sin, pi

r_start = 0xff
g_start = 0x3f
b_start = 0xff

r_end = 0x0
g_end = 0x0
b_end = 0x0

steps = 10

for i in range(steps+1):
    pct = int(i/steps*100)
    c = sin(pi/2*i/steps)
    r = int(r_start * c + r_end * (1 - c))
    g = int(g_start * c + g_end * (1 - c))
    b = int(b_start * c + b_end * (1 - c))
    print(f"{pct}% {'{'} color: #{r:02x}{g:02x}{b:02x}; {'}'}")
