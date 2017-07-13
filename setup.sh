#!/bin/bash

# Small script for creating symbolic links to the files in this repository

while getopts 


function setup_zsh {
    echo "Setting up zsh"

    if [ -d ./zsh ]; then
        for path in ./zsh/*; do
            filename=$(basename $path)
            if [ ! -f /etc/zsh/$filename ]; then
                echo "Creating link to /etc/zsh/$filename"

                ln -s "$path" "/etc/zsh/$filename"
            fi
        done
    else
        echo "Can't find zsh directory. Check your cwd!"
    fi
}


function setup_bash {
    echo "Setting up bash"

    if [ -d ./bash ]; then
        for path in ./bash/*; do
            filename=$(basename $path)
            if [ ! -f /etc/bash.$filename ]; then
                echo "Creating link to /etc/bash.$filename"

                ln -s "$path" "/etc/bash.$filename"
            fi
        done
    else
        echo "Can't find bash directory. Check your cwd!"
    fi
}
