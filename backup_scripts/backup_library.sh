#!/bin/bash

declare ts_file         # File that stores the timestamp for the 
declare log_file        # Contains the log for the current backup
declare pid_file        # Contains pid of currently running backup
declare job_file        # Contains at job id if one is created
declare ssh_host        # User name to use one remote borg server
declare backup_src      # Path to the directory that needs to be backed up
declare script_file     # Path to the currently running script
declare exclude_file    # Contains exclude patterns for borg (one per line)

slack_url="https://hooks.slack.com/services/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"
tformat="%Y-%m-%d %H:%M:%S"


backup_interval="-6 hours"
reference_file=$(mktemp)

function slack_message() {
    curl -X POST --data-urlencode "payload={'text': '$(hostname): ${1?}'}" \
        $slack_url >/dev/null 2>&1
}

function timestamp() {
    ts "[${tformat}]" >> "$log_file"
}

function log() {
    echo -e "${1?}" | timestamp
}

function log_error() {
    log "ERROR: ${1?}"
}

function blank_line() {
    echo "" >> "$log_file"
}

function require_directory() {
    if [[ ! -d "${1?}" ]]; then
        log "Creating ${2?}"
        mkdir -p "$1"
    fi
}

function require_single_instance() {
    if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
        echo "Different instance of backup already running"
        exit 0
    fi

    echo $$ > "$pid_file"
}

function require_backup_interval() {
    if [[ -f "$ts_file" ]]; then
        touch -t "$(<"$ts_file")" "$ts_file"
        touch -d "$backup_interval" "$reference_file"

        if [[ "$ts_file" -nt $reference_file ]]; then
            log_error "Attempting backup to soon after previous backup"

            exit 1
        fi
    fi
}

function set_timestamp() {
    date +%Y%m%d%H%M > "$ts_file"
}

function verify_ssh_host() {
    if ! ping -c 1 "$ssh_host" >/dev/null 2>&1; then
        log_error "Unable to communicate with ssh server"
        log "Scheduling backup to be rerun later"

        slack_message "Backup failed, unable to communicate with ssh server"
        slack_message "Scheduling backup to be rerun"

        add_scheduling
        exit 2
    fi
}

function remove_scheduling() {
    if [[ -f "$job_file" ]]; then
        job_id=$(<"$job_file")
        at -r "$job_id" >/dev/null 2>&1
        rm "$job_file" >/dev/null 2>&1
    fi
}

function add_scheduling() {
    echo "/bin/bash $script_file" | \
        at now + 1 hour 2>&1 |      \
        tail -1 |                   \
        cut -f2 -d" " >             \
        "$job_file"
}

function mount_device() {
    log "Mounting ${1?}"

    if ! mount "$1" || ! mountpoint -q "$1"; then
        log_error "Unable to mount $1"
        slack_message "Backup failed, unable to mount $1."
        exit 2
    fi
}

function unmount_device() {
    log "Unmounting ${1?}"
    umount "$1"
}

function create_backup() {
    log "Creating backup"

    borg create                 \
        --warning               \
        --filter E              \
        --compression "${2?}"   \
        --exclude-from "$exclude_file"    \
        --exclude-caches        \
                                \
        ::"${1?}-{now}"         \
        "$backup_src"           \
        2>&1 | timestamp
}

function prune_repository() {
    log "Pruning borg repository"

    borg prune                  \
        --warning               \
        --prefix "${1?}-"          \
        --keep-daily    7       \
        --keep-weekly   4       \
        --keep-monthly  12      \
        >/dev/null 2>&1 | timestamp 
}
