import math

def apply_deadzone(value, deadzone):
    """
    Applica una deadzone simmetrica a un valore in range -1..1.
    Restituisce 0 se |value| < deadzone.
    """
    if abs(value) < deadzone:
        return 0.0
    return value


def scale_axis_segment(value, deadzone=0.1):
    """
    Converte un valore -1..1 in due valori CC separati:
    - pos (0..127)
    - neg (0..127)
    con deadzone centrale.

    Restituisce: (pos, neg)
    """
    value = apply_deadzone(value, deadzone)

    if value == 0:
        return 0, 0

    if value > 0:
        scaled = (value - deadzone) / (1 - deadzone)
        return int(scaled * 127), 0

    else:
        scaled = (-value - deadzone) / (1 - deadzone)
        return 0, int(scaled * 127)


def scale_trigger(value, deadzone=0.18):
    """
    Converte un trigger PS3/Wii da -1..1 a CC 0..127.
    Deadzone iniziale (0..deadzone) mappata a 0.
    """
    # Normalizza -1..1 → 0..1
    norm = (value + 1.0) / 2.0

    if norm <= deadzone:
        return 0

    scaled = (norm - deadzone) / (1 - deadzone)
    return max(0, min(127, int(scaled * 127)))


def smooth_value(prev, current, factor=0.2):
    """
    Smoothing esponenziale per assi/accelerometri.
    factor 0.0 = nessun smoothing
    factor 1.0 = massimo smoothing
    """
    return prev + (current - prev) * (1 - factor)
