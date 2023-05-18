import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
import numpy as np

import json

import time
from time import sleep

import select_serial

arduinoSerialData = select_serial.select(115200)
fig = plt.figure(figsize=None, facecolor='white')
ax2 = plt.subplot()


ax2.set_xlabel('X')
ax2.set_ylabel('Y')
size_of_the_matrix = 4
distances_matrix = np.zeros((size_of_the_matrix, size_of_the_matrix))
x, y = np.meshgrid(
    np.linspace(0, size_of_the_matrix, size_of_the_matrix + 1),
    np.linspace(0, size_of_the_matrix, size_of_the_matrix + 1)
) #each axis is from 0 to 3 devided in 4 sections
quad1 = ax2.pcolormesh(x, y, distances_matrix, vmin=0, vmax=2250, shading='flat', cmap='plasma')
bar = fig.colorbar(quad1, ax=ax2)
bar.set_label("Ranges in each ROI")

def setup(size: int = 4):
    global size_of_the_matrix, distances_matrix, quad1, x, y
    ax2.clear()
    ax2.set_xlabel('X')
    ax2.set_ylabel('Y')
    size_of_the_matrix = size
    x, y = np.meshgrid(
        np.linspace(0, size_of_the_matrix, size_of_the_matrix + 1),
        np.linspace(0, size_of_the_matrix, size_of_the_matrix + 1)
    ) #each axis is from 0 to 3 devided in 4 sections
    distances_matrix = np.zeros((size_of_the_matrix, size_of_the_matrix))
    quad1 = ax2.pcolormesh(x, y, distances_matrix, vmin=0, vmax=2250, shading='flat', cmap='plasma')
    grid_template = np.arange(0, size_of_the_matrix, step=1)

    ax2.set_xlim(0, size_of_the_matrix)
    ax2.set_ylim(0, size_of_the_matrix)
    ax2.set_xticks(grid_template)
    ax2.set_yticks(grid_template)
    ax2.grid()

text_list = []
boxdic = {
    "facecolor" : "white",
    "edgecolor" : "black",
    "boxstyle" : "Round",
    "linewidth" : 1
}

def animate(iter):
    global distances_matrix, text_list
    if (arduinoSerialData.inWaiting() > 0): #Check if data is on the serial port
        data_receving = arduinoSerialData.readline().decode("utf-8").strip()
        try:
            obj = json.loads(data_receving)
        except Exception as e:
            print(e, data_receving)
            return

        if size_of_the_matrix != obj["size"]:
            setup(obj["size"])
        distances = [d if d != 0.0 else 9999.9 for d in obj["data"]]

        # print(' - '.join([str(v).rjust(6, ' ') for v in distances]))

        if(len(distances) == size_of_the_matrix * size_of_the_matrix):
            distances_matrix = np.reshape(distances, (size_of_the_matrix, size_of_the_matrix))            
            print('')
            print('@ ====  ====  ====  ==== @')
            print('')
            print(f'millis(): {obj["millis"]}')
            print('')
            print(distances_matrix)
          

            data = distances_matrix.ravel()
            quad1.set_array(data)


            [txt.remove() for txt in text_list]
            text_list = [
                ax2.text(x + 0.5, y + 0.5, f"{num}", horizontalalignment="center", verticalalignment="center", size='small', bbox=boxdic)
                for y, _list in enumerate(distances_matrix)
                for x, num in enumerate(_list)
            ]
    


setup()
anim = animation.FuncAnimation(fig, animate ,interval=100, blit=False, repeat=False)
plt.show()

