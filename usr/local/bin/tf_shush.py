#! /usr/bin/env python3

from dataclasses import dataclass

import io
import re
import select
import sys

unbuffered_input = True
unbuffered_output = False

if unbuffered_input:
    sys.stdin = io.open(sys.stdin.fileno(), 'rb', buffering=0) # don't buffer that shit
if unbuffered_output:
    sys.stdout = io.open(sys.stdout.fileno(), 'wb', buffering=0) # this neither!

def _print(fmt, *args, **kwargs):
    if unbuffered_output:
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
        copy = Line(self.pretty, self.line_no, self.should_print)
        copy += rhs
        return copy
    # there's also __radd__ for lhs + Line, but that seems even less necessary.

def main():
    previous_line = Line('',0)
    refreshing_lines = []
    reading_lines = []

    def process_line(next_line, unbuffered=False, is_wrapped=False, debug=False):
        nonlocal previous_line
        if is_wrapped:
            previous_line += next_line
        else:
            if debug:
                _print(f'previous line ("{previous_line.text.rstrip()}") is printable: {previous_line.should_print}')
            if previous_line.should_print:
                #print(f'{_ansi_rgb(80,0,80)}***OUTPUT:*** {_ansi_reset}{previous_line}', file=(sys.stderr if previous_line.is_err else sys.stdout))
                # the + '\n' and end='' were some stupid trick I used during debugging, and I'm too afraid to change
                # anything right now, because it's late.
                _print(previous_line.pretty + '\n', file=(sys.stderr if previous_line.is_err else sys.stdout), end='')
            previous_line = next_line
        if unbuffered:
            _print(next_line.pretty, end='')
            # Print out the prompt without waiting for the next line (because it's not coming!), and tack
            # a nothing-burger onto the end that won't print:
            previous_line = Line('', previous_line.line_no, should_print=False, is_err=False)
    recommendations = []
    line_no = 0
    prompt_seen = False
    for formatted_line in sys.stdin:
        if unbuffered_input:
            formatted_line = formatted_line.decode()
        line_no += 1
        line = Line(formatted_line.rstrip('\n'), line_no)
        # we'll keep track of the previous line because in general we want to print these out as they come in,
        # but sometimes there's weird line wrapping issues. So we'll be behind by a line, which in the grand scheme isn't so bad.
        if is_error_line(line.text):
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
            process_line(line, debug=True)
            prompt_line = Line('', line_no) # a dummy val for the loop
            while prompt_line.text.rstrip()[-1:] != ':':
                #_print(f'\tREAD UNBUFFED LINE {prompt_line.text}')
                line_no += 1
                prompt_line = Line(_read_unbuffered(sys.stdin), line_no, should_print=True)
                if len(prompt_line.pretty) == 0:
                    exit(1)
                process_line(prompt_line, unbuffered=True)
            continue

        line.should_print = is_interesting_line(line.text)
        process_line(line)

    # don't forget to print the last line:
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
        if not unbuffered_input:
            _print("I'm pretty sure there's no way to read stdin without blocking...")
        elif unbuffered_input and len(readable) == 0:
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
        _print(f'{_ansi_yellow}^^^ ***OUTPUT***: "{_ansi_reset}{formatted_line}{_ansi_yellow}" $$${_ansi_reset}')
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

_ansi_reset = _make_ansi()
_ansi_white = _make_ansi(1, 37)
_ansi_cyan = _make_ansi(36)
_ansi_orange = _make_ansi(38,5,202)
_ansi_yellow = _ansi_rgb(0xe0, 0xe0, 0x10)


def _remove_ansi_controls(line):
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
