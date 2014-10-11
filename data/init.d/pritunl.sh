#!/bin/sh -e
# upstart-job
#
# Symlink target for initscripts that have been converted to Upstart.

set -e

INITSCRIPT="$(basename "$0")"
JOB="${INITSCRIPT%.sh}"

if [ "$JOB" = "upstart-job" ]; then
    if [ -z "$1" ]; then
        echo "Usage: upstart-job JOB COMMAND" 1>&2
    exit 1
    fi

    JOB="$1"
    INITSCRIPT="$1"
    shift
else
    if [ -z "$1" ]; then
        echo "Usage: $0 COMMAND" 1>&2
    exit 1
    fi
fi

COMMAND="$1"
shift


if [ -z "$DPKG_MAINTSCRIPT_PACKAGE" ]; then
    ECHO=echo
else
    ECHO=:
fi

$ECHO "Rather than invoking init scripts through /etc/init.d, use the service(8)"
$ECHO "utility, e.g. service $INITSCRIPT $COMMAND"

initctl show-config -e "$JOB"|grep -q '^  start on' || DISABLED=1

case $COMMAND in
status)
    $ECHO
    $ECHO "Since the script you are attempting to invoke has been converted to an"
    $ECHO "Upstart job, you may also use the $COMMAND(8) utility, e.g. $COMMAND $JOB"
    $COMMAND "$JOB"
    ;;
start|stop)
    $ECHO
    $ECHO "Since the script you are attempting to invoke has been converted to an"
    $ECHO "Upstart job, you may also use the $COMMAND(8) utility, e.g. $COMMAND $JOB"
    if status "$JOB" 2>/dev/null | grep -q ' start/'; then
        RUNNING=1
    fi
    if [ -z "$RUNNING" ] && [ "$COMMAND" = "stop" ]; then
        exit 0
    elif [ -n "$RUNNING" ] && [ "$COMMAND" = "start" ]; then
        exit 0
    elif [ -n "$DISABLED" ] && [ "$COMMAND" = "start" ]; then
        exit 0
    fi
    $COMMAND "$JOB"
    ;;
restart)
    $ECHO
    $ECHO "Since the script you are attempting to invoke has been converted to an"
    $ECHO "Upstart job, you may also use the stop(8) and then start(8) utilities,"
    $ECHO "e.g. stop $JOB ; start $JOB. The restart(8) utility is also available."
    if status "$JOB" 2>/dev/null | grep -q ' start/'; then
        RUNNING=1
    fi
    if [ -n "$RUNNING" ] ; then
        stop "$JOB"
    fi
    # If the job is disabled and is not currently running, the job is
    # not restarted. However, if the job is disabled but has been forced into the
    # running state, we *do* stop and restart it since this is expected behaviour
    # for the admin who forced the start.
    if [ -n "$DISABLED" ] && [ -z "$RUNNING" ]; then
        exit 0
    fi
    start "$JOB"
    ;;
reload|force-reload)
    $ECHO
    $ECHO "Since the script you are attempting to invoke has been converted to an"
    $ECHO "Upstart job, you may also use the reload(8) utility, e.g. reload $JOB"
    reload "$JOB"
    ;;
*)
    $ECHO
    $ECHO "The script you are attempting to invoke has been converted to an Upstart" 1>&2
    $ECHO "job, but $COMMAND is not supported for Upstart jobs." 1>&2
    exit 1
esac
