# mappings/ps3_modes.py

PS3_MODES = {
    0: {
        "name": "Note",
        "note_channel": 2,
        "cc_channel": 2,
        "axis_map": {
            "l3x": {"pos": 12, "neg": 13},
            "l3y": {"pos": 16, "neg": 17},
            "r3x": {"pos": 14, "neg": 15},
            "r3y": {"pos": 18, "neg": 19},
            "l2":  {"pos": 20},
            "r2":  {"pos": 21},
        }
    },

    1: {
        "name": "Accordi",
        "note_channel": 3,
        "cc_channel": 3,
        "axis_map": {
            "l3x": {"pos": 20, "neg": 21},
            "l3y": {"pos": 24, "neg": 25},
            "r3x": {"pos": 22, "neg": 23},
            "r3y": {"pos": 26, "neg": 27},
            "l2": {"pos": 40},
            "r2": {"pos": 41},
        }
    },

    2: {
        "name": "FX",
        "note_channel": 4,
        "cc_channel": 4,
        "axis_map": {
            "l3x": {"pos": 30, "neg": 31},
            "l3y": {"pos": 34, "neg": 35},
            "r3x": {"pos": 32, "neg": 33},
            "r3y": {"pos": 36, "neg": 37},
            "l2": {"pos": 50},
            "r2": {"pos": 51},
        }
    },
}
