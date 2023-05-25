import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

def _event(root: tk.Tk, ms: int, fnc, *args):
    fnc(*args)
    print('!!!')
    root.after(ms, fnc, *args)

class GUI:
    def __init__(self, title):
        self.root = tk.Tk()
        self.root.title(title)
        self.events = []

    def attachEvent(self, ms: int, fnc, *args):
        self.events.append(
            (ms, fnc, args)
        )
    
    def setup(self, callback):
        callback(self.root)
        
    def run(self):
        for evt in self.events:
            ms, fnc, args = evt
            _event(self.root, ms, fnc, *args)
        self.root.mainloop()

    def quit(self):
        self.root.quit()
        self.root.destroy()