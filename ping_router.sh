#!/bin/bash

function attempt_recover {
	ifdown wlp3s0
	ifup wlp3s0
	ifup wlp3s0:1
}

function config {
	interval=10
	add wlp3s0 192.168.0.13 192.168.0.1
	add wlp3s0:1 192.168.0.113 192.168.0.1
	logfile=ping_router.log
	max_size=$((1024 * 1024))
}

function add {
	local dev="$1" ; shift
	local src="$1" ; shift
	local dst="$1" ; shift
	local cmd="$1" ; shift
	devs+=("$dev")
	dsts+=("$dst")
	srcs+=("$src")
}

function init {
	declare -g -a devs
	declare -g -a dsts
	declare -g -a srcs
	declare -g -i interval=1
	declare -g log_file="${BASH_SOURCE##*.}".log
	declare -g -i max_size=$((1024 * 1024))
	config
	declare -g -i n="${#devs[@]}"
	declare -g -r CANARY='-_-;;'
	if [[ "$PATH" != */sbin* ]] ; then
		PATH="$PATH:/sbin"
	fi
	if [[ "$PATH" != */usr/sbin* ]] ; then
		PATH="$PATH:/usr/sbin"
	fi
	export PATH
}

function die {
	printf '%s' "$CANARY"
	printf ' %s' "$@" "(dev=$dev src=$src dst=$dst)"
	printf '\n'
	exit 1
}

function run {
	local cmd="$1" ; shift
	local path
	if type "$cmd" >/dev/null ; then
		echo ">_> $cmd"
		"$cmd" "$@" || die "command failed: $cmd" "$@"
	else
		echo "o_O $cmd not found"
		return 0
	fi
}

function has_addr {
	ip addr show $dev \
        | grep -Fq -- "$src"
	return $?
}

function proc_wireless {
        grep -Fq -- "${dev#*:}" /proc/net/wireless
	return $?
}

function diagnose {
	i="$1" ; shift
	dst="${dsts[i]}"
	dev="${devs[i]}"
	src="${srcs[i]}"
	run ip addr show $dev
	run has_addr
	if [[ "$dev" == w* ]] ; then
		run proc_wireless
		run iw dev "$dev" station dump
	fi
	run ping \
		-I "$src" \
		-n \
		-q \
		-w 10 \
		"$dst"
}

function all_devs {
	printf '^_^ ========== '
	date
	local -i i
	for (( i = 0; i < n; i++)) ; do
		( diagnose $i ) &
	done
	wait
}

function test {
	exec 99>"$logfile".tmp
	all_devs 1>&99 2>&99
	exec 99>&-
	if [[ -t 1 ]] ; then
		grep 'packet loss' "$logfile".tmp | grep -v '0%'
	fi
	if grep -Fq -- "$CANARY" "$logfile".tmp ; then
		cat "$logfile.tmp" >>"$logfile"
		local size=$(stat --format=%s "$logfile")
		if (( size > max_size )) ; then
			lines=$(wc -l "$logfile")
			tail -n $(( lines / 2 )) "$logfile" >"$logfile".tmp
			mv -f "$logfile".tmp "$logfile"
		fi
	fi
	rm -f "$logfile".tmp
}

function loop {
	while true ; do
		test
	done
}

function ctrlc2 {
	pkill -g 0
}

function ctrlc {
	trap ctrlc2 INT
	for pid in $(jobs -p) ; do
		kill -SIGINT $pid
	done
	wait
	exit 130
}

function main {
	trap ctrlc INT
	init
	loop
}


main
