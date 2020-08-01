#!/bin/bash

# Usage: build.sh <location of configuration headers>
# Usage: build.sh ../code/my_marlin_config

# build.sh -- Simple utility to build Marlin FW
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

set -o errexit
set -o pipefail
set -o xtrace

config="$1"
shift

[[ -f "${config}/Configuration.h" ]]

[[ -d Marlin/src ]]

if [[ ! -d venv ]] ; then
	python3 -m virtualenv -p `which python3` venv
fi

source venv/bin/activate

pip install --upgrade platformio

rm -rf .pio/build

if [[ "$config" -ef "Marlin" ]] ; then
	echo Not copying config files over themselves >&2
else
	for f in "$config"/*.h ; do
		if cmp --silent "$f" "Marlin/${f##*/}" ; then
			echo Not copying "$f", it hasnt changed >&2
		else
			cp -vi "$f" "Marlin/"
		fi
	done
fi

platformio run

ls .pio/build/*/firmware.elf
ls .pio/build/*/firmware.hex
