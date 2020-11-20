let SessionLoad = 1
if &cp | set nocp | endif
let s:cpo_save=&cpo
set cpo&vim
inoremap <expr> <Plug>vim_completes_me_forward VimCompletesMe#vim_completes_me(0)
inoremap <expr> <Plug>vim_completes_me_backward VimCompletesMe#vim_completes_me(1)
imap <S-Tab> <Plug>vim_completes_me_backward
map! <S-Insert> <MiddleMouse>
map  "+y
map  :call SaveWithSession()
map <C-Up> <Up>
map <C-Down> <Down>
map <C-Right> <Right>
map <C-Left> <Left>
map  "+x
nmap s :cs find s =expand("<cword>")	
nmap g :cs find g =expand("<cword>")	
nmap c :cs find c =expand("<cword>")	
nmap t :cs find t =expand("<cword>")	
nmap e :cs find e =expand("<cword>")	
nmap f :cs find f =expand("<cfile>")	
nmap i :cs find i ^=expand("<cfile>")$
nmap d :cs find d =expand("<cword>")	
nmap ] ggVG:EasyAlign\
xmap  :s/\([^\\]\)$/\1\\/e:nohlgv:s/^$/\\/e:nohlgv:EasyAlign\
xmap \ :EasyAlign\
cmap й q
cmap к r
cmap е t
cmap н y
cmap г u
cmap з p
cmap в d
cmap а f
cmap п g
cmap о j
cmap л k
cmap д l
cmap ж ;
cmap м v
cmap и b
cmap б ,
cmap Й Q
cmap Ц W
cmap У E
cmap К R
cmap Е T
cmap Н Y
cmap Г U
cmap Ш I
cmap Щ O
cmap З P
cmap Х [
cmap Ъ ]
cmap Ф A
cmap Ы S
cmap В D
cmap А F
cmap П G
cmap Р H
cmap О J
cmap Л K
cmap Д L
cmap Ж :
cmap Э "
cmap Я Z
cmap Ч X
cmap С C
cmap М V
cmap И B
cmap Т N
cmap Ь M
cmap Б <
cmap Ю >
cmap ц w
cmap у e
cmap ш i
cmap щ o
cmap х [
cmap ъ ]
cmap ф a
cmap ы s
cmap р h
cmap э '
cmap я z
cmap ч x
cmap с c
cmap т n
cmap ь m
cmap ю .
map ^[[1~ <Home>
map ^[[4~ <End>
nmap gx <Plug>NetrwBrowseX
map <F8> :exec exec_tags:exec exec_tags_set:exec exec_cscope:exec exec_cscope_set
map <C-F8> :exec exec_tags_set:exec exec_cscope_set
map <F7> :tn
map <F6> :tp
map <C-Up> <Up>
map <C-Down> <Down>
map <C-Right> <Right>
map <C-Left> <Left>
map <F9> :silent make
map <F10> :cnext
map <F11> :cprevious
nmap <Nul>s :scs find s =expand("<cword>")	
nmap <Nul>g :scs find g =expand("<cword>")	
nmap <Nul>c :scs find c =expand("<cword>")	
nmap <Nul>t :scs find t =expand("<cword>")	
nmap <Nul>e :scs find e =expand("<cword>")	
nmap <Nul>f :scs find f =expand("<cfile>")	
nmap <Nul>i :scs find i ^=expand("<cfile>")$	
nmap <Nul>d :scs find d =expand("<cword>")	
nmap <Nul><Nul>s :vert scs find s =expand("<cword>")
nmap <Nul><Nul>g :vert scs find g =expand("<cword>")
nmap <Nul><Nul>c :vert scs find c =expand("<cword>")
nmap <Nul><Nul>t :vert scs find t =expand("<cword>")
nmap <Nul><Nul>e :vert scs find e =expand("<cword>")
nmap <Nul><Nul>f :vert scs find f =expand("<cfile>")	
nmap <Nul><Nul>i :vert scs find i ^=expand("<cfile>")$	
nmap <Nul><Nul>d :vert scs find d =expand("<cword>")
nnoremap <silent> <Plug>NetrwBrowseX :call netrw#NetrwBrowseX(expand("<cfile>"),0)
map <silent> <F3> :ToggleSpaceHi
map <S-Insert> <MiddleMouse>
imap 	 <Plug>vim_completes_me_forward
imap  :call SaveWithSession()i<Right>
map й q
map к r
map е t
map н y
map г u
map з p
map в d
map а f
map п g
map о j
map л k
map д l
map ж ;
map м v
map и b
map б ,
map Й Q
map Ц W
map У E
map К R
map Е T
map Н Y
map Г U
map Ш I
map Щ O
map З P
map Х [
map Ъ ]
map Ф A
map Ы S
map В D
map А F
map П G
map Р H
map О J
map Л K
map Д L
map Ж :
map Э "
map Я Z
map Ч X
map С C
map М V
map И B
map Т N
map Ь M
map Б <
map Ю >
map ц w
map у e
map ш i
map щ o
map х [
map ъ ]
map ф a
map ы s
map р h
map э '
map я z
map ч x
map с c
map т n
map ь m
map ю .
imap ^[[1~ <Home>
imap ^[[4~ <End>
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
cd ~/Projects/3D/Legrand
if expand('%') == '' && !&modified && line('$') <= 1 && getline(1) == ''
  let s:wipebuf = bufnr('%')
endif
set shortmess=aoO
badd +55 legrand.scad
badd +1 ~/Projects/3D/BonedPlate/hang.scad
badd +26 ~/.local/share/OpenSCAD/libraries/generic.scad
badd +102 ~/Projects/3D/BonedPlate/BonedPlate.scad
argglobal
silent! argdel *
$argadd legrand.scad
edit legrand.scad
set splitbelow splitright
wincmd _ | wincmd |
vsplit
1wincmd h
wincmd _ | wincmd |
split
1wincmd k
wincmd w
wincmd w
wincmd _ | wincmd |
split
1wincmd k
wincmd w
set nosplitbelow
set nosplitright
wincmd t
set winminheight=1 winheight=1 winminwidth=1 winwidth=1
exe '1resize ' . ((&lines * 35 + 36) / 72)
exe 'vert 1resize ' . ((&columns * 79 + 79) / 159)
exe '2resize ' . ((&lines * 34 + 36) / 72)
exe 'vert 2resize ' . ((&columns * 79 + 79) / 159)
exe '3resize ' . ((&lines * 35 + 36) / 72)
exe 'vert 3resize ' . ((&columns * 79 + 79) / 159)
exe '4resize ' . ((&lines * 34 + 36) / 72)
exe 'vert 4resize ' . ((&columns * 79 + 79) / 159)
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
let s:l = 72 - ((27 * winheight(0) + 17) / 35)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
72
normal! 040|
wincmd w
argglobal
if bufexists('~/.local/share/OpenSCAD/libraries/generic.scad') | buffer ~/.local/share/OpenSCAD/libraries/generic.scad | else | edit ~/.local/share/OpenSCAD/libraries/generic.scad | endif
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
setlocal nocursorline
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
setlocal formatoptions=croql
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
let s:l = 38 - ((22 * winheight(0) + 17) / 34)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
38
normal! 045|
wincmd w
argglobal
if bufexists('legrand.scad') | buffer legrand.scad | else | edit legrand.scad | endif
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
setlocal nocursorline
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
let s:l = 88 - ((0 * winheight(0) + 17) / 35)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
88
normal! 0
wincmd w
argglobal
if bufexists('legrand.scad') | buffer legrand.scad | else | edit legrand.scad | endif
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
setlocal nocursorline
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
let s:l = 44 - ((32 * winheight(0) + 17) / 34)
if s:l < 1 | let s:l = 1 | endif
exe s:l
normal! zt
44
normal! 0
wincmd w
exe '1resize ' . ((&lines * 35 + 36) / 72)
exe 'vert 1resize ' . ((&columns * 79 + 79) / 159)
exe '2resize ' . ((&lines * 34 + 36) / 72)
exe 'vert 2resize ' . ((&columns * 79 + 79) / 159)
exe '3resize ' . ((&lines * 35 + 36) / 72)
exe 'vert 3resize ' . ((&columns * 79 + 79) / 159)
exe '4resize ' . ((&lines * 34 + 36) / 72)
exe 'vert 4resize ' . ((&columns * 79 + 79) / 159)
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
