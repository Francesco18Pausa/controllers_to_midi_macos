import tkinter as tk
from tkinter import ttk
import mido
import time
import threading


class MidiPortSelector:
    def __init__(self, parent):
        self.parent = parent

        # Frame contenitore
        self.frame = ttk.Frame(parent)

        # -------------------------
        # LABEL
        # -------------------------
        label = ttk.Label(self.frame, text="Porta MIDI:")
        label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # -------------------------
        # DROPDOWN PORTE MIDI
        # -------------------------
        self.port_var = tk.StringVar()
        self.dropdown = ttk.Combobox(
            self.frame,
            textvariable=self.port_var,
            width=40,
            state="readonly"
        )
        self.dropdown.grid(row=0, column=1, padx=5, pady=5)

        # -------------------------
        # INPUT MANUALE INDEX
        # -------------------------
        ttk.Label(self.frame, text="Index:").grid(row=0, column=2, padx=5)

        self.index_var = tk.StringVar()
        self.index_entry = ttk.Entry(self.frame, textvariable=self.index_var, width=5)
        self.index_entry.grid(row=0, column=3, padx=5)

        # -------------------------
        # REFRESH BUTTON
        # -------------------------
        self.refresh_btn = ttk.Button(self.frame, text="↻", width=3, command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=4, padx=5)

        # Avvio refresh automatico
        self.refresh_ports()
        self.start_auto_refresh()

    # ---------------------------------------------------------
    # RILEVAZIONE PORTE MIDI
    # ---------------------------------------------------------
    def refresh_ports(self):
        try:
            ports = mido.get_output_names()
        except Exception:
            ports = []

        if not ports:
            ports = ["<Nessuna porta MIDI trovata>"]

        current = self.port_var.get()

        self.dropdown["values"] = ports

        # Mantieni selezione se possibile
        if current in ports:
            self.port_var.set(current)
        else:
            self.port_var.set(ports[0])

    # ---------------------------------------------------------
    # REFRESH AUTOMATICO OGNI 1s
    # ---------------------------------------------------------
    def start_auto_refresh(self):
        def loop():
            while True:
                time.sleep(1)
                self.refresh_ports()

        threading.Thread(target=loop, daemon=True).start()

    # ---------------------------------------------------------
    # OTTIENI PORTA SELEZIONATA
    # ---------------------------------------------------------
    def get_selected_port(self):
        """
        Ritorna l'index MIDI selezionato.
        Se l'utente inserisce un index manuale, ha priorità.
        """
        manual = self.index_var.get().strip()

        if manual.isdigit():
            return int(manual)

        # Se non c'è index manuale, usa l'indice del dropdown
        selected = self.port_var.get()

        try:
            ports = mido.get_output_names()
            return ports.index(selected)
        except Exception:
            return None
