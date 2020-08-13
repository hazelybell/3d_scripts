#!/usr/bin/env python3

# smooth.py -- Head motion smoothing
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

from math import cos, sin, tan, pi, floor, fabs, acos

import numpy
vdot = numpy.vdot
norm = numpy.linalg.norm
array = numpy.array

import matplotlib.pyplot as plot

from commands import Move
from mutator import Mutator


def vangle(v1, v2):
    return acos(vdot(v1, v2) / (norm(v1) * norm(v2)))

def close_enough(a, b):
    d = fabs(a - b)/fabs(a + b)
    return d < 0.000001 and d > -0.000001

class Smooth(Mutator):
    def __init__(self,
                 script,
                 junction_deviation,
                 command_rate,
                 ):
        self.junction_deviation = junction_deviation
        self.command_rate = command_rate
        self.modified = None
        super().__init__(script)
    
    def process_second(self, old):
        return [old.copy()]
    
    def keep(self, ci, old, cur):
        if cur is old:
            super().keep(ci, old)
        else:
            super().replace(ci, old, [cur])
            self.modified = None
    
    def process_command(self, ci, old):
        if self.modified is not None:
            cur = self.modified
        else:
            cur = old
        
        if ci > len(self.original) - 1:
            return self.keep(ci, old, cur)
        if not isinstance(cur, Move):
            return self.keep(ci, old, cur)
        next_ = self.original[ci+1]
        if not isinstance(next_, Move):
            return self.keep(ci, old, cur)
        
        try:
            assert cur is self.original[ci]
            assert cur.after is next_.before
            assert cur.after.x is next_.before.x
            assert cur.after.y is next_.before.y
            assert cur.after.z is next_.before.z
            assert cur.after.e is next_.before.e
        except:
            CRITICAL(f"{cur.after} {next_.before}")
            raise
        
        DEBUG(f"Accel limits: X{cur.before.x.accel_limit} Y{cur.before.y.accel_limit} Z{cur.before.z.accel_limit}")
        
        if (
            cur.before.x.accel_limit is not None
            and cur.before.y.accel_limit is not None
            and cur.before.z.accel_limit is not None
            ):
            assert cur.before.x.accel_limit > 0.0
            assert cur.before.y.accel_limit > 0.0
            assert cur.before.z.accel_limit > 0.0
            max_accel = max(
                cur.before.x.accel_limit,
                cur.before.y.accel_limit
                )
            t_scale = max_accel
            z_scale = max_accel / cur.before.z.accel_limit
        else:
            WARNING("Can't scale. Use M201 to set XYZ acceleration limits!")
            t_scale = 1.0
            z_scale = 1.0
        
        t_scale = 0.0
        
        if z_scale < 1.0:
            WARNING("Z moves faster than XY?!")

        if (
            cur.before.max_e_xy is not None
            and cur.before.max_e_xy > 0.0
            ):
            e_scale = 1.0 / cur.before.max_e_xy
        else:
            WARNING("Can't scale E.")
            e_scale = 1.0
            
        e_scale = (20/0.13304)
        
        if e_scale < 1.0:
            WARNING("E moves faster than XY?!")
            
        DEBUG(f"Scale: Z{z_scale} E{e_scale} T{t_scale}")
        
        if cur.before.loc_vec is None:
            return self.keep(ci, old, cur)
        if cur.after.loc_vec is None:
            assert next_.before.loc_vec is None
            return self.keep(ci, old, cur)
        if next_.after.loc_vec is None:
            return self.keep(ci, old, cur)
        
        
        assert (cur.after.loc_vec == next_.before.loc_vec).all()
        
        loc = [
            cur.before.loc_vec,
            cur.after.loc_vec,
            next_.after.loc_vec,
            ]
        
        for i in range(len(loc)):
            loc[i][2] *= z_scale
            loc[i][3] *= e_scale
            loc[i][4] *= t_scale
        
        for p in loc:
            DEBUG(f"X{p[0]} Y{p[1]} Z{p[2]} E{p[3]} T{p[4]}")
            
        fig, ax = plot.subplots()
        
        PLOTX = 0
        PLOTY = 1
        
        DEBUG(repr([p[0] for p in loc]))
        DEBUG(repr([p[1] for p in loc]))
        
        #assert loc[1][4] > loc[0][4]
        #assert loc[2][4] > loc[1][4]
        
        jd = self.junction_deviation
        
        v1 = loc[1] - loc[0]
        DEBUG(f"p0: {loc[0]}")
        DEBUG(f"v1: {v1}")
        DEBUG(f"p1: {loc[1]}")
        v2 = loc[2] - loc[1]
        DEBUG(f"v2: {v2}")
        DEBUG(f"p2: {loc[2]}")
        
        angle = vangle(-v1, v2)
        if angle < 0:
            angle += pi
        sha = sin(angle/2.0)
        rtd = 360/(2*pi)
        DEBUG(f"angle: {angle:0.3} sin(angle/2): {sha:0.3}")
        DEBUG(f"angle: {angle*rtd:0.3f}°")
        assert angle > pi / 4
        
        radius = jd * sha / ( 1.0 - sha )
        
        DEBUG(f"jd={jd:0.3f} r={radius:0.3f} jd+r={radius+jd:0.3f}")
        DEBUG(f"tan(angle/2)={tan(angle/2.0)}")
        
        modify_length = fabs(radius / tan(angle/2.0))
        DEBUG(f"L={modify_length:0.3}")
        
        assert norm(v1) > modify_length
        
        DEBUG(f"v1 length    ={norm(v1):0.3}")
        DEBUG(f"v2 length    ={norm(v2):0.3}")
        
        if modify_length > norm(v1) or modify_length > norm(v2):
            return self.keep(ci, old, cur)
        
        unmodified_length_1 = norm(v1) - modify_length
        unmodified_length_2 = norm(v2) - modify_length
        
        DEBUG(f"modify_length={modify_length:0.3}")
        DEBUG(f"v1 unmod len ={unmodified_length_1:0.3}")
        DEBUG(f"v2 unmod len ={unmodified_length_2:0.3}")
        
        u1 = v1/norm(v1)
        u2 = v2/norm(v2)

        o1 = u1 * unmodified_length_1
        o2 = u2 * unmodified_length_2
        
        m1 = u1 * modify_length
        m2 = u2 * modify_length
        
        assert close_enough(norm(m1), modify_length)
        assert close_enough(norm(m2), modify_length)
        assert close_enough(norm(o1), unmodified_length_1)
        assert close_enough(norm(o2), unmodified_length_2)
        
        ax.plot(
            [
                loc[1][PLOTX],
                (loc[1] - m1)[PLOTX],
                (loc[1] + m2)[PLOTX],
                loc[1][PLOTX],
            ], 
            [
                loc[1][PLOTY],
                (loc[1] - m1)[PLOTY],
                (loc[1] + m2)[PLOTY],
                loc[1][PLOTY],
            ],
            )
            
        new = list()
        new.append(loc[0])
        new.append(
            loc[0] + v1 * (unmodified_length_1/norm(v1))
            )
        
        new_next = list()
        new_next.append(
            loc[2] - v2 * (unmodified_length_2/norm(v2))
            )
        new_next.append(loc[2])
        
        bisector = v2 - v1
        bisector = bisector/norm(bisector)

        DEBUG(f"u1: {u1}")
        DEBUG(f"bisector: {bisector/norm(bisector)}")
        DEBUG(f"u2: {u2}")
        DEBUG(f"angle/2: {vangle(bisector, -u1)} {vangle(bisector, u1)*rtd}")
        DEBUG(f"angle/2: {vangle(bisector, u2)} {vangle(bisector, u2)*rtd}")
        DEBUG(f"angle/2: {vangle(u1, u2)} {vangle(u1, u2)*rtd}")
        assert close_enough(vangle(bisector, -v1), angle/2)
        assert close_enough(vangle(bisector, v2), angle/2)

        jv = bisector/norm(bisector) * jd
        jp = loc[1] + jv
        assert close_enough(norm(loc[1] - jp), jd)
        rv = bisector/norm(bisector) * radius
        cp = jp + rv
        assert close_enough(norm(jp - cp), radius)
        DEBUG(f"u1 {norm(u1)} {u1}")
        
        a1 = cp - (loc[1] - m1)
        assert close_enough(norm(a1), radius)
        a2 = cp - (loc[1] + m2)
        assert close_enough(norm(a2), radius)
        
        ax.plot(
            [
                (cp - a1)[PLOTX],
                (cp)[PLOTX],
                (cp - a2)[PLOTX],
            ],
            [
                (cp - a1)[PLOTY],
                (cp)[PLOTY],
                (cp - a2)[PLOTY],
            ],
            )

        assert close_enough(vangle(a1, v1), pi / 2)
        assert close_enough(vangle(a2, v2), pi / 2)
        
        #assert close_enough(norm(jrv1 + m1), 0)
        
        assert close_enough(norm(loc[1] - cp), jd + radius)
        DEBUG(f"p1 {loc[1]}")
        DEBUG(f"jv {jv}")
        DEBUG(f"jp {jp}")
        DEBUG(f"rv {rv}")
        DEBUG(f"cp {cp}")
        
        ax.plot(
            [
                loc[1][PLOTX],
                (jp)[PLOTX],
            ],
            [
                loc[1][PLOTY],
                (jp)[PLOTY],
            ],
            )

        ax.plot([
            (jp)[PLOTX],
            (cp)[PLOTX],
            ], [
            (jp)[PLOTY],
            (cp)[PLOTY],
            ])
        
        ax.plot(
            [
                (loc[1] - m1)[PLOTX],
                (loc[1] + jv)[PLOTX],
                (loc[1] + m2)[PLOTX],
                ],
            [
                (loc[1] - m1)[PLOTY],
                (loc[1] + jv)[PLOTY],
                (loc[1] + m2)[PLOTY],
                ]
            )

        circle_plot = plot.Circle(
            (cp[PLOTX], cp[PLOTY]),
            norm(rv[(PLOTX, PLOTY),]),
            color='lightgray',
            linewidth=None,
            zorder=-3,
            )
        ax.add_artist(circle_plot)

        #circle_plot = plot.Circle(
            #(loc[1][PLOTX], loc[1][PLOTY]),
            #norm(jv[(PLOTX, PLOTY),]),
            #linewidth=None,
            #color='lime',
            #)
        #ax.add_artist(circle_plot)
        ax.axis('equal')

        ax.autoscale(enable=False, axis='both')
        ax.plot(
            [p[PLOTX] for p in loc],
            [p[PLOTY] for p in loc],
            scalex=False,
            scaley=False,
            zorder=-1,
            )
       
        ax.plot(
            [
                loc[1][PLOTX],
                (loc[1] + bisector)[PLOTX],
            ], 
            [
                loc[1][PLOTY],
                (loc[1] + bisector)[PLOTY],
            ],
            scalex=False,
            scaley=False,
            zorder=-2,
            )
        plot.show()
        
        DEBUG(f"center X{cp[0]:0.4} Y{cp[1]:0.4} Z{cp[2]:0.4} E{cp[3]:0.4} T{cp[4]:0.4}")
        
        time_left = new_next[1][4] - new[1][4]
        
        segments = floor(time_left * self.command_rate)
        
        DEBUG("Will add {segments} moves")
        
        if segments < 1:
            return self.keep(ci, old, cur)
        
        circle_angle = (pi / 2 - angle / 2) * 2
        
        co = v1 * (radius / norm(v1))
        
        ca = -v1_to_center
        
        for i in range(segments):
            segment_angle = (circle_angle / segments) * (i + 1)
            vs = cos(segment_angle) * ca + sin(segment_angle) * co
            pos = center + vs
            new.append(vs)
            
        for p in new:
            DEBUG(f"after: X{p[0]:0.3} Y{p[1]:0.3} Z{p[2]:0.3} E{p[3]:0.3} T{p[4]:0.3}")
        
        for p in new_next:
            DEBUG(f"after: X{p[0]:0.3} Y{p[1]:0.3} Z{p[2]:0.3} E{p[3]:0.3} T{p[4]:0.3}")

        raise NotImplementedError()
        
        first = Move('')
        
        return self.process_first(cur, next_)
    

