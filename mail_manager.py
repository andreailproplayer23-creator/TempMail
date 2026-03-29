import threading
import time
import requests

class TempMailInstance:
    def __init__(self, duration_minutes, on_expire_callback):
        self.address = ""
        self.token = ""
        self.messages = []
        self.time_left = duration_minutes * 60
        self.is_active = True
        self.on_expire = on_expire_callback # Funzione da chiamare quando scade
        
        # Avviamo il thread per il controllo ogni secondo e il timer
        threading.Thread(target=self._run_lifecycle, daemon=True).start()

    def _run_lifecycle(self):
        # 1. Qui chiameremo l'API per creare la mail
        self.address = "esempio@mail.tm" 
        
        while self.is_active and self.time_left > 0:
            time.sleep(1)
            self.time_left -= 1
            
            # 2. Controllo nuovi messaggi ogni secondo
            self._check_messages()
            
            if self.time_left <= 0:
                self.stop()

    def _check_messages(self):
        # Logica per interrogare l'API ogni secondo
        pass

    def stop(self):
        self.is_active = False
        self.on_expire(self) # Avvisa l'interfaccia di chiudere la scheda