#!/bin/bash

script_directory="/etc/backup_scripts"
library_file="${script_directory}/backup_library.sh"

# shellcheck source=/etc/backup_scripts/backup_library.sh
source $library_file

script_file="${script_directory}/xps13_backup.sh"
exclude_file="${script_directory}/mybook.exclude"

log_directory="/var/log/backup_logs"
ts_file="${log_directory}/mybook.ts"
log_file="${log_directory}/mybook.log"
job_file="${log_directory}/mybook.job"

pid_file="/var/run/xps13-backup.pid"

interval="-24 hours"

backup_src="/hdd/mybook"
unmount_src=false

ssh_user="pascal"
ssh_host="192.168.3.47"

export BORG_REPO="ssh://${ssh_user}@${ssh_host}/pool/pascal/borg-repository"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/zfsnas_mybook"


function finish() {
    exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        set_timestamp $ts_file
    fi
    
    if [[ "$unmount_src" = true ]]; then
        unmount_device $backup_src
        unmount_src=false
    fi

    if [[ $exit_code -eq 0 ]]; then
        log "Finishing backup procedure"
        slack_message "Finished weekly mybook backup"
    else
        log "Backup procedure failed with exit code $exit_code"
        slack_message "Weekly mybook backup failed"
    fi
    
    blank_line
}

function terminate() {
    log_error "The backup procedure was interrupted by a signal"
    
    if [[ "$unmount_src" = true ]]; then
        unmount_device $backup_src
        unmount_src=false
    fi
    
    blank_line
}

trap finish EXIT

trap 'trap "" EXIT; terminate' \
    HUP INT QUIT TERM


if ! require_single_instance $pid_file; then
    exit $multiple_instance_exit
fi

require_directory $log_directory "log directory"
require_directory $backup_src "mount point for mybook"

remove_scheduling $job_file

log "Starting backup procedure"
slack_message "Starting weekly mybook backup"

if ! require_backup_interval $ts_file "$interval"; then
    exit $insufficient_interval_exit
fi

if ! verify_ssh_host $ssh_host; then
    add_scheduling $job_file $script_file
    exit $connection_exit
fi

if ! mountpoint -q $backup_src; then
    if ! mount_device $backup_src; then
        exit $mount_exit
    fi

    unmount_src=true
fi


create_backup $backup_src "mybook" "zlib,5"
backup_exit=$?

prune_repository "mybook" 
prune_exit=$?

borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ $borg_exit -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit $borg_error_exit
fi

exit 0
