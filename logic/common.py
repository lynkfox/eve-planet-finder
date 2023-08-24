def try_parse(obj, possible_int):

    try:
        return obj(possible_int)
    except:
        return possible_int
