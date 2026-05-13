import pygame

from utils.scaling import scale_axis_segment, scale_trigger
from midi.output import MidiRouter
from mappings.ps3_modes import PS3_MODES


class PS3Controller:
    """
    Controller PS3 con:
    - legato su X / O / Quadrato / Triangolo e D-Pad
    - polling veloce
    - assi mappati via PS3_MODES
    """

    def __init__(self, midi: MidiRouter, modes=PS3_MODES):
        self.midi = midi
        self.modes = modes
        self.mode = 0

        # Stato note
        self.current_note = None
        self.note_states = {}

        # Stato CC anti-spam
        self.last_cc = {}

        # Stato pulsanti
        self.pressed = set()
        self.last_button_state = {}

        # Stato HAT (D-Pad)
        self.last_hat = (0, 0)

        # Pitch (L1/R1)
        self.pitch_value = 0
        self.cc_pitch = 11

        # Mappature pulsanti principali
        self.button_to_notes = {
            0: 36,  # X
            1: 37,  # Cerchio
            2: 38,  # Quadrato
            3: 39   # Triangolo
        }

        # D-Pad mappato come pulsanti virtuali
        self.hat_to_button = {
            (0, 1): 100,   # Up
            (1, 0): 101,   # Right
            (-1, 0): 102,  # Left
            (0, -1): 103   # Down
        }

        self.button_to_notes.update({
            100: 40,
            101: 41,
            102: 42,
            103: 43
        })

        # Accordi (usati in modalità "Accordi")
        self.button_to_chords = {
            0: [36, 40, 43],
            1: [37, 41, 44],
            2: [38, 42, 45],
            3: [39, 43, 46]
        }

        # Pulsanti speciali
        self.button_L1 = 4
        self.button_R1 = 5
        self.button_L3 = 8
        self.button_R3 = 9

    # -------------------------
    # AVVIO
    # -------------------------
    def start(self):
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("❌ Nessun controller PS3 trovato")
            return

        self.joy = pygame.joystick.Joystick(0)
        self.joy.init()

        print(f"🎮 PS3 Controller connesso: {self.joy.get_name()}")
        print(f"Modalità iniziale: {self.modes[self.mode]['name']}")

        self.last_button_state = {i: False for i in range(self.joy.get_numbuttons())}

        self.loop()

    # -------------------------
    # LOOP PRINCIPALE
    # -------------------------
    def loop(self):
        clock = pygame.time.Clock()

        while True:
            pygame.event.pump()

            self.handle_buttons_fast()
            self.handle_hat()
            self.handle_axes()

            clock.tick(240)  # polling veloce e stabile

    # -------------------------
    # LETTURA PULSANTI
    # -------------------------
    def handle_buttons_fast(self):
        for b in range(self.joy.get_numbuttons()):
            state = self.joy.get_button(b)

            if state and not self.last_button_state[b]:
                self.handle_button_down(b)
            elif not state and self.last_button_state[b]:
                self.handle_button_up(b)

            self.last_button_state[b] = state

    # -------------------------
    # HAT (D-PAD) CON LEGATO E STATO PRECEDENTE
    # -------------------------
    def handle_hat(self):
        hat = self.joy.get_hat(0)

        # Se non è cambiato, non fare nulla
        if hat == self.last_hat:
            return

        # Rilascio della direzione precedente
        if self.last_hat in self.hat_to_button:
            old_b = self.hat_to_button[self.last_hat]
            if old_b in self.pressed:
                self.release_note(old_b)

        # Press della nuova direzione
        if hat in self.hat_to_button:
            b = self.hat_to_button[hat]
            self.press_note(b)

        self.last_hat = hat

    # -------------------------
    # BUTTON DOWN
    # -------------------------
    def handle_button_down(self, b):
        # Cambio modalità
        if b == self.button_R3:
            self.mode = (self.mode + 1) % len(self.modes)
            print("Modalità →", self.modes[self.mode]["name"])
            return

        if b == self.button_L3:
            self.mode = (self.mode - 1) % len(self.modes)
            print("Modalità →", self.modes[self.mode]["name"])
            return

        # Pitch (solo in modalità Note)
        if self.modes[self.mode]["name"] == "Note":
            if b == self.button_L1:
                self.pitch_value = max(0, self.pitch_value - 1)
                self.midi.cc(self.cc_pitch, self.pitch_value, self.modes[self.mode]["cc_channel"])
                return

            if b == self.button_R1:
                self.pitch_value = min(127, self.pitch_value + 1)
                self.midi.cc(self.cc_pitch, self.pitch_value, self.modes[self.mode]["cc_channel"])
                return

        # Note
        if b in self.button_to_notes:
            self.press_note(b)

    # -------------------------
    # BUTTON UP
    # -------------------------
    def handle_button_up(self, b):
        if b in self.pressed:
            self.release_note(b)

    # -------------------------
    # LOGICA NOTE (LEGATO VERO)
    # -------------------------
    def press_note(self, b):
        if b in self.pressed:
            return

        self.pressed.add(b)

        note = self.button_to_notes.get(b)
        if note is None:
            return

        mode = self.modes[self.mode]

        # LEGATO: spegne solo la nota precedente quando ne premi una nuova
        if self.current_note and self.current_note != note:
            self.midi.note_off(self.current_note, mode["note_channel"])
            self.note_states[self.current_note] = False

        if mode["name"] == "Note":
            self.midi.note_on(note, 100, mode["note_channel"])
            self.note_states[note] = True
            self.current_note = note

        elif mode["name"] == "Accordi":
            if b in self.button_to_chords:
                chord = self.button_to_chords[b]
                self.midi.play_chord(chord, mode["note_channel"])

    def release_note(self, b):
        if b in self.pressed:
            self.pressed.remove(b)

        note = self.button_to_notes.get(b)
        if note is None:
            return

        mode = self.modes[self.mode]

        # In modalità Note: NON spegniamo qui (legato),
        # la nota precedente viene spenta solo quando ne premi un'altra.
        if mode["name"] == "Accordi":
            if b in self.button_to_chords:
                chord = self.button_to_chords[b]
                self.midi.stop_chord(chord, mode["note_channel"])

    # -------------------------
    # GESTIONE ASSI
    # -------------------------
    def handle_axes(self):
        axes = [self.joy.get_axis(i) for i in range(self.joy.get_numaxes())]
        mode = self.modes[self.mode]
        axis_map = mode["axis_map"]
        cc_channel = mode["cc_channel"]

        if len(axes) < 6:
            return

        l3x, l3y, r3x, r3y, l2, r2 = axes[:6]

        axis_values = {
            "l3x": scale_axis_segment(l3x),
            "l3y": scale_axis_segment(l3y),
            "r3x": scale_axis_segment(r3x),
            "r3y": scale_axis_segment(r3y),
            "l2": (scale_trigger(l2), 0),
            "r2": (scale_trigger(r2), 0),
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
