source ~/.bashrc

# quietly set up ssh key (mostly for github)
eval $(ssh-agent -s) &>/dev/null
ssh-add ~/.ssh/id_rsa &>/dev/null

# git completion
    # i think this is only needed once:
    # source ~/.git-completion.bash

# PERFORCE?
    export P4PORT='\\<PERFORCE-REPO>:1666'

# don't use ^D to exiti
set -o ignoreeof

# ignore small typos in cd
shopt -s cdspell

# colors, plzzz
    alias ls='ls -hFG --color=auto' # human readable, decorate, don't show groups, color if term
    alias ll='ls -alF'
    alias la='ls -A'
    alias l='ls'

    alias diff='colordiff -u' # sudo apt-get install colordiff
    alias less='less -r'
    alias grep='grep --color'

# i can't keep this straight:
    alias whence='type -a'
    alias where='whereis'

# navigation convenience
    # bd - see https://github.com/vigneshwaranr/bd
    alias bd='. bd -si'
    # this next line only needs to be run once:
    # source /etc/bash_completion.d/bd

find-up() {
    curpath="$1" || return
    if [[ $curpath == . ]]; then curpath=$(pwd); fi
    shift 1 || return
    while [[ $curpath != / ]];
    do
        find "$curpath" -maxdepth 1 -mindepth 1 "$@" || return
        curpath="$(readlink -f "$curpath/..")" || return
    done
}

find-ups() {
    curpath="$1" || return
    if [[ $curpath == . ]]; then curpath=$(pwd); fi
    shift 1 || return
    while [[ $curpath != / ]];
    do
        find "$curpath" -maxdepth 1 -mindepth 1 "$@" || return
        curpath="$(realpath -s "$curpath/..")" || return
    done
}


### Set prompt:

    build_prompt() {
        # Shamelessly stolen from http://selena.deckelmann.usesthis.com/ (and improved?)
	export PS1="\[\e]0;\w\a\]\[\e[32m\]\u@\h \[\e[33m\]\w\n\`if [ \$? == 0 ]; then echo \[\e[36m\]\(\=; else echo \[\e[31m\]\)\=; fi\`\[\e[0m\] "

	export GIT_PROMPT_START="\[\e]0;\w\a\]\[\e[32m\]\u@\h \[\e[33m\]\w "
        export GIT_PROMPT_END="\n\`if [ \$? == 0 ]; then echo \[\e[36m\]\(\=; else echo \[\e[31m\]\)\=; fi\`\[\e[0m\] "

        # unfortunately, this gums up if there are quotes in the continuation:
        export PS2="\`if [ \$? == 0 ]; then echo \[\e[36m\] \>; else echo \[\e[31m\] \>; fi\`\[\e[0m\] "
    }
    build_prompt


    # add git_prompt() fn available for PS1
    # Pretty sure I used something like https://github.com/magicmonty/bash-git-prompt
    if [ -f ~/.git-bash-prompt/gitprompt.sh ]; then
        export GIT_PROMPT_ONLY_IN_REPO=1
        
        export GIT_PROMPT_SHOW_STAGED_COUNT=1
        export GIT_PROMPT_SHOW_CHANGED_COUNT=1
        export GIT_PROMPT_SHOW_CONFLICTS_COUNT=0
        export GIT_PROMPT_SHOW_UNTRACKED_COUNT=1
        export GIT_PROMPT_SHOW_STASHED_COUNT=0

        export GIT_PROMPT_THEME=Consolas_Symbology
        source ~/.git-bash-prompt/gitprompt.sh
    else
        echo "Could not load git-bash-prompt!" 1>&2
    fi 

    # Semi-official git one. Not very sexy: https://github.com/git/git/blob/master/contrib/completion/git-prompt.sh, I guess?
    #if [ -f ~/.git-prompt.sh ]; then
    #    export GIT_PS1_SHOWDIRTYSTATE=1
    #    export GIT_PS1_SHOWSTASHSTATE=1
    #    export GIT_PS1_SHOWUNTRACKEDFILES=1
    #    export GIT_PS1_SHOWUPSTREAM="verbose git"
    #    export GIT_PS1_STATESEPARATOR='|'
    #    
    #    # maybe useful - will remove the prompt if you're in a .gitignore'd folder
    #    export GIT_PS1_HIDE_IF_PWD_IGNORED=1
    #
    #    source ~/.git-prompt.sh
    #else
    #    echo "Could not find git-prompt. Disabling" >&2
    #    __git_ps1() {
    #        true
    #    }
    #fi

### Windows

function start {
    for file in "$@"
    do
        cmd.exe /C "$file"
    done
}
alias cmd='cmd.exe'

function explorer {
    if [[ $# -eq 0 ]]; then
        explorer.exe . || true
    else
        explorer.exe $1 || true
    fi
}

alias explore='explorer'

### Windows Network Drives

function mkshare {

    # check for invalid params/help
    if [[ $# -ne 2 ]]; then
        echo "mkshare [share-url] [mnt-dir]"
        echo "    mounts the network share 'share-url' to /mnt/[mnt-dir]'"
        return 0
    fi

    # check if mount-point is a file
    if [[ -f "/mnt/$2" ]]; then
        echo "error: /mnt/$2 is a file, we cannot mount onto it" 1>&2 
        return 1;
    fi

    # check if source is already mounted.
    # this might not be desirable behaviour; I guess we could want to mount the thing multiple times?
    if (findmnt -rno SOURCE,TARGET "$1" > /dev/null); then
        echo "$1 is mounted to $(findmnt -no TARGET $1)"
        return 0;
    fi

    # check if target is already mounted
    if (findmnt -rno SOURCE,TARGET "$2" > /dev/null); then
        echo "already mounted to $(findmnt -no SOURCE $2)"
        return 0;
    fi

    # check if we need to create directory
    if [[ ! -d "/mnt/$2" ]]; then
        echo "creating directory /mnt/$2"
        sudo mkdir "/mnt/$2"
    fi

    if (sudo mount -t drvfs $1 /mnt/$2); then
        echo "$1 is mounted to /mnt/$2"
    else
        echo "$1 is not mounted"
    fi
}

mkshare '\\<PUBLIC-DRIVES>' public
mkshare '\\<NUGET-DIR>' nuget

function orange_conspiracy {
  export GIT_PROMPT_THEME=Orange_Conspiracy
}  


