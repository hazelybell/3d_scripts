#!/bin/bash

# Usage: build.sh <location of configuration headers>
# Usage: build.sh ../code/my_marlin_config

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
