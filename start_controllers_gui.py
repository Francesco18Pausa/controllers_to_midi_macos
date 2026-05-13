import subprocess
import sys
import threading
import time
import tkinter as tk
from gui.launcher_gui import LauncherGUI

# Percorso loopMIDI
LOOPMIDI_PATH = r"C:\Program Files (x86)\Tobias Erichsen\loopMIDI\loopMIDI.exe"


# ----------------------------------------------------
# AVVIO loopMIDI
# ----------------------------------------------------
def start_loopmidi():
    try:
        subprocess.Popen(
            [LOOPMIDI_PATH],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("loopMIDI avviato")
    except Exception as e:
        print(f"Errore avvio loopMIDI: {e}")


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------
def main():
    # Avvio loopMIDI in background
    threading.Thread(target=start_loopmidi, daemon=True).start()

    # Attesa per permettere a loopMIDI di creare la porta
    time.sleep(3)

    # Avvio GUI principale
    root = tk.Tk()
    app = LauncherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
