"""Batch round-by-round avalanche measurements, separate from visualization."""
import argparse
import csv
import json
from pathlib import Path
from statistics import mean, stdev
from aes_rounds import random_inspection


def run_round_experiments(num_trials=25):
    """Return compact per-trial measurements and per-round statistics."""
    if type(num_trials) is not int or num_trials < 1:
        raise ValueError('num_trials must be a positive integer.')
    measurements = []
    for trial in range(1, num_trials + 1):
        inspection = random_inspection()
        for step in inspection['rounds']:
            measurements.append({
                'trial': trial,
                'flipped_bit_index': inspection['flipped_bit_index'],
                'round': step['round'],
                'changed_bits': step['changed_bits'],
                'avalanche_percentage': step['avalanche_percentage'],
            })
    summary = []
    for round_number in range(11):
        values = [row['changed_bits'] for row in measurements
                  if row['round'] == round_number]
        average = mean(values)
        deviation = stdev(values) if len(values) > 1 else None
        summary.append({
            'round': round_number, 'num_trials': num_trials,
            'mean_changed_bits': average,
            'mean_avalanche_percentage': average / 128 * 100,
            'sample_std_changed_bits': deviation,
            'sample_std_percentage_points': deviation / 128 * 100 if deviation is not None else None,
            'min_changed_bits': min(values), 'max_changed_bits': max(values),
        })
    return {'schema_version': 1, 'algorithm': 'AES-128',
            'num_trials': num_trials, 'measurement_point': 'after AddRoundKey',
            'round_zero': 'initial AddRoundKey, not a full round',
            'verified_against_pycryptodome': True,
            'measurements': measurements, 'summary': summary}


def save_results(result, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in [('round_trials.csv', result['measurements']),
                           ('round_summary.csv', result['summary'])]:
        with (output_dir / filename).open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    (output_dir / 'round_experiments.json').write_text(
        json.dumps(result, indent=2), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials', type=int, default=25)
    parser.add_argument('--output-dir', type=Path,
                        default=Path(__file__).resolve().parent / 'results')
    args = parser.parse_args()
    if args.trials < 1:
        parser.error('--trials must be at least 1')
    result = run_round_experiments(args.trials)
    save_results(result, args.output_dir)
    print(f"Completed {args.trials} trials; both ciphertexts in each trial verified against PyCryptodome.")
    print('Round    Mean bits    Mean avalanche    Sample SD (bits)')
    for row in result['summary']:
        sd = row['sample_std_changed_bits']
        sd_text = f'{sd:.2f}' if sd is not None else 'N/A'
        print(f"{row['round']:>5}    {row['mean_changed_bits']:>9.2f}    {row['mean_avalanche_percentage']:>13.2f}%    {sd_text:>16}")
    print(f'Saved CSV and JSON results to: {args.output_dir.resolve()}')


if __name__ == '__main__':
    main()
