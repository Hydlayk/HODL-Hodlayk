# wallet.py
import os
import json
import base64
from cryptography.fernet import Fernet
from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import secrets

WALLET_FILE = "wallet.json"

def password_to_key(password: str) -> bytes:
    return base64.urlsafe_b64encode(sha256(password.encode()).digest())

def create_wallet(password: str) -> dict:
    sk = SigningKey.generate(curve=SECP256k1)
    private_key = sk.to_string().hex()
    public_key = sk.verifying_key.to_string().hex()

    key = password_to_key(password)
    f = Fernet(key)
    encrypted = f.encrypt(private_key.encode()).decode()

    wallet = {
        "public_key": public_key,
        "encrypted_private_key": encrypted,
    }

    with open(WALLET_FILE, "w") as f:
        json.dump(wallet, f)

    print(f"[💾] Кошелёк сохранён: {WALLET_FILE}")
    return wallet

def load_wallet(password: str) -> dict:
    if not os.path.exists(WALLET_FILE):
        raise FileNotFoundError("Файл кошелька не найден.")

    with open(WALLET_FILE, "r") as f:
        wallet = json.load(f)

    key = password_to_key(password)
    fernet = Fernet(key)
    try:
        decrypted = fernet.decrypt(wallet["encrypted_private_key"].encode()).decode()
        return {
            "private_key": decrypted,
            "public_key": wallet["public_key"]
        }
    except:
        raise ValueError("Неверный пароль.")

def export_wallet():
    if not os.path.exists(WALLET_FILE):
        raise FileNotFoundError("Файл кошелька не найден.")
    with open(WALLET_FILE, "r") as f:
        print(f.read())

def generate_seed_phrase() -> str:
    words = [secrets.token_hex(2) for _ in range(12)]
    return " ".join(words)

def sign_message(private_key: str, message: str) -> str:
    sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
    return sk.sign(message.encode()).hex()

def verify_signature(public_key: str, message: str, signature: str) -> bool:
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
        return vk.verify(bytes.fromhex(signature), message.encode())
    except:
        return False

def delete_wallet():
    if os.path.exists(WALLET_FILE):
        os.remove(WALLET_FILE)
        print("[🗑] Кошелёк удалён.")
    else:
        print("[❌] Кошелёк не найден.")

def change_wallet_password(old_password: str, new_password: str):
    wallet = load_wallet(old_password)
    create_wallet(new_password)
    print("[🔁] Пароль кошелька обновлён.")