from pysaurus.database.property import PropertyType, Property, PropertyTypeDict, PropertyDict
from pysaurus.utils import exceptions


def assert_raises(callback, expected_exceptions):
    try:
        callback()
    except expected_exceptions:
        pass
    else:
        raise AssertionError('Should fail %s' % callback)


def test_property_type():
    property_type_float = PropertyType('property 1', float)
    property_type_float_2 = PropertyType('property 1', float)
    property_type_float_default = PropertyType('property 1', float, default=4.5)
    property_type_str_default = PropertyType('property 2', str, default='hello')
    property_type_int_list = PropertyType('property 3', int, list)
    property_type_bool_set = PropertyType('property 4', bool, set)
    property_type_int_set_default = PropertyType('property 5', int, set, default=[1, 2, 1, 5, 1, 4])
    assert not property_type_float.has_default
    assert property_type_str_default.has_default and property_type_str_default.default == 'hello'
    assert not property_type_int_list.has_default
    assert not property_type_bool_set.has_default
    assert property_type_int_set_default.has_default
    assert list(sorted(property_type_int_set_default.default)) == [1, 2, 4, 5]
    assert property_type_float == property_type_float_2
    assert property_type_float != property_type_float_default
    for property_type in (property_type_float, property_type_str_default, property_type_int_list,
                          property_type_bool_set, property_type_int_set_default):
        assert PropertyType.parse(str(property_type)) == property_type
    property_type_float.validate(3.5)
    property_type_int_list.validate((1, 2, 3, 4))
    property_type_bool_set.validate((True, False, True, True))
    assert_raises(lambda: PropertyType('float', float, default=12), (exceptions.TypeException,))
    assert_raises(lambda: property_type_float.validate(2), (exceptions.TypeException,))
    assert_raises(lambda: property_type_int_list.validate(2), (exceptions.SequenceTypeException,))
    assert_raises(lambda: property_type_bool_set.validate(True), (exceptions.SequenceTypeException,))
    assert_raises(lambda: property_type_bool_set.validate((True, 0)), (exceptions.TypeException,))
    assert list(sorted(property_type_bool_set.update((True, False, True, True)))) == [False, True]
    assert list(sorted(property_type_bool_set.update((True, True, True, True)))) == [True]
    updated_value = property_type_int_list.update({2, 7, 1, 4})
    assert isinstance(updated_value, list)
    updated_value.sort()
    assert updated_value == [1, 2, 4, 7]
    updated_value = property_type_int_set_default.update((1, 1, 7, 5, 3, 2, 7, 2, 1))
    assert isinstance(updated_value, set)
    assert list(sorted(updated_value)) == [1, 2, 3, 5, 7]


def test_property():
    property_type_simple = PropertyType('my float', float)
    property_type_simple_default = PropertyType('my float', float, default=-11.7)
    property_type_list = PropertyType('my strings', str, list)
    property_type_list_default = PropertyType('my strings', str, list, default=['a', 'bb'])
    property_simple = Property(property_type_simple)
    property_simple_default = Property(property_type_simple_default, 17.0)
    property_list = Property(property_type_list)
    property_list_default = Property(property_type_list_default)
    assert property_simple.type == PropertyType('my float', float) == property_type_simple
    assert property_simple.name == 'my float'
    assert property_simple.value is None
    assert_raises(lambda: property_simple.set(None), (exceptions.TypeException,))
    property_simple.clear()
    assert property_simple.value is None
    assert_raises(lambda: property_simple.set(12), (exceptions.TypeException,))
    property_simple.set(12.0)
    assert property_simple.value == 12.0
    assert property_simple_default.value == 17.0
    property_simple_default.clear()
    assert property_simple_default.value == -11.7
    property_simple_default.set(9.5)
    assert property_simple_default.value == 9.5, property_simple_default.value
    assert property_list.value is None
    property_list.set(('1', '2', '3'))
    assert property_list.value == ['1', '2', '3']
    property_list.clear()
    assert property_list.value is None
    assert property_list_default.value == ['a', 'bb']
    property_list_default.clear()
    assert property_list_default.value == ['a', 'bb']
    property_list_default.set([str(i) for i in range(6)])
    assert property_list_default.value == ['0', '1', '2', '3', '4', '5']


