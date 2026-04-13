"""Reversible encryption helpers built on the custom SHA-256 module.

These helpers derive a keystream from the passphrase, nonce, and counter so
report data can be encrypted and later recovered within the application
workflow. This design is included for instructional use and is not
production-grade cryptography.
"""

from __future__ import annotations

import os

from utils.sha256_scratch import sha256_digest


def generate_nonce(length: int = 16) -> bytes:
    return os.urandom(length)


def derive_keystream(passphrase: str, nonce: bytes, length: int) -> bytes:
    if not passphrase:
        raise ValueError("A passphrase is required for encryption and decryption.")

    passphrase_bytes = passphrase.encode("utf-8")
    keystream = bytearray()
    counter = 0

    # Extend the keystream one SHA-256 block at a time until it covers the requested payload length.
    while len(keystream) < length:
        counter_bytes = counter.to_bytes(8, byteorder="big")
        block = sha256_digest(passphrase_bytes + nonce + counter_bytes)
        keystream.extend(block)
        counter += 1

    return bytes(keystream[:length])


def xor_bytes(data: bytes, keystream: bytes) -> bytes:
    # XOR is symmetric, so the same helper works for both encryption and decryption.
    return bytes(value ^ key for value, key in zip(data, keystream))


def encrypt_text(plaintext: str, passphrase: str, nonce: bytes) -> bytes:
    plaintext_bytes = plaintext.encode("utf-8")
    keystream = derive_keystream(passphrase, nonce, len(plaintext_bytes))
    return xor_bytes(plaintext_bytes, keystream)


def decrypt_text(ciphertext: bytes, passphrase: str, nonce: bytes) -> str:
    keystream = derive_keystream(passphrase, nonce, len(ciphertext))
    plaintext_bytes = xor_bytes(ciphertext, keystream)

    try:
        return plaintext_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("Unable to decode the decrypted report. The passphrase may be incorrect.") from error