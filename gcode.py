#!/usr/bin/env python3

# gcode.py -- GCode utility functions and classes
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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from dataclasses import make_dataclass
from dataclasses import field
from enum import Enum
from enum import unique
from pathlib import Path

from java_envy import globalize
from sat_mixin import SATMeta
from sat_mixin import conflicts
from state_machine import state_machine
from state_machine import transition

class Source(ABC):
    @abstractmethod
    def __str__(self):
        raise NotImplemented("abstract method")

class Serial(Source):
    def __str__(self):
        return "Serial"

class Unknown(Source):
    def __str__(self):
        return "Unknown Source"

@dataclass(frozen=True)
class GCodeFile(Source):
    path : Path
    line : int
    
    def __init__(self, path, line):
        object.__setattr__(self, 'path', Path(path))
        object.__setattr__(self, 'line', int(line))
        
    def __str__(self):
        return f"f{self.path.name}: {self.line}"

@state_machine
class PrintPhase:
    @globalize
    @unique
    class States(Enum):
        INITIALIZE = 'INITIALIZE'
        PRINT = 'PRINT'
        FINALIZE = 'FINALIZE'
    
    def reset(self):
        self.state = INITIALIZE
        self.last_command = top()
        
    def __init__(self):
        self.reset()
    
    @transition(INITIALIZE, INITIALIZE)
    @transition(FINALIZE, FINALIZE)
    @transition(PRINT, FINALIZE)
    def initialize_or_finalize(self, command):
        self.last_command = command
    
    @transition(INITIALIZE, INITIALIZE)
    def initialize(self, command):
        self.last_command = command

    @transition(FINALIZE, FINALIZE)
    @transition(PRINT, FINALIZE)
    def finalize(self, command):
        self.last_command = command

    @transition(INITIALIZE, PRINT)
    def print(self, command):
        self.last_command = command

class GCommandMixin(SATMeta):
    pass

class GCommandMeta(GCommandMixin):
    pass

class Interactivity(metaclass=GCommandMixin):
    pass

class Batch(Interactivity):
    """
    Commands sensibly used noninteractively (in a gcode file),
    though they may be used interactively, too
    """
    pass

class BatchOnly(Batch):
    """
    Commands sensibly used noninteractively (in a gcode file),
    but don't make sense interactively (via serial)
    """
    pass

@conflicts(Batch)
class Interactive(Interactivity):
    """
    Commands only sensibly used interactively (serial),
    these should NOT appear in gcode files
    """
    pass

class Phased(metaclass=GCommandMixin):
    @property
    @abstractmethod
    def phase(self, print_phase):
        raise NotImplementedError("This is an abstract class")

class Print(Phased):
    def phase(self, print_phase):
        print_phase.print(self)

    @property
    def affects_filament(self):
        return True

@conflicts(Print)
class InitializeFinalize(Phased):
    def phase(self, print_phase):
        print_phase.initialize_or_finalize(self)

class Initialize(InitializeFinalize):
    def phase(self, print_phase):
        print_phase.initialize(self)

@conflicts(Initialize)
class Finalize(InitializeFinalize):
    def phase(self, print_phase):
        print_phase.finalize(self)

@conflicts(Print, InitializeFinalize)
class AnyPhase(Phased):
    def phase(self, print_phase)
        pass

class Statefulness(metaclass=GCommandMixin):
    pass

class Control(Statefulness):
    pass

@conflicts(Control)
class Informational(Statefulness):
    pass

class Capability(metaclass=GCommandMixin):
    pass

class Incapable(Capability):
    pass

class Occult(Incapable):
    """
    Control commands that are impossible to model without being the 
    printer
    """
    pass

@conflicts(Occult)
class Unimplemented(Incapable):
    """
    Control commands that are possible to model... but we haven't yet
    """
    pass

@conflicts(Occult, Unimplemented)
class Dangerous(Incapable):
    """
    Control commands that are possibly dangers to the machine
    """
    pass

