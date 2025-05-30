# network.py
import socket
import threading
import pickle
from core import Blockchain, Transaction, Block
import time

PORT = 5656
PEERS = set()
BUFFER = 4096

class P2PNode:
    def __init__(self, host='127.0.0.1', port=PORT):
        self.host = host
        self.port = port
        self.blockchain = Blockchain()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = False

    def start(self):
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.running = True
        print(f"[🌐] Узел запущен на {self.host}:{self.port}")
        threading.Thread(target=self.accept_clients, daemon=True).start()
        threading.Thread(target=self.broadcast_chain_periodically, daemon=True).start()

    def accept_clients(self):
        while self.running:
            try:
                conn, addr = self.server.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except Exception as e:
                print(f"[⚠️] Ошибка соединения: {e}")

    def handle_client(self, conn, addr):
        try:
            data = b''
            while True:
                chunk = conn.recv(BUFFER)
                if not chunk:
                    break
                data += chunk
            if not data:
                return

            message = pickle.loads(data)
            if message['type'] == 'transaction':
                tx = Transaction(**message['data'])
                self.blockchain.add_transaction(tx)
                print(f"[📨] Получена транзакция от {addr}")
            elif message['type'] == 'blockchain':
                remote_chain = self.deserialize_chain(message['data'])
                if len(remote_chain) > len(self.blockchain.chain):
                    self.blockchain.chain = remote_chain
                    print("[🔁] Синхронизирована цепочка")
        except Exception as e:
            print(f"[❌] Ошибка клиента {addr}: {e}")
        finally:
            conn.close()

    def broadcast_chain(self):
        for peer in PEERS.copy():
            try:
                self.send(peer[0], peer[1], {
                    'type': 'blockchain',
                    'data': self.serialize_chain(self.blockchain.chain)
                })
            except:
                PEERS.discard(peer)

    def broadcast_transaction(self, tx: Transaction):
        for peer in PEERS.copy():
            try:
                self.send(peer[0], peer[1], {
                    'type': 'transaction',
                    'data': tx.to_dict()
                })
            except:
                PEERS.discard(peer)

    def send(self, host, port, data: dict):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            s.sendall(pickle.dumps(data))

    def serialize_chain(self, chain):
        return [b.to_dict() for b in chain]

    def deserialize_chain(self, data):
        result = []
        for b in data:
            txs = [Transaction(**tx) for tx in b['transactions']]
            block = Block(b['index'], b['previous_hash'], txs, b['timestamp'], b['nonce'])
            result.append(block)
        return result

    def connect_to_peer(self, host, port=PORT):
        PEERS.add((host, port))
        print(f"[🔌] Подключено к пиру: {host}:{port}")

    def broadcast_chain_periodically(self):
        while self.running:
            self.broadcast_chain()
            time.sleep(60)
