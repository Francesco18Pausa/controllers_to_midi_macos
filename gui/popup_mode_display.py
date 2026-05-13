import tkinter as tk


class PopupModeDisplay:
    """
    Piccola finestra always-on-top che mostra la modalità corrente dei controller.
    Perfetta da tenere sopra Ableton durante le sessioni live.
    """

    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Modalità Controller")
        self.window.geometry("180x120")
        self.window.configure(bg="white")

        # Always on top
        self.window.attributes("-topmost", True)

        # Font Roboto (fallback automatico)
        try:
            font = ("Roboto", 28, "bold")
        except:
            font = ("Segoe UI", 28, "bold")

        # Label principale
        self.label = tk.Label(
            self.window,
            text="Modalità corrente: --",
            font=font,
            bg="white",
            fg="black"
        )
        self.label.pack(expand=True, fill="both")

        # Permetti ridimensionamento
        self.window.resizable(True, True)

        # Modalità corrente
        self.current_mode = "--"

    # ---------------------------------------------------------
    # AGGIORNA MODALITÀ
    # ---------------------------------------------------------
    def set_mode(self, mode_text: str):
        """
        Aggiorna il testo mostrato nel popup.
        Può essere chiamato da qualsiasi parte della GUI.
        """
        self.current_mode = mode_text
        self.label.config(text=mode_text)

    def update_mode(self, line):
        # line esempio: "[PS4] Modalità: FX"
        try:
            mode = line.split(":")[1].strip()
            self.mode_label.config(text=f"Modalità corrente: {mode}")
        except:
            pass


