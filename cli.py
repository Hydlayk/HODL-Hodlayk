# cli.py
import sys
import os
import json
import time
from core import Blockchain, Transaction, generate_address
from wallet import create_wallet, load_wallet, export_wallet, generate_seed_phrase, sign_message, verify_signature, delete_wallet, change_wallet_password
from network import P2PNode

blockchain = Blockchain()
node = P2PNode()
node.start()

# Автоадрес (хранение в памяти, можно расширить на файл)
my_address = generate_address()
print(f"\n[👤] Ваш адрес: {my_address}\n")
wallet_active = False
wallet_data = None

def print_menu():
    print("🚀 Hodlayk CLI (русская версия)")
    print("1. Профиль")
    print("2. Отправить монеты")
    print("3. Получить адрес")
    print("4. Майнинг")
    print("5. Наши проекты")
    print("6. Пулы")
    print("7. Баланс")
    print("8. История транзакций")
    print("9. Генерация нового адреса")
    print("10. Информация о блокчейне")
    print("26. Реальный майнинг CPU")
    print("27. Создать защищённый кошелёк")
    print("28. Загрузить кошелёк")
    print("29. Экспортировать кошелёк")
    print("30. Генерация сид-фразы")
    print("31. Проверить кошелёк")
    print("32. Сменить пароль кошелька")
    print("33. Подписать сообщение")
    print("34. Проверить подпись")
    print("35. Подписать транзакцию")
    print("36. Проверить транзакцию по подписи")
    print("37. Просмотр блока по хешу")
    print("38. Список всех транзакций блока")
    print("39. Просмотр цепочки N блоков")
    print("40. Отобразить mempool")
    print("41. Сортировка tx по комиссии")
    print("42. Статистика за последние N блоков")
    print("43. Показать список пиров")
    print("44. Подключиться к пиру")
    print("45. Отправить свою цепь")
    print("46. Получить цепь у пира")
    print("47. Синхронизировать блоки")
    print("48. Проверка ключа на подлинность")
    print("49. Генерация cold-кошелька")
    print("50. Удалить кошелёк")
    print("51. Общая капитализация")
    print("52. Средняя комиссия")
    print("53. Активных адресов")
    print("54. TX/s (real-time)")
    print("55. Кол-во нод в сети")
    print("56. Создать фейковый блок")
    print("57. Перемотка времени блока")
    print("58. Перегенерация хешей")
    print("59. Печать всей цепи в файл")
    print("60. Очистить всё (reset)")
    print("0. Выход")

def profile():
    global wallet_active, wallet_data
    print(f"\n[👤 Профиль]")
    print(f"Ваш адрес: {my_address}")
    print(f"Баланс: {blockchain.get_balance(my_address):.4f} HODL")
    if wallet_active:
        print(f"Кошелёк активен: Публичный ключ {wallet_data['public_key'][:10]}...")
    else:
        print("Кошелёк не загружен.")
    print()

def send():
    global wallet_active, wallet_data
    if not wallet_active:
        print("[❌] Загрузите кошелёк для отправки транзакций.")
        return
    to = input("Введите адрес получателя: ")
    amount = float(input("Введите сумму: "))
    tx = Transaction(sender=my_address, recipient=to, amount=amount)
    signature = sign_message(wallet_data['private_key'], tx.txid)
    blockchain.add_transaction(tx)
    print(f"[✅] Транзакция добавлена в мемпул: {tx.txid}")
    print(f"[📩] Подпись: {signature}\n")
    node.broadcast_transaction(tx)

def show_address():
    print(f"\n[📮] Ваш адрес: {my_address}\n")

def mine():
    blockchain.mine_block(miner_address=my_address)

def projects():
    print("\n🔗 Наши проекты:")
    print("- Hodlayk Wallet")
    print("- Hodlayk Explorer")
    print("- Hodlayk Miner (GUI/Web)")
    print("- Hodlayk P2P Network\n")

def pools():
    print("\n💧 Пулы майнинга:")
    print("- hodlpool.io")
    print("- termuxminers.net")
    print("- communitypool.hodlayk\n")

