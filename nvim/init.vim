:set number
:set relativenumber
:set autoindent
:set smarttab
:set mouse=a
:set smarttab

call plug#begin()

Plug 'https://github.com/vim-airline/vim-airline' " for seeing what modes you are in
Plug 'https://github.com/preservim/nerdtree' " nerd tree allows you to see file structure
Plug 'neoclide/coc.nvim', {'branch': 'release'} " lsp
call plug#end()



" NerdTree Settings
let g:NERDTreeDirArrowExpandable="+"
let g:NERDTreeDirArrowCollapsible="~"
nmap <C-f> :NERDTreeToggle<CR>

" Tab auto complete
inoremap <expr> <Tab> pumvisible() ? coc#_select_confirm() : "<Tab>"

