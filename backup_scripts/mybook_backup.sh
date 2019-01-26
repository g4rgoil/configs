#!/bin/bash

script_directory="/etc/backup_scripts"
library_file="${script_directory}/backup_library.sh"

# shellcheck source=/etc/backup_scripts/backup_library.sh
source ${library_file}

script_file="${script_directory}/xps13_backup.sh"
pattern_file="${script_directory}/mybook.pattern"

log_directory="/var/log/backup_logs"
ts_file="${log_directory}/mybook.ts"
log_file="${log_directory}/mybook.log"
job_file="${log_directory}/mybook.job"

pid_file="/var/run/xps13-backup.pid"

interval="-24 hours"

backup_src="/hdd/mybook"
unmount_src=""

repo_path="/pool/usr/pascal/planck_mybook"

ssh_user="pascal"
ssh_host="192.168.1.53"
ssh_port="2222"

export BORG_REPO="ssh://${ssh_user}@${ssh_host}:${ssh_port}${repo_path}"
export BORG_PASSPHRASE=""
export BORG_KEY_FILE="/root/.config/borg/keys/planck_mybook"

declare original_size
declare new_size

function unmount_backup_devices() {
    if ensure_unmounted ${backup_src} ${unmount_src}; then
        unmount_src=""
    fi
}

function finish() {
    exit_code=$?

    unmount_backup_devices

    if [[ ${exit_code} -eq 0 ]]; then
        set_timestamp ${ts_file}

        log "Repo size increased from ${original_size} to ${new_size}"
        slack_message "Repo size increased from ${original_size} to ${new_size}"

        log "Finishing backup procedure"
        slack_message "Finished weekly mybook backup"
    else
        log "Backup procedure failed with exit code $exit_code"
        slack_message "Weekly mybook backup failed"
    fi

    blank_line
    exit ${exit_code}
}

function terminate() {
    log_error "The backup procedure was interrupted by a signal"

    unmount_backup_devices

    blank_line
    exit ${interrupt_exit}
}

trap finish EXIT

trap 'trap "" EXIT; terminate' \
    HUP INT QUIT TERM


log "Starting backup procedure"
slack_message "Starting weekly mybook backup"

if ! require_root; then
    exit ${permission_error}
fi

if ! require_single_instance ${pid_file}; then
    exit ${multiple_instance_exit}
fi

require_directory ${log_directory} "log directory"
require_directory ${backup_src} "mount point for mybook"

remove_scheduling ${job_file}

if ! require_backup_interval ${ts_file} "$interval"; then
    exit ${insufficient_interval_exit}
fi

if ! verify_ssh_host ${ssh_host}; then
    add_scheduling ${job_file} ${script_file}
    exit ${connection_exit}
fi

if ! ensure_mounted ${backup_src} unmount_src; then
    exit ${mount_exit}
fi

original_size=$(ssh -p"${ssh_port}" "${ssh_user}@${ssh_host}" "du -hs ${repo_path}" | cut -f1)

create_backup ${backup_src} "mybook" "none"
backup_exit=$?

prune_repository "mybook"
prune_exit=$?

new_size=$(ssh -p"${ssh_port}" "${ssh_user}@${ssh_host}" "du -hs ${repo_path}" | cut -f1)

borg_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [[ ${borg_exit} -gt 0 ]]; then
    log_error "Borg exited with non-zero exit code $borg_exit"
    exit ${borg_error_exit}
fi

exit 0
