#!/usr/bin/env python3

import sys
import subprocess

# inspired by `tee`, but it redirects stdout and stderr to different pipes... And, because of the way things work,
# it runs the command instead of just received the (single-stream) piped input. So it's more like `time` in that regard.

# This is an attempt to create something like the following that preserves the order the outputs come in:

# =) function stdprint { echo '1. stdout'; >&2 echo '2. stderr'; >&2 echo '3. stderr'; echo '4. stdout'; }

# =) stdprint 2> >( rev ) > >( cat )
# rredts .2
# rredts .3
# 1. stdout
# 4. stdout

# =) ((stdprint | cat ) 3>&1 1>&2 2>&3 | rev) |& tee all.log
# 1. stdout
# 4. stdout
# rredts .2
# rredts .3

# =) eta stdprint -1 cat -2 rev
# 1. stdout
# rredts .2
# rredts .3
# 4. stdout

def main():
    if len(sys.argv == 2) and sys.argv[1] in ['-h', '--help', 'help', '?', '/?']:
        other_params_present = len(sys.argv) == 2
        print_help(sys.stderr if other_params_present else sys.stderr)
        exit(1 if other_params_present else 0)

    # preferred way to type a command is to just type it.


if '__main__' == __name__:
    main()

