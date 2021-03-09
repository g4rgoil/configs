#!/bin/bash

SCRIPT_FILE="${HOME}/.local/share/setup/setup.py"
SETUP_TIMESTAMP_FILE="${HOME}/.setup.ts"
SETUP_INTERVALL="30"

function run_setup_script() {
    if [[ ! -e $SCRIPT_FILE ]]; then
        echo "Can't locate setup script."
    else
        date +%Y%m%d > "$SETUP_TIMESTAMP_FILE"
        python "$SCRIPT_FILE" all --install all
    fi
}

(( now=$(date +%Y%m%d) ))

if [[ ! -e $SETUP_TIMESTAMP_FILE ]]; then
    (( next=0 ))
else
    (( next=$(cat "$SETUP_TIMESTAMP_FILE")+SETUP_INTERVALL ))
fi

if [[ $next -le $now ]]; then
    echo -n "Do you wish to run the setup script? [Y/n] "
    read -r answer

    case "$answer" in
        [Yy]*|"" ) run_setup_script;;
        * ) ;;
    esac
fi
