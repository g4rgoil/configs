set nocompatible
set encoding=utf-8
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
set cmdheight=1                 " Number of lines at bottom of screen
set tw=0                        " Don't use automatic line breaks
syntax enable                   " Enable syntax highlighting

"" Indentation
filetype plugin indent on       " I don't fucking know, what this does!
set tabstop=4                   " Number of hard-tabsto spaes
set shiftwidth=4                " Number of auto-indent spaces
set expandtab                   " Use spaces instead of tabs
set autoindent

"" Configure split behaviour
nnoremap <C-J> <C-W><C-J>
nnoremap <C-K> <C-W><C-K>
nnoremap <C-L> <C-W><C-L>
nnoremap <C-H> <C-W><C-H>

set splitbelow
set splitright

"" Configure tab behaviour
map <C-N> :tabp<cr>
map <C-M> :tabn<cr>

"" Airline Configuration
set laststatus=2                                    " Always show status bar
let g:airline#extensions#tabline#enabled = 1
let g:airline_powerline_fonts = 1
let g:airline_theme = 'luna'

let g:airline#extensions#whitespace#enabled = 0
"let g:airline#extensions#vimtex#enabled = 1

"" Vimtex Configuration
let g:vimtex_compiler_method = 'latexmk'
" let g:vimtex_compiler_latexmk = {'build_dir' : './latexmk_out/'}
let g:vimtex_complete_close_braces = 1
let g:vimtex_fold_enabled = 1
let g:vimtex_fold_comments = 1

let g:vimtex_view_general_viewer = 'okular'
let g:vimtex_view_general_options = '--unique file:@pdf\#src:@line@tex'
let g:vimtex_view_general_options_latexmk = '--unique'

"" Plugins
call plug#begin('~/.vim/plugged')
    Plug 'junegunn/goyo.vim'
    Plug 'junegunn/vim-easy-align'

    Plug 'tpope/vim-surround'
    Plug 'tpope/vim-fugitive'

    Plug 'scrooloose/nerdtree'

    "" Plug 'bronson/vim-trailing-whitespace'
    Plug 'ap/vim-css-color'
    Plug 'slim-template/vim-slim'
    Plug 'lervag/vimtex'

    Plug 'vim-airline/vim-airline'
    Plug 'vim-airline/vim-airline-themes'
call plug#end()

"" Templates
if has("autocmd")
    augroup templates
        autocmd BufNewFile *.sh         0r /etc/vim/templates/skeleton.sh
        autocmd BufNewFile *.py,*.pyw   0r /etc/vim/templates/skeleton.py
        autocmd BufNewFile *.java       0r /etc/vim/templates/skeleton.java
        autocmd BufNewFile *.php        0r /etc/vim/templates/skeleton.php
    augroup End
endif

"" File Type options
autocmd BufNewFile,BufReadPost *.md set filetype=markdown
let g:markdown_fenced_languages = ['javascript', 'go', 'php']

