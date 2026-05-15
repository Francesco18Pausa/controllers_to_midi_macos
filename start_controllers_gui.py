import tkinter as tk
from gui.launcher_gui import LauncherGUI


# ----------------------------------------------------
# MAIN
# ----------------------------------------------------
def main():
    # Avvio GUI principale
    root = tk.Tk()
    app = LauncherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
