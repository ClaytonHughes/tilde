scriptencoding utf-8
set encoding=utf-8

:set textwidth=120
set expandtab
set shiftwidth=4
set tabstop=4
set relativenumber
set hlsearch
set incsearch

set statusline=%f\ %m%r%=%-14.(%l,%c%V%)\ %P\ \ 
set laststatus=2
" a couple flavors or orange: 130, 166, 208, 202
highlight StatusLine ctermfg=11 ctermbg=130 cterm=NONE
highlight StatusLineNC ctermfg=0 ctermbg=130 cterm=italic
highlight Todo ctermbg=3

" dvorak!
" remap <new> <old>
" replace hjkl with something similar:

" ok this kinda sucked:
" nnoremap h h
" nnoremap t j
" nnoremap c k
" nnoremap n l
" " now 'n' is used, so switch next/prev search to g/G:
" nnoremap g n
" nnoremap G N
" but g is used in about a million places, so... 

set listchars=tab:»\ ,trail:·,precedes:…,extends:…,conceal:*
" or... ▸ »
set list

" autocmd bufnew,bufreadpre *.sh setlocal textwidth=0
autocmd FileType Makefile setlocal noexpandtab
autocmd FileType sh setlocal noexpandtab shiftwidth=2 tabstop=2
autocmd FileType json setlocal shiftwidth=2 tabstop=2 textwidth=0 wrap
autocmd FileType html setlocal shiftwidth=2 tabstop=2 textwidth=0 wrap
autocmd FileType gitcommit setlocal textwidth=80

" wtf is this? Did it maybe define a function to format the file? I'm... so unsure.
let @f='gggqG'