@conflicts(Incapable)
class Capable(Capability):
    @abstractmethod
    def run(self, machine):
        raise NotImplementedError("This is an abstract class")

@conflicts(Incapable, Capable)
class Skippable(Capability):
    def run(self, machine):
        pass

class Importance(metaclass=GCommandMixin):
    pass

class Important(Importance):
    pass

@conflicts(Important)
class Disregard(Importance):
    pass

class MainPrint(Batch, Print, Control, Capable):
    pass

class MoveAndPrint(MainPrint):
    def run(self, machine):
        machine.move(
            [
                0 if v is None else v for v in [
                    self.X,
                    self.Y,
                    self.Z,
                    self.E,
                    ]
            ],
            self.F
            )

class UnimPrint(Batch, Print, Control, Unimplemented):
    pass

class Sleep(Batch, AnyPhase, Control, Capable):
    def run(self, machine):
        if self.P is not None:
            machine.add_time(self.P/1000)

        if self.S is not None:
            machine.add_time(self.S)

class Enigma(Batch, AnyPhase, Control, Occult):
    pass

class Hazard(Batch, AnyPhase, Control, Dangerous):
    pass

class Maintenance(Interactive, Initialize, Control, Occult):
    pass

class FinishMove(Batch, Finalize, Control, Capable):
    def run(self, machine):
        machine.invalidate_position()

class PrepareMove(Batch, InitializeFinalize, Control, Capable):
    def run(self, machine):
        machine.invalidate_position()

class Home(PrepareMove):
    def run(self, machine):
        machine.invalidate_position()
        machine.home()

@conflicts(Home)
class Calibrate(PrepareMove):
    pass

@conflicts(PrepareMove)
class PrepareSkip(Batch, InitializeFinalize, Control, Skippable):
    pass

class GCommand(metaclass=GCommandMeta):
    @property
    @abstractmethod
    def concrete(self):
        raise NotImplementedError("This is an abstract class")
    
    def gcommand_parse(self, source, ac):
        if not isinstance(source, Source):
            raise TypeError()
        if not isinstance(ac, str):
            raise TypeError()
        ac = ac.split(';', 1)
        args = {
            a[0]: float(a[1:]) for a in ac[0].split()
            }
        if len(ac) > 1:
            args['comment'] = ac[1]
        args['source'] = source
        self.dataclass_init(**args)
    
    @classmethod
    def subclass(
        cls,
        name,
        gcode,
        required_args,
        optional_args,
        *bases,
        ):
        DEBUG(f"{name} {gcode}")
        fields = [
            ('source', Source, field(compare=False)),
            ('comment', str, ''),
            ]
        fields += [(c, float) for c in required_args]
        fields += [(c, float, field(default=None)) for c in optional_args]
        bases = [cls] + list(bases)
        #name = '.'.join([__name__, name])
        base_name = name + 'Base'
        ns = {
                'required_args': required_args,
                'optional_args': optional_args,
                'name': name,
                'gcode': gcode,
                }
        base = cls.__class__.submesa(
            base_name,
            bases,
            ns=ns
            )
        r = make_dataclass(
            name,
            fields,
            bases=(base,),
            frozen=True,
            namespace={
                'concrete': lambda self: True
                }
            )
        r.dataclass_init = r.__init__
        def run_gcommand_init(self, *args, **kwargs):
            try:
                self.gcommand_parse(*args, **kwargs)
            except TypeError:
                self.dataclass_init(*args, **kwargs)
        r.__init__ = run_gcommand_init
        return r
        
class Commands:
    def add(self, c):
        assert not hasattr(self, c.name)
        assert not hasattr(self, c.gcode)
        assert c.name == c.__name__
        DEBUG(f"{c.gcode} ; {c.name}")
        setattr(self, c.name, c)
        setattr(self, c.gcode, c)
        
    def __init__(self, l):
        list(map(lambda a: self.add(GCommand.subclass(*a)), l))
        DEBUG(sorted(self.__dict__.keys()))
        
