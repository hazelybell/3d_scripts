#!/bin/bash

set -o errexit
set -o pipefail
set -o xtrace

# These may be overridden in /etc/default/octoprint !
PORT=5000
BASEDIR="$HOME"
CONFIGFILE="$BASEDIR"/config.yaml
DAEMON_ARGS=""

if [[ -r /etc/default/octoprint ]] ; then
	source /etc/default/octoprint
fi

cd "$BASEDIR"

if [[ ! -d venv ]] ; then
        python3 -m virtualenv -p `which python3` venv
fi

source venv/bin/activate

function pipup {
	pip --no-input install \
		--upgrade \
		--upgrade-strategy eager \
		"$@"
}

function wait_network {
	if wget \
		--quiet \
		--output-document /dev/null \
		--tries 10 \
		--spider \
		--timeout 6 \
		--max-redirect=0 \
		--retry-on-host-error \
		--waitretry=6 \
		--retry-connrefused \
		https://pypi.org/
	then
		return 0
	else
		local r=$?
		if (( r == 8 )) ; then
			return 0
		else
			return $r
		fi
	fi
}

if wait_network ; then
	pipup pip wheel
	pipup octoprint
fi

exec octoprint serve \
	--port "$PORT" \
	--basedir "$BASEDIR" \
	--config "$CONFIGFILE" \
	$DAEMON_ARGS
