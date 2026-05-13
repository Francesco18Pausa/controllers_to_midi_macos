import tkinter as tk
from tkinter import ttk
import pygame


class ControllerStatusPanel:
    """
    Pannello che mostra lo stato dei controller:
    - PS3
    - PS4
    - Wii

    Aggiornamento automatico tramite:
    - refresh_status() → rilevamento diretto via pygame + HID
    - update_from_log(line) → aggiornamento basato sul log di main.py
    """

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)

        # Stato interno
        self.status = {
            "PS3": False,
            "PS4": False,
            "Wii": False
        }

        # -------------------------
        # LABEL TITOLO
        # -------------------------
        title = ttk.Label(self.frame, text="Stato Controller", font=("Roboto", 12, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=5)

        # -------------------------
        # LABEL CONTROLLER
        # -------------------------
        self.ps3_label = ttk.Label(self.frame, text="PS3: ❌", foreground="red")
        self.ps3_label.grid(row=1, column=0, sticky="w", padx=10, pady=3)

        self.ps4_label = ttk.Label(self.frame, text="PS4: ❌", foreground="red")
        self.ps4_label.grid(row=2, column=0, sticky="w", padx=10, pady=3)

        self.wii_label = ttk.Label(self.frame, text="Wii: ❌", foreground="red")
        self.wii_label.grid(row=3, column=0, sticky="w", padx=10, pady=3)

        # Inizializza pygame per rilevamento controller
        pygame.init()
        pygame.joystick.init()

    # ---------------------------------------------------------
    # AGGIORNAMENTO DA LOG (main.py)
    # ---------------------------------------------------------
    def update_from_log(self, line: str):
        line = line.strip()

        if "PS3 attivato" in line:
            self.set_status("PS3", True)

        if "PS4 attivato" in line:
            self.set_status("PS4", True)

        if "Wii Controller attivo" in line:
            self.set_status("Wii", True)

        if "non avviato" in line:
            if "PS3" in line:
                self.set_status("PS3", False)
            if "PS4" in line:
                self.set_status("PS4", False)
            if "Wii" in line:
                self.set_status("Wii", False)

    # ---------------------------------------------------------
    # RILEVAMENTO DIRETTO (pygame + HID)
    # ---------------------------------------------------------
    def refresh_status(self):
        """
        Rileva i controller connessi tramite pygame.
        Questo permette di aggiornare lo stato anche PRIMA
        dell'avvio dello script principale.
        """

        pygame.joystick.quit()
        pygame.joystick.init()

        names = []
        for i in range(pygame.joystick.get_count()):
            j = pygame.joystick.Joystick(i)
            j.init()
            names.append(j.get_name())

        # PS3
        ps3_connected = any("PLAYSTATION" in n or "PS3" in n for n in names)
        self.set_status("PS3", ps3_connected)

        # PS4
        ps4_connected = any(
            "Wireless Controller" in n or
            "DualShock" in n or
            "PS4 Controller" in n
            for n in names
        )
        self.set_status("PS4", ps4_connected)

        # Wii (solo HID, WiinUPro deve essere attivo)
        import hid
        wii_connected = False
        for d in hid.enumerate():
            if d["vendor_id"] == 0x057e and d["product_id"] == 0x0306:
                wii_connected = True
                break

        self.set_status("Wii", wii_connected)

    # ---------------------------------------------------------
    # AGGIORNA LABEL
    # ---------------------------------------------------------
    def set_status(self, controller, value: bool):
        if self.status[controller] == value:
            return  # nessun cambiamento

        self.status[controller] = value

        label = {
            "PS3": self.ps3_label,
            "PS4": self.ps4_label,
            "Wii": self.wii_label
        }[controller]

        if value:
            label.config(text=f"{controller}: ✔️", foreground="green")
        else:
            label.config(text=f"{controller}: ❌", foreground="red")
