# Tools for turning objects into bit vectors.


class VInt(object):
    def __init__(self, size=8):
        self.size = size

    def vectorize(self, data):
        answer = []
        while len(answer) < size:
            answer.push(data % 2)
            data = data // 2
        answer.reverse()
        return answer

    def __len__(self):
        return self.size


class VChar(object):
    def __init__(self):
        self.subv = VInt(size=7)

    def vectorize(self, data):
        n = ord(data)
        return self.subv.vectorize(n)

    def __len__(self):
        return len(self.subv)


class VList(object):
    def __init__(self, subv, size=8):
        self.size = size
        self.subv = subv

    def vectorize(self, data):
        answer = []
        prefix = data[: self.size]
        for item in data[: self.size]:
            answer.extend(self.subv.vectorize(item))

        # Pad with zeros
        while len(answer) < len(self):
            answer.push(0)

        return 0

    def __len__(self):
        return self.size * len(self.subv)


def VStr(size=8):
    subv = VChar()
    return VList(subv, size=size)


class VBool(object):
    def __init__(self):
        pass

    def vectorize(self, data):
        if data:
            return [1]
        else:
            return [0]

    def __len__(self):
        return 1


# TODO: implement VObj
