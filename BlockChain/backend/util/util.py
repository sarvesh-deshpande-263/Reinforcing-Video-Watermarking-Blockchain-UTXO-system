import hashlib
from Crypto.Hash import RIPEMD160
from math import log
from BlockChain.backend.core.EllepticCurve.EllepticCurve import BASE58_ALPHABET

def hash256(s):
    """Two Rounds of SHA256"""
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()

def hash160(s):
    return RIPEMD160.new(hashlib.sha256(s).digest()).digest()

def bytes_needed(n):
    if n == 0:
        return 1
    return int(log(n, 256)) + 1


def int_to_little_endian(n, length):
    """Int_to_little_endian takes an integer and return the little-endian byte sequence of length"""
    return n.to_bytes(length, 'little')

def little_endian_to_int(b):
    """ takes little-endian byte sequence and return the an integer """
    return int.from_bytes(b, 'little')   

def decode_base58(s):
    num = 0

    for c in s:
        num *= 58
        num += BASE58_ALPHABET.index(c)
    
    combined = num.to_bytes(25, byteorder='big')
    check_sum = combined[-4:]

    if hash256(combined[:-4])[:4] != check_sum:
        raise ValueError(f"bad Address {check_sum} {hash256(combined[:-4][:4])}") 
    
    return combined[1:-4]

def encode_variant(i):
    """encodes an integer as a varint"""
    if i < 0xFD:
        return bytes([i])
    elif i < 0x10000:
        return b"\xfd" + int_to_little_endian(i, 2)
    elif i < 0x100000000:
        return b"\xfe" + int_to_little_endian(i, 4)
    elif i < 0x10000000000000000:
        return b"\xff" + int_to_little_endian(i, 8)
    else:
        raise ValueError("integer too large: {}".format(i))
    
def merkle_parent_level(hashes):
    """takes a list of binary hashes and returns a list that is half of the length"""

    if len(hashes) % 2 == 1:
        hashes.append(hashes[-1])

    parent_level = []

    for i in range(0, len(hashes), 2):
        parent = hash256(hashes[i] + hashes[i + 1])
        parent_level.append(parent)
    return parent_level
    
def merkle_root(hashes):
    """Takes a list of binary hashes and returns the merkle root"""
    current_level = hashes

    while len(current_level) > 1:
        current_level = merkle_parent_level(current_level)

    return current_level[0]