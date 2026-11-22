from Crypto.Cipher import AES


def parse_hex_block(value, name):
    """Convert exactly 32 hexadecimal characters into 16 bytes."""
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a hexadecimal string.")

    value = value.strip()

    if len(value) != 32:
        raise ValueError(
            f"{name} must contain exactly 32 hexadecimal characters."
        )

    try:
        block = bytes.fromhex(value)
    except ValueError:
        raise ValueError(
            f"{name} contains invalid hexadecimal characters."
        ) from None

    if len(block) != 16:
        raise ValueError(f"{name} must represent exactly 16 bytes.")

    return block


def encrypt_block(plaintext_hex, key_hex):
    """Encrypt one block and return its ciphertext as hexadecimal."""
    plaintext = parse_hex_block(plaintext_hex, "Plaintext")
    key = parse_hex_block(key_hex, "Key")

    cipher = AES.new(key, AES.MODE_ECB)

    return cipher.encrypt(plaintext).hex()


def decrypt_block(ciphertext_hex, key_hex):
    """Decrypt one block and return its plaintext as hexadecimal."""
    ciphertext = parse_hex_block(ciphertext_hex, "Ciphertext")
    key = parse_hex_block(key_hex, "Key")

    cipher = AES.new(key, AES.MODE_ECB)

    return cipher.decrypt(ciphertext).hex()


def main():
    """Check encryption and decryption against a known AES example."""
    key = "000102030405060708090a0b0c0d0e0f"
    plaintext = "00112233445566778899aabbccddeeff"
    expected_ciphertext = "69c4e0d86a7b0430d8cdb78070b4c55a"

    ciphertext = encrypt_block(plaintext, key)
    recovered_plaintext = decrypt_block(ciphertext, key)

    if ciphertext != expected_ciphertext:
        raise RuntimeError("Encryption did not match the known ciphertext.")

    if recovered_plaintext != plaintext:
        raise RuntimeError("Decryption did not recover the plaintext.")

    print("Original plaintext: ", plaintext)
    print("Ciphertext:         ", ciphertext)
    print("Recovered plaintext:", recovered_plaintext)
    print()
    print("Encryption and decryption checks passed.")


if __name__ == "__main__":
    main()