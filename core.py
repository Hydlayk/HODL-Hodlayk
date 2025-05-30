# core.py
import hashlib
import json
import time
import uuid
import sqlite3
import threading
import pickle
import sys
import os
from typing import List, Dict, Optional
import multiprocessing

DB_PATH = "hodl_blockchain.db"
BLOCK_REWARD = 50
DIFFICULTY = 4
BLOCK_TIME = 60  # seconds

class Transaction:
    def __init__(self, sender, recipient, amount, timestamp=None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.txid = self.calculate_hash()

    def calculate_hash(self):
        data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self):
        return self.__dict__

class Block:
    def __init__(self, index, previous_hash, transactions, timestamp=None, nonce=0):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        data = f"{self.index}{self.timestamp}{[tx.txid for tx in self.transactions]}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.lock = threading.Lock()
        self.create_tables()
        self.load_chain()

    def create_tables(self):
        c = self.db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS blocks (
            idx INTEGER PRIMARY KEY,
            data TEXT
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS wallets (
            address TEXT PRIMARY KEY,
            balance REAL
        )''')
        self.db.commit()

    def create_genesis_block(self):
        genesis = Block(0, "0" * 64, [])
        self.chain.append(genesis)
        self.save_block(genesis)

    def load_chain(self):
        c = self.db.cursor()
        c.execute("SELECT data FROM blocks ORDER BY idx")
        rows = c.fetchall()
        if not rows:
            self.create_genesis_block()
        else:
            for row in rows:
                block_data = json.loads(row[0])
                transactions = [Transaction(**tx) for tx in block_data['transactions']]
                block = Block(block_data['index'], block_data['previous_hash'], transactions,
                              timestamp=block_data['timestamp'], nonce=block_data['nonce'])
                self.chain.append(block)

    def save_block(self, block: Block):
        with self.lock:
            c = self.db.cursor()
            c.execute("INSERT INTO blocks (idx, data) VALUES (?, ?)",
                      (block.index, json.dumps(block.to_dict())))
            self.db.commit()

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, tx: Transaction):
        self.mempool.append(tx)

    def mine_block(self, miner_address: str) -> Block:
        reward_tx = Transaction("0", miner_address, BLOCK_REWARD)
        block_transactions = [reward_tx] + self.mempool[:]
        prev_block = self.get_last_block()
        new_block = Block(len(self.chain), prev_block.hash, block_transactions)

        print("[⛏] Майнинг начался...")
        while not new_block.hash.startswith("0" * DIFFICULTY):
            new_block.nonce += 1
            new_block.hash = new_block.calculate_hash()

        print(f"[✅] Блок найден: {new_block.hash}")
        self.chain.append(new_block)
        self.save_block(new_block)
        self.mempool.clear()
        self.update_balance(miner_address, BLOCK_REWARD)
        return new_block

    def real_cpu_mine_block(self, miner_address: str, difficulty=DIFFICULTY):
        reward_tx = Transaction("0", miner_address, BLOCK_REWARD)
        block_transactions = [reward_tx] + self.mempool[:]
        prev_block = self.get_last_block()
        new_block = Block(len(self.chain), prev_block.hash, block_transactions)
        prefix = "0" * difficulty
        max_cores = multiprocessing.cpu_count()
        found = multiprocessing.Event()
        result = multiprocessing.Manager().dict()

        print(f"\n[⛏] Майнинг запущен | Цель: {prefix} | Ядер: {max_cores}")

        def worker(start_nonce, step, block_copy):
            nonce = start_nonce
            while not found.is_set():
                block_copy.nonce = nonce
                hash_candidate = block_copy.calculate_hash()
                if hash_candidate.startswith(prefix):
                    result["nonce"] = nonce
                    result["hash"] = hash_candidate
                    found.set()
                    return
                nonce += step

        start_time = time.time()
        processes = []
        for i in range(max_cores):
            block_copy = Block(new_block.index, new_block.previous_hash, block_transactions, new_block.timestamp)
            p = multiprocessing.Process(target=worker, args=(i, max_cores, block_copy))
            p.start()
            processes.append(p)

        try:
            while not found.is_set():
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[🛑] Остановка по Ctrl+C")
            found.set()

        for p in processes:
            p.terminate()

        if "nonce" in result:
            new_block.nonce = result["nonce"]
            new_block.hash = result["hash"]
            self.chain.append(new_block)
            self.save_block(new_block)
            self.update_balance(miner_address, BLOCK_REWARD)
            self.mempool.clear()
            elapsed = time.time() - start_time
            hash_rate = int((result["nonce"] + 1) / elapsed) if elapsed > 0 else 0
            print(f"[✅] Блок найден: {new_block.hash}")
            print(f"[⚡️] Средний хешрейт: {hash_rate} H/s")
            print(f"[⏱] Время: {elapsed:.2f} сек.")
            return new_block
        else:
            print("❌ Блок не найден")
            return None

    def update_balance(self, address: str, amount: float):
        c = self.db.cursor()
        c.execute("SELECT balance FROM wallets WHERE address = ?", (address,))
        row = c.fetchone()
        if row:
            new_balance = row[0] + amount
            c.execute("UPDATE wallets SET balance = ? WHERE address = ?", (new_balance, address))
        else:
            c.execute("INSERT INTO wallets (address, balance) VALUES (?, ?)", (address, amount))
        self.db.commit()

    def get_balance(self, address: str) -> float:
        c = self.db.cursor()
        c.execute("SELECT balance FROM wallets WHERE address = ?", (address,))
        row = c.fetchone()
        return row[0] if row else 0.0

    def get_address_history(self, address: str) -> List[Dict]:
        history = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address or tx.recipient == address:
                    history.append(tx.to_dict())
        return history

    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        for block in self.chain:
            if block.hash == block_hash:
                return block
        return None

    def get_block_transactions(self, block_hash: str) -> List[Dict]:
        block = self.get_block_by_hash(block_hash)
        if block:
            return [tx.to_dict() for tx in block.transactions]
        return []

    def get_last_n_blocks(self, n: int) -> List[Dict]:
        return [block.to_dict() for block in self.chain[-n:]]

    def get_mempool(self) -> List[Dict]:
        return [tx.to_dict() for tx in self.mempool]

    def get_total_supply(self) -> float:
        c = self.db.cursor()
        c.execute("SELECT SUM(balance) FROM wallets")
        result = c.fetchone()
        return result[0] if result[0] else 0.0

    def get_active_addresses(self) -> int:
        c = self.db.cursor()
        c.execute("SELECT COUNT(DISTINCT address) FROM wallets WHERE balance > 0")
        result = c.fetchone()
        return result[0] if result else 0

def generate_address() -> str:
    return hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest()