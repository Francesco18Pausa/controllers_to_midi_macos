import rtmidi

class MidiRouter:
    def __init__(self, port_index=None):
        self.midi = rtmidi.MidiOut()

        ports = self.midi.get_ports()

        if port_index is not None:
            print(f"[MIDI] Apertura porta index {port_index}: {ports[port_index]}")
            self.midi.open_port(port_index)
            return

        # fallback: prima porta disponibile
        if ports:
            print(f"[MIDI] Apertura porta default: {ports[0]}")
            self.midi.open_port(0)
        else:
            raise RuntimeError("Nessuna porta MIDI disponibile")

    # NOTE
    def note_on(self, note, velocity, channel):
        self.midi.send_message([0x90 + channel, note, velocity])

    def note_off(self, note, channel):
        self.midi.send_message([0x80 + channel, note, 0])

    # CONTROL CHANGE
    def cc(self, cc, value, channel):
        self.midi.send_message([0xB0 + channel, cc, value])

    # ACCORDI
    def play_chord(self, notes, channel):
        for n in notes:
            self.note_on(n, 100, channel)

    def stop_chord(self, notes, channel):
        for n in notes:
            self.note_off(n, channel)
    
    @staticmethod
    def list_ports():
        midi = rtmidi.MidiOut()
        return midi.get_ports()

    def close(self):
        del self.midi
