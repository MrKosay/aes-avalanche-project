# AES-128 round inspection backend

Copy aes_rounds.py and test_aes_rounds.py beside your existing avalanche.py.
Keep your existing experiment and visualization files unchanged.

With your Windows virtual environment activated:

```powershell
python -m pip install pycryptodome
python -m unittest test_aes_rounds -v
python aes_rounds.py
```

The default command generates a random 16-byte plaintext, a random 16-byte key,
and a random bit position. Both encryptions use the same key. It prints round
measurements and saves results/round_inspection.json beside this module.
Re-running replaces that JSON. Use --output to keep separate runs.

For a reproducible example:

```powershell
python aes_rounds.py --plaintext 00112233445566778899aabbccddeeff --key 000102030405060708090a0b0c0d0e0f --bit 0
```

## Import from your future backend

```python
from aes_rounds import inspect_pair, random_inspection

result = random_inspection()
# Or supply raw bytes, with one input bit position:
result = inspect_pair(bytes.fromhex('00112233445566778899aabbccddeeff'), bytes(range(16)), 0)
# result is a JSON-serializable dictionary, ready for an API response.
```

There are no server dependencies, file writes on import, or frontend changes.
Importing and calling functions does not save files; only the CLI saves JSON.

## Data contract (schema_version = 1)

- algorithm, key, plaintext, modified_plaintext, flipped_bit_index
- ciphertext, modified_ciphertext, verified_against_pycryptodome
- round_keys: 11 hexadecimal keys, initial key followed by rounds 1–10
- steps: 41 aligned state comparisons, including input and every transformation
- rounds: 11 comparisons after AddRoundKey (initial round 0, then rounds 1–10)

Each comparison contains round, operation, both state hex strings, both 4x4
state matrices, xor_hex, xor_matrix, changed_bit_indices, changed_bits,
changed_bytes, avalanche_percentage.

Input is round -1. Round 0 is initial AddRoundKey, not a full AES round.
Round 10 omits MixColumns. State offset is row + 4*column. Matrices are four
visible rows; each cell holds one hex byte. Bit indices run MSB first, 0–127.
The snapshots are independent values, not references to a changing state.

## Interpretation

For a plaintext-only change under the same key:
- Initial AddRoundKey preserves exactly one differing bit.
- SubBytes can change the number of differing bits through nonlinear substitution.
- ShiftRows rearranges bytes and preserves the current differing-bit count.
- MixColumns mixes bytes within each column and spreads byte differences.
- AddRoundKey preserves the XOR difference when both states use the same round key.
- After several rounds, the differing-bit count typically fluctuates near 64/128.
  It need not rise monotonically or finish at exactly 50%.

## Implementation and validation

This module implements educational AES-128 tracing because PyCryptodome does
not expose intermediate states. PyCryptodome independently verifies both final
ciphertexts on every inspect_pair call; mismatch raises RuntimeError.
The S-box is generated from GF(2^8) inverses and the AES affine transform.
No external AES source code is copied. Encryption only; no padding, IV, chaining,
or AES-192/256. This Python tracer is for learning and experiments, not for
protecting application secrets. Output includes the experimental key.

Tests cover NIST intermediate states and key expansion, 1,000 random reference
encryptions, all 128 flip positions, matrix ordering, invalid inputs, and
ShiftRows/AddRoundKey difference invariants.

Algorithm and example vectors: NIST FIPS 197, original Appendix C.1:
https://nvlpubs.nist.gov/nistpubs/fips/nist.fips.197.pdf

## Batch round experiments (25 trials by default)

From inside aes_round_backend, with your existing environment active:

```powershell
python round_experiments.py
python -m unittest discover -v
```

Each trial uses a fresh random plaintext and key, flips one random plaintext
bit, and compares both encryptions using that same key. Both final outputs
are independently checked against PyCryptodome before collecting measurements.

Outputs (replaced on each run):
- results/round_trials.csv: 275 rows = 25 trials x 11 measurement points.
- results/round_summary.csv: 11 rows with mean, sample standard deviation,
  minimum and maximum. Percentage SD is in percentage points.
- results/round_experiments.json: the same compact measurements and summary
  for future server/frontend integration.

Round 0 is initial AddRoundKey. Rounds 1–10 are measured after AddRoundKey,
so comparisons always use the same checkpoint. Full state traces remain
available through aes_rounds.py; the batch saves only counts, not matrices.
The batch does not replace round_inspection.json.

Optional: python round_experiments.py --trials 25 --output-dir results/run2
25 trials provide an exploratory view; expect more variation than 1,000 trials.
No tests require a particular random average or a monotonic increase.
