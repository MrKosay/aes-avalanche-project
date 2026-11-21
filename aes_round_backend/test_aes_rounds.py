import unittest
from secrets import token_bytes
from Crypto.Cipher import AES
from aes_rounds import trace_encrypt, inspect_pair, expand_key, flip_bit


class RoundTests(unittest.TestCase):
    def test_nist_intermediate_values(self):
        p = bytes.fromhex('00112233445566778899aabbccddeeff')
        k = bytes(range(16))
        result = trace_encrypt(p, k)
        self.assertEqual(result['ciphertext'], '69c4e0d86a7b0430d8cdb78070b4c55a')
        expected = {
            (0, 'AddRoundKey'): '00102030405060708090a0b0c0d0e0f0',
            (1, 'SubBytes'): '63cab7040953d051cd60e0e7ba70e18c',
            (1, 'ShiftRows'): '6353e08c0960e104cd70b751bacad0e7',
            (1, 'MixColumns'): '5f72641557f5bc92f7be3b291db9f91a',
            (1, 'AddRoundKey'): '89d810e8855ace682d1843d8cb128fe4',
        }
        for snapshot in result['snapshots']:
            at = snapshot['round'], snapshot['operation']
            if at in expected:
                self.assertEqual(snapshot['state_hex'], expected[at])
        self.assertEqual(expand_key(k)[1].hex(), 'd6aa74fdd2af72fadaa678f1d6ab76fe')
        self.assertEqual(len(result['snapshots']), 41)
        self.assertFalse(any(s['operation'] == 'MixColumns' and s['round'] == 10 for s in result['snapshots']))

    def test_random_reference_and_diff_invariants(self):
        for i in range(1000):
            p, k = token_bytes(16), token_bytes(16)
            self.assertEqual(trace_encrypt(p, k)['ciphertext'], AES.new(k, AES.MODE_ECB).encrypt(p).hex())
            if i < 128:
                result = inspect_pair(p, k, i)
                self.assertEqual(result['steps'][0]['changed_bit_indices'], [i])
                self.assertEqual(result['rounds'][0]['changed_bits'], 1)
                self.assertEqual(len(result['rounds']), 11)
                for before, after in zip(result['steps'], result['steps'][1:]):
                    if after['operation'] in ('ShiftRows', 'AddRoundKey'):
                        self.assertEqual(before['changed_bits'], after['changed_bits'])

    def test_matrix_layout(self):
        snapshot = trace_encrypt(bytes(range(16)), bytes(16))['snapshots'][0]
        self.assertEqual(snapshot['state_matrix'][0], ['00', '04', '08', '0c'])

    def test_invalid_inputs(self):
        for value in [-1, 128, True, 1.5]:
            with self.assertRaises(ValueError):
                flip_bit(bytes(16), value)
        for size in [0, 15, 17, 24, 32]:
            with self.assertRaises(ValueError):
                trace_encrypt(bytes(16), bytes(size))
        with self.assertRaises(TypeError):
            trace_encrypt('0' * 16, bytes(16))


if __name__ == '__main__':
    unittest.main()
