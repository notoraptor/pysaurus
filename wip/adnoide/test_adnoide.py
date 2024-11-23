from .adnoide import Life, Utils
from .mutation import Deletion, Duplication, Insertion, Substitution


def test_argname():
    assert Utils.argname(0) == "x"
    assert Utils.argname(1) == "y"
    assert Utils.argname(2) == "z"
    assert Utils.argname(3) == "a"
    assert Utils.argname(4) == "b"
    assert Utils.argname(23) == "u"
    assert Utils.argname(24) == "v"
    assert Utils.argname(25) == "w"
    assert Utils.argname(26) == "x27"


def test_unum():
    assert Utils.unum("abc") == 10203
    assert Utils.unum("abc_z12") == 1020389269192


def test_mutations():
    life = Life(123456)
    gene = life.random_dna()
    insertion = Insertion(life, gene)
    substitution = Substitution(life, gene)
    deletion = Deletion(life, gene)
    duplication = Duplication(life, gene)
    print(gene)
    print(insertion.random())
    print(substitution.random())
    print(deletion.random())
    print(duplication.random())