def show_balance():
    balance = blockchain.get_balance(my_address)
    print(f"\n💰 Баланс: {balance:.4f} HODL\n")

def tx_history():
    history = blockchain.get_address_history(my_address)
    if not history:
        print("\n📭 История пуста.\n")
    else:
        print("\n📜 История транзакций:")
        for tx in history:
            print(f"{tx['timestamp']:.0f} | {tx['sender'][:6]} -> {tx['recipient'][:6]} | {tx['amount']}")

def generate_new_address():
    global my_address
    my_address = generate_address()
    print(f"\n[🎲] Новый адрес сгенерирован: {my_address}\n")

def chain_info():
    print("\n📊 Состояние сети:")
    print(f"- Блоков в цепи: {len(blockchain.chain)}")
    print(f"- Баланс: {blockchain.get_balance(my_address):.4f} HODL")
    print(f"- Неподтверждённых транзакций: {len(blockchain.mempool)}")
    print(f"- Текущая награда за блок: 50 HODL")
    print(f"- Сложность: 4")
    print(f"- Примерное время блока: 1 минута\n")

def real_cpu_mine():
    blockchain.real_cpu_mine_block(miner_address=my_address)

def create_secure_wallet():
    password = input("Придумайте пароль: ")
    wallet = create_wallet(password)
    print("✅ Кошелёк создан. Публичный ключ:", wallet['public_key'][:10], "...")

def load_secure_wallet():
    global wallet_active, wallet_data
    password = input("Введите пароль кошелька: ")
    try:
        wallet_data = load_wallet(password)
        wallet_active = True
        print("🔓 Кошелёк разблокирован. Адрес:", wallet_data['public_key'][:10], "...")
    except Exception as e:
        print("❌ Ошибка:", str(e))

def export_secure_wallet():
    try:
        export_wallet()
    except Exception as e:
        print("❌ Ошибка:", str(e))

def generate_seed():
    print("🧠 Seed-фраза:", generate_seed_phrase())

def check_wallet():
    if os.path.exists("wallet.json"):
        print("✅ Кошелёк найден.")
    else:
        print("❌ Кошелёк не найден.")

def change_wallet_password():
    old = input("Старый пароль: ")
    try:
        wallet = load_wallet(old)
        new = input("Новый пароль: ")
        change_wallet_password(old, new)
    except Exception as e:
        print("❌ Ошибка:", str(e))

def sign_message_cmd():
    global wallet_active, wallet_data
    if not wallet_active:
        print("[❌] Загрузите кошелёк для подписи.")
        return
    msg = input("Введите сообщение: ")
    try:
        signature = sign_message(wallet_data['private_key'], msg)
        print("📩 Подпись:", signature)
    except Exception as e:
        print("❌ Ошибка:", e)

def verify_signature_cmd():
    public_key = input("Введите публичный ключ: ")
    message = input("Введите сообщение: ")
    signature = input("Введите подпись: ")
    if verify_signature(public_key, message, signature):
        print("[✅] Подпись верна.")
    else:
        print("[❌] Подпись неверна.")

def sign_transaction():
    global wallet_active, wallet_data
    if not wallet_active:
        print("[❌] Загрузите кошелёк для подписи.")
        return
    to = input("Введите адрес получателя: ")
    amount = float(input("Введите сумму: "))
    tx = Transaction(sender=my_address, recipient=to, amount=amount)
    signature = sign_message(wallet_data['private_key'], tx.txid)
    print(f"[✅] Транзакция создана: {tx.txid}")
    print(f"[📩] Подпись: {signature}")

def verify_transaction():
    txid = input("Введите TXID: ")
    public_key = input("Введите публичный ключ отправителя: ")
    signature = input("Введите подпись: ")
    if verify_signature(public_key, txid, signature):
        print("[✅] Подпись транзакции верна.")
    else:
        print("[❌] Подпись транзакции неверна.")

