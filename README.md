# AES Avalanche Lab

An interactive application for investigating the avalanche effect in AES-128.

Changing one plaintext bit while keeping the key unchanged should change approximately half the ciphertext bits on average. This project measures that behavior and visualizes how differences develop through AES rounds.

**Team:** Kosay Darwish and Mohammad Wahbi  
**Course:** EECE 455 — American University of Beirut

## Features

### 1. Encryption / Decryption Oracles

- Encrypt an original plaintext and a version with exactly one bit flipped.
- Use the same AES-128 key for both encryptions.
- Display ciphertexts in hexadecimal and Base64.
- Measure the Hamming distance and avalanche percentage.
- Decrypt either ciphertext using the corresponding key.
- Enter plaintext as raw hexadecimal bytes or UTF-8 text.

### 2. Round Inspector

- Inspect the original and modified states after each AES transformation.
- View both 4 × 4 byte matrices and their XOR difference.
- Navigate through 41 checkpoints, including the input and initial key addition.
- Track changed bits, changed bytes, and avalanche percentage.
- Inspect a pair directly from the oracle or an individual statistics trial.
- Download the inspection results as JSON.

### 3. 1,000-Trial Statistics

- Generate a fresh random plaintext and key for each trial.
- Flip one randomly selected plaintext bit.
- Keep the key unchanged within each comparison.
- Display the average, range, sample standard deviation, distribution,
  running average, and output-bit change frequencies.
- Explore individual trials and download results as CSV or JSON.

## Technology

- Python
- PyCryptodome
- FastAPI and Uvicorn
- HTML, CSS, and JavaScript

The frontend is served by FastAPI. No Node.js, database, or frontend build step
is required.

## Setup

Run all commands from the project root—the directory containing `server.py`.

### Windows PowerShell

Clone the repository:

```powershell
git clone https://github.com/MrKosay/aes-avalanche-project.git
cd aes-avalanche-project
```

Create a virtual environment and install the web application dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-web.txt
```

Start the application:

```powershell
.\.venv\Scripts\python.exe -m uvicorn server:app --reload
```

Open:

http://127.0.0.1:8000

Keep the terminal running while using the application. Press `Ctrl+C` to stop
the server.

Open the application through the server; do not open `web/index.html` directly.

### macOS / Linux

```bash
git clone https://github.com/MrKosay/aes-avalanche-project.git
cd aes-avalanche-project
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-web.txt
.venv/bin/python -m uvicorn server:app --reload
```

## Quick Demo

1. Open **Encryption / Decryption Oracles**.
2. Select **Text** and enter `Hello AES!`.
3. Enter a 32-character hexadecimal key, for example:
   `000102030405060708090a0b0c0d0e0f`.
4. Select a plaintext bit and click **Encrypt & compare**.
5. Review the plaintexts, ciphertexts, and changed-bit count.
6. Click **Inspect these rounds** to follow the differences through AES.
7. Switch to **Decryption**, select **Use original ciphertext**, and decrypt.
8. Open **1,000 trials** and run the statistical experiment.

## Input Formats

### Hexadecimal Mode

- Plaintext: exactly 32 hexadecimal characters, representing 16 bytes.
- Key: exactly 32 hexadecimal characters, representing 16 bytes.
- Bit index: an integer from 0 to 127.
- No padding is applied.

Bit numbering is most-significant-bit first: bit 0 is the leftmost bit of the
first byte.

### UTF-8 Text Mode

- Accepts 1–15 UTF-8 bytes.
- The limit counts bytes, not characters.
- PKCS#7 padding completes one 16-byte AES block.
- The bit selector targets message bytes only, excluding padding.
- The key remains a 32-character hexadecimal value.

Some characters, including Arabic letters and emoji, require multiple UTF-8
bytes. A 16-byte text message is not accepted because PKCS#7 would add another
block.

Flipping a message bit can produce bytes that are not valid UTF-8. The
application retains their hexadecimal representation and reports when a
readable text preview is unavailable.

### Ciphertext Formats

Hexadecimal and Base64 are two representations of the same ciphertext bytes.
Base64 is an encoding, not an additional encryption step.

The manual decryption input accepts hexadecimal ciphertext. The
**Use original ciphertext** and **Use modified ciphertext** buttons fill the
ciphertext, key, and padding selection automatically.

For text experiments, select PKCS#7 padding removal during decryption.
For raw hexadecimal experiments, select no padding.

## Experimental Method

For each trial:

1. Generate a random 16-byte plaintext and AES-128 key.
2. Flip exactly one plaintext bit.
3. Encrypt both blocks using the same key.
4. XOR the ciphertexts and count the set bits.

The Hamming distance is the number of differing ciphertext bits:

```text
changed_bits = number of 1 bits in (ciphertext XOR modified_ciphertext)

