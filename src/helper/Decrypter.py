import base64
import hashlib
from .AESCipher import AESCipher
from PIL import Image
from random import randint
class Decrypter:
    def __init__(self, cipher):
        self.cipher = cipher
    def decrypt_image(self,k):
        #key = self.get_key_from_image()
        key = k
        cipher = self.cipher
        aes = AESCipher(key)
        base64_decoded = aes.decrypt(cipher)
        return (base64.b64decode(base64_decoded))
        



