#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

PS1='[\u@\h \W]\$ '

# Source alias definitions from ~/.bash_aliases
if [ -f ~/.bash_aliases ]; then
    source ~/.bash_aliases
fi

export KDEDIRS=$HOME/umbrello:$KDEDIRS
export PATH=$HOME/umbrello/bin:$PATH
export VISUAL=vim
export STUDIUM=$HOME/Dropbox/Studium
