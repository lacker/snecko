# Tools for parsing JSON where we know the structure.
# Each of these x-functions returns a function that turns json into a typed output.


def xint(data):
    answer = int(data)
    if answer != data:
        raise ValueError(f"expected int but got {data}")
    return answer


def xstr(data):
    if type(data) != str:
        raise ValueError(f"expected str but got {data}")
    return data


def xbool(data):
    if type(data) != bool:
        raise ValueError(f"expected bool but got {data}")


# Subparser is a function that takes the data and returns the value for a subtype
def xlist(subparser):
    def find_answer(data):
        if type(data) != list:
            raise ValueError(f"expected list but got {data}")
        answer = []
        for value in data:
            answer.append(subparser(value))
        return answer

    return find_answer


# Subparsers has a subparser for each key
# Returns an object of the provided class, constructed with no arguments
# Key ends with "?" to indicate optionality
def xobj(cls, subparsers):
    def find_answer(data):
        if type(data) != dict:
            raise ValueError(f"expected dict but got {data}")
        answer = cls()
        for key, subparser in subparsers.items():
            optional = False
            if key.endswith("?"):
                key = key.strip("?")
                optional = True
            if key not in data:
                if optional:
                    answer.__setattr__(key, None)
                    continue
                raise ValueError(f"expected key {key} but data is {data}")
            value = subparser(data.get(key))
            answer.__setattr__(key, value)
        return answer

    return find_answer
