import codecs
import struct
import json


class Stat(object):

    def __init__(self, _string=None):
        self.name = None
        self._type = None
        self.value = None

        if _string is not None:
            self.read(_string)

    def read(self, _string):
        values = _string.split(":")
        self._type = values[0]
        self.name = codecs.decode(values[1], "hex").decode(Stash.encoding)

        if not values[2]:
            return

        value = codecs.decode(values[2], "hex")

        # probably string
        if self._type == "3":
            self.value = value.decode(Stash.encoding)

        # probably IEEE 754 64bit float (in little endian?!)
        if self._type == "1":
            padded_value = value.ljust(8, b"\x00")
            self.value = struct.unpack(">d", padded_value)[0]

    def write(self):

        name = codecs.encode(bytes(self.name, Stash.encoding),
                             "hex").decode(Stash.encoding)
        value = ""
        if self.value:
            if self._type == "1":
                value = struct.pack(">d", self.value)
                while value.endswith(b"\x00"):
                    value = value[:-1]
            if self._type == "3":
                value = bytes(self.value, Stash.encoding)

            value = codecs.encode(value, "hex").decode(Stash.encoding)

        return "{}:{}:{}".format(self._type, name, value).upper()

    def to_tuple(self):
        return (self.name, self.value)


class Item(object):

    def __init__(self, _bytes=None):
        self.stats = None

        if _bytes is not None:
            self.read(_bytes)

    def read(self, _bytes):
        self.stats = []
        text = _bytes.decode(Stash.encoding)
        stats = text.split(",")
        self.stats += [Stat(s) for s in stats if s]

    def write(self):
        stats = ",".join([s.write() for s in self.stats])
        return bytes(stats, Stash.encoding)

    def to_dict(self):
        name = [s.value for s in self.stats if s.name == "name"]
        stats = [s.to_tuple()
                 for s in self.stats if s.value and s.name != "name"]
        return {"name": name[0] if name else None, "stats": dict(stats)}


class Stash(object):
    encoding = "ascii"
    header_size = 24

    def __init__(self, _file=None):
        self.header = None
        self.items = None
        self.version = None
        self.size = None

        if _file is not None:
            with open(_file, 'r') as f:
                self.read(f.read())

    def read(self, _string):
        _string = self.read_header(_string)
        _string = self.read_footer(_string)
        self.read_body(_string)

    def write(self):
        return "{}{}\n{}".format(self.write_header(),
                                 self.write_body(), self.write_footer())

    def read_header(self, _string):
        self.header = []
        # 3 bytes
        for i in range(0, Stash.header_size, 8):
            self.header += struct.unpack("<I",
                                         codecs.decode(_string[i:i + 8], "hex"))

        return _string[Stash.header_size:]

    def write_header(self):
        return "".join([codecs.encode(struct.pack("<I", h), "hex").decode(Stash.encoding) for h in self.header])

    def read_footer(self, _string):
        lines = _string.split("\n")
        self.version = float(lines[1].strip())
        self.size = int(lines[2].strip())

        return lines[0]

    def write_footer(self):
        return "\n".join([str(self.version), str(self.size)]) + " "

    def read_body(self, _string):
        binary = codecs.decode(_string, "hex")
        i = 0
        length = len(binary)
        self.items = []

        while i < length:
            # unknown value
            struct.unpack("<I", binary[i:i + 4])
            i += 4

            item_length = struct.unpack("<I", binary[i:i + 4])[0]
            i += 4

            self.items.append(Item(binary[i: i + item_length]))
            i += item_length

            # 12 zero bytes padding
            i += 12

    def write_body(self):
        binary = b""
        for item in self.items:
            binary += struct.pack("<I", 1)
            item_bytes = item.write()
            binary += struct.pack("<I", len(item_bytes))
            binary += item_bytes
            binary += 12 * b"\x00"

        return codecs.encode(binary, "hex").decode(Stash.encoding).upper()

    def to_dict(self):
        return {"size": self.size, "items": [i.to_dict() for i in self.items[:self.size]]}


if __name__ == "__main__":
    stash = Stash("player.stash")
    #print(json.dumps(stash.to_dict(), indent=3))
    [s for s in stash.items[0].stats if s.name == "dmg"][0].value = 200000.0
    with open("modified.stash", "w") as f:
        f.write(stash.write())
