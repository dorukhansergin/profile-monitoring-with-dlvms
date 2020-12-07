#!/bin/bash
latexdiff --preamble=diffpreamble.tex --exclude-textcmd="section,enumerate" --config MINWORDSBLOCK=5 --flatten jqt_original.tex jqt.tex >diff.tex

