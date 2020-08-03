#!/usr/bin/env python3

# state_machine.py -- Simple finite state machines
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

from enum import Enum

from utility_decorator import ClassDecorator
from utility_decorator import CollapsingLateMemberDecorator

class state_machine(ClassDecorator):
    def decorate(self):
        self.cls = cls = self.decorated
        if not hasattr(cls, 'States') and isinstance(cls.States, Enum):
            raise TypeError("State machine must an enum named 'States.'")
        self.convenience()
    
    def convenience(self):
        cls = self.cls
        # Namespacing: copy states to machine class for convenience
        for name, member in cls.States.__members__.items():
            if hasattr(cls, name):
                raise TypeError(
                    f"{getattr(cls, name)} conflicts with state {name}"
                    )
            setattr(cls, name, member)
        
        if hasattr(cls, 'states_by_name'):
            raise TypeError('State machine cannot already have a states_by_name')
        cls.states_by_name = cls.States.__members__

    
    def decorated_call(self):
        new = self.cls()
        assert new.state in new.States
        return new

class InvalidTransitionError(ValueError):
    pass

class transition(CollapsingLateMemberDecorator):
    """ 
    Decorator for state machine transition methods.
    """
    def decorate_late():
        pass
    
    def single_decorator_args(self, pred_state, next_state):
        assert pred_state in self.member_of.States
        assert next_state in self.member_of.States
        if not hasattr(self, 'valid_transitions'):
            self.valid_transitions = dict()
        self.valid_transitions[pred_state] = self.next_state
    
    def decorated_call(self, instance, *args, **kwargs):
        if instance.state not in self.valid_transitions:
            name = self.decorated.__name__
            cname = self.member_of.__name__
            sname = instance.state.__name__
            raise InvalidTransitionError(
                f"Can't call {name} on a {cname} in state {sname}"
                )
        else:
            instance.state = self.valid_transitions[instance.state]
            self.decoratd(*args, **kwargs)
