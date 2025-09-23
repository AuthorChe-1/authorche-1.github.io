import sqlite3


class Database:
    def __init__(self, db_file='donations.db'):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Створює таблицю для донатів через Stars, якщо її не існує."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS star_donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                amount INTEGER NOT NULL,
                telegram_payment_charge_id TEXT UNIQUE NOT NULL
            )
        ''')
        self.conn.commit()

    def add_donation(self, user_id: int, username: str, amount: int, charge_id: str) -> int:
        """Додає донат в БД і повертає його унікальний ID."""
        self.cursor.execute(
            "INSERT INTO star_donations (user_id, username, amount, telegram_payment_charge_id) VALUES (?, ?, ?, ?)",
            (user_id, username, amount, charge_id)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all_donations(self) -> list:
        """Повертає список всіх донатів через Stars."""
        self.cursor.execute("SELECT * FROM star_donations ORDER BY id DESC")
        return self.cursor.fetchall()

    def get_donation_by_id(self, donation_id: int):
        """Знаходить конкретний донат за його ID."""
        self.cursor.execute("SELECT * FROM star_donations WHERE id = ?", (donation_id,))
        return self.cursor.fetchone()

    def delete_donation(self, donation_id: int) -> bool:
        """Видаляє донат з БД (використовується після повернення)."""
        self.cursor.execute("DELETE FROM star_donations WHERE id = ?", (donation_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0