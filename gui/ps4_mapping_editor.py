import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import copy


CONFIG_PATH = "config/ps4_mapping.json"

BUTTON_LIST = [
    "X", "Cerchio", "Quadrato", "Triangolo",
    "DPadUp", "DPadRight", "DPadDown", "DPadLeft",
    "L1", "R1", "L2", "R2", "L3", "R3",
    "Share", "Options"
]

AXIS_LIST = ["l3x", "l3y", "r3x", "r3y", "l2", "r2"]


# ------------------------------------------------------------
# FINESTRA EDITOR COMPLETA
# ------------------------------------------------------------
class PS4MappingEditor(tk.Toplevel):

    def __init__(self, master):
        super().__init__(master)
        self.title("PS4 Mapping Editor")
        self.geometry("650x500")
        self.resizable(False, False)

        self.original_data = self.load_json()
        self.data = copy.deepcopy(self.original_data)

        self.create_main_ui()


    # ------------------------------------------------------------
    # CARICAMENTO JSON
    # ------------------------------------------------------------
    def load_json(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile leggere il JSON:\n{e}")
            return {}


    # ------------------------------------------------------------
    # SALVATAGGIO JSON
    # ------------------------------------------------------------
    def save_json(self):
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(self.data, f, indent=4)
            messagebox.showinfo("Salvato", "Configurazione salvata con successo.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile salvare il JSON:\n{e}")


    # ------------------------------------------------------------
    # UI PRINCIPALE
    # ------------------------------------------------------------
    def create_main_ui(self):
        frame = tk.Frame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Modalità PS4", font=("Segoe UI", 14, "bold")).pack(pady=5)

        self.mode_frame = tk.Frame(frame)
        self.mode_frame.pack(fill="x", pady=10)

        self.refresh_mode_list()

        # Bottoni globali
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="New Mode", command=self.new_mode).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Save All", command=self.save_json).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Load", command=self.load_from_file).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Export", command=self.export_file).grid(row=0, column=3, padx=5)


    # ------------------------------------------------------------
    # RENDER LISTA MODALITÀ
    # ------------------------------------------------------------
    def refresh_mode_list(self):
        for w in self.mode_frame.winfo_children():
            w.destroy()

        mode_names = list(self.data.keys())

        for i, mode_name in enumerate(mode_names):
            row = tk.Frame(self.mode_frame)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=mode_name, width=20, anchor="w").pack(side="left")

            # Move Up
            ttk.Button(
                row, text="▲",
                command=lambda m=mode_name: self.move_mode_up(m)
            ).pack(side="left", padx=2)

            # Move Down
            ttk.Button(
                row, text="▼",
                command=lambda m=mode_name: self.move_mode_down(m)
            ).pack(side="left", padx=2)

            ttk.Button(row, text="Rename", command=lambda m=mode_name: self.rename_mode(m)).pack(side="left", padx=5)
            ttk.Button(row, text="Edit", command=lambda m=mode_name: self.edit_mode(m)).pack(side="left", padx=5)
            ttk.Button(row, text="Clone", command=lambda m=mode_name: self.clone_mode(m)).pack(side="left", padx=5)
            ttk.Button(row, text="Remove", command=lambda m=mode_name: self.remove_mode(m)).pack(side="left", padx=5)



    # ------------------------------------------------------------
    # OPERAZIONI SULLE MODALITÀ
    # ------------------------------------------------------------
    def rename_mode(self, mode):
        new_name = tk.simpledialog.askstring("Rename Mode", "Nuovo nome:", initialvalue=mode)
        if not new_name:
            return

        self.data[new_name] = self.data.pop(mode)
        self.refresh_mode_list()


    def clone_mode(self, mode):
        base = self.data[mode]
        new_name = mode + "_Copy"
        i = 1
        while new_name in self.data:
            new_name = f"{mode}_Copy{i}"
            i += 1

        self.data[new_name] = copy.deepcopy(base)
        self.refresh_mode_list()


    def remove_mode(self, mode):
        if messagebox.askyesno("Conferma", f"Eliminare la modalità '{mode}'?"):
            del self.data[mode]
            self.refresh_mode_list()


    def new_mode(self):
        name = tk.simpledialog.askstring("New Mode", "Nome nuova modalità:")
        if not name:
            return

        self.data[name] = {
            "note_channel": 1,
            "cc_channel": 1,
            "buttons": {},
            "axes": {}
        }
        self.refresh_mode_list()

    def move_mode_up(self, mode):
        keys = list(self.data.keys())
        idx = keys.index(mode)

        if idx == 0:
            return  # già in cima

        # swap
        keys[idx], keys[idx - 1] = keys[idx - 1], keys[idx]

        # ricostruisci il dict mantenendo l’ordine
        self.data = {k: self.data[k] for k in keys}

        self.refresh_mode_list()


    def move_mode_down(self, mode):
        keys = list(self.data.keys())
        idx = keys.index(mode)

        if idx == len(keys) - 1:
            return  # già in fondo

        # swap
        keys[idx], keys[idx + 1] = keys[idx + 1], keys[idx]

        # ricostruisci il dict mantenendo l’ordine
        self.data = {k: self.data[k] for k in keys}

        self.refresh_mode_list()



    # ------------------------------------------------------------
    # CARICA / ESPORTA
    # ------------------------------------------------------------
    def load_from_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return

        try:
            with open(path, "r") as f:
                self.data = json.load(f)
            self.refresh_mode_list()
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile caricare:\n{e}")


    def export_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return

        try:
            with open(path, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile esportare:\n{e}")


    # ------------------------------------------------------------
    # EDITOR DI UNA MODALITÀ
    # ------------------------------------------------------------
    def edit_mode(self, mode_name):
        EditWindow(self, mode_name, self.data)


# ------------------------------------------------------------
# FINESTRA EDIT DI UNA MODALITÀ
# ------------------------------------------------------------
class EditWindow(tk.Toplevel):

    def __init__(self, master, mode_name, data):
        super().__init__(master)
        self.title(f"Edit Mode: {mode_name}")
        self.geometry("700x500")
        self.resizable(False, False)

        self.master = master
        self.mode_name = mode_name
        self.data = data
        self.original = copy.deepcopy(data[mode_name])

        self.create_ui()


    def create_ui(self):
        tk.Label(self, text=f"Edit Mode: {self.mode_name}", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # Notebook: Buttons + Axes
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        self.button_frame = tk.Frame(nb)
        self.axis_frame = tk.Frame(nb)

        nb.add(self.button_frame, text="Buttons")
        nb.add(self.axis_frame, text="Axes")

        self.render_buttons()
        self.render_axes()

        # Bottom buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Save", command=self.save).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Reset", command=self.reset).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Discard", command=self.destroy).grid(row=0, column=2, padx=5)


    # ------------------------------------------------------------
    # BUTTON TABLE
    # ------------------------------------------------------------
    def render_buttons(self):
        for w in self.button_frame.winfo_children():
            w.destroy()

        tk.Label(self.button_frame, text="Comando", width=15).grid(row=0, column=0)
        tk.Label(self.button_frame, text="Tipo", width=10).grid(row=0, column=1)
        tk.Label(self.button_frame, text="Valore", width=10).grid(row=0, column=2)
        tk.Label(self.button_frame, text="Canale", width=10).grid(row=0, column=3)

        self.button_vars = {}

        buttons = self.data[self.mode_name]["buttons"]

        for i, btn in enumerate(buttons.keys(), start=1):
            mapping = buttons[btn]

            tk.Label(self.button_frame, text=btn).grid(row=i, column=0)

            type_var = tk.StringVar(value=mapping["type"])
            val_var = tk.StringVar(value=str(mapping["value"]))
            ch_var = tk.StringVar(value=str(mapping["channel"]))

            ttk.Combobox(self.button_frame, textvariable=type_var,
                         values=["note", "cc", "cc_fixed", "cc_ramp_up", "cc_ramp_down"],
                         width=10).grid(row=i, column=1)

            tk.Entry(self.button_frame, textvariable=val_var, width=10).grid(row=i, column=2)
            tk.Entry(self.button_frame, textvariable=ch_var, width=10).grid(row=i, column=3)

            self.button_vars[btn] = (type_var, val_var, ch_var)


    # ------------------------------------------------------------
    # AXIS TABLE
    # ------------------------------------------------------------
    def render_axes(self):
        for w in self.axis_frame.winfo_children():
            w.destroy()

        tk.Label(self.axis_frame, text="Asse", width=10).grid(row=0, column=0)
        tk.Label(self.axis_frame, text="Pos CC", width=10).grid(row=0, column=1)
        tk.Label(self.axis_frame, text="Pos Ch", width=10).grid(row=0, column=2)
        tk.Label(self.axis_frame, text="Neg CC", width=10).grid(row=0, column=3)
        tk.Label(self.axis_frame, text="Neg Ch", width=10).grid(row=0, column=4)

        self.axis_vars = {}

        axes = self.data[self.mode_name]["axes"]

        for i, axis in enumerate(axes.keys(), start=1):
            mapping = axes[axis]

            tk.Label(self.axis_frame, text=axis).grid(row=i, column=0)

            pos_cc = tk.StringVar(value=str(mapping.get("pos", {}).get("cc", "")))
            pos_ch = tk.StringVar(value=str(mapping.get("pos", {}).get("channel", "")))
            neg_cc = tk.StringVar(value=str(mapping.get("neg", {}).get("cc", "")))
            neg_ch = tk.StringVar(value=str(mapping.get("neg", {}).get("channel", "")))

            tk.Entry(self.axis_frame, textvariable=pos_cc, width=10).grid(row=i, column=1)
            tk.Entry(self.axis_frame, textvariable=pos_ch, width=10).grid(row=i, column=2)
            tk.Entry(self.axis_frame, textvariable=neg_cc, width=10).grid(row=i, column=3)
            tk.Entry(self.axis_frame, textvariable=neg_ch, width=10).grid(row=i, column=4)

            self.axis_vars[axis] = (pos_cc, pos_ch, neg_cc, neg_ch)


    # ------------------------------------------------------------
    # SAVE / RESET
    # ------------------------------------------------------------
    def save(self):
        # Buttons
        btns = self.data[self.mode_name]["buttons"]
        for btn, vars in self.button_vars.items():
            t, v, ch = vars
            btns[btn]["type"] = t.get()
            btns[btn]["value"] = int(v.get())
            btns[btn]["channel"] = int(ch.get())

        # Axes
        axes = self.data[self.mode_name]["axes"]
        for axis, vars in self.axis_vars.items():
            pos_cc, pos_ch, neg_cc, neg_ch = vars

            axes[axis] = {}

            if pos_cc.get():
                axes[axis]["pos"] = {
                    "cc": int(pos_cc.get()),
                    "channel": int(pos_ch.get())
                }

            if neg_cc.get():
                axes[axis]["neg"] = {
                    "cc": int(neg_cc.get()),
                    "channel": int(neg_ch.get())
                }

        self.master.save_json()
        self.destroy()


    def reset(self):
        self.data[self.mode_name] = copy.deepcopy(self.original)
        self.render_buttons()
        self.render_axes()
