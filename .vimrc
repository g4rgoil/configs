"" Plugins
call plug#begin('~/.vim/plugged')
    Plug 'junegunn/goyo.vim'
    Plug 'junegunn/vim-easy-align'
    Plug 'tpope/vim-surround'
    Plug 'bronson/vim-trailing-whitespace'
    Plug 'ap/vim-css-color'
    Plug 'slim-template/vim-slim'
call plug#end()

"" Templates
if has("autocmd")
    augroup templates
        autocmd BufNewFile *.sh 0r ~/.vim/templates/skeleton.sh
        autocmd BufNewFile *.py,*.pyw 0r ~/.vim/templates/skeleton.py
        autocmd BufNewFile *.java 0r ~/.vim/templates/skeleton.java
        autocmd BufNewFile *.php 0r ~/.vim/templates/skeleton.php
    augroup End
endif
