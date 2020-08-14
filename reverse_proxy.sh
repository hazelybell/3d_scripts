#!/bin/bash

# reverse_proxy.sh -- Install apache2 reverse proxy for octoprint
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

SERVERNAME="$HOSTNAME"
CONFIGFILE="$SERVERNAME.conf"

set -o errexit
set -o pipefail
set -o xtrace

local index="${BASH_SOURCE%/*}/www/index.html"
[[ -f "$index" ]]
local flask="${BASH_SOURCE%/*}/www/index.html"
[[ -f "$index" ]]

if [[ ! -d /etc/apache2/sites-available ]] ; then
	sudo aptitude install apache2 apache2-doc
fi

if [[ ! -f /etc/apache2/mods-available/wsgi.load ]] ; then
	sudo aptitude install libapache2-mod-wsgi-py3
fi

if ! which sar ; then
	sudo aptitude install sysstat
fi

if ! which flask ; then
	sudo aptitude install python3-flask
fi

sudo tee /etc/apache2/sites-available/"$CONFIGFILE" <<EOF
ServerName $SERVERNAME
<VirtualHost *:80>
	ServerName $SERVERNAME
	ServerAdmin apache@hazel.zone
	DocumentRoot /var/www/html
        ErrorLog \${APACHE_LOG_DIR}/error.log
        CustomLog \${APACHE_LOG_DIR}/access.log combined
	ProxyPass "/christine"  "http://127.0.0.1:5000/"
	ProxyPassReverse "/christine"  "http://127.0.0.1:5000/"
	ProxyTimeout 5
	<Location "/">
	<RequireAny>
		Require ip 192.168
		Require ip 127
		Require ip 10
	</RequireAny>
	</Location>
	<Location "/christine">
		SetEnv proxy-sendcl
	</Location>
</VirtualHost>
EOF

sudo cp "$index" /var/www/index.html

(
	cd /etc/apache2/sites-enabled
	sudo rm -f *.conf
	sudo ln -s ../sites-available/"$CONFIGFILE" 000-"$CONFIGFILE"
)

enable proxy.conf
enable proxy.load
enable proxy_http.load
enable wsgi.load
enable wsgi.conf

if [[ -f /etc/init.d/sysstat ]] ; then
	sudo mv /etc/init.d/sysstat /etc/init.d/sadc
	sudo systemctl enable sadc
	sudo systemclt restart sadc
fi

sudo systemctl reenable apache2
sudo systemctl restart apache2

} # main

function enable {
	local mod=$1 ; shift
	(
	cd /etc/apache2/mods-enabled
	[[ -f ../mods-available/"$mod" ]]
	sudo ln -s -f ../mods-available/"$mod"
	)
}

main
