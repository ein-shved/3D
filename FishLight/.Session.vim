let SessionLoad = 1
if &cp | set nocp | endif
let s:cpo_save=&cpo
set cpo&vim
imap <S-Tab> <Plug>vim_completes_me_backward
inoremap <expr> <Plug>vim_completes_me_backward VimCompletesMe#vim_completes_me(1)
inoremap <expr> <Plug>vim_completes_me_forward VimCompletesMe#vim_completes_me(0)
map! <S-Insert> <MiddleMouse>
map  "+y
map  :call SaveWithSession()
map <C-Left> <Left>
map <C-Right> <Right>
map <C-Down> <Down>
map <C-Up> <Up>
map  "+x
nmap d :cs find d =expand("<cword>")	
nmap i :cs find i ^=expand("<cfile>")$
nmap f :cs find f =expand("<cfile>")	
nmap e :cs find e =expand("<cword>")	
nmap t :cs find t =expand("<cword>")	
nmap c :cs find c =expand("<cword>")	
nmap g :cs find g =expand("<cword>")	
nmap s :cs find s =expand("<cword>")	
nmap ] ggVG:EasyAlign\
xmap  :s/\([^\\]\)$/\1\\/e:nohlgv:s/^$/\\/e:nohlgv:EasyAlign\
xmap \ :EasyAlign\
cmap Ю >
cmap Б <
cmap Ь M
cmap Т N
cmap И B
cmap М V
cmap С C
cmap Ч X
cmap Я Z
cmap Э "
cmap Ж :
cmap Д L
cmap Л K
cmap О J
cmap Р H
cmap П G
cmap А F
cmap В D
cmap Ы S
cmap Ф A
cmap Ъ ]
cmap Х [
cmap З P
cmap Щ O
cmap Ш I
cmap Г U
cmap Н Y
cmap Е T
cmap К R
cmap У E
cmap Ц W
cmap Й Q
cmap б ,
cmap и b
cmap м v
cmap ж ;
cmap д l
cmap л k
cmap о j
cmap п g
cmap а f
cmap в d
cmap з p
cmap г u
cmap н y
cmap е t
cmap к r
cmap й q
cmap ю .
cmap ь m
cmap т n
cmap с c
cmap ч x
cmap я z
cmap э '
cmap р h
cmap ы s
cmap ф a
cmap ъ ]
cmap х [
cmap щ o
cmap ш i
cmap у e
cmap ц w
map ^[[4~ <End>
map ^[[1~ <Home>
nmap gx <Plug>NetrwBrowseX
map <silent> <F3> :ToggleSpaceHi
nnoremap <silent> <Plug>NetrwBrowseX :call netrw#NetrwBrowseX(expand("<cfile>"),0)
nmap <Nul><Nul>d :vert scs find d =expand("<cword>")
nmap <Nul><Nul>i :vert scs find i ^=expand("<cfile>")$	
nmap <Nul><Nul>f :vert scs find f =expand("<cfile>")	
nmap <Nul><Nul>e :vert scs find e =expand("<cword>")
nmap <Nul><Nul>t :vert scs find t =expand("<cword>")
nmap <Nul><Nul>c :vert scs find c =expand("<cword>")
nmap <Nul><Nul>g :vert scs find g =expand("<cword>")
nmap <Nul><Nul>s :vert scs find s =expand("<cword>")
nmap <Nul>d :scs find d =expand("<cword>")	
nmap <Nul>i :scs find i ^=expand("<cfile>")$	
nmap <Nul>f :scs find f =expand("<cfile>")	
nmap <Nul>e :scs find e =expand("<cword>")	
nmap <Nul>t :scs find t =expand("<cword>")	
nmap <Nul>c :scs find c =expand("<cword>")	
nmap <Nul>g :scs find g =expand("<cword>")	
nmap <Nul>s :scs find s =expand("<cword>")	
map <F11> :cprevious
map <F10> :cnext
map <F9> :silent make
map <C-Left> <Left>
map <C-Right> <Right>
map <C-Down> <Down>
map <C-Up> <Up>
map <F6> :tp
map <F7> :tn
map <C-F8> :exec exec_tags_set:exec exec_cscope_set
map <F8> :exec exec_tags:exec exec_tags_set:exec exec_cscope:exec exec_cscope_set
map <S-Insert> <MiddleMouse>
imap 	 <Plug>vim_completes_me_forward
imap  :call SaveWithSession()i<Right>
map Ю >
map Б <
map Ь M
map Т N
map И B
map М V
map С C
map Ч X
map Я Z
map Э "
map Ж :
map Д L
map Л K
map О J
map Р H
map П G
map А F
map В D
map Ы S
map Ф A
map Ъ ]
map Х [
map З P
map Щ O
map Ш I
map Г U
map Н Y
map Е T
map К R
map У E
map Ц W
map Й Q
map б ,
map и b
map м v
map ж ;
map д l
map л k
map о j
map п g
map а f
map в d
map з p
map г u
map н y
map е t
map к r
map й q
map ю .
map ь m
map т n
map с c
map ч x
map я z
map э '
map р h
map ы s
map ф a
map ъ ]
map х [
map щ o
map ш i
map у e
map ц w
imap ^[[4~ <End>
imap ^[[1~ <Home>
let &cpo=s:cpo_save
unlet s:cpo_save
set autoindent
set background=dark
set backspace=indent,eol,start
set cinoptions=:0
set completeopt=menu
set cscoperelative
set cscopetag
set cscopetagorder=1
set cscopeverbose
set directory=~/.vim_swaps
set expandtab
set fileencodings=ucs-bom,utf-8,default,latin1
set guifont=JetBrains\ Mono\ Bold\ 8
set guioptions=a
set helplang=en
set hlsearch
set listchars=tab:→\ ,nbsp:␣,trail:���,precedes:«,extends:»
set mouse=a
set ruler
set runtimepath=~/.vim,~/.vim/bundle/Vundle.vim,~/.vim/bundle/vim-colors-solarized,~/.vim/bundle/ExpandBackspace.vim,~/.vim/bundle/VimCompletesMe,~/.vim/bundle/tagbar,~/.vim/bundle/vim-easy-align,~/.vim/bundle/vim-openscad,/usr/share/vim/vimfiles,/usr/share/vim/vim80,/usr/share/vim/vimfiles/after,~/.vim/after,~/.vim/bundle/Vundle.vim,~/.vim/bundle/Vundle.vim/after,~/.vim/bundle/vim-colors-solarized/after,~/.vim/bundle/ExpandBackspace.vim/after,~/.vim/bundle/VimCompletesMe/after,~/.vim/bundle/tagbar/after,~/.vim/bundle/vim-easy-align/after,~/.vim/bundle/vim-openscad/after
set shiftwidth=4
set smartindent
set suffixes=.bak,~,.swp,.o,.info,.aux,.log,.dvi,.bbl,.blg,.brf,.cb,.ind,.idx,.ilg,.inx,.out,.toc,.png,.jpg
set tabstop=4
set termencoding=utf-8
set wildmode=longest,full,list
set window=71
let s:so_save = &so | let s:siso_save = &siso | set so=0 siso=0
let v:this_session=expand("<sfile>:p")
silent only
cd ~/Projects/3D/FishLight
if expand('%') == '' && !&modified && line('$') <= 1 && getline(1) == ''
  let s:wipebuf = bufnr('%')
endif
set shortmess=aoO
badd +1 fishlight.scad
badd +44 ../Legrand/legrand.scad
badd +1 ../Cabel/ParametricCableChain.scad
argglobal
silent! argdel *
$argadd fishlight.scad
edit fishlight.scad
set splitbelow splitright
wincmd _ | wincmd |
vsplit
1wincmd h
wincmd w
set nosplitbelow
set nosplitright
wincmd t
set winminheight=1 winheight=1 winminwidth=1 winwidth=1
exe 'vert 1resize ' . ((&columns * 79 + 79) / 159)
exe 'vert 2resize ' . ((&columns * 79 + 79) / 159)
argglobal
setlocal keymap=
setlocal noarabic
setlocal autoindent
setlocal backupcopy=
setlocal balloonexpr=
setlocal nobinary
setlocal nobreakindent
setlocal breakindentopt=
setlocal bufhidden=
setlocal buflisted
setlocal buftype=
setlocal nocindent
setlocal cinkeys=0{,0},0),:,0#,!^F,o,O,e
setlocal cinoptions=:0
setlocal cinwords=if,else,while,do,for,switch
set colorcolumn=81
setlocal colorcolumn=81
setlocal comments=sO:*\ -,mO:*\ \ ,exO:*/,s1:/*,mb:*,ex:*/,://
setlocal commentstring=/*%s*/
setlocal complete=.,w,b,u,t,i
setlocal concealcursor=
setlocal conceallevel=0
setlocal completefunc=
setlocal nocopyindent
setlocal cryptmethod=
setlocal nocursorbind
setlocal nocursorcolumn
setlocal cursorline
setlocal define=
setlocal dictionary=
setlocal nodiff
setlocal equalprg=
setlocal errorformat=
setlocal expandtab
if &filetype != 'openscad'
setlocal filetype=openscad
endif
setlocal fixendofline
setlocal foldcolumn=0
setlocal foldenable
setlocal foldexpr=0
setlocal foldignore=#
setlocal foldlevel=0
setlocal foldmarker={{{,}}}
setlocal foldmethod=manual
setlocal foldminlines=1
setlocal foldnestmax=20
setlocal foldtext=foldtext()
setlocal formatexpr=
setlocal formatoptions=tcq
setlocal formatlistpat=^\\s*\\d\\+[\\]:.)}\\t\ ]\\s*
setlocal formatprg=
setlocal grepprg=
setlocal iminsert=0
setlocal imsearch=-1
setlocal include=
setlocal includeexpr=
setlocal indentexpr=
setlocal indentkeys=0{,0},:,0#,!^F,o,O,e
setlocal noinfercase
setlocal iskeyword=@,48-57,_,192-255
setlocal keywordprg=
setlocal nolinebreak
setlocal nolisp
setlocal lispwords=
set list
setlocal list
setlocal makeencoding=
setlocal makeprg=
setlocal matchpairs=(:),{:},[:]
setlocal modeline
setlocal modifiable
setlocal nrformats=bin,octal,hex
setlocal nonumber
setlocal numberwidth=4
setlocal omnifunc=
setlocal path=
setlocal nopreserveindent
setlocal nopreviewwindow
setlocal quoteescape=\\
setlocal noreadonly
setlocal norelativenumber
setlocal norightleft
setlocal rightleftcmd=search
setlocal noscrollbind
setlocal shiftwidth=4
setlocal noshortname
setlocal signcolumn=auto
setlocal smartindent
setlocal softtabstop=0
set spell
setlocal spell
setlocal spellcapcheck=[.?!]\\_[\\])'\"\	\ ]\\+
setlocal spellfile=
setlocal spelllang=en
setlocal statusline=
setlocal suffixesadd=
setlocal swapfile
setlocal synmaxcol=3000
if &syntax != 'openscad'
setlocal syntax=openscad
endif
setlocal tabstop=4
setlocal tagcase=
setlocal tags=
setlocal termkey=
setlocal termsize=
setlocal textwidth=0
setlocal thesaurus=
setlocal noundofile
setlocal undolevels=-123456
setlocal nowinfixheight
setlocal nowinfixwidth
set nowrap
setlocal nowrap
setlocal wrapmargin=0
silent! normal! zE
let s:l = 266 - ((40 * winheight(0) + 35) / 70)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
266
normal! 047|
wincmd w
argglobal
if bufexists('../Cabel/ParametricCableChain.scad') | buffer ../Cabel/ParametricCableChain.scad | else | edit ../Cabel/ParametricCableChain.scad | endif
setlocal keymap=
setlocal noarabic
setlocal autoindent
setlocal backupcopy=
setlocal balloonexpr=
setlocal nobinary
setlocal nobreakindent
setlocal breakindentopt=
setlocal bufhidden=
setlocal buflisted
setlocal buftype=
setlocal nocindent
setlocal cinkeys=0{,0},0),:,0#,!^F,o,O,e
setlocal cinoptions=:0
setlocal cinwords=if,else,while,do,for,switch
set colorcolumn=81
setlocal colorcolumn=81
setlocal comments=sO:*\ -,mO:*\ \ ,exO:*/,s1:/*,mb:*,ex:*/,://
setlocal commentstring=/*%s*/
setlocal complete=.,w,b,u,t,i
setlocal concealcursor=
setlocal conceallevel=0
setlocal completefunc=
setlocal nocopyindent
setlocal cryptmethod=
setlocal nocursorbind
setlocal nocursorcolumn
setlocal cursorline
setlocal define=
setlocal dictionary=
setlocal nodiff
setlocal equalprg=
setlocal errorformat=
setlocal expandtab
if &filetype != 'openscad'
setlocal filetype=openscad
endif
setlocal fixendofline
setlocal foldcolumn=0
setlocal foldenable
setlocal foldexpr=0
setlocal foldignore=#
setlocal foldlevel=0
setlocal foldmarker={{{,}}}
setlocal foldmethod=manual
setlocal foldminlines=1
setlocal foldnestmax=20
setlocal foldtext=foldtext()
setlocal formatexpr=
setlocal formatoptions=tcq
setlocal formatlistpat=^\\s*\\d\\+[\\]:.)}\\t\ ]\\s*
setlocal formatprg=
setlocal grepprg=
setlocal iminsert=0
setlocal imsearch=-1
setlocal include=
setlocal includeexpr=
setlocal indentexpr=
setlocal indentkeys=0{,0},:,0#,!^F,o,O,e
setlocal noinfercase
setlocal iskeyword=@,48-57,_,192-255
setlocal keywordprg=
setlocal nolinebreak
setlocal nolisp
setlocal lispwords=
set list
setlocal list
setlocal makeencoding=
setlocal makeprg=
setlocal matchpairs=(:),{:},[:]
setlocal modeline
setlocal modifiable
setlocal nrformats=bin,octal,hex
setlocal nonumber
setlocal numberwidth=4
setlocal omnifunc=
setlocal path=
setlocal nopreserveindent
setlocal nopreviewwindow
setlocal quoteescape=\\
setlocal noreadonly
setlocal norelativenumber
setlocal norightleft
setlocal rightleftcmd=search
setlocal noscrollbind
setlocal shiftwidth=4
setlocal noshortname
setlocal signcolumn=auto
setlocal smartindent
setlocal softtabstop=0
set spell
setlocal spell
setlocal spellcapcheck=[.?!]\\_[\\])'\"\	\ ]\\+
setlocal spellfile=
setlocal spelllang=en
setlocal statusline=
setlocal suffixesadd=
setlocal swapfile
setlocal synmaxcol=3000
if &syntax != 'openscad'
setlocal syntax=openscad
endif
setlocal tabstop=4
setlocal tagcase=
setlocal tags=
setlocal termkey=
setlocal termsize=
setlocal textwidth=0
setlocal thesaurus=
setlocal noundofile
setlocal undolevels=-123456
setlocal nowinfixheight
setlocal nowinfixwidth
set nowrap
setlocal nowrap
setlocal wrapmargin=0
silent! normal! zE
let s:l = 12 - ((11 * winheight(0) + 35) / 70)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
12
normal! 017|
wincmd w
exe 'vert 1resize ' . ((&columns * 79 + 79) / 159)
exe 'vert 2resize ' . ((&columns * 79 + 79) / 159)
tabnext 1
if exists('s:wipebuf')
  silent exe 'bwipe ' . s:wipebuf
endif
unlet! s:wipebuf
set winheight=1 winwidth=20 shortmess=filnxtToO
set winminheight=1 winminwidth=1
let s:sx = expand("<sfile>:p:r")."x.vim"
if file_readable(s:sx)
  exe "source " . fnameescape(s:sx)
endif
let &so = s:so_save | let &siso = s:siso_save
doautoall SessionLoadPost
unlet SessionLoad
" vim: set ft=vim :
