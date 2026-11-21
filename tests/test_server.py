import unittest
from fastapi.testclient import TestClient
from Crypto.Cipher import AES
from server import app


class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.payload = {'plaintext':'00112233445566778899aabbccddeeff',
                        'key':'000102030405060708090a0b0c0d0e0f','bit_index':0}

    def test_static_and_docs(self):
        for path in ['/', '/static/app.js', '/static/style.css', '/docs', '/api/health']:
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_pair_and_trace_are_identical(self):
        for bit in [0, 7, 8, 127]:
            payload = {**self.payload, 'bit_index':bit}
            first=self.client.post('/api/oracle/compare',json=payload)
            second=self.client.post('/api/rounds/inspect',json=payload)
            self.assertEqual(first.status_code,200)
            self.assertEqual(second.status_code,200)
            pair,trace=first.json(),second.json()
            for field in ['ciphertext','modified_ciphertext','modified_plaintext']:
                self.assertEqual(pair[field],trace[field])
            self.assertEqual(pair['changed_bits'],trace['steps'][-1]['changed_bits'])
            self.assertEqual(trace['steps'][0]['changed_bit_indices'],[bit])
        self.assertEqual(pair['ciphertext'],'69c4e0d86a7b0430d8cdb78070b4c55a')

    def test_validation(self):
        for path in ['/api/oracle/compare','/api/rounds/inspect']:
            for bad in [{'key':'a'}, {'plaintext':'g'*32}, {'bit_index':128},
                        {'bit_index':-1}, {'bit_index':True}, {'bit_index':0.5}]:
                self.assertEqual(self.client.post(path,json={**self.payload,**bad}).status_code,422)
        for bad in [0,10001,True,1.5]:
            self.assertEqual(self.client.post('/api/experiments',json={'trials':bad}).status_code,422)

    def test_1000_trials_statistics_and_ciphertexts(self):
        response=self.client.post('/api/experiments',json={})
        self.assertEqual(response.status_code,200)
        data=response.json()
        self.assertEqual(len(data['trials']),1000)
        self.assertEqual(sum(data['histogram']),1000)
        mean=sum(r['changed_bits'] for r in data['trials'])/1000
        self.assertAlmostEqual(data['summary']['mean_changed_bits'],mean)
        self.assertAlmostEqual(data['running_average'][-1],mean/128*100)
        self.assertAlmostEqual(sum(data['bit_change_percentages'])/128,mean/128*100)
        for row in data['trials']:
            p=bytes.fromhex(row['plaintext']); q=bytes.fromhex(row['modified_plaintext'])
            self.assertEqual(sum((a^b).bit_count() for a,b in zip(p,q)),1)
            cipher=AES.new(bytes.fromhex(row['key']),AES.MODE_ECB)
            self.assertEqual(cipher.encrypt(p).hex(),row['ciphertext'])
            self.assertEqual(cipher.encrypt(q).hex(),row['modified_ciphertext'])

    def test_random_and_single_trial(self):
        random=self.client.get('/api/random-input').json()
        self.assertEqual(len(bytes.fromhex(random['key'])),16)
        self.assertEqual(len(bytes.fromhex(random['plaintext'])),16)
        result=self.client.post('/api/experiments',json={'trials':1}).json()
        self.assertIsNone(result['summary']['sample_std_changed_bits'])


if __name__ == '__main__':
    unittest.main()
