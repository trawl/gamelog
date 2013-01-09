#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

inputfile = "phasecodes.txt"


grammar = r'(\d)([src]|cr)(\d)'

def main():
    with open(inputfile,'r') as fd:
        for line in fd:
            line = line.strip()
            if line: 
                desc = decodePhase(line)
                print(desc)

def decodePhase(phasecode):
    types = {'c':"cartas del mismo color", 'r': ['escalera de', 'escaleras de'], 'cr': ['escalera de color de', 'escaleras de color de']}
    sets = {'2':['pareja','parejas'], '3':['trío','tríos'], '4':['cuarteto','cuartetos'], '5':['quinteto','quintetos']}
    #types = {'c':"cards of the same colour", 'r': ['run of', 'runs of'], 'cr': ['colour run of', 'colour runs of']}
    #sets = {'2':['pair','pairs'], '3':['three of a kind','three of a kind'], '4':['four of a kind','four of a kind'], '5':['five of a kind','five of a kind']}
    desc = ""
    first = True
    for part in phasecode.split():
        m = re.match(grammar,part)
        if m:
            n, tcode, cards = m.groups()
            if int(n)>1: plural = 1
            else: plural = 0
            if not first: desc += " + "
            first = False
            if tcode == 's':
                desc += "{} {}".format(n,sets[cards][plural])
            elif tcode == 'c':
                desc += "{} {}".format(cards,types[tcode])
            elif tcode in ['r', 'cr']:
                desc += "{} {} {}".format(n,types[tcode][plural],cards)
    return desc
        
        
if __name__ == "__main__": main()