def validate_argument_types(expected_types):
    for _value, _name, _types in expected_types:
        if _value is None:
            continue

        if not isinstance(_value, _types):
            if isinstance(_types, tuple):
                acceptable_types = ' or '.join([_t.__name__ for _t in _types])
            else:
                acceptable_types = _types.__name__

            raise TypeError("Argument '%s' should be type %s, but is type %s" % (_name, acceptable_types,
                                                                                 type(_value).__name__))

    return {_name: _value for _value, _name, _types in expected_types}


def print_red(text): print(f"\x1b[31m{text}\x1b[0m")
