from construct import Construct, UBInt8


class VarInt(Construct):

    def _parse(self, stream, ctx):
        val = 0
        base = 1
        exit = False
        while exit is False:
            b = UBInt8('b')._parse(stream, ctx)
            if b < 128:
                exit = True
            else:
                b -= 128
            val += b * base
            base *= 128
        return val

    def _build(self, obj, stream=None, ctx=None):
        number = obj
        data = ''
        exit = False
        while exit is False:
            digit = number % 128
            if digit == number:
                exit = True
            else:
                number /= 128
                digit += 128
            data += chr(digit)
        if stream is not None:
            stream.write(data)
        else:
            return data

    def _sizeof(self, ctx):
        pass


if __name__ == '__main__':
    testvals = (("\x01", 1), ("\xac\x02", 300))
    for testval in testvals:
        testvarint, testnumber = testval
        checkvarint = VarInt('test').build(testnumber)
        if checkvarint == testvarint:
            print 'success with %d' % testnumber
        else:
            print 'failure: %s %s' % (checkvarint, testvarint)
        checknumber = VarInt('test').parse(testvarint)
        if checknumber == testnumber:
            print 'success with %d' % testnumber
        else:
            print 'failure: %d %d' % (checknumber, testnumber)
