# Tools for turning objects into bit vectors.
from typing import List


class VInt(object):
    def __init__(self, size=8):
        self.size = size

    def vectorize(self, data) -> List[int]:
        answer = []
        while len(answer) < self.size:
            answer.append(data % 2)
            data = data // 2
        answer.reverse()
        return answer

    def __len__(self):
        return self.size


class VCharImpl(object):
    def __init__(self):
        self.subv = VInt(size=7)

    def vectorize(self, data) -> List[int]:
        n = ord(data)
        return self.subv.vectorize(n)

    def __len__(self):
        return len(self.subv)


VChar = VCharImpl()


class VList(object):
    def __init__(self, subv, size=8):
        self.size = size
        self.subv = subv

    def vectorize(self, data) -> List[int]:
        answer = []
        if not data:
            data = []
        for item in data[: self.size]:
            answer.extend(self.subv.vectorize(item))

        # Pad with zeros
        while len(answer) < len(self):
            answer.append(0)

        return answer

    def __len__(self):
        return self.size * len(self.subv)


def VStr(size=8):
    return VList(VChar, size=size)


class VBoolImpl(object):
    def __init__(self):
        pass

    def vectorize(self, data) -> List[int]:
        if data:
            return [1]
        else:
            return [0]

    def __len__(self):
        return 1


VBool = VBoolImpl()


class VObj(object):
    def __init__(self, sublist):
        """
        sublist is a list of (keyname, subvectorizer) tuples
        """
        if type(sublist) == dict:
            sublist = list(sublist.items())
            sublist.sort()
        self.sublist = sublist
        self.size = 0
        for key, subv in self.sublist:
            if "?" in key:
                raise ValueError(f"bad VObj key: {key}")
            try:
                self.size += len(subv)
            except TypeError:
                raise ValueError(f"bad vectorizer type for key: {key}")

    def vectorize(self, data) -> List[int]:
        answer = []
        for key, subv in self.sublist:
            if hasattr(data, key):
                attr = getattr(data, key)
                answer.extend(subv.vectorize(attr))
            else:
                answer.extend([0] * len(subv))
        return answer

    def debug_size(self, indent=0):
        if indent == 0:
            print(f"overall size: {len(self)}")
        for key, subv in self.sublist:
            print(" " * indent + f"{key}: {len(subv)}")
            if hasattr(subv, "debug_size"):
                subv.debug_size(indent=indent + 2)

    def __len__(self):
        return self.size
