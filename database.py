import sqlite3

class MailDB:
    def __init__(self):
        self.conn = sqlite3.connect("tempmail_data.db", check_same_thread=False)
        self._create_table()

    def _create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS active_mails (
            id TEXT PRIMARY KEY,
            address TEXT,
            password TEXT,
            token TEXT,
            time_left INTEGER,
            duration INTEGER
        )
        """
        self.conn.execute(query)
        self.conn.commit()

    def save_mail(self, instance):
        query = "REPLACE INTO active_mails VALUES (?, ?, ?, ?, ?, ?)"
        self.conn.execute(query, (instance.id, instance.address, instance.password, 
                                 instance.token, instance.time_left, instance.duration))
        self.conn.commit()

    def remove_mail(self, instance_id):
        self.conn.execute("DELETE FROM active_mails WHERE id = ?", (instance_id,))
        self.conn.commit()

    def get_all(self):
        return self.conn.execute("SELECT * FROM active_mails").fetchall()