def test_property_type_dict():
    type_dict = PropertyTypeDict([
        PropertyType('an int', int, default=4),
        PropertyType('a bool list', bool, list),
        PropertyType('a string', str)
    ])
    assert type_dict
    assert len(type_dict) == 3
    assert 'an int' in type_dict
    assert 'a bool list' in type_dict
    assert 'a string' in type_dict
    assert 'random string' not in type_dict
    assert type_dict['an int'] != PropertyType('an int', int)
    assert type_dict['an int'] == PropertyType('an int', int, default=4)

    parsed = PropertyTypeDict.parse(str(type_dict))
    assert isinstance(parsed, PropertyTypeDict)
    assert parsed
    assert len(parsed) == 3
    for name in ('an int', 'a bool list', 'a string'):
        assert name in parsed
        assert isinstance(parsed[name], PropertyType)
        assert parsed[name] == type_dict[name]

    assert len(parsed.names()) == 3
    assert len(parsed.types()) == 3
    assert all((isinstance(pt, PropertyType) and type_dict[pt.name] == pt) for pt in parsed.types())
    parsed.add(PropertyType('a float set', float, set, default=(4.,)))
    assert len(parsed) == 4
    assert 'a float set' in parsed
    assert parsed['a float set'].sequence_type == set
    parsed.remove('a bool list')
    assert len(parsed) == 3
    assert 'a bool list' not in parsed
    parsed.update(PropertyType('a string', str, set))
    assert len(parsed) == 3
    assert parsed['a string'] != type_dict['a string']
    assert parsed['a string'] == PropertyType('a string', str, set)
    assert_raises(lambda: parsed.add_new_type('a string', str), (AssertionError,))
    parsed.add_new_type('a bool', bool)
    parsed.add_new_list_type('a float list', float, default=[5.])
    parsed.add_new_set_type('a bool set', bool)
    assert len(parsed) == 6
    assert 'a bool' in parsed
    assert 'a float list' in parsed
    assert 'a bool set' in parsed
    assert parsed['a float list'].has_default
    assert parsed['a float list'].default == [5.0]
    val = parsed.new_value('a float list')
    val2 = parsed.new_value('a bool set')
    assert isinstance(val, Property)
    assert isinstance(val2, Property)
    assert val.type == parsed['a float list']
    assert val.value == [5.]
    assert val2.value is None
    val2.set((True, True))
    assert isinstance(val2.value, set) and len(val2.value) == 1 and True in val2.value


def test_property_dict():
    type_dict = PropertyTypeDict([
        PropertyType('an int', int, default=4),
        PropertyType('a bool list', bool, list),
        PropertyType('a string', str)
    ])
    properties = PropertyDict(type_dict, **{'a string': 'my string'})
    parsed = PropertyDict.parse(str(properties), property_type_set=type_dict)
    assert isinstance(parsed, PropertyDict)
    assert properties.is_defined('an int')
    assert not properties.is_defined('a bool list')
    assert properties.is_defined('a string')
    assert parsed.is_defined('an int')
    assert not parsed.is_defined('a bool list')
    assert parsed.is_defined('a string')
    assert properties['a bool list'] is None
    assert parsed['a bool list'] is None
    for name in ('an int', 'a string'):
        assert properties[name] is not None
        assert parsed[name] is not None
        assert properties[name] == parsed[name]
    assert properties['a string'] == 'my string'
    assert properties['an int'] == 4
    properties.clear('a string')
    properties.clear('an int')
    assert properties['a string'] is None
    assert properties['an int'] == 4
    properties['a string'] = 'new string'
    properties['an int'] = 2
    assert properties['a string'] == 'new string'
    assert properties['an int'] == 2
