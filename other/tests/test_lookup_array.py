from pysaurus.database.viewport.view_tools import LookupArray


def test_lookup_array():
    arr = LookupArray()
    arr.append(1)
    arr.append("a")
    arr.append(4.5)
    print(arr)
    assert arr.lookup_index(4.5) == 2
    assert arr.lookup_index(1) == 0
