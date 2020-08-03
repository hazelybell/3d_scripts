#!/usr/bin/env python3

# state_machine.py -- Useful decorators and decorator utilities
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

from abc import ABC
from abc import abstractmethod
from inspect import isclass
from inspect import ismethod

class UtilityDecorator(ABC):
    """
    Override these methods:
    
    decorator_args() will be called with args if decorator is used with args.
    decorator_args() will be called with no args if decorator is used without args.
    
    decorate() will be called when callable to be decorated is available
    in .decorated.
    
    decorated_call() will be called instead of the callable if overriden.
    """
    
    def decorator_args(self):
        """
        Override me if you want your decorator to be able to take args.
        """
    
    @abstractmethod
    def decorate(self):
        raise NotImplementedError("Abstract Method")
    
    def decorated_call(self, *args, **kwargs):
        """
        Override me if you want call wrapping.
        """
        self.decorated(*args **kwargs)
    
    def _decorate(self, what):
        self.decorated = what
        self.decorate()
    
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            self.with_args = False
            self.decorator_args()
            self._decorate(args[0])
        else:
            self.with_args = True
            self.decorator_args(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        if self.with_args:
            assert len(args) == 1
            assert len(kwargs) == 0
            assert callable(args[0])
            self._decorate(args[0])
            return self.decorated_call
        else:
            return self.decorated_call(*args, **kwargs)

class ClassDecorator(UtilityDecorator):
    def apply_late_member_decorators(self):
        for name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, LateMemberDecorator):
                attr.member_of = cls
                decorator._decorate_late()
    
    def decorate_class(self):
        """
        Override me to the decorated class (self.decorated)
        """
        pass


    def decorate(self):
        assert isclass(self.decorated)
        self.decorate_class()
        assert isclass(self.decorated)
        self.apply_late_member_decorators()
    
    def decorated_instance(self, *args, **kwargs):
        """
        Override me to modify new instances.
        """
        return self.decorated(*args, **kwargs)
    
    def decorated_call(self, *args, **kwargs):
        return self.decorated_instance(*args, **kwargs)
    
class LateMemberDecorator(UtilityDecorator):
    def decorate(self):
        """
        Wait for later when we know who our class is.
        """
        pass

    @abstractmethod
    def decorate_late(self):
        """
        Override me to perform decoration once the class we're a member of is known.UtilityDecorator
        This will be stored in self.member_of
        """
        raise NotImplementedError("Abstract Method")

    def _decorate_late(self):
        if isinstance(self.decorated, LateMemberDecorator):
            self.decorated.member_of = self.member_of
            self.decorated._decorate_late()
        self.decorate_late()

class CollapsingLateMemberDecorator(LateMemberDecorator):
    def can_collapse_with(self, other):
        return isinstance(other, self.__class__)
    
    def decorator_args(self, *args, **kwargs):
        self.my_args = (args, kwargs)
        
    @abstractmethod
    def single_decorator_args(*args, **kwargs):
        raise NotImplementedError("Abstract Method")
    
    def multi_decorator_args(self, all_args):
        for args, kwargs in all_args:
            self.single_decorator_args(*args, **kwargs)
    
    def _decorate_late(self):
        all_args = [self.my_args]
        while (
            isinstance(self.decorated, CollapsingLateMemberDecorator)
            and self.can_collapse_with(self.decorated)
            ):
            all_args.append(self.decorated.my_args)
        
        self.multi_decorator_args(all_args)
        
        super()._decorate_late()


