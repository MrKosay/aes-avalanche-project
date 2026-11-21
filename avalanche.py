import csv
from pathlib import Path
from secrets import randbelow

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


BLOCK_BYTES = AES.block_size  # 16 bytes
BLOCK_BITS = BLOCK_BYTES * 8  # 128 bits
KEY_BYTES = 16                # AES-128


def flip_bit(data, bit_index):
    """Flip one bit, counting from the left starting at index 0."""
    if not 0 <= bit_index < len(data) * 8:
        raise ValueError("Bit index is outside the input.")

    modified = bytearray(data)
    byte_index, bit_position = divmod(bit_index, 8)
    modified[byte_index] ^= 1 << (7 - bit_position)
    return bytes(modified)


def hamming_distance(first, second):
    """Count differing bits between two equal-length byte sequences."""
    if len(first) != len(second):
        raise ValueError("Inputs must have the same length.")

    return sum((a ^ b).bit_count() for a, b in zip(first, second))


def run_trial(trial_number):
    """Run one experiment with a fresh random plaintext and key."""
    key = get_random_bytes(KEY_BYTES)
    plaintext = get_random_bytes(BLOCK_BYTES)

    # Randomly choose exactly one plaintext bit to flip.
    bit_index = randbelow(BLOCK_BITS)
    modified_plaintext = flip_bit(plaintext, bit_index)

    # Both encryptions use the same key.
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(plaintext)
    modified_ciphertext = cipher.encrypt(modified_plaintext)

    changed_bits = hamming_distance(ciphertext, modified_ciphertext)

    return {
        "trial": trial_number,
        "key": key.hex(),
        "plaintext": plaintext.hex(),
        "modified_plaintext": modified_plaintext.hex(),
        "flipped_bit_index": bit_index,
        "ciphertext": ciphertext.hex(),
        "modified_ciphertext": modified_ciphertext.hex(),
        "changed_bits": changed_bits,
        "avalanche_percentage": changed_bits / BLOCK_BITS * 100,
    }


def run_experiments(num_trials):
    """Run multiple independent trials."""
    if num_trials < 1:
        raise ValueError("Number of trials must be at least 1.")

    return [run_trial(i) for i in range(1, num_trials + 1)]


def save_results(results, output_path):
    """Save measurements for later analysis and visualization."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)


def main():
    num_trials = 1000
    results = run_experiments(num_trials)

    # Display one example without flooding the terminal.
    example = results[0]
    print("First trial")
    print(f"Key:                 {example['key']}")
    print(f"Original plaintext:  {example['plaintext']}")
    print(f"Modified plaintext:  {example['modified_plaintext']}")
    print(f"Flipped bit index:   {example['flipped_bit_index']}")
    print(f"Original ciphertext: {example['ciphertext']}")
    print(f"Modified ciphertext: {example['modified_ciphertext']}")
    print(f"Output bits changed: {example['changed_bits']}/{BLOCK_BITS}")
    print(f"Avalanche:           {example['avalanche_percentage']:.2f}%")

    average_bits = sum(row["changed_bits"] for row in results) / num_trials

    output_path = Path(__file__).resolve().parent / "results" / "trials.csv"
    save_results(results, output_path)

    print(f"\nCompleted {num_trials} trials.")
    print(f"Average changed bits: {average_bits:.2f}/{BLOCK_BITS}")
    print(f"Average avalanche:    {average_bits / BLOCK_BITS * 100:.2f}%")
    print(f"Results saved to:     {output_path}")


if __name__ == "__main__":
    main()