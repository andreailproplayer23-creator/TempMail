import customtkinter as ctk
from mail_engine import TempMailInstance
import tkinter.messagebox as messagebox
import pyperclip
import sqlite3
import time

ctk.set_appearance_mode("dark")

# --- DIZIONARIO TRADUZIONI ---
LANGS = {
    "Italiano": {
        "title": "TempMail PRO - Multi-Lang",
        "expiry": "Scadenza (Minuti):",
        "new_btn": "+ NUOVA EMAIL",
        "manage": "Gestione Email Attive:",
        "delete_btn": "🗑️ ELIMINA SELEZIONATA",
        "no_mail": "Nessuna email",
        "limit_msg": "Massimo 10 email attive.",
        "limit_title": "Limite",
        "gen": "Generazione...",
        "copy": "📋 Copia",
        "msg_title": "Messaggi Ricevuti"
    },
    "English": {
        "title": "TempMail PRO - Multi-Lang",
        "expiry": "Expiry (Minutes):",
        "new_btn": "+ NEW EMAIL",
        "manage": "Manage Active Emails:",
        "delete_btn": "🗑️ DELETE SELECTED",
        "no_mail": "No emails",
        "limit_msg": "Maximum 10 active emails.",
        "limit_title": "Limit",
        "gen": "Generating...",
        "copy": "📋 Copy",
        "msg_title": "Received Messages"
    },
    "Español": {
        "title": "TempMail PRO - Multi-Lang",
        "expiry": "Expiración (Minutos):",
        "new_btn": "+ NUEVO CORREO",
        "manage": "Gestionar correos activos:",
        "delete_btn": "🗑️ ELIMINAR SELECCIONADO",
        "no_mail": "Sin correos",
        "limit_msg": "Máximo 10 correos activos.",
        "limit_title": "Límite",
        "gen": "Generando...",
        "copy": "📋 Copiar",
        "msg_title": "Mensajes Recibidos"
    },
    "Français": {
        "title": "TempMail PRO - Multi-Lang",
        "expiry": "Expiration (Minutes):",
        "new_btn": "+ NOUVEL E-MAIL",
        "manage": "Gérer les e-mails actifs:",
        "delete_btn": "🗑️ SUPPRIMER LA SÉLECTION",
        "no_mail": "Aucun e-mail",
        "limit_msg": "Maximum 10 e-mails actifs.",
        "limit_title": "Limite",
        "gen": "Génération...",
        "copy": "📋 Copier",
        "msg_title": "Messages Reçus"
    }
}

class TempMailApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.current_lang = "Italiano"
        self.title(LANGS[self.current_lang]["title"])
        self.geometry("1100x750")
        self.instances = {} 
        self.setup_ui()
        self.after(500, self.restore_sessions_silent)

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=240)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # --- SELETTORE LINGUA ---
        ctk.CTkLabel(self.sidebar, text="🌐 Language:").pack(pady=(10,0))
        self.lang_menu = ctk.CTkOptionMenu(self.sidebar, values=list(LANGS.keys()), command=self.change_language)
        self.lang_menu.set("Italiano")
        self.lang_menu.pack(pady=10, padx=20)

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#3d3d3d").pack(fill="x", padx=10, pady=10)

        # --- UI TRADUCIBILE ---
        self.lbl_expiry = ctk.CTkLabel(self.sidebar, text=LANGS[self.current_lang]["expiry"])
        self.lbl_expiry.pack(pady=(10,0))
        
        self.dur_select = ctk.CTkOptionMenu(self.sidebar, values=["1", "5", "10", "30", "60", "120"])
        self.dur_select.set("10")
        self.dur_select.pack(pady=10)

        self.btn_go = ctk.CTkButton(self.sidebar, text=LANGS[self.current_lang]["new_btn"], command=self.generate_one, 
                                   fg_color="#2fa572", hover_color="#106a43", font=("Arial", 16, "bold"), height=45)
        self.btn_go.pack(pady=20, padx=20, fill="x")

        ctk.CTkFrame(self.sidebar, height=2, fg_color="#3d3d3d").pack(fill="x", padx=10, pady=20)

        self.lbl_manage = ctk.CTkLabel(self.sidebar, text=LANGS[self.current_lang]["manage"], font=("Arial", 13, "bold"))
        self.lbl_manage.pack()
        
        self.delete_menu = ctk.CTkComboBox(self.sidebar, values=[LANGS[self.current_lang]["no_mail"]])
        self.delete_menu.pack(pady=10, padx=20, fill="x")

        self.btn_delete = ctk.CTkButton(self.sidebar, text=LANGS[self.current_lang]["delete_btn"], command=self.delete_selected_mail,
                                       fg_color="#942a2a", hover_color="#6e1f1f")
        self.btn_delete.pack(pady=5, padx=20, fill="x")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

    def change_language(self, new_lang):
        self.current_lang = new_lang
        self.title(LANGS[new_lang]["title"])
        # Aggiorna i testi fissi
        self.lbl_expiry.configure(text=LANGS[new_lang]["expiry"])
        self.btn_go.configure(text=LANGS[new_lang]["new_btn"])
        self.lbl_manage.configure(text=LANGS[new_lang]["manage"])
        self.btn_delete.configure(text=LANGS[new_lang]["delete_btn"])
        self.update_delete_menu()

    def update_delete_menu(self):
        active_addresses = [info["actual_obj"].address for info in self.instances.values() if info["actual_obj"].is_ready]
        if not active_addresses:
            self.delete_menu.configure(values=[LANGS[self.current_lang]["no_mail"]])
            self.delete_menu.set(LANGS[self.current_lang]["no_mail"])
        else:
            self.delete_menu.configure(values=active_addresses)
            if self.delete_menu.get() not in active_addresses and self.delete_menu.get() != LANGS[self.current_lang]["no_mail"]:
                self.delete_menu.set(active_addresses[0])

    def delete_selected_mail(self):
        selected_addr = self.delete_menu.get()
        if selected_addr == LANGS[self.current_lang]["no_mail"]: return
        for info in list(self.instances.values()):
            if info["actual_obj"].address == selected_addr:
                info["actual_obj"].stop()
                break

    def generate_one(self):
        if len(self.instances) >= 10:
            messagebox.showwarning(LANGS[self.current_lang]["limit_title"], LANGS[self.current_lang]["limit_msg"])
            return
        duration = int(self.dur_select.get())
        TempMailInstance(duration, self.add_empty_tab, self.fill_tab_data, self.update_ui, self.remove_mail)

    def restore_sessions_silent(self):
        try:
            conn = sqlite3.connect("session.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions")
            rows = cursor.fetchall()
            conn.close()
            for row in rows:
                addr, pwd, token, expiry = row
                time_left = expiry - time.time()
                if time_left > 0 and len(self.instances) < 10:
                    data = {'address': addr, 'password': pwd, 'token': token, 'time_left': time_left}
                    TempMailInstance(0, self.add_empty_tab, self.fill_tab_data, self.update_ui, self.remove_mail, existing_data=data)
        except: pass

    def add_empty_tab(self, instance):
        self.after(0, lambda: self._ui_create_slot(instance))

    def _ui_create_slot(self, instance):
        slot_id = f"Slot_{instance.id}"
        self.tabview.add(slot_id)
        frame = self.tabview.tab(slot_id)
        header = ctk.CTkFrame(frame)
        header.pack(fill="x", pady=10)
        
        addr_text = instance.address if instance.is_ready else LANGS[self.current_lang]["gen"]
        addr_lbl = ctk.CTkLabel(header, text=addr_text, font=("Arial", 14))
        addr_lbl.pack(side="left", padx=15)

        copy_btn = ctk.CTkButton(header, text=LANGS[self.current_lang]["copy"], width=60, height=25, 
                                 command=lambda: pyperclip.copy(instance.address),
                                 state="normal" if instance.is_ready else "disabled")
        copy_btn.pack(side="left", padx=10)

        timer_lbl = ctk.CTkLabel(header, text="--:--", font=("Arial", 15, "bold"), text_color="orange")
        timer_lbl.pack(side="right", padx=15)

        msg_area = ctk.CTkScrollableFrame(frame, label_text=LANGS[self.current_lang]["msg_title"])
        msg_area.pack(fill="both", expand=True, padx=10, pady=10)

        self.instances[instance.id] = {
            "tab_id": slot_id, "addr_label": addr_lbl, "copy_button": copy_btn,
            "timer_label": timer_lbl, "msg_area": msg_area, "msg_count": 0, "actual_obj": instance 
        }
        self.update_delete_menu()

    def fill_tab_data(self, instance):
        if instance.id in self.instances:
            data = self.instances[instance.id]
            self.after(0, lambda: [
                data["addr_label"].configure(text=instance.address, font=("Arial", 14, "bold")),
                data["copy_button"].configure(state="normal", fg_color="#1f538d"),
                self.update_delete_menu()
            ])

    def update_ui(self, instance):
        if instance.id in self.instances:
            data = self.instances[instance.id]
            m, s = divmod(int(max(0, instance.time_left)), 60)
            display_time = f"⏳ {m:02d}:{s:02d}" if instance.is_ready else "--:--"
            self.after(0, lambda: data["timer_label"].configure(text=display_time))
            if len(instance.messages) > data["msg_count"]:
                self.after(0, lambda: self._refresh_messages(instance))

    def _refresh_messages(self, instance):
        data = self.instances[instance.id]
        data["msg_count"] = len(instance.messages)
        for w in data["msg_area"].winfo_children(): w.destroy()
        for m in instance.messages:
            btn = ctk.CTkButton(data["msg_area"], text=f"📩 {m['from']['address']} | {m['subject']}", 
                               anchor="w", command=lambda id=m['id']: instance.open_message_in_browser(id))
            btn.pack(fill="x", pady=2, padx=5)

    def remove_mail(self, instance):
        if instance.id in self.instances:
            tab_id = self.instances[instance.id]["tab_id"]
            self.after(0, lambda: [self._safe_delete(tab_id, instance.id), self.update_delete_menu()])

    def _safe_delete(self, tab_id, instance_id):
        try:
            if tab_id in self.tabview._tab_dict:
                self.tabview.delete(tab_id)
            if instance_id in self.instances: del self.instances[instance_id]
        except: pass

if __name__ == "__main__":
    app = TempMailApp()
    app.mainloop()