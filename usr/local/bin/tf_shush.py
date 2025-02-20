#! /usr/bin/env python3

from dataclasses import dataclass

import sys
import re

@dataclass
class Line:
    text: str
    should_print: bool = False
    is_err: bool = False

    def __str__(self):
        return self.text

    # iadd is +=
    def __iadd__(self, other):
        separator = ' '
        separator = ' <NEWLINE> ' # for dev
        if isinstance(other, str):
            self.text += separator + other
        elif isinstance(other, Line):
            self.text += separator + other.text
            # We're going to ignore should_print and is_err...
            if self.is_err != other.is_err:
                raise ValueError('trying to append stdout/stderr')
            if self.should_print != other.should_print:
                print(f'{_ansy_yellow}Warning: adding lines with different `should_print` values.')
        else:
            raise ValueError('+ is only defined for `str` and `Line`')
    # Line + rhs
    def __add__(self, rhs):
        copy = Line(self.text, self.should_print)
        copy += rhs
        return copy
    # there's also __radd__ for lhs + Line, but that seems even less necessary.

def main():
    previous_line = Line('')

    def process_line(next_line, is_wrapped=False):
        nonlocal previous_line
        if is_wrapped:
            previous_line += next_line
        else:
            if previous_line.should_print:
                print(f'{_ansi_rgb(80,0,80)}***OUTPUT:*** {_ansi_reset}{previous_line}', file=(sys.stderr if previous_line.is_err else sys.stdout))
            previous_line = next_line

    recommendations = []
    count = 0
    for formatted_line in sys.stdin:
        count += 1
        formatted_line = formatted_line.rstrip('\n')
        # we'll keep track of the previous line because in general we want to print these out as they come in,
        # but sometimes there's weird line wrapping issues. So we'll be behind by a line, which in the grand scheme isn't so bad.
        line = _remove_ansi_controls(formatted_line)
        print(f'{_ansi_cyan}^^^ input line {count}: "{_ansi_reset}{line}{_ansi_cyan}"  $$${_ansi_reset}')

        # note: we're calling process with the original line, not the one we stripped so we could parse it
        if is_error_line(line):
            line = line[1:].lstrip()
            possible_fix = _get_err_recommendation(line)
            if possible_fix:
                recommendations.append(possible_fix)
            process_line(Line(formatted_line, is_err=True))
            continue

        if is_wrapped_line(line):
            process_line(formatted_line, is_wrapped=True)
            continue

        process_line(Line(formatted_line, should_print=is_interesting_line(line)))
    # don't forget to print the last line:
    process_line(None)



_tfs_stupid_error_bars = ['╷','│', '╵']

def is_error_line(line):
    line = line.lstrip()
    return 0 < len(line) and line[0] in _tfs_stupid_error_bars

def is_wrapped_line(line):
    # TODO: ???? How to detect maybe?
    return False

def is_interesting_line(line):
    return True

# This was going to be an entry point for just the stderr stream to redirect to but that was too complicated to get working in real time.

def suggest_fixes():
    # if --err was passed, stderr was redirect to our stdin
    recommendations = []
    count = 0
    for formatted_line in sys.stdin:
        count += 1
        formatted_line = formatted_line.strip()
        line = _remove_ansi_controls(formatted_line)
        print(f'{_ansi_cyan}^^^ err input line {count}: "{_ansi_reset}{line}{_ansi_cyan}" $$${_ansi_reset}')
        if line and not any(line.startswith(bar) for bar in _tfs_stupid_error_bars):
            raise ValueError('Hey we got something that wasn\'t empty or formatted with tf\'s stupid "pretty" error bar')
        line = line[1:].lstrip() # it's probably just a space but we'll be careful
        print(f'{_ansi_yellow}^^^ ***OUTPUT***: "{_ansi_reset}{formatted_line}{_ansi_yellow}" $$${_ansi_reset}')
        possible_fix = _get_err_recommendation(line)
        if possible_fix:
            recommendations.append(possible_fix)
    if 0 < len(recommendations):
        print()
        print(f'{_ansi_orange}Recommended Actions:{_ansi_reset}')
        for recco in recommendations:
            print(f'  * {recco}')

def _get_err_recommendation(line):
    if 'google' in line:
        if 'could not find default credentials' in line:
            return 'Run `gcloud auth application-default login` to obtain ADC'
        if 'querying Cloud Storage failed' in line:
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

if '__main__' == __name__:
    main()