def view_block_by_hash():
    block_hash = input("Введите хеш блока: ")
    block = blockchain.get_block_by_hash(block_hash)
    if block:
        print(f"\n[📍] Блок #{block.index}")
        print(f"Хеш: {block.hash}")
        print(f"Предыдущий хеш: {block.previous_hash}")
        print(f"Время: {block.timestamp:.0f}")
        print(f"Транзакции: {len(block.transactions)}")
    else:
        print("[❌] Блок не найден.")

def list_block_transactions():
    block_hash = input("Введите хеш блока: ")
    transactions = blockchain.get_block_transactions(block_hash)
    if transactions:
        print("\n📜 Транзакции блока:")
        for tx in transactions:
            print(f"{tx['txid'][:10]}... | {tx['sender'][:6]} -> {tx['recipient'][:6]} | {tx['amount']}")
    else:
        print("[❌] Блок не найден или пуст.")

def view_last_n_blocks():
    n = int(input("Введите количество блоков: "))
    blocks = blockchain.get_last_n_blocks(n)
    print(f"\n📚 Последние {len(blocks)} блоков:")
    for block in blocks:
        print(f"Блок #{block['index']} | Хеш: {block['hash'][:10]}... | TX: {len(block['transactions'])}")

def show_mempool():
    mempool = blockchain.get_mempool()
    if not mempool:
        print("\n📭 Мемпул пуст.")
    else:
        print("\n📜 Неподтверждённые транзакции:")
        for tx in mempool:
            print(f"{tx['txid'][:10]}... | {tx['sender'][:6]} -> {tx['recipient'][:6]} | {tx['amount']}")

def sort_mempool_by_fee():
    print("\n[⚠️] Сортировка по комиссиям пока не реализована (требуется поле fee в Transaction).")
    # Placeholder: Add fee to Transaction class and implement sorting logic.

def block_stats():
    n = int(input("Введите количество блоков для анализа: "))
    blocks = blockchain.get_last_n_blocks(n)
    if not blocks:
        print("[❌] Нет блоков для анализа.")
        return
    total_tx = sum(len(block['transactions']) for block in blocks)
    avg_time = sum(block['timestamp'] for block in blocks) / len(blocks)
    print(f"\n📊 Статистика за последние {len(blocks)} блоков:")
    print(f"Всего транзакций: {total_tx}")
    print(f"Среднее время блока: {avg_time:.0f}")

def show_peers():
    print("\n📡 Список пиров:")
    for peer in node.PEERS:
        print(f"- {peer[0]}:{peer[1]}")

def connect_to_peer():
    host = input("Введите хост пира: ")
    port = input("Введите порт (по умолчанию 5656): ") or "5656"
    node.connect_to_peer(host, int(port))

def send_chain():
    node.broadcast_chain()
    print("[✅] Цепочка отправлена всем пирам.")

def get_chain():
    print("[⚠️] Получение цепи от пира не реализовано в текущей версии network.py.")
    # Placeholder: Implement fetching chain from a specific peer.

def sync_blocks():
    node.broadcast_chain_periodically()
    print("[🔁] Синхронизация запущена.")

def check_key_authenticity():
    public_key = input("Введите публичный ключ: ")
    message = input("Введите сообщение: ")
    signature = input("Введите подпись: ")
    if verify_signature(public_key, message, signature):
        print("[✅] Ключ подлинный.")
    else:
        print("[❌] Ключ неподлинный.")

def generate_cold_wallet():
    password = input("Придумайте пароль для cold-кошелька: ")
    wallet = create_wallet(password)
    seed = generate_seed_phrase()
    print(f"[❄️] Cold-кошелёк создан. Публичный ключ: {wallet['public_key'][:10]}...")
    print(f"[🧠] Seed-фраза (сохраните!): {seed}")

def delete_secure_wallet():
    try:
        delete_wallet()
    except Exception as e:
        print("❌ Ошибка:", str(e))

def total_capitalization():
    supply = blockchain.get_total_supply()
    print(f"\n💰 Общая капитализация: {supply:.4f} HODL")