avalanche_percentage = changed_bits / 128 × 100
```

An average near 50% is consistent with the avalanche effect. Individual trials
are not expected to produce exactly 64 changed bits.

The output-bit frequency chart pools randomly selected input-bit positions.
It is not a complete strict avalanche criterion test.

## AES Round Inspection

PyCryptodome provides the oracle encryption and decryption operations.
A separate AES-128 implementation records intermediate states for inspection.

The trace includes:

- Input plaintext.
- Initial AddRoundKey, labeled round 0.
- All four transformations in rounds 1–9.
- SubBytes, ShiftRows, and AddRoundKey in round 10.

The final round omits MixColumns.

Whenever a pair is inspected, both final ciphertexts are checked against
PyCryptodome. The inspector raises an error if either result differs.

## Validation

The automated tests cover:

- A known NIST AES-128 ciphertext.
- Initial AddRoundKey and all four round-1 transformation outputs.
- The first expanded round key.
- Random-input final ciphertext comparisons with PyCryptodome.
- State matrix layout.
- Exactly one selected input bit changing.
- Preservation of the differing-bit count through ShiftRows and same-key
  AddRoundKey.
- Invalid inputs.
- API behavior, statistics, and round-batch exports.

Intermediate states in rounds 2–10 are not individually checked against NIST
values.

Run the API tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run the AES and round-experiment tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s aes_round_backend -v
```

## Command-Line Experiments

Run the 1,000-trial ciphertext experiment:

```powershell
.\.venv\Scripts\python.exe avalanche.py
```

Results are saved to `results/trials.csv`.

Run the round-by-round batch experiment, using 25 trials by default:

```powershell
.\.venv\Scripts\python.exe aes_round_backend/round_experiments.py
```

Choose another trial count:

```powershell
.\.venv\Scripts\python.exe aes_round_backend/round_experiments.py --trials 100
```

Round-batch results are saved under `aes_round_backend/results/`.

The web application does not automatically overwrite these saved files.
Download browser results before refreshing or closing the page.

## API Reference

Interactive documentation is available while the server is running:

http://127.0.0.1:8000/docs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check server availability |
| GET | `/api/random-input` | Generate a random plaintext and key |
| POST | `/api/oracle/compare` | Compare two encryptions from a raw hex block |
| POST | `/api/oracle/compare-text` | Compare two encryptions from UTF-8 text |
| POST | `/api/oracle/decrypt` | Decrypt a hex ciphertext block |
| POST | `/api/rounds/inspect` | Generate both AES traces and their differences |
| POST | `/api/experiments` | Run a batch of avalanche trials |

### Hex Comparison / Round Inspection

```json
{
  "plaintext": "00112233445566778899aabbccddeeff",
  "key": "000102030405060708090a0b0c0d0e0f",
  "bit_index": 0
}
```

### Text Comparison

```json
{
  "text": "Hello AES!",
  "key": "000102030405060708090a0b0c0d0e0f",
  "bit_index": 0
}
```

### Decryption

```json
{
  "ciphertext": "69c4e0d86a7b0430d8cdb78070b4c55a",
  "key": "000102030405060708090a0b0c0d0e0f",
  "padded": false
}
```

Set `padded` to `true` for a ciphertext produced by the text experiment.

### Batch Experiments

```json
{
  "trials": 1000
}
```

The API accepts 1–10,000 trials. The frontend runs 1,000 trials.

## Main Files

| File / Directory | Purpose |
|---|---|
| `server.py` | FastAPI endpoints, validation, statistics, and frontend serving |
| `aes_oracle.py` | Single-block AES encryption and decryption helpers |
| `avalanche.py` | Bit flipping, Hamming distance, and random experiments |
| `aes_round_backend/aes_rounds.py` | AES-128 implementation and state tracing |
| `aes_round_backend/round_experiments.py` | Round-by-round batch experiments and exports |
| `web/index.html` | Application structure |
| `web/style.css` | Application styling |
| `web/app.js` | UI interactions, API requests, and visualizations |
| `tests/` | API tests |
| `aes_round_backend/test_*.py` | AES and round-experiment tests |
| `requirements-web.txt` | Dependencies for running the web application |

## Scope

This is an educational AES-128, single-block application. ECB is used to
observe the block cipher directly without an IV or inter-block chaining.

It is not intended as a general-purpose secure messaging application.
Avalanche measurements illustrate diffusion; they do not establish
cryptographic security.

## Reference

NIST, *FIPS 197: Advanced Encryption Standard (AES)*, original 2001 edition,
Appendix C.1.

https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197.pdf