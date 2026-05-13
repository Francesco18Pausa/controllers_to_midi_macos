import os
import sys
import time
import threading

# Pygame deve essere inizializzato UNA SOLA VOLTA
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import hid

from midi.output import MidiRouter
from controllers.ps3 import PS3Controller
from controllers.ps4 import PS4Controller
from controllers.wii import WiiController

if len(sys.argv) > 1:
    midi_port_name = sys.argv[1]
else:
    midi_port_name = None

def safe_print(*args):
    try:
        print(*args, flush=True)
    except:
        pass


# ----------------------------------------------------
# RILEVAMENTO CONTROLLER (ROBUSTO)
# ----------------------------------------------------
def detect_controllers():
    try:
        pygame.event.pump()
    except:
        return []

    names = []
    try:
        count = pygame.joystick.get_count()
        for i in range(count):
            try:
                j = pygame.joystick.Joystick(i)
                if not j.get_init():
                    j.init()
                names.append(j.get_name())
            except:
                continue
    except:
        return []

    return names


# ----------------------------------------------------
# CONNESSIONE WII (ROBUSTA)
# ----------------------------------------------------
def connect_wiimote():
    try:
        devices = hid.enumerate()
    except:
        return None

    for d in devices:
        try:
            if d["vendor_id"] == 0x057e and d["product_id"] == 0x0306:
                dev = hid.device()
                dev.open_path(d["path"])
                return dev
        except:
            return None

    return None


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------
def main():
    safe_print("🎹 Avvio sistema MIDI + Controller...")

    # Inizializzazione pygame
    try:
        pygame.init()
        pygame.joystick.init()
        safe_print("Pygame inizializzato")
    except Exception as e:
        safe_print("Errore init pygame:", e)

    # Porta MIDI
    try:
        port_index = int(sys.argv[1])
    except:
        port_index = None

    # Inizializzazione MIDI
    try:
        midi = MidiRouter(port_index=MidiRouter.list_ports().index(midi_port_name))
    except Exception as e:
        safe_print("Errore apertura porta MIDI:", e)
        while True:
            time.sleep(1)

    safe_print("Inizializzazione HID...")

    ps3 = None
    ps4 = None
    wii = None

    last_wii_check = 0

    safe_print("🔄 Monitoraggio controller attivo...")

    # ----------------------------------------------------
    # LOOP PRINCIPALE (NON PUÒ PIÙ CRASHARE)
    # ----------------------------------------------------
    while True:
        try:
            names = detect_controllers()

            # -------------------------
            # PS3
            # -------------------------
            ps3_found = any("PLAYSTATION" in n or "PS3" in n for n in names)

            if ps3_found and ps3 is None:
                safe_print("PS3 attivato")
                try:
                    ps3 = PS3Controller(midi)
                    threading.Thread(target=ps3.start, daemon=True).start()
                except Exception as e:
                    safe_print("Errore avvio PS3:", e)
                    ps3 = None

            if not ps3_found and ps3 is not None:
                safe_print("PS3 disconnesso")
                ps3 = None

            # -------------------------
            # PS4
            # -------------------------
            ps4_found = any(
                "Wireless Controller" in n or
                "DualShock" in n or
                "PS4" in n
                for n in names
            )

            if ps4_found and ps4 is None:
                safe_print("PS4 attivato")
                try:
                    ps4 = PS4Controller(midi)
                    threading.Thread(target=ps4.start, daemon=True).start()
                except Exception as e:
                    safe_print("Errore avvio PS4:", e)
                    ps4 = None

            if not ps4_found and ps4 is not None:
                safe_print("PS4 disconnesso")
                ps4 = None

            # -------------------------
            # WII
            # -------------------------
            now = time.time()
            if now - last_wii_check > 2:
                last_wii_check = now
                wii_dev = connect_wiimote()

                if wii_dev and wii is None:
                    safe_print("Wii Controller attivo tramite HID")
                    try:
                        wii = WiiController(midi, channel=3)
                        wii.attach_device(wii_dev)
                        threading.Thread(target=wii.start, daemon=True).start()
                    except Exception as e:
                        safe_print("Errore avvio Wii:", e)
                        wii = None

                if not wii_dev and wii is not None:
                    safe_print("Wii disconnesso")
                    wii = None

        except Exception as e:
            safe_print("Errore loop principale:", e)

        time.sleep(0.5)


if __name__ == "__main__":
    main()
