#!/usr/bin/env python3 

import sys
import tempfile
import io
import os

MANUAL="""
Usage: my-lyx-headerutil.py COMMAND ARG ...
A command for manipulation of the header section of lyx files. 
It is intended to be used, when you need to keep document settings
synchronized across several '.lyx' files.
Commands:
   getheader INFILE
      Print header section to stdout.
   putheader INFILE 
      Read a header section from stdin.
      Print a copy of INFILE with replaced header to stdout.
   copyheader HEADERFILE CONTENTFILE
      Print to stdout contents of CONTENTFILE 
      with header of HEADERFILE.
   copyheaderinplace HEADERFILE CONTENTFILE
      Exchange header of CONTENTFILE with header of HEADERFILE.
      BEWARE: This command doesn't create a backup of CONTENTFILE! 
   help, --help, or -h
      Print this help message.
"""

ERR_INVALID_COMMAND = 2
ERR_INVALID_NUMBER_OF_ARGUMENTS = 3
ERR_INVALID_HEADER = 4

_COMMAND_DICT = {}


def iscommand(name, numargs):
    """Decorator that registerst function as handler for command NAME,
    expecting NUMARGS arguments."""
    def decorator(function):
        _COMMAND_DICT[name] = {"numargs": numargs, "function": function}
        return function
    return decorator


def die(statuscode, msg):
    print(msg, file=sys.stderr)
    sys.exit(statuscode)


def main(*args):
    args = list(args) 
    if len(args) == 1:
        command_help()
    executable = args.pop(0)
    command = args.pop(0)
    if not command in _COMMAND_DICT:
        die(ERR_INVALID_COMMAND, 
            "Unknown command `{0}'".format(command))
    else:
        numargs = _COMMAND_DICT[command]["numargs"]
        function = _COMMAND_DICT[command]["function"]
        if len(args) != numargs:
            die(ERR_INVALID_NUMBER_OF_ARGUMENTS,
                "Command `{0}' expected {1} arguments, got {2}".format(
                    command, numargs, args))
        else:
            return function(*args)


@iscommand("help", 0)
@iscommand("--help", 0)
@iscommand("-h", 0)
def command_help(out = sys.stdout):
    print(MANUAL, file=out)
    sys.exit(0)


@iscommand("getheader",1)
def command_getheader(infilepath, out=sys.stdout):
    with open(infilepath) as infile:
        state = "beforeheader"
        for line in infile:
            if state == "insideheader":
                print(line, end="", file=out)
                if line.startswith("\\end_header"):
                    state = "afterheader"
                    break
            else:
                if line.startswith("\\begin_header"):
                    print(line, end="", file=out)
                    state = "insideheader"
        if not state == "afterheader":
            die(ERR_INVALID_HEADER,
                "File `{0}' did not contain valid lyx header".format(infilepath))


@iscommand("putheader",1)
def command_putheader(infilepath, headerstream=sys.stdin, outstream=sys.stdout):
    with open(infilepath) as infile:
        state = "beforeheader"
        for line in infile:
            if state == "beforeheader":
                if not line.startswith("\\begin_header"):
                    print(line, end="", file=outstream)
                else:
                    state = "insideheader"
                    for headerline in headerstream:
                        print(headerline, end="", file=outstream)
            if state == "insideheader":
                if line.startswith("\\end_header"):
                    state = "afterheader"
            if state == "afterheader":
                print(line, end="", file=outstream)
        if not state == "afterheader":
            die(ERR_INVALID_HEADER, 
                "File `{0}' did not contain valid lyx header".format(infilepth))


@iscommand("copyheader", 2)
def command_copyheader(headerfrompath, bodyfrompath, outstream=sys.stdout):
    header = io.StringIO()
    command_getheader(headerfrompath, out=header)
    header.seek(0)
    command_putheader(bodyfrompath, headerstream=header, outstream=outstream)


@iscommand("copyheaderinplace", 2)
def command_copyheaderinplace(headerfrompath, bodyfrompath, msgstream=sys.stdout):
    bodyfrompath = os.path.abspath(bodyfrompath)
    headerfrompath = os.path.abspath(headerfrompath)
    tmpfilepath = tempfile.mktemp(prefix=bodyfrompath+".", suffix=".tmp~")
    with open(tmpfilepath, "w") as tmpfile:
        print("Writing {0}...".format(tmpfilepath), file=msgstream)
        command_copyheader(headerfrompath, bodyfrompath, outstream=tmpfile)
        print("Done.", file=msgstream)
    print("Overwriting {0}...".format(bodyfrompath), file=msgstream)
    os.rename(tmpfilepath, bodyfrompath)
    print("Done.", file=msgstream)


if __name__ == "__main__":
    main(*sys.argv)
