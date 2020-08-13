#!/usr/bin/env python3

# command.py -- Model G-code command
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

import numpy as np

from machine_state import MachineState

class Command:
    def copy(self):
        new = self.__class__(self.g_code, self.args, self.comment)
        return new
    
    def __init__(
        self,
        g_code,
        args,
        comment
        ):
        assert not ('G' in args and 'M' in args)
        self.__dict__.update(args)
        self.g_code = g_code
        self.comment = comment
        self.before = None
        self.after = None
        self.oln = None
        self.ln = None
    
    @property
    def args(self):
        return {
            k: v for k, v in self.__dict__.items() if (len(k) == 1)
            }
    
    @property
    def aargs(self):
        return {k: v for k, v in self.__dict__.items() if (
                len(k) == 1
                and k != 'G'
                and k != 'M'
                )
            }
    
    @property
    def head_dist(self):
        if (
            self.after.pos_vec_xyz is None
            or self.before.pos_vec_xyz is None
            ):
            return None
        return np.linalg.norm(
            self.after.pos_vec_xyz
            - self.before.pos_vec_xyz
            )
    
    @property
    def head_dist_xy(self):
        if (
            self.after.pos_vec_xy is None
            or self.before.pos_vec_xy is None
            ):
            return None
        return np.linalg.norm(
            self.after.pos_vec_xy
            - self.before.pos_vec_xy
            )

    @property
    def head_dist_z(self):
        if (
            self.after.z.position is None
            or self.before.z.position is None
            ):
            return None
        return (
            self.after.z.position
            - self.before.z.position
            )
    
    @property
    def head_dist_e(self):
        if (
            self.after.e.position is None
            or self.before.e.position is None
            ):
            return None
        return (
            self.after.e.position
            - self.before.e.position
            )

    @property
    def moves_head(self):
        before = self.before.positions
        after = self.after.positions
        dist_sq = 0.0
        for ai in range(3):
            if before[ai] == after[ai]:
                continue
            else:
                return True
        return False
    
    @property
    def vector(self):
        if (
            self.after.pos_vec is None
            or self.before.pos_vec is None
            ):
                return None
        return (
            self.after.pos_vec - self.before.pos_vec
            )

class Control(Command):
    def evolve(self, before):
        self.before = before
        self.after = MachineState(before)
        self._evolve()
        return self.after

class NoOp(Command):
    def evolve(self, before):
        self.before = before
        self.after = before
        return before

class ParseError(ValueError):
    pass

def parse_arg(arg):
    l = arg[0]
    v = arg[1:]
    if v == '':
        v = v
    else:
        v = float(v)
    return (l, v)

codes = None

def load_codes():
    global codes
    if codes is None:
        DEBUG("Loading codes...")
        import commands
        codes = dict()
        for name in dir(commands):
            c = getattr(commands, name)
            if (
                c.__class__ == Command.__class__
                and issubclass(c, Command)
                and hasattr(c, 'code')
                ):
                DEBUG(c.code)
                assert c.code not in codes
                codes[c.code] = c

def _parse(g_code):
    load_codes()
    if ';' in g_code:
        (args, comment) = g_code.split(';', 1)
    else:
        args = g_code
        comment = None
    args = {a[0]: a[1] for a in map(parse_arg, args.split())}
    if len(args) == 0:
        r = NoOp(g_code, args, comment)
        assert r is not None
    elif 'G' in args:
        r = codes[f"G{args['G']}".replace('.0', '')](g_code, args, comment)
        assert r is not None
    elif 'M' in args:
        r = codes[f"M{args['M']}".replace('.0', '')](g_code, args, comment)
        assert r is not None
    else:
        raise ParseError(f"Unknown command: {g_code}")
    return r

def parse(g_code):
    try:
        r = _parse(g_code)
        assert r is not None
    except:
        CRITICAL(f"Couldn't parse: {g_code}")
        raise
    return r
