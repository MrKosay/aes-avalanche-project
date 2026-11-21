# Run the integrated AES Avalanche Lab

Place these files in your existing aes-avalanche-project folder. Run commands
from the project root (the folder containing avalanche.py and server.py).

Windows PowerShell, using your existing virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-web.txt
python -m uvicorn server:app --reload
```

Open http://127.0.0.1:8000 in your browser. Keep the terminal running.
Ctrl+C stops the server. Do not double-click web/index.html.
No Node, npm, build step, CDN, database, hosting, or internet is needed at runtime.

## Three tabs

1. Encryption oracle: working reference adapter encrypts the original block and
   a version with one chosen bit flipped using PyCryptodome. Shows both ciphertexts.
   Full encryption/decryption oracle belongs to your teammate; decryption is
   visibly disabled until their module is integrated.
2. Round inspection: use independent inputs or click Inspect these rounds in
   the oracle tab. Both final ciphertexts are checked against the selected pair.
   Step through all 41 checkpoints, view 4x4 byte matrices, XOR differences,
   bit grid, and round progression. Changing inputs invalidates stale results.
3. 1,000-trial statistics: runs your original avalanche.run_experiments(1000).
   Shows summary, histogram, running average, output-bit change frequencies,
   and selectable trials. Inspect a selected trial in tab 2. Download CSV/JSON.

Round experiments with 25 trials remain available as a separate CLI module,
not a fourth tab. The web app does not overwrite saved experiment files.
Download results to retain them before closing or refreshing the browser.

## Test

```powershell
python -m unittest discover -s tests -v
python -m unittest discover -s aes_round_backend -v
```

## New files

- server.py: API validation, existing module adapters, statistics aggregation,
  and static frontend serving.
- requirements-web.txt: dependencies for this web application; original frozen
  requirements.txt is preserved (it was exported as UTF-16 on Windows).
- web/index.html, web/style.css, web/app.js: interface and API requests.
- tests/test_server.py: API, reference cipher, statistics, and validation tests.
- START_HERE.md: these instructions.
- TEAMMATE_API.md: integration agreement for your teammate.

Existing experiment modules, tests, and CSV/JSON result files are preserved.
The archive excludes .venv, .git, and __pycache__.

## Verification performed on this package

All 5 API tests and 6 existing AES/batch tests passed. Frontend JavaScript
syntax and DOM-simulated flows passed, including state invalidation and
1,000-trial charts. Live Chromium launch was blocked by the execution
environment, so browser appearance and real pointer/keyboard flows still
need a local review.
