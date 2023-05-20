import itertools
import sys


def listify(filepath):
    depth = 0
    print("<ul>" * (depth + 1))
    for line in open(filepath):
        line = line.rstrip()
        newDepth = sum(1 for i in itertools.takewhile(lambda c: c == "\t", line))
        if newDepth > depth:
            print("<ul>" * (newDepth - depth))
        elif depth > newDepth:
            print("</ul>" * (depth - newDepth))
        print("<li>%s</li>" % (line.strip()))
        depth = newDepth
    print("</ul>" * (depth + 1))


listify(sys.argv[1])
