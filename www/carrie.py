#!/usr/bin/env python3

# carrie.py - homepage for reverse proxy
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

import subprocess
import sys
import time

import logging
logger = logging.getLogger(__name__)
DEBUG = logger.debug
INFO = logger.info
WARNING = logger.warning
ERROR = logger.error
CRITICAL = logger.critical

from flask import Flask, render_template
app = Flask(__name__, template_folder='.')

class Status:
    def getcol(self, lines, col):
        val = -1.0
        index = None
        for line in lines:
            split = line.split()
            if col in split:
                index = split.index(col)
            elif (
                index is not None 
                and index < len(split)
                and 'Average' not in split[0]
                ):
                try:
                    val = float(split[index].replace('%', ''))
                except ValueError:
                    pass
        return val
    
    def du(self):
        lines = subprocess.run(
            [
                '/bin/df',
                '/var'
                ],
            capture_output=True,
            ).stdout.decode().splitlines()
        used = self.getcol(lines, 'Use%')
        return f"{used:2.0f}"
    
    def sar(self, opt, col):
        now = time.time()
        then = now - 100
        now = time.strftime('%H:%M:%S', time.localtime(now))
        then = time.strftime('%H:%M:%S', time.localtime(then))
        lines = subprocess.run(
            [
                '/usr/bin/sar',
                '-0',
                opt,
                '-s', then,
                '-e', now
                ],
            capture_output=True,
            ).stdout.decode().splitlines()
        return self.getcol(lines, col)
    
    def get_cpu(self):
        idle = self.sar('-u', '%idle')
        used = 100 - idle
        return f"{used:2.0f}"

    def get_ram(self):
        used = self.sar('-r', '%memused')
        return f"{used:2.0f}"

    def __init__(self):
        self.cpu = self.get_cpu()
        self.ram = self.get_ram()
        self.disk = self.du()

@app.route("/")
def index():
    return render_template(
        'index.html',
        status=Status()
        )

if __name__ == '__main__':
    app.run(debug=True)
