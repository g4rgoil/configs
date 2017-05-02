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
alias l='ls'
alias ls='ls -CF --color=auto'
alias la='ls -A'
alias ll='ls -al'
alias lr='ls -R'

alias tree='tree -CF -L 5'
alias Xtree='tree -X'
alias Jtree='tree -J'

# Some random aliases
alias ping='ping -c 5'
alias openports='ss --all --numeric --processes --ipv4 --ipv6'
alias ..='cd ..'
alias cp='cp -i'
alias mv='mv -i'
alias rm='rm -I'
alias svim='sudo vim'
alias scat='sudo cat'

# Edit commands
alias edit='$VISUAL'
alias sedit='sudo $VISUAL'
alias e='edit'
alias se='sedit'

# Error Tolerance
alias cd..='cd ..'
