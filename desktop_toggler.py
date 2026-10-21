import threading
import tkinter as tk
from tkinter import messagebox
import keyboard
import pystray
from PIL import Image, ImageDraw
import os
import socket
import sys
import urllib.request
import json
import subprocess

# --- UPDATE CONFIGURATION ---
CURRENT_VERSION = "1.2.0"
REPO = "hiexefrombloxd/Desktop-Switcher"
# ----------------------------

PORT = 58421  # Local port used to coordinate single tray instance

def check_single_instance():
    """Checks if an instance is already running. If so, signals it to open a new window and exits."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", PORT))
        client.sendall(b"OPEN_WINDOW")
        client.close()
        sys.exit(0)
    except (ConnectionRefusedError, socket.timeout, OSError):
        pass

def check_for_updates_background():
    """Checks GitHub in the background when the app starts."""
    url = f"https://api.github.com/repos/{REPO}/releases/latest"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Python-Updater'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            latest_version = data["tag_name"].lstrip("v")
            
            current_parts = [int(x) for x in CURRENT_VERSION.lstrip("v").split(".")]
            latest_parts = [int(x) for x in latest_version.split(".")]
            
            if latest_parts > current_parts:
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        download_url = asset["browser_download_url"]
                        if messagebox.askyesno("Update Available", f"A new version ({latest_version}) is available! Would you like to update now?"):
                            apply_update(download_url)
                        return
    except Exception:
        pass

def apply_update(download_url):
    temp_dir = os.environ['TEMP']
    new_exe_path = os.path.join(temp_dir, "app_new.exe")
    current_exe_path = sys.executable  
    
    try:
        urllib.request.urlretrieve(download_url, new_exe_path)
    except Exception:
        return

    bat_path = os.path.join(temp_dir, "update.bat")
    bat_content = f"""
