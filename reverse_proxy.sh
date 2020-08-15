#!/bin/bash

# reverse_proxy.sh -- Install apache2 reverse proxy for octoprint/gitit
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
GITIT_HOME="/var/lib/gitit"

set -o errexit
set -o pipefail
set -o xtrace

local www="${BASH_SOURCE%/*}/www"
[[ -d "$www" ]]

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

if ! which gitit ; then
	sudo aptitude install gitit
fi

sudo tee /etc/apache2/sites-available/"$CONFIGFILE" <<EOF
ServerName $SERVERNAME
<VirtualHost *:80>
	ServerName $SERVERNAME
	ServerAdmin apache@hazel.zone
	DocumentRoot /var/www/html
	WSGIDaemonProcess carrie user=www-data group=www-data threads=1
	WSGIScriptAlias / $www/carrie.wsgi
ErrorLog \${APACHE_LOG_DIR}/error.log
CustomLog \${APACHE_LOG_DIR}/access.log combined
	ProxyTimeout 5
	<Location "/">
	<RequireAny>
		Require ip 192.168
		Require ip 127
		Require ip 10
	</RequireAny>
	</Location>
	<Location "/christine/">
		ProxyPass  "http://127.0.0.1:5000/"
		ProxyPassReverse "/"
		SetEnv proxy-sendcl
		RequestHeader set X-Script-Name "/christine/"
	</Location>
	<Location "/wiki/">
		RequestHeader set Authorization "expr=%{base64:%{REMOTE_ADDR}:hunter2}"
		ProxyPass  "http://127.0.0.1:5002/"
		ProxyPassReverse "/"
		SetEnv proxy-sendcl
		SetOutputFilter proxy-html
		ProxyHTMLURLMap / /wiki/
		RequestHeader unset Accept-Encoding
	</Location>
	<Directory /var/www>
		WSGIProcessGroup carrie
		WSGIApplicationGroup %{GLOBAL}
		Require all granted
	</Directory>
</VirtualHost>
EOF

sudo rsync -rP "$www"/ /var/www/

(
	cd /etc/apache2/sites-enabled
	sudo rm -f *.conf
	sudo ln -s ../sites-available/"$CONFIGFILE" 000-"$CONFIGFILE"
)

enable proxy.conf
enable proxy.load
enable proxy_http.load
enable proxy_html.load
enable proxy_html.conf
enable wsgi.load
enable wsgi.conf
enable headers.load

sudo tee /etc/systemd/system/sadc.service <<-EOF
	[Unit]
	Description=sysstat's sadc
	After=network.target

	[Service]
	User=root
	Group=root
	Nice=19
	Type=simple
	ExecStart=/usr/lib/sysstat/sadc -F 10 -

	[Install]
	WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/gitit.service <<-EOF
	[Unit]
	Description=gitit wiki
	After=network.target

	[Service]
	User=gitit
	Group=gitit
	Nice=19
	Type=exec
	WorkingDirectory=$GITIT_HOME
	StandardOutput=journal
	ExecStart=$(which gitit) --debug --config-file=$GITIT_HOME/config

	[Install]
	WantedBy=multi-user.target
EOF

# I like matching username/group IDs for some reason...
if [[ -r /etc/adduser.conf ]] ; then
source /etc/adduser.conf
else
local FIRST_SYSTEM_UID=100
local FIRST_SYSTEM_GID=100
local DSHELL=/bin/bash
fi

local -i id=$FIRST_SYSTEM_UID
if (( FIRST_SYSTEM_GID > FIRST_SYSTEM_UID )) ; then
id=FIRST_SYSTEM_UID
fi

if ! { id -g gitit || id -u gitit ; } >/dev/null ; then
while { getent passwd $id || getent group $id ; } >/dev/null ; do
id+=1
done
elif ! id -g gitit >/dev/null ; then
id=$(id -u gitit)
else
id=$(id -g gitit)
fi

if ! id -g gitit >/dev/null ; then
sudo addgroup \
--system \
--gid $id \
gitit
fi

if ! id -u gitit >/dev/null ; then
# Leave the user with a disabled password, but a shell.
# This means they can login if ssh keys are set up.
# Could be useful for rsyncing things to the gitit user, etc.
sudo adduser \
--system \
--disabled-password \
--gecos "Gitit Daemon User" \
--home "$GITIT_HOME" \
--ingroup gitit \
--home "$GITIT_HOME" \
--ingroup gitit \
--uid $id \
--shell "$DSHELL" \
gitit
fi

if [[ ! -d "$GITIT_HOME" ]] ; then
sudo mkdir -p "$GITIT_HOME"
sudo rsync -aP /etc/skel/ "$GITIT_HOME"/
fi

sudo mkdir -p "$GITIT_HOME"/.ssh
cat <(
if [[ -f "$HOME"/.ssh/authorized_keys ]] ; then
cat "$HOME"/.ssh/authorized_keys
else
echo
fi
) <(
if sudo test -f "$GITIT_HOME"/.ssh/authorized_keys ; then
sudo cat "$GITIT_HOME"/.ssh/authorized_keys
else
echo
fi
) | sort | uniq | sudo tee "$GITIT_HOME"/.ssh/authorized_keys

sudo tee "$GITIT_HOME"/config <<EOF
address: 127.0.0.1
port: 5002
wiki-title: Carrieki
repository-type: Git
repository-path: wikidata
require-authentication: none
authentication-method: http
static-dir: wikidata/static
default-extension: page
default-page-type: Markdown
math: mathjax
templates-dir: wikidata/templates
log-file: gitit.log
log-level: WARNING
front-page: Front Page
no-delete: Front Page, Help
no-edit: Help
default-summary: Too lazy to write a summary of my changes.
delete-summary: Deleted using web interface.
table-of-contents: yes
use-cache: no
max-upload-size: 100M
max-page-size: 1M
compress-responses: no
use-recaptcha: no
mail-command:
use-feed: no
base-url: /wiki
absolute-urls: no
EOF

sudo chown gitit:gitit -Rc "$GITIT_HOME"

sudo systemctl daemon-reload
sudo systemctl reenable sadc
sudo systemctl restart sadc
sudo systemctl reenable gitit
sudo systemctl restart gitit
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
