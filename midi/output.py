import rtmidi
import platform

class MidiRouter:
    def __init__(self, port_name="ControllersToAbleton", port_index=None):
        self.midi = rtmidi.MidiOut()
        system = platform.system()

        # ----------------------------------------------------
        # macOS → CoreMIDI virtual port
        # ----------------------------------------------------
        if system == "Darwin":
            print(f"[MIDI] Creazione porta virtuale CoreMIDI: {port_name}")
            self.midi.open_virtual_port(port_name)
            return

        # ----------------------------------------------------
        # Windows/Linux → porte hardware
        # ----------------------------------------------------
        ports = self.midi.get_ports()

        if port_index is not None:
            print(f"[MIDI] Apertura porta index {port_index}: {ports[port_index]}")
            self.midi.open_port(port_index)
            return

        if ports:
            print(f"[MIDI] Apertura porta default: {ports[0]}")
            self.midi.open_port(0)
        else:
            raise RuntimeError("Nessuna porta MIDI disponibile")

    # ----------------------------------------------------
    # NOTE
    # ----------------------------------------------------
    def note_on(self, note, velocity, channel):
        self.midi.send_message([0x90 + channel, note, velocity])

    def note_off(self, note, channel):
        self.midi.send_message([0x80 + channel, note, 0])

    # ----------------------------------------------------
    # CONTROL CHANGE
    # ----------------------------------------------------
    def cc(self, cc, value, channel):
        self.midi.send_message([0xB0 + channel, cc, value])

    # ----------------------------------------------------
    # PITCH BEND
    # ----------------------------------------------------
    def pitch_bend(self, value, channel=0):
        """
        value: 0–16383 (8192 = centro)
        """
        value = max(0, min(16383, int(value)))
        lsb = value & 0x7F
        msb = (value >> 7) & 0x7F
        status = 0xE0 | (channel & 0x0F)
        self.midi.send_message([status, lsb, msb])

    # ----------------------------------------------------
    # UTILITY
    # ----------------------------------------------------
    @staticmethod
    def list_ports():
        midi = rtmidi.MidiOut()
        return midi.get_ports()

    def close(self):
        del self.midi
