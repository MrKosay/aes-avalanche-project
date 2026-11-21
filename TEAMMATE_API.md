# Oracle integration agreement

The working reference endpoint is isolated in server.py's oracle APIRouter.
Replace or delegate the cipher calls there to your teammate's implementation.
Keep this contract so the UI and round inspector keep working:

POST /api/oracle/compare
Request:
{"plaintext":"00112233445566778899aabbccddeeff",
 "key":"000102030405060708090a0b0c0d0e0f", "bit_index":0}

Plaintext and key: exactly 32 hexadecimal characters (16 bytes). Bit index:
integer 0–127, most significant bit first. Modified plaintext flips exactly
that bit. One-block AES-128, no padding, IV, or chaining for this comparison.

Response keys: plaintext, modified_plaintext, key, flipped_bit_index,
ciphertext, modified_ciphertext, changed_bits, avalanche_percentage.
Hex strings encode raw bytes, not the UTF-8 characters of their hex spelling.

Tab 1 sends original plaintext, key, and bit index to tab 2. Tab 2 calls
POST /api/rounds/inspect with the same request schema, recomputes the trace,
and verifies its ciphertexts against the original selected result.
Changing tab 1 inputs clears its result and any linked round trace.

Other endpoints:
- GET /api/random-input: random 16-byte plaintext and key.
- POST /api/experiments: {"trials":1000}; UI uses exactly 1000. API accepts
  1–10000. Returns measurements, summary and chart series; does not save files.
- GET /api/health, GET /docs, GET /openapi.json.

No decryption endpoint is implemented yet. Add a dedicated endpoint and enable
its UI when your teammate's decryption module is available. Do not reinterpret
an AES inverse operation as avalanche round tracing.
