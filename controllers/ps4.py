import pygame
import time

from utils.scaling import scale_axis_segment, scale_trigger
from midi.output import MidiRouter
from mappings.ps4_modes import PS4_MODES


class PS4Controller:
    """
    Modalità:
    - Note
    - Accordi
    - FX (CC32, CC33, assi 22–31, D-Pad = note)
    """

    def __init__(self, midi: MidiRouter, modes=PS4_MODES):
        self.midi = midi
        self.modes = modes
        self.mode = 0

        # Stato note
        self.current_note = None
        self.pressed = set()
        self.last_button_state = {}

        # Anti-spam CC
        self.last_cc = {}

        # Pitch (solo modalità Note)
        self.pitch_value = 0
        self.cc_pitch = 11

        # Pulsanti speciali
        self.button_L1 = 9
        self.button_R1 = 10
        self.button_L3 = 7
        self.button_R3 = 8

        # Deadzone trigger
        self.trigger_deadzone = 0.02

        # Rampa CC33
        self.ramp_value = 64
        self.ramp_direction = 0

        # Mappatura note
        self.button_to_notes = {
            0: 36,  # X
            1: 37,  # Cerchio
            2: 38,  # Quadrato
            3: 39,  # Triangolo
            11: 40, # D-Pad UP
            14: 41, # D-Pad RIGHT
            12: 42, # D-Pad DOWN
            13: 43, # D-Pad LEFT
        }

        # Joystick gestito in modo sicuro
        self.joy = None
        self.running = False


    # -------------------------
    # AVVIO
    # -------------------------
    def start(self):
        print("[PS4] Controller connesso", flush=True)
        print(f"[PS4] Modalità: {self.modes[self.mode]['name']}", flush=True)
        self.running = True
        import threading
        threading.Thread(target=self.loop, daemon=True).start()



    def loop(self):
        while self.running:
            try:
                pygame.event.pump()

                # Se non c'è joystick → aspetta che torni
                if pygame.joystick.get_count() == 0:
                    if self.joy is not None:
                        print("[PS4] Joystick disconnesso", flush=True)
                    self.joy = None
                    time.sleep(0.1)
                    continue

                # Se non abbiamo ancora un joystick → inizializza UNA VOLTA
                if self.joy is None:
                    self.joy = pygame.joystick.Joystick(0)
                    self.joy.init()
                    self.last_button_state = {i: False for i in range(self.joy.get_numbuttons())}
                    print("[PS4] Joystick inizializzato", flush=True)

                # Se pygame lo invalida → NON reinizializzare subito
                if not self.joy.get_init():
                    print("[PS4] Joystick perso, attendo riconnessione...", flush=True)
                    self.joy = None
                    time.sleep(0.1)
                    continue

                # Ora possiamo usare self.joy in sicurezza
                self.handle_buttons()
                self.handle_axes()

            except pygame.error:
                # Joystick perso → reset e attesa
                print("[PS4] Errore pygame, joystick perso", flush=True)
                self.joy = None
                time.sleep(0.1)
                continue

            except Exception as e:
                print("[PS4] Errore loop:", e, flush=True)

            time.sleep(0.01)




    # -------------------------
    # RAMPA CC33
    # -------------------------
    def handle_ramp(self):
        if self.modes[self.mode]["name"] != "FX":
            return

        if self.ramp_direction != 0:
            self.ramp_value += self.ramp_direction * 0.5
            self.ramp_value = max(0, min(127, self.ramp_value))
            self.midi.cc(33, self.ramp_value, 2)  # CHANNEL 2



    # -------------------------
    # LETTURA PULSANTI (PATCHATA)
    # -------------------------
    def handle_buttons(self):
        if self.joy is None:
            return

        for b in range(self.joy.get_numbuttons()):
            state = self.joy.get_button(b)

            if b not in self.last_button_state:
                self.last_button_state[b] = False

            if state and not self.last_button_state[b]:
                self.handle_button_down(b)
            elif not state and self.last_button_state[b]:
                self.handle_button_up(b)

            self.last_button_state[b] = state



    # -------------------------
    # BUTTON DOWN
    # -------------------------
    def handle_button_down(self, b):

        # Cambio modalità
        if b == self.button_R3:
            self.mode = (self.mode + 1) % len(self.modes)
            print(f"[PS4] Modalità: {self.modes[self.mode]['name']}", flush=True)
            return

        if b == self.button_L3:
            self.mode = (self.mode - 1) % len(self.modes)
            print(f"[PS4] Modalità: {self.modes[self.mode]['name']}", flush=True)
            return

        mode_name = self.modes[self.mode]["name"]

        # -------------------------
        # FX MODE
        # -------------------------
        if mode_name == "FX":

            # D-Pad → NOTE
            if b in (11, 14, 12, 13):
                note = self.button_to_notes[b]
                self.midi.note_on(note, 100, 2)
                self.current_note = note
                return

            # X / Cerchio / Quadrato / Triangolo → CC32
            if b == 0:
                self.midi.cc(32, 20, 2)
                return
            if b == 1:
                self.midi.cc(32, 60, 2)
                return
            if b == 2:
                self.midi.cc(32, 90, 2)
                return
            if b == 3:
                self.midi.cc(32, 120, 2)
                return

            # R1 → rampa crescente
            if b == self.button_R1:
                self.ramp_direction = +1
                return

            # L1 → rampa decrescente
            if b == self.button_L1:
                self.ramp_direction = -1
                return


        # -------------------------
        # MODALITÀ ACCORDI
        # -------------------------
        if mode_name == "Accordi":

            mapping = {
                0: 10,   # X
                2: 27,   # Quadrato
                1: 44,   # Cerchio
                3: 61,   # Triangolo
                12: 78,  # D-Pad Giù
                13: 95,  # D-Pad Sinistra
                14: 112, # D-Pad Destra
                11: 127  # D-Pad Su
            }

            if b in mapping:
                self.midi.cc(40, mapping[b], 3)
                return


        # -------------------------
        # MODALITÀ NOTE
        # -------------------------
        if mode_name == "Note":
            if b == self.button_L1:
                self.pitch_value = max(0, self.pitch_value - 1)
                self.midi.cc(self.cc_pitch, self.pitch_value, 0)
                return

            if b == self.button_R1:
                self.pitch_value = min(127, self.pitch_value + 1)
                self.midi.cc(self.cc_pitch, self.pitch_value, 0)
                return

        # Note normali
        if b in self.button_to_notes:
            self.press_note(b)



    # -------------------------
    # BUTTON UP
    # -------------------------
    def handle_button_up(self, b):

        mode_name = self.modes[self.mode]["name"]

        # -------------------------
        # FX MODE — RESET
        # -------------------------
        if mode_name == "FX":

            # D-Pad → NOTE OFF
            if b in (11, 14, 12, 13):
                note = self.button_to_notes[b]
                self.midi.note_off(note, 2)
                return

            # Reset CC32
            if b in (0, 1, 2, 3):
                self.midi.cc(32, 0, 2)
                return

            # Reset rampa CC33
            if b in (self.button_L1, self.button_R1):
                self.ramp_direction = 0
                self.ramp_value = 64
                self.midi.cc(33, 64, 2)
                return
        
        # -------------------------
        # ACCORDI — RESET
        # -------------------------
        if mode_name == "Accordi":
            mapping = {0,1,2,3,11,12,13,14}
            if b in mapping:
                self.midi.cc(40, 0, 3)
                return


        # Note OFF (solo accordi)
        if b in self.pressed:
            self.release_note(b)



    # -------------------------
    # LOGICA NOTE (LEGATO)
    # -------------------------
    def press_note(self, b):
        if b in self.pressed:
            return

        self.pressed.add(b)

        note = self.button_to_notes.get(b)
        if note is None:
            return

        mode = self.modes[self.mode]

        if mode["name"] == "Note":
            if self.current_note and self.current_note != note:
                self.midi.note_off(self.current_note, mode["note_channel"])

            self.midi.note_on(note, 100, mode["note_channel"])
            self.current_note = note

        elif mode["name"] == "Accordi":
            if b in self.button_to_chords:
                chord = self.button_to_chords[b]
                self.midi.play_chord(chord, mode["note_channel"])


    def release_note(self, b):
        if b in self.pressed:
            self.pressed.remove(b)

        mode = self.modes[self.mode]

        if mode["name"] == "Accordi":
            if b in self.button_to_chords:
                chord = self.button_to_chords[b]
                self.midi.stop_chord(chord, mode["note_channel"])



    # -------------------------
    # GESTIONE ASSI (PATCHATA)
    # -------------------------
    def handle_axes(self):
        if self.joy is None:
            return

        axes = [self.joy.get_axis(i) for i in range(self.joy.get_numaxes())]
        mode = self.modes[self.mode]
        axis_map = mode["axis_map"]
        cc_channel = 2 if mode["name"] == "FX" else mode["cc_channel"]

        if len(axes) < 6:
            return

        # Assi PS4
        l3x = axes[0]
        l3y = axes[1]
        r3x = axes[2]
        r3y = axes[3]
        l2  = axes[4]
        r2  = axes[5]

        # Deadzone per L2/R2
        if abs(l2 + 1.0) < self.trigger_deadzone:
            l2_val = 0
        else:
            l2_val = scale_trigger(l2)

        if abs(r2 + 1.0) < self.trigger_deadzone:
            r2_val = 0
        else:
            r2_val = scale_trigger(r2)

        axis_values = {
            "l3x": scale_axis_segment(l3x),
            "l3y": scale_axis_segment(l3y),
            "r3x": scale_axis_segment(r3x),
            "r3y": scale_axis_segment(r3y),
            "l2": (l2_val, 0),
            "r2": (r2_val, 0),
        }

        for axis_name, (pos_val, neg_val) in axis_values.items():
            if axis_name not in axis_map:
                continue

            mapping = axis_map[axis_name]

            if "pos" in mapping:
                self.send_cc_if_changed(mapping["pos"], pos_val, axis_name + "_pos", cc_channel)

            if "neg" in mapping:
                self.send_cc_if_changed(mapping["neg"], neg_val, axis_name + "_neg", cc_channel)



    # -------------------------
    # ANTI-SPAM CC
    # -------------------------
    def send_cc_if_changed(self, cc, value, key, channel):
        prev = self.last_cc.get(key)
        if prev is not None and abs(prev - value) < 2:
            return

        self.midi.cc(cc, value, channel)
        self.last_cc[key] = value
