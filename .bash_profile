# don't use ^D to exit
    set -o ignoreeof

# ignore small typos in cd
    shopt -s cdspell

#########

# make fuck work
# nb: something's broke. fix later... >=(
    eval $(thefuck --alias)

# command line google, why not?
    alias google='googler --noprompt --count 3'

# set up rbenv so `brew update` doesn't break shit
    eval "$(rbenv init -)"


#########


# java home
    export JAVA_HOME=$(/usr/libexec/java_home)

# brew's ruby
    export PATH=/usr/local/opt/ruby/bin:$PATH

# colors, plzzz
    alias ls='ls -hFG'
    alias ll='ls -l'
    alias la='ls -A'
    alias l='ls'

    alias diff='colordiff -u'
    alias less='less -r'
    alias grep='grep --color'

# i can't keep this straight:
    alias whence='type -a'
    alias whereis='which'

# navigation convenience:
    alias bd='. bd -si'
    alias nextd="pushd +1"
    alias prevd="pushd -1"
    alias showd="dirs -v"

# navigation to/from common directories:

    # can't stop pwd from expanding ~, have to expand ~ everywhere:
    core_dir="/Users/clayton/wgc/core"
    game_dir="/Users/clayton/wgc/games/"

    function in_dir_stack {
        dirs -l -v | grep $1 2>&1 >/dev/null
    }

    function pwd_in_dir_stack {
        # trivially, it's at the top. Is it deeper?
        dirs -l -v | tail -n +2 | grep $(pwd)$ 2>&1 >/dev/null
    }

    function rotate_dir_stack_to {
        pushd +$(dirs -l -v | grep $1 | awk '{print $1}' | head -n 1)
    } 

    # "to core" cds to most recent core directory
    function toc {
        if in_dir_stack $core_dir ; then
            rotate_dir_stack_to $core_dir
        else
            # save pwd if not already on stack
            if ! pwd_in_dir_stack ; then
                pushd . 2>&1 >/dev/null
            fi
            cd $core_dir
        fi
    }

    # "to game" cds to game directory
    function tog {
        if [[ $# -lt 1 ]]; then
            echo "syntax: togame <gamename>" >&2
            return 1
        fi
        target_dir=$game_dir$1
        if in_dir_stack $target_dir ; then
            rotate_dir_stack_to $target_dir
        else
            if ! pwd_in_dir_stack ; then
                pushd . 2>&1 > /dev/null
            fi
            cd $target_dir
        fi
    }

# git stuff
    export PATH=~/gitcommands:$PATH

# add git_prompt() fn available for PS1
    if [ -f ~/.git_prompt ]; then
        . ~/.git_prompt
    else
        git_prompt() {
            true
        }
    fi

# LnL tab completion
    export SMITHY_HOME=~/forge/cardhunter-mobile/tools
    SMITHY_SCRIPT=$SMITHY_HOME/smithy.sh
    if [ -f "$SMITHY_SCRIPT" ]; then
        . "$SMITHY_SCRIPT"
    fi

    . $SMITHY_HOME/thor_tab_completion.sh

# Git tab completion
    if [ -f $(brew --prefix)/etc/bash_completion ]; then
        . $(brew --prefix)/etc/bash_completion
    else
        echo "Warning: no git tab completion" >&2
    fi

# PERFORCE
    export P4PORT='ssl:dropforge.cloud.perforce.com:1666'


### Set prompt:
    build_prompt() {
        # Shamelessly stolen from http://selena.deckelmann.usesthis.com/ (and improved?)
	export PS1="\[\e]0;\w\a\]\[\e[32m\]\u@\h \[\e[33m\]\w $(git_prompt)\n\`if [ \$? == 0 ]; then echo \[\e[36m\]\(\=; else echo \[\e[31m\]\)\=; fi\`\[\e[0m\] "

        # unfortunately, this gums up if there are quotes in the continuation:
        export PS2="\`if [ \$? == 0 ]; then echo \[\e[36m\] \>; else echo \[\e[31m\] \>; fi\`\[\e[0m\] "
    }
    PROMPT_COMMAND=build_prompt




# Ruby, I guess?
    export PATH=/usr/local/ruby/bin:$PATH


test -e "${HOME}/.iterm2_shell_integration.bash" && source "${HOME}/.iterm2_shell_integration.bash"


# OSX PORT FORWARDING NOTES:

    pf_show() {
        sudo pfctl -s nat
    }

    pf_clear() {
        sudo pfctl -F all -f /etc/pf.conf
    }

    pf_fwd() {
        local src=$1
        local dest=$2
        echo "rdr pass inet proto tcp from any to any port $src -> 127.0.0.1 port $dest" | sudo pfctl -ef -
    }
    
    pf_help() {
        echo "pf_fwd(\$src \$dest)"
        echo "pf_clear()"
        echo "pf_show()"
    }

# OSX (POSIX?) PORT UTILITY:
    port_free() {
        lsof -i :$1
    } 

# a port forwarding rule looks like this:
  # rdr pass inet proto tcp from any to <any> port 80 -> 127.0.0.1 port <target>
  # feed such rules (pipe, file, whatever) to `sudo pfctl`

# to remove all port forwardings, do this:
  # sudo pfctl -F all -f /etc/pf.conf

#


