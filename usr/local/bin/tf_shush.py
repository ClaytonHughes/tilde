#! /usr/bin/env python3

# TODO: If we want to support additional args (e.g. --keep-extra-newline), then we need to refactor
# how we're determining whether we were called in `start` mode or not (and which flags are for us or not)

def _print_usage():
    usage = """
This is intended to be invoked by a shell script like the following (here, bash):

tf()
{
    tf_shush.py --start "$@" && terraform "$@" | tf_shush.py
}
"""
    print(usage)

from dataclasses import dataclass
from datetime import datetime, timedelta

import io
import itertools
from pathlib import Path
import re
import select
import sys

## I had to tweak these until things were right. I guess this was it?
_unbuffered_input = True
_unbuffered_output = False

def _print(fmt, *args, **kwargs):
    if _unbuffered_output:
        outfile = sys.stdout
        if 'end' in kwargs:
            fmt += kwargs['end']
            del(kwargs['end'])
        else:
            fmt += '\n'
        if 'file' in kwargs:
            outfile = kwargs['file']
            del(kwargs['file'])
        outfile.write(*[fmt.encode('ascii'), *args], **kwargs)
    else:
        print(*[fmt, *args], **kwargs)

@dataclass
class Line:
    pretty: str
    line_no: int
    time: datetime
    should_print: bool = False
    is_err: bool = False

    @property
    def text(self):
        return _remove_ansi_controls(self.pretty)

    def __str__(self):
        return self.pretty

    # iadd is +=
    def __iadd__(self, other):
        separator = 't'
        separator = ' <NEWLINE> ' # for dev
        if isinstance(other, str):
            self.pretty += separator + other
        elif isinstance(other, Line):
            self.pretty += separator + other.pretty
            # We're going to ignore should_print and is_err...
            if self.is_err != other.is_err:
                raise ValueError('trying to append stdout/stderr')
            if self.should_print != other.should_print:
                _print(f'{_ansy_yellow}Warning: adding lines with different `should_print` values.'.encode('ascii'))
        else:
            raise ValueError('+ is only defined for `str` and `Line`')
    # Line + rhs
    def __add__(self, rhs):
        copy = Line(self.pretty, self.line_no, self.time, self.should_print)
        copy += rhs
        return copy
    # there's also __radd__ for lhs + Line, but that seems even less necessary.

def _unescape(arg):
    """ We're assuming non-pathological input here. Gargabe In/Garbage out is fine for user display, anyway"""
    if any(x in arg for x in [' ', '$', '\\', '"']):
        return f"'{arg}'"
    if "'" in arg:
        return f'"{arg}"'
    return arg

# python's hash() doesn't work across invocations, so we have to use an external lib:
# xxhash is a lot faster than md5, but the latter will always be available
try:
    import xxhash
    def _mk_hash(value):
        return xxhash.xxh32_hexdigest(value)
except:
    import hashlib
    def _mk_hash(value):
        return hashlib.md5(value).hexdigest

# Use the current working directory to get consistent hashing on our start time file:
_TIME_FILE = Path.home() / '.tf_start_times' / _mk_hash(bytes(Path.cwd()))

