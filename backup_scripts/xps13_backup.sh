#!/bin/bash

script_directory="/etc/backup_scripts"
library_file="${script_directory}/backup_library.sh"

# shellcheck source=/etc/backup_scripts/backup_library.sh
source $library_file

script_file="${script_directory}/xps13_backup.sh"
pattern_file="${script_directory}/root.pattern"

log_directory="/var/log/backup_logs"
ts_file="${log_directory}/xps13.ts"
log_file="${log_directory}/xps13.log"
job_file="${log_directory}/xps13.job"

pid_file="/var/run/xps13-backup.pid"

interval="-6 hours"

backup_src="/"

ssh_user="root"
ssh_host="pascal_desktop"

export BORG_REPO="ssh://${ssh_user}@${ssh_host}/hdd/mybook/Borg_Backups/pascal_xps13"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/mybook_xps13"


function finish() {
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        set_timestamp $ts_file
    fi

    if [[ $exit_code -eq 0 ]]; then
        log "Finishing backup procedure"
    else
        log "Backup procedure failed with exit code $exit_code"
    fi

    blank_line
    exit $exit_code
}

function terminate() {
    log_error "The backup procedure was interrupted by a signal"
    blank_line
    exit $interrupt_exit
}

trap finish EXIT

trap 'trap "" EXIT; terminate' \
    HUP INT QUIT TERM

log "Starting backup procedure"

if ! require_root; then
    exit $permission_error
fi

if ! require_single_instance $pid_file; then
    exit $multiple_instance_exit
fi

require_directory $log_directory "log directory"

remove_scheduling $job_file

if ! require_backup_interval $ts_file "$interval"; then
    exit $insufficient_interval_exit
fi

if ! verify_ssh_host $ssh_host; then
    add_scheduling $job_file $script_file
    exit $connection_exit
fi

create_backup $backup_src "pascal_xps13" "lz4"
backup_exit=$?

prune_repository "pascal_xps13-"
prune_exit=$?

borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ ${borg_exit} -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit $borg_error_exit
fi

exit 0
