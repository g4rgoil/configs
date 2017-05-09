#
# ~/.bash_aliases
#

# Some pacman aliasses
alias update='yaourt -Syua'
alias install='sudo pacman -S'
alias uninstall='sudo pacman -Rns'
alias uninstall-force='sudo pacman -Rdd'

# Some handy aliasses for everyday commands
alias die='shutdown now'
alias hibernate='systemctl hibernate'
alias wheather='curl wttr.in/Karlsruhe'

# Some Wifi aliases
alias wifiedit='nm-connection-editor'
alias wificon='nmcli connection up'
alias wifistat='nmcli general'
alias wifion='nmcli radio wifi on && nmcli radio wwan on'
alias wifioff='nmcli radio wifi off && nmcli radio wwan off'

# Some ls aliasses
alias l='ls'
alias ls='ls -CF --color=auto'
alias la='ls -A'
alias ll='ls -al'
alias lr='ls -R'

# Some tree aliasses
alias tree='tree -CF -L 5'
alias Xtree='tree -X'
alias Jtree='tree -J'

# Some random aliases
alias ping='ping -c 5'
alias openports='ss --all --numeric --processes --ipv4 --ipv6'
alias ..='cd ..'
alias q='exit'
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
