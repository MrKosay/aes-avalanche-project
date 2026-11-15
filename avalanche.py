from Crypto.Cipher import AES

def flip_bit(data, bit_index):
    """Bit 0 is the most significant bit of the first byte."""
    modified = bytearray(data)
    byte_index, bit_position = divmod(bit_index, 8)
    modified[byte_index] ^= 1 << (7 - bit_position)
    return bytes(modified)

def hamming_distance(first, second):
    """Count the differing bits."""
    return sum((a ^ b).bit_count() for a, b in zip(first, second))

# Exactly 16 bytes each: AES-128 key and one plaintext block.
key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
plaintext = bytes.fromhex("00112233445566778899aabbccddeeff")

# Change exactly one plaintext bit.
modified_plaintext = flip_bit(plaintext, 0)

cipher = AES.new(key, AES.MODE_ECB)
ciphertext = cipher.encrypt(plaintext)
modified_ciphertext = cipher.encrypt(modified_plaintext)

changed_bits = hamming_distance(ciphertext, modified_ciphertext)

print("Original plaintext: ", plaintext.hex())
print("Modified plaintext: ", modified_plaintext.hex())
print("Input bits changed: ", hamming_distance(plaintext, modified_plaintext))
print()
print("Original ciphertext:", ciphertext.hex())
print("Modified ciphertext:", modified_ciphertext.hex())
print(f"Output bits changed: {changed_bits}/128")
print(f"Avalanche percentage: {changed_bits / 128 * 100:.2f}%")