def main():
    _start_t = datetime.utcnow()

    def fmt_time(t=None):
        t = t if t else datetime.utcnow()
        relative_t = t - _start_t
        # oh just hardcode it
        if relative_t < timedelta(seconds=100):
            return f'{relative_t.seconds:02}.{int(relative_t.microseconds/1_000):03}'
        elif relative_t < timedelta(seconds=1000):
            return f'{relative_t.seconds:03}.{int(relative_t.microseconds/10_000):02}'
        else:
            return f'{relative_t.seconds:04}.{int(relative_t.microseconds/100_000):01}'

    def get_time_header(t=None):
        ansi_push='\x1b[#{' #   `CSI # {` -- create a stack frame for graphics settings
        ansi_pop='\x1b[#}' #    `CSI # }` -- pop any changes that have been made to the current graphics frame
        return f'{ansi_push}{_ansi_dim}{fmt_time(t)} {_ansi_default}| {ansi_pop}'

    # first invocation lets us print the commands, and setup better measure durations when the first
    # line of output doesn't happen immediately
    if 1 < len(sys.argv):
        if '--' not in sys.argv:
            our_args = ['--start']
            tf_args = sys.argv[2:]
        else:
            arg_separator_index = sys.argv.index('--')
            our_args = sys.argv[1:arg_separator_index]
            tf_args = sys.argv[arg_separator_index+1:]

        if any(h in our_args for h in ['--help', '-help', 'help', '/?']):
            _print_usage()
            exit(0)

        if our_args[0] == '--start':
            # try to add any shell quotes back into the arguments...
            pretty_args = ' '.join(_unescape(a) for a in tf_args)
            # We haven't messed with our output streams, so 'print' is fine here.
            print(get_time_header(_start_t) + f'{_ansi_cyan}terraform {pretty_args}{_ansi_reset}')
            _TIME_FILE.parent.mkdir(parents=True, exist_ok=True)
            _TIME_FILE.touch()
            exit(0)
        else:
            _print_usage()
            exit(1)

    ## MUCK with stdio streams
    if _unbuffered_input:
        sys.stdin = io.open(sys.stdin.fileno(), 'rb', buffering=0) # don't buffer that shit
    if _unbuffered_output:
        sys.stdout = io.open(sys.stdout.fileno(), 'wb', buffering=0) # this neither!

    # second invocation, now we're being piped our input on stdin
    # load time file to see if there is perhaps a more accurate _start_t.
    try:
        _start_t = datetime.utcfromtimestamp(_TIME_FILE.stat().st_mtime)
    except Exception as e:
        _print(f'{_ansi_hi_red}{e}{_ansi_reset}')
        _print(f'{_ansi_yellow}??.??? {_ansi_default}| {_ansi_yellow}start time lost; resetting...{_ansi_reset}')
    _TIME_FILE.unlink(missing_ok=True)

    previous_line = Line('', 0, _start_t)
    refreshing_lines = []
    reading_lines = []

    ###
    ## Everything is mostly good!
    ##
    ## There's a little bit of work to do around putting up our time_fmt when an interactive prompt appears:
    ##
    ## > 05.228 | var.environment
    ## > 05.228 |   The environment name to use
    ## >
    ## >   Enter a value: dev
    ## > 59.122 |
    ## > 59.122 | var.release_name
    ## > 59.122 |   The name of the release
    ## >
    ## >   Enter a value: release/global-sms-hotfix-c
    ## > 65.764 |
    ## > 121.58 |
    ##
    ###

    def process_line(next_line, unbuffered=False, is_wrapped=False, debug=False):
        nonlocal previous_line
        if is_wrapped:
            previous_line += next_line
        else:
            is_trailing_newline = previous_line.text.strip() == '' and not next_line
            if debug:
                _print(f'previous line ("{previous_line.text.rstrip()}") is printable: {previous_line.should_print}')
            if previous_line.should_print and not is_trailing_newline:
                #print(f'{_ansi_rgb(80,0,80)}***OUTPUT:*** {_ansi_reset}{previous_line}', file=(sys.stderr if previous_line.is_err else sys.stdout))
                # the + '\n' and end='' were some stupid trick I used during debugging, and I'm too afraid to change
                # anything right now, because it's late.
                _print(get_time_header(previous_line.time) + previous_line.pretty + '\n', file=(sys.stderr if previous_line.is_err else sys.stdout), end='')
            previous_line = next_line
        if unbuffered:
            _print(get_time_header(next_line.time) + next_line.pretty, end='')
            # Print out the prompt without waiting for the next line (because it's not coming!), and tack
            # a nothing-burger onto the end that won't print:
            previous_line = Line('', previous_line.line_no, previous_line.time, should_print=False, is_err=False)
    recommendations = []
    line_no = 0
    prompt_seen = False
    for formatted_line in sys.stdin:
        read_t = datetime.utcnow()
        if _unbuffered_input:
            formatted_line = formatted_line.decode()
        line_no += 1
        line = Line(formatted_line.rstrip('\n'), line_no, read_t)
        # we'll keep track of the previous line because in general we want to print these out as they come in,
        # but sometimes there's weird line wrapping issues. So we'll be behind by a line, which in the grand scheme isn't so bad.
        if is_error_line(line.text):
            line.should_print = True
            line.is_err = True
            # there's definitely line wrapping going on here but we're going to ignore it. I don't think it happens on the case(s) we currently care about
            # most errors are pretty irrelevant anyway.
            err_text = line.text[1:].lstrip()
            possible_fix = _get_err_recommendation(err_text)
            if possible_fix:
                recommendations.append(possible_fix)
            process_line(line)
            continue

        # it's prompting us for a value. We're gonna have to read a char at a time because python's
        # input is line-buffered.
        if line.text.startswith('var'):
            line.should_print = True
            process_line(line, debug=False)
            #process_line(line, debug=True)
            prompt_line = Line('', line_no, read_t) # a dummy val for the loop
            while prompt_line.text.rstrip()[-1:] != ':':
                #_print(f'\tREAD UNBUFFED LINE {prompt_line.text}')
                line_no += 1
                prompt_line = Line(_read_unbuffered(sys.stdin), line_no, read_t, should_print=True)
                if len(prompt_line.pretty) == 0:
                    exit(1)
                process_line(prompt_line, unbuffered=True)
            continue

        line.should_print = is_interesting_line(line.text)
        process_line(line)

    # don't forget to print the last line:
    if timedelta(seconds=.1) < datetime.utcnow() - previous_line.time:
        # wth took so long?
        process_line(Line(f'{_ansi_dim_cyan}(done){_ansi_reset}', line_no + 1, datetime.utcnow(), should_print=True))
    process_line(None)

    # and any recommendations
    if 0 < len(recommendations):
        _print()
        _print(f'{_ansi_orange}Recommended Actions:{_ansi_reset}')
        for recco in recommendations:
            _print(f'  * {recco}')


_tfs_stupid_error_bars = ['╷','│', '╵']

# like TextIOWrapper.readline (or its iterator), but returns immediately at EOF instead of waiting forever.
# (readline() only returns immediately if EOF is the *first* file it encounters, otherwise it waits for a
# newline or for the file to close.)
def _read_unbuffered(reader):
    _str = ''
    while True:
 #       _print(f'\t\t(continuing to getchar...)')
        # doesn't take kwargs, but the params here are (readfiles, writefiles, excfiles, timeout_seconds)
        # timeout 0 is nonblocking poll
        readable, _, _ = select.select([reader.fileno()], [], [], 0)
        if not _unbuffered_input:
            _print("I'm pretty sure there's no way to read stdin without blocking...")
        elif _unbuffered_input and len(readable) == 0:
#            _print('\tSELECT says there\'s nothing to read. Moving on!')
            return _str
        c = reader.read(1)
        if len(c) == 0:
            escaped = "EOF"
        elif len(c) == 1 and isinstance(c, str):
            escaped = ("\\n" if c == '\n'
                else "EOF" if c == ''
                else "\\r" if c == '\r'
                else "\\t" if c == '\t'
                else "NUL" if c == '\0'
                else "DEL" if c == chr(127)
                else hex(ord(c)) if c < ' ' # under space, it's all ctrl chars
                else c
            )
        elif isinstance(c, str):
            escaped = c.encode('ascii')
        else:
            escaped = c # already just bytes
        _str += c if isinstance(c, str) else c.decode()
#        _print(f'getchar got  "{escaped}". string is now "{_str}"')
        if c in ['', '\n']:
            return _str

def is_error_line(line):
    line = line.lstrip()
    return 0 < len(line) and line[0] in _tfs_stupid_error_bars

def is_wrapped_line(line):
    # TODO: ???? How to detect maybe? I thought this was sometimes the case...
    return False

def is_prompt(line):
    trimmed = line.strip()
    return trimmed.startswith('Enter') and trimmed.endswith(':')

def is_interesting_line(line):
    if any(line.startswith(hint) for hint in ['module.', 'data.']):
        return all(snoozefest not in line for snoozefest in [
            ': Refreshing state... ',
            ': Reading...',
            ': Read complete after',
        ])
    return True

# This was going to be an entry point for just the stderr stream to redirect to but that was too complicated to get working in real time.

def suggest_fixes():
    # if --err was passed, stderr was redirect to our stdin
    recommendations = []
    line_no = 0
    for formatted_line in sys.stdin:
        line_no += 1
        formatted_line = formatted_line.strip()
        line = _remove_ansi_controls(formatted_line)
        _print(f'{_ansi_cyan}^^^ err input line {line_no}: "{_ansi_reset}{line}{_ansi_cyan}" $$${_ansi_reset}')
        if line and not any(line.startswith(bar) for bar in _tfs_stupid_error_bars):
            raise ValueError('Hey we got something that wasn\'t empty or formatted with tf\'s stupid "pretty" error bar')
        line = line[1:].lstrip() # it's probably just a space but we'll be careful
        _print(f'{_ansi_yell}^^^ ***OUTPUT***: "{_ansi_reset}{formatted_line}{_ansi_yell}" $$${_ansi_reset}')
        possible_fix = _get_err_recommendation(line)
        if possible_fix:
            recommendations.append(possible_fix)
    if 0 < len(recommendations):
        _print()
        _print(f'{_ansi_orange}Recommended Actions:{_ansi_reset}')
        for recco in recommendations:
            _print(f'  * {recco}')

