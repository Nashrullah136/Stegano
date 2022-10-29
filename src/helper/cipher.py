from .Encrypter import Encrypter
from .Decrypter import Decrypter
import base64


def encrypt_vigenere(plainText, key):
    output = ""
    key = key.upper()

    for i in range(0, len(plainText)):
        output += chr((ord(plainText[i]) + ord(key[i % len(key)])) % 256)

    return output


def decrypt_vigenere(cipherText, key):
    output = ""
    key = key.upper()

    for i in range(0, len(cipherText)):
        output += chr((ord(cipherText[i]) - ord(key[i % len(key)])) % 256)

    return output


def encrypt_aes(cipher, key):
    cipher_base64 = base64.b64encode(bytes(cipher, 'utf-8'))
    x = Encrypter(cipher_base64, key)
    cipher = x.encrypt_image()
    return cipher.decode('utf-8')


def decrypt_aes(cipher, key):
    x = Decrypter(bytes(cipher, 'utf-8'))
    plain = x.decrypt_image(key)
    return plain.decode('utf-8')
