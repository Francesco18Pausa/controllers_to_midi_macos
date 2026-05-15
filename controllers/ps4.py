import pygame
import time
import json
import os

from utils.scaling import scale_axis_segment, scale_trigger
from midi.output import MidiRouter


# ----------------------------------------------------
# MAPPATURA NOMI UMANI → INDICI PYGAME
# ----------------------------------------------------
BUTTON_NAMES = {
    0: "X",
    1: "Cerchio",
    2: "Quadrato",
    3: "Triangolo",
    4: "L1",
    5: "R1",
    6: "L2",
    7: "L3",
    8: "R3",
    9: "Share",
    10: "Options",
    11: "DPadUp",
    12: "DPadDown",
    13: "DPadLeft",
    14: "DPadRight",
}

AXIS_NAMES = {
    0: "l3x",
    1: "l3y",
    2: "r3x",
    3: "r3y",
    4: "l2",
    5: "r2"
}


class PS4Controller:
    """
    Controller PS4 dinamico basato su JSON.
    """

    def __init__(self, midi: MidiRouter, config_path="config/ps4_mapping.json"):
        self.midi = midi
        self.config_path = config_path
        self.modes = {}
        self.mode_names = []
        self.mode_index = 0

        self.last_json_mtime = 0
        self.load_json(force=True)

        # Stato
        self.current_note = None
        self.pressed = set()
        self.last_button_state = {}
        self.last_cc = {}

        # Joystick
        self.joy = None
        self.running = False

        # Trigger
        self.trigger_deadzone = 0.02

        # Rampa
        self.ramp_value = 64
        self.ramp_direction = 0


    # ----------------------------------------------------
    # JSON HOT RELOAD
    # ----------------------------------------------------
    def load_json(self, force=False):
        try:
            mtime = os.path.getmtime(self.config_path)
            if not force and mtime == self.last_json_mtime:
                return

            with open(self.config_path, "r") as f:
                self.modes = json.load(f)

            self.mode_names = list(self.modes.keys())
            self.last_json_mtime = mtime

            print("[PS4] Mapping aggiornato dal JSON", flush=True)

        except Exception as e:
            print("[PS4] Errore caricamento JSON:", e, flush=True)


    # ----------------------------------------------------
    # AVVIO
    # ----------------------------------------------------
    def start(self):
        print("[PS4] Controller connesso", flush=True)
        print(f"[PS4] Modalità: {self.mode_names[self.mode_index]}", flush=True)
        self.running = True

        import threading
        threading.Thread(target=self.loop, daemon=True).start()


    # ----------------------------------------------------
    # LOOP PRINCIPALE
    # ----------------------------------------------------
    def loop(self):
        while self.running:
            self.load_json()  # hot reload

            try:
                pygame.event.pump()

                if pygame.joystick.get_count() == 0:
                    if self.joy is not None:
                        print("[PS4] Joystick disconnesso", flush=True)
                    self.joy = None
                    time.sleep(0.1)
                    continue

                if self.joy is None:
                    self.joy = pygame.joystick.Joystick(0)
                    self.joy.init()
                    self.last_button_state = {i: False for i in range(self.joy.get_numbuttons())}
                    print("[PS4] Joystick inizializzato", flush=True)

                if not self.joy.get_init():
                    print("[PS4] Joystick perso, attendo riconnessione...", flush=True)
                    self.joy = None
                    time.sleep(0.1)
                    continue

                self.handle_buttons()
                self.handle_axes()

            except Exception as e:
                print("[PS4] Errore loop:", e, flush=True)

            time.sleep(0.01)


    # ----------------------------------------------------
    # GESTIONE PULSANTI
    # ----------------------------------------------------
    def handle_buttons(self):
        if self.joy is None:
            return

        for b in range(self.joy.get_numbuttons()):
            state = self.joy.get_button(b)
            prev = self.last_button_state.get(b, False)

            if state and not prev:
                self.handle_button_down(b)

            elif not state and prev:
                self.handle_button_up(b)

            self.last_button_state[b] = state


    def handle_button_down(self, b):
        name = BUTTON_NAMES.get(b)
        if not name:
            return

        mode = self.modes[self.mode_names[self.mode_index]]
        buttons = mode.get("buttons", {})

        # Cambio modalità
        if name == "R3":
            self.mode_index = (self.mode_index + 1) % len(self.mode_names)
            print(f"[PS4] Modalità: {self.mode_names[self.mode_index]}", flush=True)
            return

        if name == "L3":
            self.mode_index = (self.mode_index - 1) % len(self.mode_names)
            print(f"[PS4] Modalità: {self.mode_names[self.mode_index]}", flush=True)
            return

        if name not in buttons:
            return

        mapping = buttons[name]
        t = mapping["type"]

        if t == "note":
            self.midi.note_on(mapping["value"], 100, mapping["channel"])
            self.current_note = mapping["value"]

        elif t == "cc":
            self.midi.cc(mapping["value"], 127, mapping["channel"])

        elif t == "cc_fixed":
            self.midi.cc(mapping["value"], mapping["fixed"], mapping["channel"])

        elif t == "cc_ramp_up":
            self.ramp_direction = +1

        elif t == "cc_ramp_down":
            self.ramp_direction = -1


    def handle_button_up(self, b):
        name = BUTTON_NAMES.get(b)
        if not name:
            return

        mode = self.modes[self.mode_names[self.mode_index]]
        buttons = mode.get("buttons", {})

        if name not in buttons:
            return

        mapping = buttons[name]
        t = mapping["type"]

        if t == "note":
            self.midi.note_off(mapping["value"], mapping["channel"])

        elif t == "cc":
            self.midi.cc(mapping["value"], 0, mapping["channel"])

        elif t in ("cc_ramp_up", "cc_ramp_down"):
            self.ramp_direction = 0
            self.ramp_value = 64
            self.midi.cc(33, 64, mapping["channel"])


    # ----------------------------------------------------
    # GESTIONE ASSI
    # ----------------------------------------------------
    def handle_axes(self):
        if self.joy is None:
            return

        axes = [self.joy.get_axis(i) for i in range(self.joy.get_numaxes())]
        mode = self.modes[self.mode_names[self.mode_index]]
        axis_map = mode.get("axes", {})

        for idx, axis_name in AXIS_NAMES.items():
            if axis_name not in axis_map:
                continue

            val = axes[idx]

            if axis_name in ("l2", "r2"):
                if abs(val + 1.0) < self.trigger_deadzone:
                    pos_val = 0
                else:
                    pos_val = scale_trigger(val)
                neg_val = 0
            else:
                pos_val, neg_val = scale_axis_segment(val)

            mapping = axis_map[axis_name]

            if "pos" in mapping:
                m = mapping["pos"]
                self.send_cc_if_changed(m["cc"], pos_val, axis_name + "_pos", m["channel"])

            if "neg" in mapping:
                m = mapping["neg"]
                self.send_cc_if_changed(m["cc"], neg_val, axis_name + "_neg", m["channel"])


    # ----------------------------------------------------
    # ANTI-SPAM CC
    # ----------------------------------------------------
    def send_cc_if_changed(self, cc, value, key, channel):
        prev = self.last_cc.get(key)
        if prev is not None and abs(prev - value) < 2:
            return

        self.midi.cc(cc, int(value), channel)
        self.last_cc[key] = value
