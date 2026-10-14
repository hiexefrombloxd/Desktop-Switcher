import time
import tkinter as tk
from tkinter import messagebox
import keyboard

class DesktopTogglerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Desktop Toggler")
        self.root.geometry("320x180")
        self.root.attributes("-topmost", True)  # Keep panel visible
        self.root.resizable(False, False)

        self.current_hotkey = "grave"
        self.is_registered = False
        self.going_right = True  # Tracks direction to flip back and forth

        # --- UI Elements ---
        self.label = tk.Label(root, text="Set your toggle hotkey:", font=("Arial", 11))
        self.label.pack(pady=10)

        self.entry_var = tk.StringVar(value=self.current_hotkey)
        self.entry = tk.Entry(root, textvariable=self.entry_var, font=("Arial", 11), justify="center")
        self.entry.pack(pady=5, ipadx=10, ipady=3)

        self.btn = tk.Button(root, text="Start Toggler", font=("Arial", 10, "bold"), bg="#4CAF50", fg="white", command=self.toggle_active)
        self.btn.pack(pady=12, ipadx=15, ipady=3)

        # Auto-start with default hotkey
        self.start_hotkey()

    def trigger_switch(self):
        """Alternates between moving right and moving left to flip back and forth."""
        try:
            if self.going_right:
                keyboard.send("windows+ctrl+right")
            else:
                keyboard.send("windows+ctrl+left")
            
            # Flip direction for the next press
            self.going_right = not self.going_right
        except Exception as e:
            print(f"Error switching desktop: {e}")

    def start_hotkey(self):
        hotkey_str = self.entry_var.get().strip()
        if not hotkey_str:
            messagebox.showerror("Error", "Hotkey cannot be empty!")
            return

        try:
            if self.is_registered:
                keyboard.unhook_all_hotkeys()

            keyboard.add_hotkey(hotkey_str, self.trigger_switch)
            self.current_hotkey = hotkey_str
            self.is_registered = True
            
            self.entry.config(state="disabled")
            self.btn.config(text="Stop Toggler", bg="#f44336")
            self.label.config(text=f"Active! Press [{hotkey_str}] to switch.")
        except Exception as e:
            messagebox.showerror("Hotkey Error", f"Could not register hotkey:\n{e}")
            self.is_registered = False

    def stop_hotkey(self):
        keyboard.unhook_all_hotkeys()
        self.is_registered = False
        self.entry.config(state="normal")
        self.btn.config(text="Start Toggler", bg="#4CAF50")
        self.label.config(text="Set your toggle hotkey:")

    def toggle_active(self):
        if not self.is_registered:
            self.start_hotkey()
        else:
            self.stop_hotkey()

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopTogglerApp(root)
    root.mainloop()