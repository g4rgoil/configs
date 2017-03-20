#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

if [ -f /usr/share/git/completion/git-prompt.sh ]; then
    source /usr/share/git/completion/git-prompt.sh
    PS1='[\u@\h \W$(__git_ps1 " (%s)")]\$ '
else
    echo "Can't find git-completion.bash"
    PS1='[\u@\h \W]\$ '

fi

# Enable git completion
[ -f /usr/share/git/completion/git-completion.sh ] && source /usr/share/git/completion/git-completion.sh

# Source alias definitions from ~/.bash_aliases
[ -f ~/.bash_aliases ] && source ~/.bash_aliases

export KDEDIRS=$HOME/umbrello:$KDEDIRS
export PATH=$HOME/umbrello/bin:$PATH
export VISUAL=vim
export STUDIUM=$HOME/Dropbox/Studium
