# Config files by Pascal Mehnert

## setup

## zsh

Configuration files for the Z Shell (zsh), oh-my-zsh and powerlevel9k.

- [`zsh/zshrc`](zsh/zshrc) - main zsh configuration
- [`zsh/zsh-aliases`](zsh/zsh-aliases) - alias definitions, gets sourced in `zshrc`
- [`zsh/zsh-functions`](zsh/zsh-functions) - function definitions, gets sourced in `zshrc`
- [`zsh/oh-my-zsh-config`](zsh/oh-my-zsh-config) - oh-my-zsh and powerlevel9k configuration, gets sourced in `zshrc`
- [`zsh/zshenv`](zsh/zshenv) - envrionment variable definitions, gets automatically sourced by zsh

## bash

Configuration files for the Bourne-Again Shell (bash).

- [`bash/bash-profile`](bash/bash-profile) - ensures bashrc is being sourced
- [`bash/bashrc`](bash/bashrc) - main bash configuration
- [`bash/bash-aliases`](bash/bash-aliases) - alias definitions, get sourced in `bashrc` (symlinked to `zsh/zsh-aliases`)
- [`bash/bashenv`](bash/bashenv) - envrionment variable definitions, gets sourced in `bashrc` (symlinked to `zsh/zshenv`)

## tmux

Configuration files for tmux, tmux-powerline and tmuxinator.

- [`tmux/tmux.conf`](tmux/tmux.conf) - mainly key bindings for tmux, sources either tmux.local.conf or tmux.remote.conf
- [`tmux/tmux.local.conf`](tmux/tmux.local.conf) - configuration for local tmux sessions, sources tmux-powerline and tmux-plugin-manager
- [`tmux/tmux.remote.conf`](tmux/tmux.remote.conf) - configuration for remote tmux session, provides basic styling for the status bar
- [`tmux/powerlinerc`](tmux/powerlinerc) - main configuration for the tmux powerline
- [`tmux/powerline-themes/`](tmux/powerline-themes) - contains user themes for the tmux powerline
- [`tmux/powerline-segments/`](tmux/powerline-segments) - contains user segments for the tmux powerline
- [`tmux/tmuxinator/`](tmux/tmuxinator) - contains layouts for tmuxinator to use
- [`tmux/layouts/`](tmux/layouts) - contains custom scripted layouts that can be sourced in tmux

## vim

Configuration files for vim, neovim, gvim and ideavim.

- [`vim/vimrc`](vim/vimrc) - main configuration file for vim, currently only fully works in neovim
- [`vim/gvimrc`](vim/gvimrc) - configuartion for gvim
- [`vim/ideavimrc`](vim/ideavimrc) - configuration for ideavim in the jetbrains IDEs
- [`vim/ftdetect/`](vim/ftdetect) - contains files for filetype detection in vim
- [`vim/skeletons/`](vim/skeletons) - contains skeleton files for vim-skeletons
- [`vim/snippets/`](vim/snippets) - contains user snippets for UltiSnips

## misc

Miscellaneous configuration files for various applications.

- [`misc/todo.cfg`](misc/todo.cfg) - configuration for main todo.txt file
- [`misc/pse.todo.cfg`](misc/pse.todo.cfg) - configuration for pse todo.txt file
- [`misc/tobuy.cfg`](misc/tobuy.cfg) - configuration for tobuy todo.txt file
- [`misc/todo-actions/`](misc/todo-actions) - custom action for todo.txt
- [`misc/cleanup.hook`](misc/cleanup.hook) - pacman hook that keeps the pacman package cache clean
- [`misc/latexmkrc`](misc/latexmkrc) - basic configuration for latexmk
- [`misc/neofetch.cfg`](misc/neofetch.cfg) - configuration for neofetch
- [`misc/pycodestylerc`](misc/pycodestylerc) - configuration for pycodestyle
- [`misc/warprc`](misc/warprc) - warp point definitions for the oh-my-zsh wd tool
- [`misc/yay.cfg`](misc/yay.cfg) - main configuration for the yay yaourt helper

## backup\_scripts

Various backup scripts, mostly using borg to backup my systems and data.

- [`backup_scripts/backup_library.sh`](backup_scripts/backup_library.sh) - contains reusable functionality used by one or more backup scripts
- [`backup_scripts/desktop_backup.sh`](backup_scripts/desktop_backup.sh) - creates a root directory backup of my desktop on my external hard drive
- [`backup_scripts/xps13_backup.sh`](backup_scripts/xps13_backup.sh) - creates a root directory backup of my laptop on my external hard drive
- [`backup_scripts/media_backup.sh`](backup_scripts/media_backup.sh) -  creates a backup of my media hard drive on my my external hard drive
- [`backup_scripts/mybook_backup.sh`](backup_scripts/mybook_backup.sh) - creates an _offsite_ backup of my external hard drive on our local server
- [`backup_scripts/usb_backup.sh`](backup_scripts/usb_backup.sh) - creates a backup of a USB stick on my external hard drive
- `backup_scripts/*.pattern` - contains patterns used by borg to include and exclude files

## templates

Various templates used to create system specific configuration files.

- [`templates/git-setup-hook`](templates/git-setup-hook) - git hook that automatically runs the setup script, runs after every commit and push if placed and named correctly
- [`templates/xinitrc`](templates/xinitrc) - basic xinitrc, based on the one provided by LightDM