@echo off
timeout /t 2 /nobreak > nul
move /y "{new_exe_path}" "{current_exe_path}"
start "" "{current_exe_path}"
del "%~f0"
"""
    
    with open(bat_path, "w") as f:
        f.write(bat_content)
        
    subprocess.Popen([bat_path], shell=True)
    os._exit(0)

class DesktopTogglerApp:
    def __init__(self, root, is_primary=True):
        self.root = root
        self.is_primary = is_primary
        self.root.title("Desktop Toggler")
        self.root.geometry("310x190")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)

        # Handle window close (X button) to minimize to tray instead of quitting
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.hotkey = "grave"
        self.hotkey_handle = None
        self.active = False
        self.going_right = True
        self.extra_windows = []

        # --- UI Elements ---
        self.lbl = tk.Label(root, text="Set your toggle hotkey:", font=("Arial", 11))
        self.lbl.pack(pady=10)

        frame = tk.Frame(root)
        frame.pack(pady=5)

        self.var = tk.StringVar(value=self.hotkey)
        self.entry = tk.Entry(frame, textvariable=self.var, font=("Arial", 11), justify="center", state="readonly", width=12)
        self.entry.pack(side=tk.LEFT, padx=5, ipady=3)

        self.rec_btn = tk.Button(frame, text="Change", font=("Arial", 9, "bold"), command=self.record_hotkey)
        self.rec_btn.pack(side=tk.LEFT, padx=2, ipady=3)

        self.btn = tk.Button(root, text="Start Toggler", font=("Arial", 10, "bold"), bg="#4CAF50", fg="white", command=self.toggle)
        self.btn.pack(pady=12, ipadx=15, ipady=3)

        # Setup System Tray Icon (Only for the primary instance)
        self.tray_icon = None
        if self.is_primary:
            self.setup_tray()
            self.start_socket_server()

        self.start_toggler()

    def create_image(self):
        """Generates a sleek, modern system tray icon internally via Pillow."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Background rounded card style (Dark Slate)
        draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill="#1E293B")
        
        # Left mini desktop window
        draw.rectangle([10, 18, 28, 42], fill="#38BDF8", outline="#E2E8F0", width=2)
        draw.rectangle([13, 21, 25, 25], fill="#1E293B") # titlebar
        
        # Right mini desktop window
        draw.rectangle([36, 18, 54, 42], fill="#38BDF8", outline="#E2E8F0", width=2)
        draw.rectangle([39, 21, 51, 25], fill="#1E293B") # titlebar
        
        # Connecting switch arrow indicator in the middle
        draw.polygon([(29, 26), (35, 30), (29, 34)], fill="#4ADE80")

        return img

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("Open", self.show_window, default=True),
            pystray.MenuItem("Quit", self.quit_app)
        )
        self.tray_icon = pystray.Icon("DesktopToggler", self.create_image(), "Desktop Toggler", menu)
        # Run tray in a background daemon thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def start_socket_server(self):
        """Listens for subsequent app launches to spawn new window copies."""
        def server_thread():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                server.bind(("127.0.0.1", PORT))
                server.listen(5)
                while True:
                    conn, addr = server.accept()
                    data = conn.recv(1024)
                    if data == b"OPEN_WINDOW":
                        self.root.after(0, self.spawn_new_window)
                    conn.close()
            except Exception as e:
                print(f"Socket server error: {e}")

        threading.Thread(target=server_thread, daemon=True).start()

    def spawn_new_window(self):
        """Spawns a new independent application window copy."""
        new_win = tk.Toplevel(self.root)
        app = DesktopTogglerApp(new_win, is_primary=False)
        self.extra_windows.append((new_win, app))

    def hide_to_tray(self):
        self.root.withdraw()

    def show_window(self, icon=None, item=None):
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        # Also deiconify any open extra window copies
        for win, app in self.extra_windows:
            try:
                win.deiconify()
                win.attributes("-topmost", True)
            except Exception:
                pass

    def quit_app(self, icon=None, item=None):
        """Completely kills all hooks, stops the tray, and terminates the Python process."""
        try:
            keyboard.unhook_all()
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        
        try:
            for win, app in self.extra_windows:
                try:
                    win.destroy()
                except Exception:
                    pass
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass

        os._exit(0)

    def toggle_desktop(self):
        try:
            keyboard.send("windows+ctrl+right" if self.going_right else "windows+ctrl+left")
            self.going_right = not self.going_right
        except Exception as e:
            print(f"Switch error: {e}")

    def record_hotkey(self):
        if self.active: 
            return
        self.rec_btn.config(state="disabled")
        self.btn.config(state="disabled")
        self.lbl.config(text="Press any key/hotkey...")

        def listen():
            try:
                hk = keyboard.read_hotkey(suppress=False)
                self.root.after(0, lambda: self.apply_hotkey(hk))
            except Exception as e:
                self.root.after(0, lambda: self.apply_hotkey(None, str(e)))

        threading.Thread(target=listen, daemon=True).start()

    def apply_hotkey(self, hk=None, err=None):
        self.rec_btn.config(state="normal")
        self.btn.config(state="normal")
        self.lbl.config(text="Set your toggle hotkey:")
        if err:
            return messagebox.showerror("Error", f"Failed: {err}")
        if hk:
            self.var.set(hk)
            self.start_toggler()

    def start_toggler(self):
        try:
            if self.hotkey_handle:
                keyboard.remove_hotkey(self.hotkey_handle)
            self.hotkey = self.var.get().strip()
            self.hotkey_handle = keyboard.add_hotkey(self.hotkey, self.toggle_desktop)
            self.active = True
            self.rec_btn.config(state="disabled")
            self.btn.config(text="Stop Toggler", bg="#f44336")
            self.lbl.config(text=f"Active! Press [{self.hotkey}] to switch.")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid hotkey:\n{e}")
            self.active = False
            self.rec_btn.config(state="normal")

    def stop_toggler(self):
        try:
            if self.hotkey_handle:
                keyboard.remove_hotkey(self.hotkey_handle)
                self.hotkey_handle = None
        except Exception:
            pass
        self.active = False
        self.rec_btn.config(state="normal")
        self.btn.config(text="Start Toggler", bg="#4CAF50")
        self.lbl.config(text="Set your toggle hotkey:")

    def toggle(self):
        self.stop_toggler() if self.active else self.start_toggler()

if __name__ == "__main__":
    check_single_instance()
    # Start the update checker thread right when the application launches
    threading.Thread(target=check_for_updates_background, daemon=True).start()
    root = tk.Tk()
    DesktopTogglerApp(root, is_primary=True)
    root.mainloop()
