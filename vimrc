set nocompatible
packadd! matchit
set backupext=.bak

"" General
set ruler                       " Show row and column ruler information 
set number                      " Show line numbers
set listchars=tab:>-,trail:-    " Show tabs as >--- and trailing spaces as -
set linebreak                   " Break lines at work
set showbreak=+++               " Wrap-broken line prefix
set textwidth=100               " Line wrap (after cols)
set showmatch                   " Highlight matching braces
set cmdheight=2                 " Number of lines at bottome of screen
syntax enable                   " Enable syntax highlighting

"" Indentation
filetype plugin indent on       " I don't fucking know, what this does!
set tabstop=4                   " Number of hard-tabsto spaes
set shiftwidth=4                " Number of auto-indent spaces
set expandtab                   " Use spaces instead of tabs
set autoindent

"" File Type options
autocmd BufNewFile,BufReadPost *.md set filetype=markdown
let g:markdown_fenced_languages = ['javascript', 'go', 'php']
