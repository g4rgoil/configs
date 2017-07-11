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
[ -f /usr/share/git/completion/git-completion.bash ] && source /usr/share/git/completion/git-completion.bash

# Enable maven completion (github.com/juven/maven-bash-completion)
[ -f /etc/maven-bash-completion.bash ] && source /etc/maven-bash-completion.bash

# Source alias definitions from ~/.bash_alias
[ -f ~/.bash_aliases ] && source ~/.bash_aliases

# Start the ssh-agent if it is not already running
if ! pgrep -u "$USER" ssh-agent > /dev/null; then
    ssh-agent > ~/.ssh-agent-thing
fi

if [[ "$SSH_AGENT_PID" == "" ]]; then
    eval "$(<~/.ssh-agent-thing)"
fi

export VISUAL=vim
export GRAPHICAL=gvim
export PDFVIEW=okular


