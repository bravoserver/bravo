from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.Hash import SHA
from Crypto import Random


class BravoCryptRSA:
    dsize = SHA.digest_size

    def __init__(self, public_key, private_key, server_id):
        self.public_key = public_key
        self.private_key = private_key
        self.server_id = server_id
        self.cipher = PKCS1_v1_5.new(self.private_key)

    def public_key_pem(self):
        return self.public_key.exportKey('PEM')

    def public_key_der(self):
        return self.public_key.exportKey('DER')

    def decrypt(self, secret, strict=False):
        sentinel = Random.new().read(15+self.dsize)

        message = self.cipher.decrypt(secret, sentinel)
        digest = SHA.new(message[:-self.dsize]).digest()
        if not strict or digest == message[-self.dsize:]:
            return message
        else:
            return None

    def hash(self, secret):
        # JMT: write tests with '' for server_id and public_key, with names for secret!
        maxval = 2**(self.dsize*8)
        msbval = maxval/2
        s = SHA.new()
        s.update(self.server_id)
        s.update(secret)
        s.update(self.public_key_der())
        val = int(s.hexdigest(), 16)
        if val >= msbval:
            val -= maxval
        return '{0:{1}x}'.format(val, self.dsize).lstrip()


class BravoCryptAES:
    bsize = AES.block_size

    def __init__(self, key, iv):
        if key is None:
            print "Key is None!"
            return None
        if key != iv:
            print "key must match iv"
            return None
        if len(iv) != self.bsize:
            print "iv must be of len %d" % self.bsize
        self.key = key
        self.iv = iv
        self.cipher = AES.new(self.key, AES.MODE_CFB, IV=self.iv)

    def encrypt(self, bytestream):
        return self.cipher.encrypt(bytestream)

    def decrypt(self, bytestream):
        return str(self.cipher.decrypt(self.iv+bytestream))[self.bsize:]

if __name__ == '__main__':

    # AES
    key = '0123456789012345'
    iv = key
    cryptAES = BravoCryptAES(key=key, iv=iv)
    plain = 'The quick young fox jumped over the lazy dog.'
    cipher = cryptAES.encrypt(plain)
    newplain = cryptAES.decrypt(cipher)
    if plain != newplain:
        print "Plain texts do not match: %s versus %s" % (plain, newplain)
    else:
        print "AES okay!"
