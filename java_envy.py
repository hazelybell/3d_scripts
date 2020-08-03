#!/usr/bin/env python3

# java_envy.py -- Python utilities I wish it had
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
logging.basicConfig(stream=sys.stderr,level=logging.DEBUG)

from inspect import ismethod
from inspect import isfunction
from enum import Enum

def globalize(enum):
    assert issubclass(enum, Enum)
    module = sys.modules[enum.__module__]
    for name, value in enum.__members__.items():
        if hasattr(module, name):
            raise NameError(f"{module.__name__} already has a {name}!")
        setattr(module, name, value)
    return enum
