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

if [ -f /usr/lib/bash-git-prompt/gitprompt.sh ]; then
    GIT_PROMPT_ONLY_IN_REPO=1
    # To use upstream's default theme
    # GIT_PROMPT_THEME=Default
    # To use upstream's default theme, modified by arch maintainer
    GIT_PROMPT_THEME=Default_Arch
    source /usr/lib/bash-git-prompt/gitprompt.sh
fi

export KDEDIRS=$HOME/umbrello:$KDEDIRS
export PATH=$HOME/umbrello/bin:$PATH
export VISUAL=vim
export STUDIUM=$HOME/Dropbox/Studium
