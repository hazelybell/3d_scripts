#!/usr/bin/env python3

# sat_mixin.py -- NP-complete mixins so your modules won't load
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

import sys
import logging
logger = logging.getLogger(__name__)
DEBUG = logger.debug
INFO = logger.info
WARNING = logger.warning
ERROR = logger.error
CRITICAL = logger.critical

from abc import ABCMeta
from collections.abc import Hashable

DEBUG_SAT_MIXIN = True

def noop(*args, **kwargs):
    pass

if DEBUG_SAT_MIXIN:
    pass
else:
    DEBUG = noop

class HashableSet(set, Hashable):
    def __hash__(self):
        return sum([hash(e) for e in self])


class SATObject:
    pass

class SATMeta(ABCMeta):
    @classmethod
    def all_bases(cls, bases):
        visited = set()
        while len(visited) < len(bases):
            base = (bases - visited).pop()
            if (
                hasattr(base, '__metaclass__')
                and base.__metaclass__ is cls
                ):
                bases |= base._bases
            visited.add(base)
        return bases
    
    #@classmethod
    #def all_conflicts(cls, conflicts):
        #visited = set()
        #while len(visited) < len(conflicts):
            #conflict = (conflicts - visited).pop()
            #if (
                #hasattr(conflict, '__metaclass__')
                #and conflict.__metaclass__ is cls
                #):
                #conflicts |= conflict._conflicts
            #visited.add(conflict)
        #return conflicts
    
    @classmethod
    def solve1(cls, bases, conflicts, others):
        # called by solve0/solve2
        # assume all_bases and all_conflicts have been applied
        # assume no contradiction
        
        call = (bases, conflicts) 
        if call in cls.cache:
            return cls.cache[call]
        
        candidates = set()
        candidates.add((bases, conflicts))
        
        n_others = len(others)
        
        for other in set(others):
            if (
                len(bases & other._conflicts) > 0
                or len(conflicts & other._bases) > 0
                ):
                others.remove(other)
                continue
            other_proper_bases = {
                base for base in other._bases if (
                    hasattr(base, "__metaclass__")
                    and base.__metaclass__ is cls
                    )
                }
            if (
                len(other_proper_bases) > 0
                and other._bases <= bases
                and conflicts <= other._conflicts
                ):
                bases2 = HashableSet(bases)
                bases2 |= cls.all_bases(set((other,)))
                conflicts2 = HashableSet(conflicts)
                conflicts2 |= {
                        conflict
                    for base in bases2 if hasattr(base, '_conflicts')
                        for conflict in base._conflicts
                    }
                assert(other in bases2)
                if len(conflicts2 & bases2) > 0:
                    others.remove(other)
                    continue
                others2 = others - bases2
                assert(other in bases2)
                assert(len(others2) < n_others)
                candidates.add(cls.solve1(bases2, conflicts2, others2))
        
        return max(
            candidates,
            key = lambda r: len(r[0])
            )
    
    @classmethod
    def solve0(cls, bases, conflicts):
        cls.cache = dict()
        bases = HashableSet(bases)
        conflicts |= {
                conflict
            for base in bases if hasattr(base, '_conflicts')
                for conflict in base._conflicts
            }
        conflicts = HashableSet(conflicts)
        bases = cls.all_bases(bases)
        #conflicts = cls.all_conflicts(conflicts)
        if len(conflicts & bases) > 0:
            raise TypeError(f"Contradiction: {repr(conflicts & bases)}")
        others = set(cls.mesaclasses) - bases - conflicts
        return cls.solve1(bases, conflicts, others)
    
    def __new__(cls, name, bases, _dict):
        explicit = bases
        if '_conflicts' in _dict:
            conflicts = _dict['_conflicts']
        else:
            conflicts = set()
        if not hasattr(cls, 'mesaclasses'):
            cls.mesaclasses = list()
        (bases, conflicts) = cls.solve0(bases, conflicts)
        DEBUG(f"name: {name}")
        DEBUG(f"    metaclass: {cls}")
        DEBUG(f"    bases: {' '.join(map(lambda c: c.__name__, bases))}")
        DEBUG(f"    conflicts: {' '.join(map(lambda c: c.__name__, conflicts))}")
        cls.precomputed_mro = (
            list(explicit)
            + [
                c for c in reversed(cls.mesaclasses) if (
                    c in bases and c not in explicit
                    )
                ]
            + []
            )
        #bases.add(SATObject)
        #print(f"precomputed: {repr(cls.precomputed_mro)}")
        new = super(SATMeta, cls).__new__(cls, name, tuple(cls.precomputed_mro), _dict)
        cls.mesaclasses.append(new)
        new.__metaclass__ = cls
        new._bases = bases
        new._explicit_bases = explicit
        new._conflicts = conflicts
        return new
    
    def mro(cls):
        #DEBUG(f"mro for: {repr(cls)}")
        if cls is SATMeta:
            assert False
            return super(SATMeta, cls).mro()
        else:
            bases = [cls] + cls.precomputed_mro + [object]
            #DEBUG(f"MRO BASE: {repr(bases)}")
            assert None.__class__ not in bases
            r = []
            for base in bases:
                r.append(base)
                if base is not cls:
                    for base_base in base.__mro__:
                        if base_base not in r:
                            r.append(base_base)
        #DEBUG(f"MRO: {repr(r)}")
        return r
    
    @classmethod
    def submesa(cls, name, bases=(object,), ns=dict(), metans=dict()):
        meta = cls.__class__(
            name + 'Meta',
            (cls,),
            metans
            )
        mesa = meta(name, bases, ns)
        return mesa

def conflicts(*conflicts):
    def conflicts2(cls):
        cls._conflicts = set(conflicts)
        del cls._bases
        cls.__metaclass__.mesaclasses.remove(cls)
        return cls.__metaclass__.__new__(
            cls.__metaclass__,
            cls.__name__,
            cls._explicit_bases,
            { k: getattr(cls, k) for k in dir(cls) },
            )
    return conflicts2

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)
    class D(metaclass=SATMeta):
        pass
    
    class X(metaclass=SATMeta):
        _conflicts = {D}
        pass
    
    class Y(metaclass=SATMeta):
        pass
    
    class XY(X, Y):
        pass
    
    class Z(X, Y):
        pass

    class A(metaclass=SATMeta):
        pass
    
    class B(A):
        pass
    
    @conflicts(B)
    class C(A):
        pass
        
    class E(B):
        pass
    
    class F(C):
        pass
    
