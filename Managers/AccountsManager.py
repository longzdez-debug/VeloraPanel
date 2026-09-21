import os
import json
import threading
import queue
import time
from core.paths import LOGPASS_PATH, MAFILES_DIR
from core import secrets

from Instances.AccountInstance import Account
from Managers.SettingsManager import SettingsManager


class AccountManager:
    _instance = None  # статическое поле для хранения одного экземпляра

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logpass_file=None, mafiles_dir=None):
        if hasattr(self, "_initialized"):
            return  # чтобы __init__ не выполнялся повторно
        self._initialized = True
        self.selected_accounts = []
        self.logpass_file = str(logpass_file or LOGPASS_PATH)
        self.mafiles_dir = str(mafiles_dir or MAFILES_DIR)
        self.accounts = self._load_accounts()

        self.accounts_start_queue = queue.Queue()
        self._batch_start_remaining = 0
        self._batch_lock = threading.Lock()
        self._batch_done_event = threading.Event()
        self._batch_done_event.set()
        settings = SettingsManager()
        self.post_launch_delay_seconds = max(
            5, int(settings.get("PostLaunchDelay", 8) or 8)
        )
        self.inter_account_delay_seconds = max(
            15, int(settings.get("InterAccountLaunchDelay", 20) or 20)
        )
        self.accounts_start_queue_thread = threading.Thread(target=self._accounts_start_process_queue, daemon=True)
        self.accounts_start_queue_thread.start()

    def _load_accounts(self):
        # Создаем файл, если его нет
        if not os.path.exists(self.logpass_file):
            os.makedirs(os.path.dirname(self.logpass_file), exist_ok=True)
            with open(self.logpass_file, "w", encoding="utf-8") as f:
                f.write("# login:password\n")

        encrypted_accounts = {}
        try:
            encrypted_accounts = secrets.get_accounts()
        except RuntimeError as exc:
            print(f"⚠️ Зашифрованное хранилище недоступно: {exc}")
        had_encrypted_store = bool(encrypted_accounts)

        # Загружаем логины и пароли; encrypted store is preferred.
        with open(self.logpass_file, "r", encoding="utf-8") as f:
            lines = []
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                login, password = line.split(":", 1)
                if login.strip() and password:
                    lines.append((login.strip(), password))

        if encrypted_accounts:
            lines = [
                (login, data.get("password", ""))
                for login, data in encrypted_accounts.items()
                if isinstance(data, dict) and data.get("password")
            ]

        # Загружаем mafiles
        mafiles = {}
        if os.path.exists(self.mafiles_dir):
            for file in os.listdir(self.mafiles_dir):
                if file.lower().endswith(".mafile"):
                    try:
                        with open(os.path.join(self.mafiles_dir, file), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            session = data.get("Session") or {}

                            # В разных экспортерах поля могут называться по-разному.
                            account_name = (
                                data.get("account_name")
                                or data.get("AccountName")
                                or session.get("AccountName")
                                or session.get("account_name")
                                or ""
                            ).strip().lower()

                            # Извлекаем shared_secret и identity_secret (поддержка альтернативных ключей)
                            shared_secret = (
                                data.get("shared_secret")
                                or data.get("SharedSecret")
                                or session.get("SharedSecret")
                            )
                            identity_secret = (
                                data.get("identity_secret")
                                or data.get("IdentitySecret")
                                or session.get("IdentitySecret")
                            )

                            # Извлекаем steam_id из mafile
                            steam_id = (
                                session.get("SteamID")
                                or data.get("steamid")
                                or data.get("SteamID")
                                or 0
                            )

                            if account_name:
                                mafiles[account_name] = {
                                    "shared_secret": shared_secret,
                                    "identity_secret": identity_secret,
                                    "steam_id": steam_id
                                }
                                encrypted_accounts.setdefault(account_name, {}).update(
                                    {
                                        "shared_secret": shared_secret,
                                        "identity_secret": identity_secret,
                                        "steam_id": steam_id,
                                    }
                                )
                    except (OSError, ValueError, json.JSONDecodeError) as exc:
                        print(f"⚠️ Не удалось прочитать mafile {file}: {exc}")

        # Создаем список аккаунтов
        accounts = []
        for login, password in lines:
            mafile_data = mafiles.get(login.lower())
            if not mafile_data:
                mafile_data = encrypted_accounts.get(login.lower())
            if mafile_data:
                try:
                    if not mafile_data.get("shared_secret"):
                        print(f"⚠️ [{login}] mafile найден, но shared_secret пустой")
                    accounts.append(Account(
                        login,
                        password,
                        mafile_data.get("shared_secret"),
                        int(mafile_data.get("steam_id", 0)),
                        mafile_data.get("identity_secret")
                        ))
                except Exception as e:
                    print(f"⚠️ [{login}] Ошибка чтения mafile: {e}")
                    accounts.append(Account(login, password, None, 0, None))
            else:
                print(f"⚠️ [{login}] mafile не найден по account_name")
                accounts.append(Account(login, password, None, 0, None))  # Без секретов и steam_id
        if not had_encrypted_store:
            try:
                secrets.set_accounts(
                    {
                        login.lower(): {
                            "password": password,
                            **{
                                key: value
                                for key, value in encrypted_accounts.get(login.lower(), {}).items()
                                if key != "password"
                            },
                        }
                        for login, password in lines
                    }
                )
                print("✅ Credentials migrated to DPAPI storage")
            except (OSError, RuntimeError) as exc:
                print(f"⚠️ Не удалось создать DPAPI-хранилище: {exc}")
        else:
            try:
                secrets.set_accounts(encrypted_accounts)
            except (OSError, RuntimeError) as exc:
                print(f"⚠️ Не удалось обновить DPAPI-хранилище: {exc}")
        return accounts

    def get_all_accounts(self):
        return self.accounts

    def count_launched_accounts(self):
        return sum(1 for account in self.accounts if account.isCSValid())

    def get_account(self, login):
        login = login.lower()
        for account in self.accounts:
            if account.login.lower() == login:
                return account
        return None

    def add_account(self, login, password, shared_secret=None, steam_id=0, identity_secret=None):
        login = str(login or "").strip()
        password = str(password or "")
        if not login or not password:
            raise ValueError("Логин и пароль обязательны")
        if self.get_account(login):
            raise ValueError("Аккаунт с таким логином уже добавлен")

        try:
            steam_id = int(steam_id or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError("SteamID должен быть числом") from exc

        encrypted_accounts = secrets.get_accounts()
        encrypted_accounts[login.lower()] = {
            "password": password,
            "shared_secret": str(shared_secret or "").strip() or None,
            "identity_secret": str(identity_secret or "").strip() or None,
            "steam_id": steam_id,
        }
        secrets.set_accounts(encrypted_accounts)

        account = Account(login, password, shared_secret, steam_id, identity_secret)
        self.accounts.append(account)
        return account

    def reload_accounts_from_disk(self):
        self.accounts = self._load_accounts()
        self.selected_accounts = [
            account for account in self.selected_accounts
            if self.get_account(account.login) is not None
        ]
        return self.accounts


    def begin_start_selected_batch(self, count):
        with self._batch_lock:
            self._batch_start_remaining = max(0, int(count))
            if self._batch_start_remaining > 0:
                self._batch_done_event.clear()
            else:
                self._batch_done_event.set()

    def _consume_batch_item(self):
        with self._batch_lock:
            if self._batch_start_remaining > 0:
                self._batch_start_remaining -= 1
            if self._batch_start_remaining == 0:
                self._batch_done_event.set()
            return self._batch_start_remaining

    def is_batch_start_finished(self):
        return self._batch_done_event.is_set()

    def skip_batch_item(self):
        self._consume_batch_item()
    def add_to_start_queue(self, account):
        if account.isCSValid():
            print(f"{account.login} is already running skip")
            return False

        # Проверка: уже в очереди
        if account in list(self.accounts_start_queue.queue):
            print(f"{account.login} in start queue skip")
            return False
        account.setColor("yellow")
        # Если не в очереди и не запущен, добавляем
        self.accounts_start_queue.put(account)
        print(f"{account.login} added to start queue")
        return True
    def _accounts_start_process_queue(self):
        """Обрабатываем очередь аккаунтов по одному"""
        while True:
            account = self.accounts_start_queue.get()
            if account is None:
                break

            try:
                account.StartGame()  # запуск аккаунта

                # Ждём 5 секунд после открытия каждого аккаунта
                time.sleep(self.post_launch_delay_seconds)

                # После успешного запуска меняем цвет на зелёный
                account.setColor("green")
                account.MonitorCS2(interval=5)  # запускаем мониторинг CS2

                # Если запускаем пачку из нескольких аккаунтов — задержка 10 сек перед следующим
                remaining_batch = self._consume_batch_item()
                if remaining_batch > 0:
                    time.sleep(self.inter_account_delay_seconds)
            except Exception as e:
                print(f"Ошибка запуска {account.login}: {e}")
                account.KillSteamAndCS()
            finally:
                self.accounts_start_queue.task_done()