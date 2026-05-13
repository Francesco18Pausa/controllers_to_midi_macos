import subprocess
import threading
import time
import sys
import tkinter as tk
from tkinter import ttk
from midi.output import MidiRouter


# ----------------------------------------------------
# POPUP MODALITÀ (PS4 + WII)
# ----------------------------------------------------
class ModePopup(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)

        self.title("Modalità Controller")
        self.geometry("260x120")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(bg="black")

        # PS4
        self.ps4_frame = tk.Frame(self, bg="black", width=120, height=100)
        self.ps4_frame.grid(row=0, column=0, padx=5, pady=5)

        tk.Label(self.ps4_frame, text="PS4", fg="white", bg="black",
                 font=("Segoe UI", 12, "bold")).pack()

        self.ps4_label = tk.Label(
            self.ps4_frame, text="--", fg="#00aaff", bg="black",
            font=("Segoe UI", 36, "bold")
        )
        self.ps4_label.pack()

        # WII
        self.wii_frame = tk.Frame(self, bg="white", width=120, height=100)
        self.wii_frame.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.wii_frame, text="WII", fg="black", bg="white",
                 font=("Segoe UI", 12, "bold")).pack()

        self.wii_label = tk.Label(
            self.wii_frame, text="--", fg="#00aaff", bg="white",
            font=("Segoe UI", 36, "bold")
        )
        self.wii_label.pack()

    def update_ps4(self, mode):
        self.ps4_label.config(text=str(mode))

    def update_wii(self, mode):
        self.wii_label.config(text=str(mode))


# ----------------------------------------------------
# GUI PRINCIPALE
# ----------------------------------------------------
class LauncherGUI:

    def __init__(self, root):
        self.root = root
        self.process = None
        self.popup = None

        root.title("Controller to Ableton")

        # LOG
        self.text = tk.Text(root, height=20, width=90, font=("Consolas", 10))
        self.text.pack(padx=10, pady=10)

        # ----------------------------------------------------
        # MENU MIDI
        # ----------------------------------------------------
        ports = MidiRouter.list_ports()
        self.selected_port = tk.StringVar(value=ports[0] if ports else "")

        port_frame = tk.Frame(root)
        port_frame.pack(pady=5,)

        tk.Label(port_frame, text="Porta MIDI:", font=("Segoe UI", 10)).pack(side="left",)
        self.port_menu = ttk.OptionMenu(port_frame, self.selected_port, self.selected_port.get(), *ports)
        self.port_menu.pack(side="left", padx=10)

        # ----------------------------------------------------
        # LISTA CONTROLLER
        # ----------------------------------------------------
        self.controller_list = tk.Label(
            root,
            text="Controller: nessuno",
            font=("Segoe UI", 10),
            anchor="w",
            width=50
        )

        self.controller_list.pack(padx=10, pady=5, anchor="w")

        # ----------------------------------------------------
        # BOTTONI
        # ----------------------------------------------------
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Avvia", command=self.start_script)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.stop_script, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.popup_btn = ttk.Button(btn_frame, text="Popup Display", command=self.toggle_popup)
        self.popup_btn.grid(row=0, column=2, padx=5)

    # ----------------------------------------------------
    # LOG
    # ----------------------------------------------------
    def append_log(self, msg):
        self.text.insert(tk.END, msg)
        self.text.see(tk.END)

    # ----------------------------------------------------
    # POPUP
    # ----------------------------------------------------
    def toggle_popup(self):
        if self.popup is None or not self.popup.winfo_exists():
            self.popup = ModePopup(self.root)
        else:
            self.popup.destroy()
            self.popup = None

    # ----------------------------------------------------
    # AVVIO PROCESSO
    # ----------------------------------------------------
    def start_script(self):
        if self.process:
            return

        self.append_log("Avvio controller...\n")

        self.process = subprocess.Popen(
            [sys.executable, "-u", "main.py", self.selected_port.get()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        threading.Thread(target=self.read_stdout, daemon=True).start()
        threading.Thread(target=self.read_stderr, daemon=True).start()
        threading.Thread(target=self.monitor_process, daemon=True).start()

    # ----------------------------------------------------
    # LETTURA STDOUT
    # ----------------------------------------------------
    def read_stdout(self):
        for line in self.process.stdout:
            self.append_log(line)

            # Modalità PS4
            if "[PS4] Modalità:" in line and self.popup and self.popup.winfo_exists():
                mode = line.split(":")[1].strip()
                self.popup.update_ps4(mode)

            # Modalità WII
            if "[WII] Modalità:" in line and self.popup and self.popup.winfo_exists():
                mode = line.split(":")[1].strip()
                self.popup.update_wii(mode)


            # Controller connessi/disconnessi
            if "attivato" in line or "disconnesso" in line:
                self.update_controller_list(line.strip())

    # ----------------------------------------------------
    # LISTA CONTROLLER
    # ----------------------------------------------------
    def update_controller_list(self, line):
        current = self.controller_list.cget("text").replace("Controller: ", "")
        controllers = set(c.strip() for c in current.split(",") if c.strip() and c.strip() != "nessuno")

        if "attivato" in line:
            name = line.split()[0]
            controllers.add(name)

        if "disconnesso" in line:
            name = line.split()[0]
            controllers.discard(name)

        if controllers:
            self.controller_list.config(text="Controller: " + ", ".join(sorted(controllers)))
        else:
            self.controller_list.config(text="Controller: nessuno")


    # ----------------------------------------------------
    # LETTURA STDERR
    # ----------------------------------------------------
    def read_stderr(self):
        for line in self.process.stderr:
            self.append_log("ERRORE: " + line)

    # ----------------------------------------------------
    # MONITOR PROCESSO
    # ----------------------------------------------------
    def monitor_process(self):
        while True:
            if self.process is None:
                return

            if self.process.poll() is not None:
                self.append_log("Processo terminato\n")
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                self.process = None
                return

            time.sleep(0.2)

    # ----------------------------------------------------
    # STOP PROCESSO
    # ----------------------------------------------------
    def stop_script(self):
        if self.process:
            self.append_log("Terminazione richiesta\n")
            self.process.terminate()
            self.process = None
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
