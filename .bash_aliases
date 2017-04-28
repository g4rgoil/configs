#
# ~/.bash_aliases
#

# Some handy aliasses for everyday commands
alias update='yaourt -Syua'
alias uninstall='yaourt -Rns'
alias die='shutdown now'
alias hibernate='systemctl hibernate'
alias wheather='curl wttr.in/Karlsruhe'

# Some ls aliasses
alias ls='ls --color=auto'
alias la='ls -AF'
alias l='ls -CF'
alias ll='ls -alF'
alias lr='ls -R'

# Some random aliases
alias ping='ping -c 5'
alias openports='ss --all --numeric --processes --ipv4 --ipv6'
alias ..='cd ..'
alias cp='cp -i'
alias mv='mv -i'
alias rm='rm -I'
alias svim='sudo vim'
alias scat='sudo cat'

# Error Tolerance
alias cd..='cd ..'
