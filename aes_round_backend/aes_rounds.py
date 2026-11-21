"""Educational AES-128 encryption tracing. State offset = row + 4 * column.

PyCryptodome remains the reference implementation. No server dependencies.
"""
import argparse
import json
from pathlib import Path
from secrets import randbelow, token_bytes


def _multiply(a, b):
    """Multiply bytes in GF(2^8), modulo x^8+x^4+x^3+x+1."""
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        a = ((a << 1) ^ (0x11B if a & 0x80 else 0)) & 255
        b >>= 1
    return result


def _sbox_value(value):
    # The multiplicative inverse is value^254; zero maps to zero before affine.
    inverse, base, exponent = 1, value, 254
    while exponent:
        if exponent & 1:
            inverse = _multiply(inverse, base)
        base = _multiply(base, base)
        exponent >>= 1
    result = inverse ^ 0x63
    for shift in range(1, 5):
        result ^= ((inverse << shift) | (inverse >> (8 - shift))) & 255
    return result


SBOX = tuple(_sbox_value(i) for i in range(256))


def _block(value, name):
    if not isinstance(value, bytes):
        raise TypeError(f'{name} must be bytes.')
    if len(value) != 16:
        raise ValueError(f'{name} must be exactly 16 bytes (AES-128).')


def flip_bit(data, bit_index):
    if not isinstance(data, bytes):
        raise TypeError('data must be bytes.')
    if type(bit_index) is not int or not 0 <= bit_index < len(data) * 8:
        raise ValueError('bit_index must be an integer within the input bit range.')
    result = bytearray(data)
    byte, position = divmod(bit_index, 8)
    result[byte] ^= 1 << (7 - position)
    return bytes(result)


def expand_key(key):
    """Return eleven immutable 16-byte keys: initial key and rounds 1–10."""
    _block(key, 'key')
    words = [list(key[i:i + 4]) for i in range(0, 16, 4)]
    rcon = 1
    for i in range(4, 44):
        temp = words[i - 1].copy()
        if i % 4 == 0:
            temp = [SBOX[x] for x in temp[1:] + temp[:1]]
            temp[0] ^= rcon
            rcon = _multiply(rcon, 2)
        words.append([a ^ b for a, b in zip(words[i - 4], temp)])
    return tuple(bytes(sum(words[i:i + 4], [])) for i in range(0, 44, 4))


def _shift_rows(state):
    return [state[row + 4 * ((column + row) % 4)]
            for column in range(4) for row in range(4)]


def _mix_columns(state):
    result = []
    for column in range(4):
        a, b, c, d = state[column * 4:column * 4 + 4]
        result.extend([
            _multiply(a, 2) ^ _multiply(b, 3) ^ c ^ d,
            a ^ _multiply(b, 2) ^ _multiply(c, 3) ^ d,
            a ^ b ^ _multiply(c, 2) ^ _multiply(d, 3),
            _multiply(a, 3) ^ b ^ c ^ _multiply(d, 2),
        ])
    return result


def _matrix(state):
    """Four visible rows; each cell is one hexadecimal byte."""
    return [[f'{state[row + 4 * column]:02x}' for column in range(4)]
            for row in range(4)]


def trace_encrypt(plaintext, key):
    """Record input, initial AddRoundKey, and every round transformation.

    Returns 41 JSON-compatible snapshots. Round 10 has no MixColumns.
    Initial AddRoundKey is labeled round 0; input is labeled round -1.
    """
    _block(plaintext, 'plaintext')
    keys = expand_key(key)
    state, snapshots = list(plaintext), []

    def record(round_number, operation):
        snapshots.append({'round': round_number, 'operation': operation,
                          'state_hex': bytes(state).hex(),
                          'state_matrix': _matrix(state)})

    record(-1, 'Input')
    state = [a ^ b for a, b in zip(state, keys[0])]
    record(0, 'AddRoundKey')
    for number in range(1, 11):
        state = [SBOX[x] for x in state]
        record(number, 'SubBytes')
        state = _shift_rows(state)
        record(number, 'ShiftRows')
        if number != 10:
            state = _mix_columns(state)
            record(number, 'MixColumns')
        state = [a ^ b for a, b in zip(state, keys[number])]
        record(number, 'AddRoundKey')
    return {'ciphertext': bytes(state).hex(), 'snapshots': snapshots,
            'round_keys': [key.hex() for key in keys]}


