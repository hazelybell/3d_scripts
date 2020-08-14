#!/bin/bash

set -o errexit
set -o pipefail
#set -o xtrace

SERIAL=/dev/ttyUSB0

function upload {
	f="$1" ; shift
	if [[ ! -r "$f" ]] ; then
		echo "No such file $f"
		exit 2
	fi
	avrdude -c wiring \
		-b 115200 \
		-p ATmega2560 \
		-P /dev/ttyUSB0 \
		-U flash:w:"$f"
}

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
	stty time 0 \
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

function hello {
	while true ; do
		send M118 ping
		local -i s=$EPOCHSECONDS
		while (( s == EPOCHSECONDS )) ; do
			IFS='' read -sr RESPONSE <&99 || true
			if [[ ! -z "$RESPONSE" ]] ; then
				echo "< $RESPONSE"
			fi
			if [[ "$RESPONSE" == *ping* ]] ; then
				return 0
			fi
		done
	done
}

function commcheck {
	max=$((96-6)) # -6 for "M118 \n"
	send M118 $r
	for (( l = 0; l < max ; l++ )) ; do
	for i in {1..100} ; do
		s="$RANDOM$RANDOM$RANDOM$RANDOM$RANDOM"
		s="$s$s$s$s$s"
		s="${s:0:l}"
		send M118 $s >/dev/null
		while [[ "$RESPONSE" != *$s* ]] ; do
			IFS='' read -sr RESPONSE <&99 || true
			#echo "< $RESPONSE"
		done
	done
		echo "l=$l passed"
	done
	ok
}

function main {
	if (( $# > 0 )) ; then
		upload "$1"
		shift
	fi
	exec 99<>"$SERIAL"
	reset_printer <&99
	setup 500000
	hello
	send M115; ok
	send M502; ok
	send M851 Z-2.8; ok
	send M900 K2.4; ok
	send M205 E2.5; ok
	send M500; ok
	send M504; ok
	send M503; ok
	time commcheck
}

if [[ "$0" == "$BASH_SOURCE" ]] ; then
	main "$@"
fi
