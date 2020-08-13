#!/bin/bash

set -o errexit
set -o pipefail
#set -o xtrace

SERIAL=/dev/ttyUSB0

f="$1"
shift

if [[ ! -r "$f" ]] ; then
	echo "No such file $f"
	exit 2
fi

if [[ ! -c "$SERIAL" ]] ; then
	echo "No such port $SERIAL"
	exit 3
fi


function setup {
	speed="$1"
	shift
	(( speed > 0 ))
	setserial -a /dev/fd/99 spd_cust divisor $((24000000/speed))
	stty 38400 <&99 || true
	stty time 10 \
		rows 0 cols 0 line 0 min 1 \
		-parenb -parodd -cmspar cs8 hupcl -cstopb cread clocal \
		-crtscts \
		-ignbrk -brkint -ignpar -parmrk -inpck -istrip -inlcr -igncr \
		-icrnl -ixon -ixoff -iuclc -ixany -imaxbel -iutf8 \
		-opost -olcuc -ocrnl -onlcr -onocr -onlret -ofill -ofdel \
		nl0 cr0 tab0 bs0 vt0 ff0 -isig -icanon -iexten -echo -echoe \
		-echok -echonl -noflsh -xcase -tostop -echoprt \
		-echoctl -echoke -flusho -extproc \
		<&99
}

function ok {
	RESPONSE=
	while [[ "$RESPONSE" != *ok* ]] ; do
		IFS='' read -sr RESPONSE <&99 || true
		echo "< $RESPONSE"
	done
}

function send {
        echo "> $@"
	printf "%s " "$@" >&99
	printf "\n" >&99
}

function main {
	exec 99<>"$SERIAL"
	./reset <&99
	setup 250000
	ok
	send M502
	ok
	send M500
	ok
	send M575 B1000000
	setup 1000000
	sleep 0.1
	send M115
	ok
	send M115
	ok
}

main
