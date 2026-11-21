"""Local FastAPI bridge. Run from project root: python -m uvicorn server:app --reload"""
from pathlib import Path
from secrets import token_bytes
from statistics import mean, stdev
from typing import Annotated

from Crypto.Cipher import AES
from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from avalanche import flip_bit, hamming_distance, run_experiments
from aes_round_backend.aes_rounds import inspect_pair

ROOT = Path(__file__).resolve().parent
HexBlock = Annotated[str, Field(pattern=r'^[0-9a-fA-F]{32}$')]


class PairRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    plaintext: HexBlock
    key: HexBlock
    bit_index: Annotated[int, Field(strict=True, ge=0, le=127)] = 0


class BatchRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    trials: Annotated[int, Field(strict=True, ge=1, le=10000)] = 1000


class PairResponse(BaseModel):
    plaintext: str
    modified_plaintext: str
    key: str
    flipped_bit_index: int
    ciphertext: str
    modified_ciphertext: str
    changed_bits: int
    avalanche_percentage: float


# This router is the integration boundary for your teammate's oracle.
# The pair endpoint is a working reference adapter, using PyCryptodome.
oracle = APIRouter(prefix='/api/oracle', tags=['Oracle integration'])


@oracle.post('/compare', response_model=PairResponse)
def compare(request: PairRequest):
    plaintext, key = bytes.fromhex(request.plaintext), bytes.fromhex(request.key)
    modified = flip_bit(plaintext, request.bit_index)
    cipher = AES.new(key, AES.MODE_ECB)
    first, second = cipher.encrypt(plaintext), cipher.encrypt(modified)
    count = hamming_distance(first, second)
    return dict(plaintext=plaintext.hex(), modified_plaintext=modified.hex(), key=key.hex(),
                flipped_bit_index=request.bit_index, ciphertext=first.hex(),
                modified_ciphertext=second.hex(), changed_bits=count,
                avalanche_percentage=count / 128 * 100)


app = FastAPI(title='AES Avalanche Lab', version='1.0.0')
app.include_router(oracle)


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/random-input')
def random_input():
    return {'plaintext': token_bytes(16).hex(), 'key': token_bytes(16).hex()}


@app.post('/api/rounds/inspect', tags=['Round inspection'])
def rounds(request: PairRequest):
    return inspect_pair(bytes.fromhex(request.plaintext), bytes.fromhex(request.key), request.bit_index)


@app.post('/api/experiments', tags=['Avalanche statistics'])
def experiments(request: BatchRequest):
    # Reuse the user's existing module; API requests do not overwrite disk CSVs.
    rows = run_experiments(request.trials)
    values = [row['changed_bits'] for row in rows]
    histogram = [0] * 129
    changes = [0] * 128
    running, total = [], 0
    for index, row in enumerate(rows, 1):
        histogram[row['changed_bits']] += 1
        total += row['changed_bits']
        running.append(total / index / 128 * 100)
        xor = int(row['ciphertext'], 16) ^ int(row['modified_ciphertext'], 16)
        for bit in range(128):
            changes[bit] += (xor >> (127 - bit)) & 1
    average = mean(values)
    return {
        'algorithm': 'AES-128', 'num_trials': request.trials,
        'summary': {'mean_changed_bits': average, 'mean_percentage': average / 128 * 100,
                    'min_changed_bits': min(values), 'max_changed_bits': max(values),
                    'sample_std_changed_bits': stdev(values) if len(values) > 1 else None},
        'histogram': histogram, 'running_average': running,
        'bit_change_percentages': [count / request.trials * 100 for count in changes],
        'trials': rows,
    }


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(ROOT / 'web' / 'index.html')


app.mount('/static', StaticFiles(directory=ROOT / 'web'), name='static')
