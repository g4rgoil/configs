
_notepy()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $( compgen -W '-d= --dir= -d= --dir= -d= --dir= -h --help -h --help --version create list gen-make gen-config' -- $cur) )
    else
        case ${COMP_WORDS[1]} in
            create)
            _notepy_create
        ;;
            list)
            _notepy_list
        ;;
            gen-make)
            _notepy_gen-make
        ;;
            gen-config)
            _notepy_gen-config
        ;;
        esac

    fi
}

_notepy_create()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '--author= --edit --noedit --editor= ' -- $cur) )
    fi
}

_notepy_list()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 2 ]; then
        COMPREPLY=( $( compgen -fW '-m --modified -l --lines -w --words -c --chars -a --all -r --reverse ' -- $cur) )
    fi
}

_notepy_gen-make()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W ' --' -- $cur) )
    else
        case ${COMP_WORDS[2]} in
            --)
            _notepy_gen-make_--
        ;;
        esac

    fi
}

_notepy_gen-make_--()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 3 ]; then
        COMPREPLY=( $( compgen -W ' ' -- $cur) )
    fi
}

_notepy_gen-config()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -eq 2 ]; then
        COMPREPLY=( $( compgen -W ' --' -- $cur) )
    else
        case ${COMP_WORDS[2]} in
            --)
            _notepy_gen-config_--
        ;;
        esac

    fi
}

_notepy_gen-config_--()
{
    local cur
    cur="${COMP_WORDS[COMP_CWORD]}"

    if [ $COMP_CWORD -ge 3 ]; then
        COMPREPLY=( $( compgen -W ' ' -- $cur) )
    fi
}

complete -o bashdefault -o default -o filenames -F _notepy note.py