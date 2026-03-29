import threading
import time
import requests
import uuid
import webbrowser
import os
import sqlite3
from win10toast import ToastNotifier

class TempMailInstance:
    API_URL = "https://api.mail.tm"

    def __init__(self, duration_minutes, on_start_callback, on_ready_callback, on_update_callback, on_expire_callback, existing_data=None):
        self.id = str(uuid.uuid4())[:8]
        self.is_active = True
        self.is_ready = False
        self.messages = []
        self.notifier = ToastNotifier()
        
        if existing_data:
            self.address = existing_data['address']
            self.password = existing_data['password']
            self.token = existing_data['token']
            self.time_left = existing_data['time_left']
            self.is_ready = True
        else:
            self.address = "In generazione..."
            self.password = str(uuid.uuid4())
            self.token = ""
            self.time_left = duration_minutes * 60

        self.on_start = on_start_callback
        self.on_ready = on_ready_callback
        self.on_update = on_update_callback 
        self.on_expire = on_expire_callback
        
        self.on_start(self)
        threading.Thread(target=self._timer_logic, daemon=True).start()
        threading.Thread(target=self._network_logic, daemon=True).start()

    def _save_to_db(self):
        try:
            conn = sqlite3.connect("session.db")
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS sessions 
                              (address TEXT PRIMARY KEY, password TEXT, token TEXT, expiry REAL)''')
            expiry_time = time.time() + self.time_left
            cursor.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?)", 
                           (self.address, self.password, self.token, expiry_time))
            conn.commit()
            conn.close()
        except: pass

    def _timer_logic(self):
        while self.is_active and self.time_left > 0:
            if self.is_ready:
                self.time_left -= 1
            self.on_update(self) 
            time.sleep(1)
        if self.time_left <= 0:
            self.stop()

    def _network_logic(self):
        try:
            if not self.token:
                dom_res = requests.get(f"{self.API_URL}/domains", timeout=5).json()
                domain = dom_res['hydra:member'][0]['domain']
                temp_addr = f"user_{str(uuid.uuid4())[:6]}@{domain}"
                requests.post(f"{self.API_URL}/accounts", json={"address": temp_addr, "password": self.password}, timeout=5)
                token_res = requests.post(f"{self.API_URL}/token", json={"address": temp_addr, "password": self.password}, timeout=5).json()
                self.token = token_res['token']
                self.address = temp_addr
                self.is_ready = True
                self._save_to_db()
                self.on_ready(self)

            headers = {"Authorization": f"Bearer {self.token}"}
            while self.is_active:
                try:
                    m_res = requests.get(f"{self.API_URL}/messages", headers=headers, timeout=3).json()
                    new_msgs = m_res.get('hydra:member', [])
                    if len(new_msgs) > len(self.messages):
                        latest = new_msgs[0]
                        self.notifier.show_toast("Nuova Email!", f"Da: {latest['from']['address']}\nOggetto: {latest['subject']}", duration=5)
                        self.messages = new_msgs
                except: pass
                time.sleep(2) 
        except: self.stop()

    def open_message_in_browser(self, msg_id):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            m_data = requests.get(f"{self.API_URL}/messages/{msg_id}", headers=headers).json()
            html = m_data.get('html', [m_data.get('intro', 'Vuoto')])[0]
            path = os.path.abspath(f"mail_{msg_id}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"<div style='font-family:sans-serif;padding:20px;'>{html}</div>")
            webbrowser.open(f"file://{path}")
        except: pass

    def stop(self):
        if not self.is_active: return
        self.is_active = False
        try:
            conn = sqlite3.connect("session.db")
            conn.execute("DELETE FROM sessions WHERE address = ?", (self.address,))
            conn.commit()
            conn.close()
        except: pass
        self.on_expire(self)