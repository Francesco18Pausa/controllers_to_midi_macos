PS4_MODES = [
    {
        "name": "Note",
        "note_channel": 1,
        "cc_channel": 1,
        "axis_map": {
            "l3x": {"pos": 12, "neg": 13},
            "l3y": {"pos": 16, "neg": 17},
            "r3x": {"pos": 14, "neg": 15},
            "r3y": {"pos": 18, "neg": 19},
            "l2":  {"pos": 20},
            "r2":  {"pos": 21},
        }
    },

    {
        "name": "FX",
        "note_channel": 2,
        "cc_channel": 2,

        "axis_map": {
            "l3x": {"pos": 22, "neg": 23},
            "l3y": {"pos": 26, "neg": 27},
            "r3x": {"pos": 24, "neg": 25},
            "r3y": {"pos": 28, "neg": 29},
            "l2":  {"pos": 30},
            "r2":  {"pos": 31},
        }
    },

    {
        "name": "Accordi",
        "note_channel": 0,
        "cc_channel": 3,
        "axis_map": {}   # in questa modalità gli assi sono disattivati
    }
]