def average_fee():
    print("\n[⚠️] Средняя комиссия не реализована (требуется поле fee в Transaction).")
    # Placeholder: Implement fee tracking.

def active_addresses():
    count = blockchain.get_active_addresses()
    print(f"\n📈 Активных адресов: {count}")

def transactions_per_second():
    print("📡 Измерение TPS за 5 сек...")
    initial = len(blockchain.chain)
    time.sleep(5)
    final = len(blockchain.chain)
    tps = (final - initial) / 5
    print(f"⚡ TPS ≈ {tps:.2f}")

def node_count():
    print(f"\n📡 Количество нод в сети: {len(node.PEERS)}")

def create_fake_block():
    print("\n[⚠️] Создание фейкового блока не реализовано (для тестов).")
    # Placeholder: Add test block creation logic.

def rewind_block_time():
    print("\n[⚠️] Перемотка времени блока не реализована.")
    # Placeholder: Implement block timestamp manipulation for testing.

def regenerate_hashes():
    print("\n[⚠️] Перегенерация хешей не реализована.")
    # Placeholder: Implement hash recalculation for chain validation.

def print_chain_to_file():
    with open("blockchain_export.json", "w") as f:
        json.dump([block.to_dict() for block in blockchain.chain], f, indent=2)
    print("[💾] Цепочка сохранена в blockchain_export.json")

def reset_blockchain():
    if input("Вы уверены? (y/n): ").lower() == 'y':
        os.remove(DB_PATH)
        blockchain.chain.clear()
        blockchain.mempool.clear()
        blockchain.create_genesis_block()
        print("[🗑] Блокчейн сброшен.")
    else:
        print("[❌] Сброс отменён.")

def run():
    while True:
        print_menu()
        choice = input("👉 Выберите команду: ").strip()
        if choice == '1':
            profile()
        elif choice == '2':
            send()
        elif choice == '3':
            show_address()
        elif choice == '4':
            mine()
        elif choice == '5':
            projects()
        elif choice == '6':
            pools()
        elif choice == '7':
            show_balance()
        elif choice == '8':
            tx_history()
        elif choice == '9':
            generate_new_address()
        elif choice == '10':
            chain_info()
        elif choice == '26':
            real_cpu_mine()
        elif choice == '27':
            create_secure_wallet()
        elif choice == '28':
            load_secure_wallet()
        elif choice == '29':
            export_secure_wallet()
        elif choice == '30':
            generate_seed()
        elif choice == '31':
            check_wallet()
        elif choice == '32':
            change_wallet_password()
        elif choice == '33':
            sign_message_cmd()
        elif choice == '34':
            verify_signature_cmd()
        elif choice == '35':
            sign_transaction()
        elif choice == '36':
            verify_transaction()
        elif choice == '37':
            view_block_by_hash()
        elif choice == '38':
            list_block_transactions()
        elif choice == '39':
            view_last_n_blocks()
        elif choice == '40':
            show_mempool()
        elif choice == '41':
            sort_mempool_by_fee()
        elif choice == '42':
            block_stats()
        elif choice == '43':
            show_peers()
        elif choice == '44':
            connect_to_peer()
        elif choice == '45':
            send_chain()
        elif choice == '46':
            get_chain()
        elif choice == '47':
            sync_blocks()
        elif choice == '48':
            check_key_authenticity()
        elif choice == '49':
            generate_cold_wallet()
        elif choice == '50':
            delete_secure_wallet()
        elif choice == '51':
            total_capitalization()
        elif choice == '52':
            average_fee()
        elif choice == '53':
            active_addresses()
        elif choice == '54':
            transactions_per_second()
        elif choice == '55':
            node_count()
        elif choice == '56':
            create_fake_block()
        elif choice == '57':
            rewind_block_time()
        elif choice == '58':
            regenerate_hashes()
        elif choice == '59':
            print_chain_to_file()
        elif choice == '60':
            reset_blockchain()
        elif choice == '0':
            print("👋 До свидания!")
            sys.exit()
        else:
            print("❌ Неверный выбор\n")

if __name__ == "__main__":
    run()