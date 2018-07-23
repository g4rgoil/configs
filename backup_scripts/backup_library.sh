#!/bin/bash

export multiple_instance_exit=1
export insufficient_interval_exit=2
export connection_exit=3
export mount_exit=4
export borg_error_exit=5
export interrupt_exit=6


declare log_file        # Contains the log for the current backup
declare exclude_file    # Contains exclude patterns for borg (one per line)
declare slack_url       # The variable to use as webhook, when sending messagaes to slack

slack_hook_file="${HOME}/.slack-hook"
tformat="%Y-%m-%d %H:%M:%S"
empty_file="$(mktemp)"


# Send a message with the specified string to slack
#
# $1: the string to send
function slack_message() {
    if [[ -z $slack_url ]]; then
        set_slack_url "$slack_hook_file"
    fi

    curl -X POST --data-urlencode "payload={'text': '$(hostname): ${1?}'}" \
        "$slack_url" >/dev/null 2>&1
}


# Sets the value in $slack_url to the contets of the specified file
#
# $1: the file to use
function set_slack_url() {
    if [[ -f "${1?}" ]]; then
        slack_url="$(<"${1}")"
    else
        log_error "Plese create a file at '${1}' that contains your slack webhook"
        slack_url=""
    fi
}


# Add a timestamp to the beginning of each line and print it to the log file
function timestamp() {
    ts "[${tformat}]" >> "$log_file"
}


# Print the specified string to the log file
#
# $1: the string to print
function log() {
    echo -e "${1?}" | timestamp
    echo -e "${1?}"
}


# Print the specified string as error to the log file
#
# $1: the string to print
function log_error() {
    log "ERROR: ${1?}"
    >&2 echo "ERROR: ${1?}" >/dev/null
}


# Print a blank line to the log file
function blank_line() {
    echo "" >> "$log_file"
}


# Create the specified directory if it doesn't exist
#
# $1: the directory to create
# $2: the name of the directory (used for printing a log message)
function require_directory() {
    if [[ ! -d "${1?}" ]]; then
        log "Creating ${2?}"
        mkdir -p "$1"
    fi
}


# Return 0 if there is no process with the id in the specified file, 1 otherwise
#
# $1: the file with the pid in it
function require_single_instance() {
    if [[ -f "${1?}" ]] && kill -0 "$(cat "$1")" 2>/dev/null; then
        echo "Different instance of backup already running"
        return 1
    fi

    echo $$ > "$1"
}


# Return 0 if the last backup was more that the specified time interval ago, 1 otherwise
#
# $1: the file with the time of the last backup in it
# $2: The time interval to use
function require_backup_interval() {
    if [[ -f "${1?}" ]]; then
        local reference_file
        reference_file=$(mktemp)

        touch -t "$(<"$1")" "$1"
        touch -d "${2?}" "$reference_file"

        if [[ "$1" -nt $reference_file ]]; then
            log_error "Attempting backup to soon after previous backup"

            return 1
        fi
    fi
}


# Write the current timestamp to the specified file
#
# $1: the file to store the timestamp in
function set_timestamp() {
    date +%Y%m%d%H%M > "${1?}"
}


# Return 0 if the specified host can be pinged, 1 otherwise
#
# $1: the ssh host to ping
function verify_ssh_host() {
    if ! ping -c 1 "${1?}" >/dev/null 2>&1; then
        log_error "Unable to communicate with ssh server"
        log "Scheduling backup to be rerun later"

        slack_message "Backup failed, unable to communicate with ssh server"
        slack_message "Scheduling backup to be rerun"

        return 1
    fi
}


# Remove the at job with the id in the specified file, and delete the file
#
# $1: the file with the at id in it
function remove_scheduling() {
    if [[ -f "${1?}" ]]; then
        local job_id
        job_id=$(<"$1")
        at -r "$job_id" >/dev/null 2>&1
        rm "$1" >/dev/null 2>&1
    fi
}


# Create an at job that executes the specified script, and write the id to the
# specified file
#
# $1: the script to exectue
# $2: the file to write the id to
function add_scheduling() {
    echo "/bin/bash ${2?}" | \
        at now + 1 hour 2>&1 |      \
        tail -1 |                   \
        cut -f2 -d" " >             \
        "${1?}"
}

# Prompts the user for a password entry
#
# $1: the message to prompt with
# $2: the name variable to store the password in
function require_password {
    log "Quoting user for password"
    echo -n "${1:-Enter password}: "
    read -r -s "${2?}"
    echo ""
}


# Return 0 if mounting the device at the specified mountpoint is succesful,
# 1 otherwise
#
# $1: the mount point
function mount_device() {
    log "Mounting ${1?}"

    if ! mount "$1" || ! mountpoint -q "$1"; then
        log_error "Unable to mount $1"
        slack_message "Backup failed, unable to mount $1."

        return 1
    fi
}

# Checks if the device at the specified mountpoint is mounted, mounts it
# if necessary and checks if the mount was succesfull. If the the device
# was mounted, 'true' is stored in the specified variable
#
# $1: the mount point
# $2: the name of the variable
function ensure_mounted() {
    if ! mountpoint -q "${1?}"; then
        if ! mount_device "$1"; then
            return 1
        fi

        "$2"=true
    fi

    return 0
}


# Unmount the device at the specified mountpoint
#
# $1: the mount point
function unmount_device() {
    log "Unmounting ${1?}"
    umount "$1"
}


# Checks if the device at the specified mountpoint was mounted, using the
# specified value name and unmounts it if necessary.
#
# $1: the mount point
# $2: empty if not mounted, otherwise not empty. If not specified, nothing is done.
function ensure_unmounted() {
    if [[ -n "$2" ]]; then
        unmount_device "${1?}"
        return 0
    fi

    return 1
}


# Create a borg backup of the specified src directory, name the backup with the
# specified prefix and compress it with the specified compression algorithm
# This function uses the value in $BORG_REPO as the borg repository
# The value in $exclude_file is used as file that contains exclude_patterns
#
# $1: the source directory for the backup
# $2: the prefix used to name the backup
# $3: the algorithm used to compress the backup
function create_backup() {
    log "Creating backup"

    local rc
    rc=$(borg --show-rc create  \
        --warning               \
        --filter E              \
        --compression "${3:-lz4}"   \
        --exclude-from "${exclude_file:-$empty_file}"   \
        --patterns-from "${pattern_file:-$empty_file}"  \
        --exclude-caches        \
                                \
        ::"${2?}-{now}"         \
        "${1?}"                 \
        2>&1 | tee >(head -n -1 | timestamp) | tail -1 | awk 'NF>1{print $NF}')

    return "$rc"
}


# Prunes the borg repository specified in $BORG_REPO, only considers backups
# with the specified prefix in their names
#
# $1: the prefix to use
function prune_repository() {
    log "Pruning borg repository"

    local rc
    rc=$(borg --show-rc prune   \
        --warning               \
        --prefix "${1?}-"       \
        --keep-daily    7       \
        --keep-weekly   4       \
        --keep-monthly  12      \
        2>&1 | tee >(head -n -1 | timestamp) | tail -1 | awk 'NF>1{print $NF}')

    return "$rc"
}
