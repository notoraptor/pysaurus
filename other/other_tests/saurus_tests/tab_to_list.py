import itertools
import sys


def listify(filepath):
    depth = 0
    print("<ul>" * (depth + 1))
    for line in open(filepath):
        line = line.rstrip()
        new_depth = sum(1 for _ in itertools.takewhile(lambda c: c == "\t", line))
        if new_depth > depth:
            print("<ul>" * (new_depth - depth))
        elif depth > new_depth:
            print("</ul>" * (depth - new_depth))
        print("<li>%s</li>" % (line.strip()))
        depth = new_depth
    print("</ul>" * (depth + 1))


listify(sys.argv[1])
