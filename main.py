import pygame
import time
from midi.output import MidiRouter
from controllers.ps4 import PS4Controller

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"


def main():
    print("[MAIN] Avvio sistema...")

    # Inizializza pygame
    pygame.init()
    pygame.joystick.init()

    # Inizializza MIDI (porta virtuale CoreMIDI su macOS)
    midi = MidiRouter(port_name="ControllersToAbleton")

    # Inizializza controller PS4
    ps4 = PS4Controller(midi)
    ps4.start()

    print("[MAIN] Sistema avviato. Premi CTRL+C per uscire.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MAIN] Uscita...")
        ps4.running = False

if __name__ == "__main__":
    main()