all_args = 'ABCDEFHIJKLNOPQRSTWXYZ' # no G or M

commands = Commands([
    ('LinearMoveAlt', 'G0', '', 'EFXYZ', MoveAndPrint),
    ('LinearMove', 'G1', '', 'EFXYZ', MoveAndPrint),
    ('ClockwiseMove', 'G2', '', 'EFIJPRXYZ', UnimPrint),
    ('CounterClockwiseMove', 'G3', '', 'EFIJPRXYZ', UnimPrint),
    ('Dwell', 'G4', '', 'PS', Sleep),
    ('BezierSpline', 'G5', '', 'EFIJPQXY', UnimPrint),
    ('DirectMove', 'G6', '', 'ABCR', Hazard),
    ('FirmwareRetract', 'G10', '', 'S', Enigma),
    ('FirmwareExtend', 'G11', '', 'S', Enigma),
    ('CleanNozzle', 'G12', '', 'PRST', Maintenance),
    ('XYPlane', 'G17', '', '', UnimPrint),
    ('ZXPlane', 'G18', '', '', UnimPrint),
    ('YZPlane', 'G19', '', '', UnimPrint),
    ('InchUnits', 'G20', '', '', UnimPrint),
    ('MillimeterUnits', 'G21', '', '', UnimPrint),
    ('PrintValidationPattern', 'G26', '', 'BCDFHIKLOPQRSUXY', AutomaticMaintenance),
    ('Park', 'G27', '', 'P', FinishMove),
    ('Home', 'G28', '', 'ORXYZ', Home),
    ('LevelBed', 'G29', '', all_args, Calibrate),
    ('ZProbe', 'G30', '', 'EXY', Calibrate),
    ('DockSled', 'G31', '', '', PrepareSkip),
    ('UndockSled', 'G32', '', '', PrepareSkip),
    ('DeltaCalibrate', 'G33', '', 'CEFPTV', Calibrate),
    ('AutoAlignment', 'G34', '', 'AEIT', Calibrate),
    ('Tram', 'G35', '', 'S', Maintenance),
    ('ProbeWorkpiece', 'G38.2', '', 'FXYZ', UnimPrint),
    ('QuietProbeWorkpiece', 'G38.3', '', 'FXYZ', UnimPrint),
    ('MoveToMeshCoordinate', 'G42', '', 'FIJ', Calibrate),
    ('MoveNative', 'G53', 'GEFXYZ', UnimPrint),
    ('CoordinateSystem1', 'G54', '', UnimPrint),
    ('CoordinateSystem2', 'G55', '', UnimPrint),
    ('CoordinateSystem3', 'G56', '', UnimPrint),
    ('CoordinateSystem4', 'G56.1', '', UnimPrint), # bad documentation? they both say they're G56
    ('CoordinateSystem5', 'G57', '', UnimPrint),
    ('CoordinateSystem6', 'G58', '', UnimPrint),
    ('CoordinateSystem7', 'G59', '', UnimPrint),
    ('CoordinateSystem8', 'G59.1', '', UnimPrint),
    ('CoordinateSystem9', 'G59.2', '', UnimPrint),
    ('CoordinateSystem9', 'G59.3', '', UnimPrint),
    ])

if __name__ == '__main__':
    assert commands.LinearMoveAlt is commands.G0
    try:
        a = commands.LinearMoveAlt(Unknown(), "X1.0 Y0.2 Z0 F1000")
        b = commands.G0(Unknown(), "X1.0 Y0.2 Z0 F1000")
        assert a == b
    except:
        DEBUG(b.__eq__)
        raise
    try:
        pass
    except:
        raise

#DEBUG("abs"+ " ".join(LinearMoveAlt.__abstractmethods__))
#DEBUG(LinearMoveAlt.__qualname__)
#LMA = LinearMoveAlt(Unknown(), '')
#LMA.run()

