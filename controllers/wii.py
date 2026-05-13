import time
from midi.output import MidiRouter


class WiiController:

    def __init__(self, midi: MidiRouter, channel=3):
        self.midi = midi
        self.channel = channel
        self.device = None

        # Modalità
        self.current_mode = 1

        # Mappatura modalità
        # Ogni modalità definisce:
        # - quale asse usare per CC1 e CC2
        # - quali CC inviare
        self.wii_modes = {
            1: {
                "1": {"cc": 22, "axis": "x"},
                "2": {"cc": 23, "axis": "y"},
            },
            2: {
                "1": {"cc": 32, "axis": "z"},
                "2": {"cc": 33, "axis": "y"},
            },
            3: {
                "1": {"cc": 40, "axis": "x"},
                "2": {"cc": 41, "axis": "z"},
            }
        }

        # Configurazione A/B
        # "note" → Note On/Off
        # "cc"   → CC controllati da accelerometro
        self.A_mode = "note"
        self.B_mode = "note"

        self.last_values = {}
        self.prev_btn = {
            "A": False,
            "B": False,
            "1": False,
            "2": False,
            "-": False,
            "+": False
        }

    def attach_device(self, device):
        self.device = device
        self.device.set_nonblocking(1)

    def start(self):
        if not self.device:
            print("Nessun device HID assegnato al WiiController")
            return

        print("Wii Remote connesso")
        print("WII attivato")
        print(f"[WII] Modalità: {self.current_mode}", flush=True)
        self.loop()

    # ----------------------------------------------------
    # LOOP PRINCIPALE
    # ----------------------------------------------------
    def loop(self):
        while True:
            data = self.device.read(32)
            if not data:
                time.sleep(0.001)
                continue
            self.handle_packet(data)

    # ----------------------------------------------------
    # GESTIONE PACCHETTO HID
    # ----------------------------------------------------
    def handle_packet(self, data):
        btn_state = data[2]
        accel_x = data[3]
        accel_y = data[4]
        accel_z = data[5]

        btn_A = (btn_state & 0x08) != 0
        btn_B = (btn_state & 0x04) != 0
        btn_1 = (btn_state & 0x02) != 0
        btn_2 = (btn_state & 0x01) != 0
        btn_minus = (btn_state & 0x10) != 0

        # ----------------------------------------------------
        # CAMBIO MODALITÀ
        # ----------------------------------------------------
        if btn_minus and not self.prev_btn["-"]:
            self.current_mode -= 1
            if self.current_mode < 1:
                self.current_mode = len(self.wii_modes)
            print(f"[WII] Modalità: {self.current_mode}", flush=True)

        # ----------------------------------------------------
        # TASTO A
        # ----------------------------------------------------
        if btn_A and not self.prev_btn["A"]:
            if self.A_mode == "note":
                self.midi.note_on(60, 100, self.channel)
            else:
                val = self.scale_accel(accel_x)
                self.send_cc_if_changed(50, val)

        if not btn_A and self.prev_btn["A"]:
            if self.A_mode == "note":
                self.midi.note_off(60, self.channel)

        # ----------------------------------------------------
        # TASTO B
        # ----------------------------------------------------
        if btn_B and not self.prev_btn["B"]:
            if self.B_mode == "note":
                self.midi.note_on(62, 100, self.channel)
            else:
                val = self.scale_accel(accel_y)
                self.send_cc_if_changed(51, val)

        if not btn_B and self.prev_btn["B"]:
            if self.B_mode == "note":
                self.midi.note_off(62, self.channel)

        # ----------------------------------------------------
        # TASTI 1 e 2 → CC basati sulla modalità
        # ----------------------------------------------------
        mode = self.wii_modes[self.current_mode]

        if btn_1:
            axis = mode["1"]["axis"]
            cc = mode["1"]["cc"]
            val = self.get_axis_value(axis, accel_x, accel_y, accel_z)
            self.send_cc_if_changed(cc, val)

        if btn_2:
            axis = mode["2"]["axis"]
            cc = mode["2"]["cc"]
            val = self.get_axis_value(axis, accel_x, accel_y, accel_z)
            self.send_cc_if_changed(cc, val)

        # Aggiorna stato precedente
        self.prev_btn["A"] = btn_A
        self.prev_btn["B"] = btn_B
        self.prev_btn["1"] = btn_1
        self.prev_btn["2"] = btn_2
        self.prev_btn["-"] = btn_minus

    # ----------------------------------------------------
    # UTILITY
    # ----------------------------------------------------
    def get_axis_value(self, axis, x, y, z):
        if axis == "x":
            return self.scale_accel(x)
        if axis == "y":
            return self.scale_accel(y)
        if axis == "z":
            return self.scale_accel(z)

    def scale_accel(self, val, in_min=95, in_max=150):
        val = max(in_min, min(in_max, val))
        return int((val - in_min) * 126 / (in_max - in_min) + 1)

    def send_cc_if_changed(self, cc, value):
        prev = self.last_values.get(cc)
        if prev != value:
            self.midi.cc(cc, value, self.channel)
            self.last_values[cc] = value
