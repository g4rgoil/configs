#!/bin/bash

script_directory="/etc/backup_scripts"
library_file="${script_directory}/backup_library.sh"

# shellcheck source=/dev/null
source $library_file

script_file="${script_directory}/xps13_backup.sh"
exclude_file="${script_directory}/root.exclude"

log_directory="/var/log/backup_logs"
ts_file="${log_directory}/xps13.ts"
log_file="${log_directory}/root.log"
job_file="${log_directory}/xps13.job"

pid_file="/var/run/xps13-backup.pid"

backup_src="/"

ssh_user="root"
ssh_host="pascal_desktop"

export BORG_REPO="ssh://${ssh_user}@${ssh_host}/hdd/mybook/Borg_Backups/pascal_xps13"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/mybook_xps13"


function finish() {
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        set_timestamp
    fi
    
    if [[ $exit_code -eq 0 ]]; then
        log "Finishing backup procedure"
    else
        log "Backup procedure failed with exit code $exit_code"
    fi

    blank_line
}

function terminate() {
    log_error "The backup procedure was interrupted by a signal"
    blank_line
}

trap finish EXIT

trap 'trap "" EXIT; terminate' \
    HUP INT QUIT TERM


require_single_instance

require_directory $log_directory "log directory"

remove_scheduling

log "Starting backup procedure"

require_backup_interval
verify_ssh_host


create_backup "pascal_xps13" "lz4"
backup_exit=$?

prune_repository "pascal_xps13-"
prune_exit=$?

borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ $borg_exit -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit 3
fi

exit 0
