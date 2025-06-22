
import numpy as np
import matplotlib.pyplot as plt



class Plotter:




    def __init__(self):
        self.fig, self.ax = plt.subplots()


    def plot_single_componet(self, comp, label): # lbl for symbol
        # Re und Im der ersten Komponente
        plt.plot(np.real(comp[:, 0]), label=f"Re{label}")
        plt.plot(np.imag(comp[:, 0]), label=f"Im{label}")
        plt.legend()
        plt.title(label)
        plt.show()
