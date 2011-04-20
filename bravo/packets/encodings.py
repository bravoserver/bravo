from codecs import (BufferedIncrementalDecoder, CodecInfo, IncrementalEncoder,
                    StreamReader, StreamWriter, utf_16_be_encode,
                    utf_16_be_decode)

def ucs2(name):
    if name.lower() not in ("ucs2", "ucs-2"):
        return None

    def ucs2_encode(input, errors="replace"):
        input = u"".join(i if ord(i) < 65536 else u"?" for i in input)
        return utf_16_be_encode(input, errors)

    ucs2_decode = utf_16_be_decode

    class UCS2IncrementalEncoder(IncrementalEncoder):
        def encode(self, input, final=False):
            return ucs2_encode(input, self.errors)[0]

    class UCS2IncrementalDecoder(BufferedIncrementalDecoder):
        _buffer_decode = ucs2_decode

    class UCS2StreamWriter(StreamWriter):
        encode = ucs2_encode

    class UCS2StreamReader(StreamReader):
        decode = ucs2_decode

    return CodecInfo(
        name="ucs2",
        encode=ucs2_encode,
        decode=ucs2_decode,
        incrementalencoder=UCS2IncrementalEncoder,
        incrementaldecoder=UCS2IncrementalDecoder,
        streamwriter=UCS2StreamWriter,
        streamreader=UCS2StreamReader,
    )
