#compdef note.py

_message_next_arg()
{
    argcount=0
    for word in "${words[@][2,-1]}"
    do
        if [[ $word != -* ]] ; then
            ((argcount++))
        fi
    done
    if [[ $argcount -le ${#myargs[@]} ]] ; then
        _message -r $myargs[$argcount]
        if [[ $myargs[$argcount] =~ ".*file.*" || $myargs[$argcount] =~ ".*path.*" ]] ; then
            _files
        fi
    fi
}

_note.py ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
		'(-d=-)-d=-' \
		'(--dir=-)--dir=-' \
		'(-d=-)-d=-' \
		'(--dir=-)--dir=-' \
		'(-d=-)-d=-' \
		'(--dir=-)--dir=-' \
		'(-h)-h' \
		'(--help)--help' \
		'(-h)-h' \
		'(--help)--help' \
		'(--version)--version' \
        '*::options:->options'

    case $state in
        (command)
            local -a subcommands
            subcommands=(
				'create[Create a new note with the required pandoc header]'
				'list[List notes and corresponding information]'
				'gen-make[Create a Makefile that can compile the notes, using pandoc]'
				'gen-config[Write a default config file to '\''~/.config/noterc'\'' or stdout]'
            )
            _values 'note.py' $subcommands
        ;;

        (options)
            case $line[1] in
                create)
                    _note.py-create
                ;;
                list)
                    _note.py-list
                ;;
                gen-make)
                    _note.py-gen-make
                ;;
                gen-config)
                    _note.py-gen-config
                ;;
            esac
        ;;
    esac

}

_note.py-create ()
{
    local context state state_descr line
    typeset -A opt_args

    if [[ $words[$CURRENT] == -* ]] ; then
        _arguments -C \
        ':command:->command' \
		'(--author=-)--author=-[The author of the note, will be used in the header]' \
		'(--edit)--edit[Open the note in an editor upon creation]' \
		'(--noedit)--noedit[Don'\''t open the note in an editor (always overrules --edit)]' \
		'(--editor=-)--editor=-[Use the specified progam to edit notes]' \

    else
        myargs=('<prefix>')
        _message_next_arg
    fi
}

_note.py-list ()
{
    local context state state_descr line
    typeset -A opt_args

    if [[ $words[$CURRENT] == -* ]] ; then
        _arguments -C \
        ':command:->command' \
		'(-c=-)-c=-' \
		'(--columns=-)--columns=-' \
		'(-s=-)-s=-' \
		'(--sort=-)--sort=-' \
		'(-r)-r' \
		'(--reverse)--reverse' \

    else
        myargs=('<prefix>')
        _message_next_arg
    fi
}

_note.py-gen-make ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
        '*::options:->options'

    case $state in
        (command)
            local -a subcommands
            subcommands=(
				'--'
            )
            _values 'note.py gen make' $subcommands
        ;;

        (options)
            case $line[1] in
                --)
                    _note.py-gen-make---
                ;;
            esac
        ;;
    esac

}

_note.py-gen-make--- ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
        
}

_note.py-gen-config ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
        '*::options:->options'

    case $state in
        (command)
            local -a subcommands
            subcommands=(
				'--'
            )
            _values 'note.py gen config' $subcommands
        ;;

        (options)
            case $line[1] in
                --)
                    _note.py-gen-config---
                ;;
            esac
        ;;
    esac

}

_note.py-gen-config--- ()
{
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        ':command:->command' \
        
}


_note.py "$@"