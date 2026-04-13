"""SHA-256 implementation written from scratch in pure Python.
"""

from __future__ import annotations


INITIAL_HASHES = [
    0x6A09E667,
    0xBB67AE85,
    0x3C6EF372,
    0xA54FF53A,
    0x510E527F,
    0x9B05688C,
    0x1F83D9AB,
    0x5BE0CD19,
]


ROUND_CONSTANTS = [
    0x428A2F98,
    0x71374491,
    0xB5C0FBCF,
    0xE9B5DBA5,
    0x3956C25B,
    0x59F111F1,
    0x923F82A4,
    0xAB1C5ED5,
    0xD807AA98,
    0x12835B01,
    0x243185BE,
    0x550C7DC3,
    0x72BE5D74,
    0x80DEB1FE,
    0x9BDC06A7,
    0xC19BF174,
    0xE49B69C1,
    0xEFBE4786,
    0x0FC19DC6,
    0x240CA1CC,
    0x2DE92C6F,
    0x4A7484AA,
    0x5CB0A9DC,
    0x76F988DA,
    0x983E5152,
    0xA831C66D,
    0xB00327C8,
    0xBF597FC7,
    0xC6E00BF3,
    0xD5A79147,
    0x06CA6351,
    0x14292967,
    0x27B70A85,
    0x2E1B2138,
    0x4D2C6DFC,
    0x53380D13,
    0x650A7354,
    0x766A0ABB,
    0x81C2C92E,
    0x92722C85,
    0xA2BFE8A1,
    0xA81A664B,
    0xC24B8B70,
    0xC76C51A3,
    0xD192E819,
    0xD6990624,
    0xF40E3585,
    0x106AA070,
    0x19A4C116,
    0x1E376C08,
    0x2748774C,
    0x34B0BCB5,
    0x391C0CB3,
    0x4ED8AA4A,
    0x5B9CCA4F,
    0x682E6FF3,
    0x748F82EE,
    0x78A5636F,
    0x84C87814,
    0x8CC70208,
    0x90BEFFFA,
    0xA4506CEB,
    0xBEF9A3F7,
    0xC67178F2,
]


def _right_rotate(value: int, shift: int) -> int:
    return ((value >> shift) | (value << (32 - shift))) & 0xFFFFFFFF


def _pad_message(message: bytes) -> bytearray:
    """Apply the SHA-256 preprocessing and padding rules."""
    padded = bytearray(message)
    bit_length = len(padded) * 8

    padded.append(0x80)
    while (len(padded) * 8) % 512 != 448:
        padded.append(0)

    padded.extend(bit_length.to_bytes(8, byteorder="big"))
    return padded


def sha256_digest(message: bytes) -> bytes:
    """Return the 32-byte SHA-256 digest for the supplied message bytes."""
    if not isinstance(message, (bytes, bytearray)):
        raise TypeError("sha256_digest expects bytes-like input.")

    padded_message = _pad_message(bytes(message))
    hash_values = INITIAL_HASHES[:]

    for chunk_start in range(0, len(padded_message), 64):
        chunk = padded_message[chunk_start : chunk_start + 64]

        # Build the 64-word message schedule from the 512-bit chunk.
        schedule = [0] * 64
        for index in range(16):
            word_start = index * 4
            schedule[index] = int.from_bytes(chunk[word_start : word_start + 4], byteorder="big")

        for index in range(16, 64):
            sigma0 = (
                _right_rotate(schedule[index - 15], 7)
                ^ _right_rotate(schedule[index - 15], 18)
                ^ (schedule[index - 15] >> 3)
            )
            sigma1 = (
                _right_rotate(schedule[index - 2], 17)
                ^ _right_rotate(schedule[index - 2], 19)
                ^ (schedule[index - 2] >> 10)
            )
            schedule[index] = (
                schedule[index - 16] + sigma0 + schedule[index - 7] + sigma1
            ) & 0xFFFFFFFF

        # Initialize the working variables for this compression round.
        a, b, c, d, e, f, g, h = hash_values

        # Run the 64 compression rounds.
        for index in range(64):
            big_sigma1 = _right_rotate(e, 6) ^ _right_rotate(e, 11) ^ _right_rotate(e, 25)
            choice = (e & f) ^ ((~e) & g)
            temp1 = (h + big_sigma1 + choice + ROUND_CONSTANTS[index] + schedule[index]) & 0xFFFFFFFF

            big_sigma0 = _right_rotate(a, 2) ^ _right_rotate(a, 13) ^ _right_rotate(a, 22)
            majority = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (big_sigma0 + majority) & 0xFFFFFFFF

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        # Fold the working variables back into the running hash state.
        hash_values = [
            (hash_values[0] + a) & 0xFFFFFFFF,
            (hash_values[1] + b) & 0xFFFFFFFF,
            (hash_values[2] + c) & 0xFFFFFFFF,
            (hash_values[3] + d) & 0xFFFFFFFF,
            (hash_values[4] + e) & 0xFFFFFFFF,
            (hash_values[5] + f) & 0xFFFFFFFF,
            (hash_values[6] + g) & 0xFFFFFFFF,
            (hash_values[7] + h) & 0xFFFFFFFF,
        ]

    return b"".join(value.to_bytes(4, byteorder="big") for value in hash_values)


def sha256_hex(message: bytes) -> str:
    """Return the hexadecimal SHA-256 digest string."""
    return sha256_digest(message).hex()