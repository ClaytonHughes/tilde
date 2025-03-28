source ~/.bashrc

# quietly set up ssh key (mostly for github)
	eval $(ssh-agent -s) &>/dev/null
	ssh-add ~/.ssh/id_rsa &>/dev/null

### Friendlier Shell

	# git completion
		# i think this was only needed once:
		# source ~/.git-completion.bash

	# don't use ^D to exit the terminal
		set -o ignoreeof

	# ignore small typos in cd
		shopt -s cdspell

	# `ls` is too many characters
		alias l='ls'
		alias ls='ls --human-readable --classify --group-directories-first --color=auto'
		alias la='ls --almost-all' # include dotfiles, but not ./ and ../

		alias ll='ls --no-group --format=long'
		alias lla='ls --almost-all --format=long'
		alias lll='ll --almost-all'

		alias lz='ll --sort=size'
		alias llz='lla --sort=size'

	# colors, plzzz
		alias diff='colordiff -u' # sudo apt-get install colordiff
		alias less='less --RAW-CONTROL-CHARACTERS --HILITE-UNREAD' # ... but only the color control characters, i.e. the form "ESC [ color-def m".
		alias grep='grep --color'

	# i can't keep this straight:
		alias whence='type -a' # -a lists all instances. -P just the first on the path
		alias where='whereis'
		alias cls='clear'

# Navigation convenience
	# bd - see https://github.com/vigneshwaranr/bd
	alias bd='. bd -si'
	# this next line only needs to be run once:
	# source /etc/bash_completion.d/bd

	# Works like "find", but looks at parents.
	find-up() {

		curpath="$1" || return
		curpath="$1" || return
		if [[ $curpath == . ]]; then curpath=$(pwd); fi
		shift 1 || return
		while [[ $curpath != / ]];
		do
			find "$curpath" -maxdepth 1 -mindepth 1 "$@" || return
			curpath="$(readlink -f "$curpath/..")" || return
		done
	}

	# Works like "find", but looks at parents. Does not follow symlinks
	find-ups() {
		curpath="$1" || return
		if [[ $curpath == . ]]; then curpath=$(pwd); fi
		shift 1 || return
		while [[ $curpath != / ]];
		do
			find "$curpath" -maxdepth 1 -mindepth 1 "$@" || return
			curpath="$(realpath --strip "$curpath/..")" || return
		done
	}

### Tools with crappy CLIs

	# They used to support plugins but no got rid of it?!
	if [ -n "$(type docker)" ]; then
		function doco {
			doco_plugins_folder=$"$HOME/.docker/compose-cli-plugins"
			if [ -f "${doco_plugins_folder}/$1" ]; then
				local plugin=$1
				shift 1
				${local_pluns_folder}/${plugin} "$@"
			else
				docker compose "$@"
			fi
		}
	fi

	# razzn frazzn ragrl bargl
	# why are you failing .editorconfig?
	function newlines {
		temp=$(mktemp)
		find . -type f -iname "*${@}" > "$temp"
		echo "Converting $(<$temp wc -l) files."
		<$temp xargs dos2unix --quiet
		rm $temp
	}



### Set prompt:
	build_prompt() {
		# Shamelessly stolen from http://selena.deckelmann.usesthis.com/ (and improved/broken?)
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
		export GIT_PROMPT_SHOW_STASHED_COUNT=1
		export GIT_PROMPT_SHOW_STASHED_COUNT=1
		export GIT_PROMPT_THEME=Consolas_Symbology
		source ~/.git-bash-prompt/gitprompt.sh
	else
		echo "Could not load git-bash-prompt!" 1>&2
	fi
	# Pretty colors
	function orange_conspiracy {
		 export GIT_PROMPT_THEME=Orange_Conspiracy
	}


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

### Windows (WSL)
	# There's tons of ways to detect if we're on WSL. -- see https://superuser.com/a/1749811
	# I'm not doing anything wild, so this should be pretty dang reliable:
	if [ -f '/proc/sys/fs/binfmt_misc/WSLInterop' ]; then
		source ~/.bash_profile_wsl_extras
	fi