def inspect_pair(plaintext, key, bit_index=0):
    """Flip one plaintext bit and compare matching intermediate states.

    Both final ciphertexts MUST match PyCryptodome or this function raises.
    """
    from Crypto.Cipher import AES

    _block(plaintext, 'plaintext')
    _block(key, 'key')
    modified = flip_bit(plaintext, bit_index)
    original_trace = trace_encrypt(plaintext, key)
    modified_trace = trace_encrypt(modified, key)
    cipher = AES.new(key, AES.MODE_ECB)
    for block, trace in [(plaintext, original_trace), (modified, modified_trace)]:
        if cipher.encrypt(block).hex() != trace['ciphertext']:
            raise RuntimeError('Traced AES ciphertext does not match PyCryptodome.')
    comparisons = []
    for original, altered in zip(original_trace['snapshots'], modified_trace['snapshots']):
        difference = bytes(a ^ b for a, b in zip(
            bytes.fromhex(original['state_hex']), bytes.fromhex(altered['state_hex'])))
        count = sum(byte.bit_count() for byte in difference)
        comparisons.append({
            'round': original['round'], 'operation': original['operation'],
            'original_state_hex': original['state_hex'],
            'modified_state_hex': altered['state_hex'],
            'original_state_matrix': original['state_matrix'],
            'modified_state_matrix': altered['state_matrix'],
            'xor_hex': difference.hex(), 'xor_matrix': _matrix(difference),
            'changed_bit_indices': [i for i in range(128)
                                    if difference[i // 8] & (1 << (7 - i % 8))],
            'changed_bits': count, 'changed_bytes': sum(x != 0 for x in difference),
            'avalanche_percentage': count / 128 * 100,
        })
    return {
        'schema_version': 1, 'algorithm': 'AES-128',
        'state_layout': 'column-major: offset = row + 4 * column',
        'bit_order': 'MSB-first, indices 0–127',
        'key': key.hex(), 'plaintext': plaintext.hex(),
        'modified_plaintext': modified.hex(), 'flipped_bit_index': bit_index,
        'ciphertext': original_trace['ciphertext'],
        'modified_ciphertext': modified_trace['ciphertext'],
        'verified_against_pycryptodome': True,
        'round_keys': original_trace['round_keys'], 'steps': comparisons,
        'rounds': [step.copy() for step in comparisons if step['operation'] == 'AddRoundKey'],
    }


def random_inspection():
    return inspect_pair(token_bytes(16), token_bytes(16), randbelow(128))


def main():
    parser = argparse.ArgumentParser(description='Inspect AES-128 intermediate states.')
    parser.add_argument('--plaintext', help='Exactly 32 hexadecimal characters.')
    parser.add_argument('--key', help='Exactly 32 hexadecimal characters.')
    parser.add_argument('--bit', type=int, default=None, help='Bit index 0–127; default random.')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent / 'results' / 'round_inspection.json')
    args = parser.parse_args()
    try:
        def decode(text, name):
            if text is None:
                return token_bytes(16)
            if len(text) != 32:
                raise ValueError(f'{name} must be exactly 32 hexadecimal characters.')
            return bytes.fromhex(text)
        result = inspect_pair(decode(args.plaintext, 'plaintext'), decode(args.key, 'key'),
                              randbelow(128) if args.bit is None else args.bit)
    except (ValueError, TypeError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Both ciphertexts verified against PyCryptodome.')
    print(f"Flipped input bit: {result['flipped_bit_index']}")
    print('Round    Changed bits    Percentage (after AddRoundKey)')
    for row in result['rounds']:
        print(f"{row['round']:>5}    {row['changed_bits']:>8}/128    {row['avalanche_percentage']:>8.2f}%")
    print(f'Saved: {args.output}')


if __name__ == '__main__':
    main()
