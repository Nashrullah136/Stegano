from email import message
import numpy as np

import random
import base64
from ..helper.deflate.skalg import *
from math import ceil

from src.helper.file import File
from src.helper.cipher import decrypt_aes

Wc = np.indices((8, 8)).sum(axis=0) % 2


class Extractor:
    def __init__(self, file_dir, key):
        stegano_image_file = File(file_dir)
        self.ndarray = stegano_image_file.read_ndarray_image_file()
        self.h, self.w, self.color = self.ndarray.shape
        self.key = key

    def conjugate(self, P):
        return P ^ Wc

    def pbc_to_cgc(self):
        b = self.ndarray
        g = b >> 7
        for i in range(7, 0, -1):
            g <<= 1
            g |= ((b >> i) & 1) ^ ((b >> (i - 1)) & 1)
        self.ndarray = g

    def cgc_to_pbc(self):
        g = self.ndarray
        b = g >> 7
        for i in range(7, 0, -1):
            b_before = b.copy()
            b <<= 1
            b |= (b_before & 1) ^ ((g >> (i - 1)) & 1)
        self.ndarray = b

    def complexity(self, matrix):
        maxim = ((matrix.shape[0] - 1) * matrix.shape[1]) + ((matrix.shape[1] - 1) * matrix.shape[0])
        curr = 0.0
        first = matrix[0,0]
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                if (first != matrix[i,j]):
                    curr = curr + 1
                    first = matrix[i,j]
        first = matrix[0,0]
        for i in range(matrix.shape[1]):
            for j in range(matrix.shape[0]):
                if (first != matrix[j,i]):
                    curr = curr + 1
                    first = matrix[j,i]
        return curr/maxim

    def count_seed(self):
        return sum([ord(i) for i in self.key])

    def get_ndarray_pos(self, idx):
        color = idx % self.color
        w = (idx // self.color) % self.w
        h = idx // (self.color * self.w)
        return h, w, color

    def extract_alpha(self):
        index = 0
        mod_index = 8
        temp = ""
        alpha_str = ""

        for i in range(1, 8):
            for j in range(8):
                extracted = self.ndarray[i][j][0] & 1
                if index % mod_index != (mod_index - 1):
                    temp += str(extracted)
                else:
                    temp += str(extracted)
                    alpha_str += chr(int(temp, 2))
                    temp = ""
                index += 1
        return float(alpha_str)

    def convert_to_binary(self, string):
        return ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in string])

    def get_len_from_structure(self, msg):
        len = []
        index = 0
        temp = ''
        while msg[index] != "#":
            if msg[index] != "|":
                temp += msg[index]
            else:
                len.append(int(temp))
                temp = ''
            index += 1
        len.append(int(temp))
        index += 1
        len.append(index)
        return len

    def extract_structure(self, msg, len):
        index = 0
        result = list()
        len_in_bit = len[:2]
        len[0] = ceil(len[0]/8)
        len[1] = ceil(len[1]/8)
        for length in len:
            temp = msg[index:index+length]
            result.append(temp)
            index += length
        result[0] = self.convert_to_binary(result[0])[:len_in_bit[0]]
        result[1] = self.convert_to_binary(result[1])[:len_in_bit[1]]
        return result

    def destructure(self, message):
        message_info = self.get_len_from_structure(message)
        print("message_info > ", message_info)
        return self.extract_structure(message[message_info.pop():], message_info)
        # len_result1 = int(len_result1)
        # len_char_result1 = ceil(len_result1/8)
        # len_result2 = int(len_result2)
        # len_char_result2 = ceil(len_result2/8)
        # len_key_o = int(len_key_o)
        # result1 = message[index:index+len_char_result1]
        # result1 = (self.convert_to_binary(result1))[:len_result1]
        # index += len_char_result1
        # result2 = message[index:index+len_char_result2]
        # result2 = (self.convert_to_binary(result2))[:len_result2]
        # index += len_char_result2
        # key_o = message[index:index+len_key_o]
        # index += len_key_o
        # key_s = message[index:]
        # return result1, result2, key_o, key_s

    def write_to_file(self, filename, body):
        with open(filename, "w", encoding="utf-8") as file:
            file.write(body)

    def extract_messages(self):
        self.seed = self.count_seed()

        extracted = [self.ndarray[self.get_ndarray_pos(i)] & 1 for i in range(self.h * self.w * self.color)]
        encrypted = extracted[0]
        random_pixels = extracted[1]
        method = 'bpcs' if extracted[2] else 'lsb'

        index = 0
        mod_index = 8

        message = ""
        temp = ""

        if method == 'lsb':
            pixel_list = list(range(len(extracted)))
            if random_pixels:
                random.seed(self.seed)
                random.shuffle(pixel_list)

            for i in pixel_list:
                if i >= 3:
                    if index % mod_index != (mod_index - 1):
                        temp += str(extracted[i])
                    else:
                        temp += str(extracted[i])
                        message += chr(int(temp, 2))
                        temp = ""
                    index += 1
        elif method == 'bpcs':
            alpha = self.extract_alpha()
            block_list = []
            for h in range(0, self.h - (self.h % 8), 8):
                for w in range(0, self.w - (self.w % 8), 8):
                    for color in range(0, self.color):
                        block_list += [(h, w, color)]
            if random_pixels:
                random.seed(self.seed)
                random.shuffle(block_list)
            self.pbc_to_cgc()
            for bitplane in range(7, -1, -1):
                for h, w, color in block_list:
                    if h != 0 and w != 0 and color != 0:
                        matrix = self.ndarray[h:h+8, w:w+8, color] >> (7 - bitplane) & 1
                        if self.complexity(matrix) > alpha:
                            if matrix[0, 0]:
                                matrix = self.conjugate(matrix)
                            for i in range(8):
                                for j in range(8):
                                    if i > 0 or j > 0:
                                        extracted_bit = matrix[i][j]
                                        if index % mod_index != (mod_index - 1):
                                            temp += str(extracted_bit)
                                        else:
                                            temp += str(extracted_bit)
                                            message += chr(int(temp, 2))
                                            temp = ""
                                        index += 1
        self.write_to_file("structurize_message_ext.txt", message)
        result1, result2, key_o, key_s = self.destructure(message)
        self.write_to_file("result_ext.txt", result1)
        self.write_to_file("result2_ext.txt", result2)
        self.write_to_file("key_o_ext.txt", key_o)
        self.write_to_file("key_s_ext.txt", key_s)
        message = deflate().decode(result1+'\n'+result2, key_o, key_s)
        self.write_to_file("encrypted_message_ext.txt", message)
        if encrypted:
            self.string_message = decrypt_aes(message, self.key)
        else:
            self.string_message = message

    def parse_message(self):
        message_info = self.string_message.split("#")

        self.len_message = int(message_info[0])
        self.extension = message_info[1]

    def write_secret_message(self):
        init = len(str(self.len_message)) + len(str(self.extension)) + 2
        decoded = self.string_message[init : init + self.len_message]

        bytes_file = decoded.encode('utf-8')
        bytes_file = base64.b64decode(bytes_file)

        return bytes_file
