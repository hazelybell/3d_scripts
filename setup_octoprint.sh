#!/bin/bash

# setup_octoprint.sh -- Install octoprint as a separate user
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

function main {

OCTOPRINT_HOME=/var/lib/octoprint

set -o errexit
set -o pipefail
set -o xtrace

local start_script="${BASH_SOURCE%/*}/start_octoprint.sh"
[[ -f "$start_script" ]]

# I like matching username/group IDs for some reason...
if [[ -r /etc/adduser.conf ]] ; then
	source /etc/adduser.conf
else
	local FIRST_SYSTEM_UID=100
	local FIRST_SYSTEM_GID=100
	local DSHELL=/bin/bash
fi

check_installed wget
PACKAGE=coreutils check_installed tee
check_installed python3
PACKAGE=python3-virtualenv check_installed python3 -m virtualenv --version
PACKAGE=python3-dev check_installed python3-config

local -i id=$FIRST_SYSTEM_UID
if (( FIRST_SYSTEM_GID > FIRST_SYSTEM_UID )) ; then
	id=FIRST_SYSTEM_UID
fi

if ! { id -g octoprint || id -u octoprint ; } >/dev/null ; then
	while { getent passwd $id || getent group $id ; } >/dev/null ; do
		id+=1
	done
elif ! id -g octoprint >/dev/null ; then
	id=$(id -u octoprint)
else
	id=$(id -g octoprint)
fi


if ! id -g octoprint >/dev/null ; then
	sudo addgroup \
		--system \
		--gid $id \
		octoprint
fi

if ! id -u octoprint >/dev/null ; then
	# Leave the user with a disabled password, but a shell.
	# This means they can login if ssh keys are set up.
	# Could be useful for rsyncing things to the octoprint user, etc.
	sudo adduser \
		--system \
		--disabled-password \
		--gecos "OctoPrint Daemon User" \
		--home "$OCTOPRINT_HOME" \
		--ingroup octoprint \
		--uid $id \
		--shell "$DSHELL" \
		octoprint
fi

if [[ ! -d "$OCTOPRINT_HOME" ]] ; then
	sudo mkdir -p "$OCTOPRINT_HOME"
	sudo rsync -aP /etc/skel/ "$OCTOPRINT_HOME"/
fi

sudo mkdir -p "$OCTOPRINT_HOME"/.ssh
cat <(
	if [[ -f "$HOME"/.ssh/authorized_keys ]] ; then
		cat "$HOME"/.ssh/authorized_keys
	else
		echo
	fi
) <(
	if sudo test -f "$OCTOPRINT_HOME"/.ssh/authorized_keys ; then
		sudo cat "$OCTOPRINT_HOME"/.ssh/authorized_keys
	else
		echo
	fi
) | sort | uniq | sudo tee "$OCTOPRINT_HOME"/.ssh/authorized_keys

start_script_dest="${OCTOPRINT_HOME}/${start_script##*/}"
sudo cp "$start_script" "$start_script_dest"
sudo chmod +x "$start_script_dest"

sudo chown -Rc octoprint:octoprint "$OCTOPRINT_HOME"

sudo tee /etc/systemd/system/octoprint.service <<-EOF
	[Unit]
	Description=OctoPrint - the snappy web interface for your 3D printer
	After=network.target

	[Service]
	User=octoprint
	Group=octoprint
	# BEGIN FROM https://github.com/OctoPrint/OctoPrint/pull/1716/files
	# Process priority, 0 here will result in a priority 20 process.
	# -2 ensures Octoprint has a slight priority over user processes.
	Nice=-2
	# END FROM
	Restart=always
	StartLimitIntervalSec=600
	StartLimitBurst=3
	WorkingDirectory=$OCTOPRINT_HOME
	AmbientCapabilities=CAP_NET_BIND_SERVICE
	StandardOutput=journal
	Type=exec
	ExecStart=$start_script_dest

	[Install]
	WantedBy=multi-user.target
EOF

addline "%octoprint ALL=$(which systemctl) restart octoprint.service" \
	/etc/sudoers

addline "%octoprint ALL=$(which systemctl) reboot" \
	/etc/sudoers

sudo systemctl daemon-reload

sudo systemctl reenable octoprint

sudo systemctl restart octoprint

echo "Octoprint service started... it's downloading and installing itself..."
echo "Check journalctl -f -u octoprint"

} # main

function check_installed {
	local -i r=0
	if (( $# > 1 )) ; then
		"$@" || r=$?
	else
		which "$1" || r=$?
	fi
	if (( r > 0 )) ; then
		if [[ -v PACKAGE ]] ; then
			echo "Install $PACKAGE"
		else
			echo "Install $1"
		fi
		exit $r
	else
		unset PACKAGE
		return $r
	fi
}

function addline {
	line="$1" ; shift
	file="$1" ; shift
	if sudo grep -q -F "$line" "$file" ; then
		return 0
	fi
	printf '%s\n' "$line" | sudo tee -a "$file"
}

main "$@"