def _get_err_recommendation(line):
    if 'google' in line:
        if 'could not find default credentials' in line:
            return 'Run `gcloud auth application-default login` to obtain ADC'
        if 'querying Cloud Storage failed' in line:
            return 'Run `gcloud auth application-default login` to refresh ADC'
        if 'invalid_grant' in line:
            return 'Run `gcloud auth application-default login` to refresh ADC'
    return None

def _make_ansi(*esc_params):
    param_list = ";".join(str(p) for p in (esc_params or []))
    return f'\x1b[{param_list}m'

def _ansi_rgb(r,g,b, bg=False):
    selector = 38 if not bg else 48
    return _make_ansi(selector, 2, r, g, b)


__ansi_colors = {
    'black': 0,
    'red': 1,
    'green': 2,
    'yellow': 3,
    'blue': 4,
    'magenta': 5,
    'cyan': 6,
    'white': 7,
    'default': 9,
}

def __ansi_fg(color_index):
    if type(color_index) is str:
        color_index = __ansi_colors[color_index]
    return 30 + color_index
def __ansi_bg(color_index):
    if type(color_index) is str:
        color_index = __ansi_colors[color_index]
    return 40 + color_index

__ansi_attrs = {
    'normal': 0,
    'default': 0,
    'ecma_normal': 22, # idk, man
    'bold': 1,  # probably overrides 2 ??
    'faint': 2, # probably overrides 1 ??
    'dim': 2,
    'italics': 3,
    'italic': 3,
    'italicized': 3,
    'underline': 4,
    'underlined': 4,
    'blink': 5,
    'blinking': 5,
    'inverse': 6,
    'reverse': 6,
    'invisible': 7,
    'hidden': 7,
    'stricken': 8,
    'strike-thru': 8,
    'strike-through': 8,
    'crossed-out': 8,
    'reset_italics': 23,
    'not_italics': 23,
    'reset_italicized': 23,
    'not_italic': 23,
    'not_italicized': 23,
    # there's a zillion others, I'm done.
    # 23-29 are all negations of 3-9
}

_ansi_reset = _make_ansi()
_ansi_white = _make_ansi(__ansi_attrs['bold'], __ansi_fg('white'))
_ansi_dim = _make_ansi(__ansi_attrs['faint'], __ansi_fg('default'))
_ansi_default = _make_ansi(__ansi_attrs['ecma_normal'], __ansi_fg('default'))
_ansi_hicyan = _make_ansi(__ansi_attrs['bold'], __ansi_fg('cyan'))
_ansi_cyan = _make_ansi(__ansi_attrs['normal'], __ansi_fg('cyan'))
_ansi_dim_cyan = _make_ansi(__ansi_attrs['dim'], __ansi_fg('cyan'))
_ansi_yellow = _make_ansi(__ansi_attrs['normal'], __ansi_fg('yellow'))
_ansi_hi_red = _make_ansi(__ansi_attrs['bold'], __ansi_fg('red'))
_ansi_orange = _make_ansi(38,5,202)
_ansi_yell = _ansi_rgb(0xe0, 0xe0, 0x10)


def _remove_ansi_controls(line):
    # not just colors, but stuff like moving the cursor around, too
    return re.sub(r'\x1b\[.*?[\x40-\x7e]', '', line) # lordy, ansi. This seems to work, at least.

# ... do I want to try doing a whole parsing thing from this output? Surely no. Isn't there json output or something?

# class ResourceBlock:
#     def __init__(self, decl_line):
#         self.lines = []
#         if not decl_line.startswith('#'):
#             raise ValueError('not a resource block decl line')

#     def update(self, line):
#         if '# (config will be reloaded to verify a check block)' in line:
#             self.verification = True
#         elif '(because' in line and 'is not in configuration)' in line:
#             self.missing = True
#         return False



#     @staticmethod
#     def try_create(line):
#         if line.startswith('#')


if '__main__' == __name__:
    main()
