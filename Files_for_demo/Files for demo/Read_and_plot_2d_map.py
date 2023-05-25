from typing import Tuple

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

try:
    con_serial = select_serial.select(115200)
except:
    con_serial = None

if con_serial:
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

    def setup(size: Tuple[int] = [4, 4]):
        global size_of_the_matrix, distances_matrix, quad1, x, y
        ax2.clear()
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        size_of_the_matrix = size
        matrix_x, matrix_y = size_of_the_matrix
        x, y = np.meshgrid(
            np.linspace(0, matrix_x, matrix_x + 1),
            np.linspace(0, matrix_y, matrix_y + 1)
        ) #each axis is from 0 to 3 devided in 4 sections
        distances_matrix = np.zeros((matrix_y, matrix_x))
        quad1 = ax2.pcolormesh(x, y, distances_matrix, vmin=0, vmax=2250, shading='flat', cmap='plasma')
        
        grid_template_x = np.arange(0, matrix_x, step=1)
        grid_template_y = np.arange(0, matrix_y, step=1)

        ax2.set_xlim(0, matrix_x)
        ax2.set_ylim(0, matrix_y)

        ax2.set_xticks(grid_template_x)
        ax2.set_yticks(grid_template_y)
        ax2.grid()

    text_list = []
    boxdic = {
        "facecolor" : "white",
        "edgecolor" : "black",
        "boxstyle" : "Round",
        "linewidth" : 1
    }

    def txt(x, y, num):
        #print(f"[x, y] = [{x}, {y}] ({num})")
        return ax2.text(x + 0.5, y + 0.5, f"{num}", horizontalalignment="center", verticalalignment="center", size='small', bbox=boxdic)

    def animate(iter):
        global distances_matrix, text_list
        if (con_serial.inWaiting() > 0): #Check if data is on the serial port
            try:
                line = con_serial.readline()
                data_received = line.decode("utf-8").strip()
                obj = json.loads(data_received)
                # print(obj)
            except Exception as e:
                # print(e)
                return
            
            _temp = (obj["size_x"], obj["size_y"])

            if size_of_the_matrix != _temp:
                setup(_temp)
            distances = [d if d != 0.0 else 9999.9 for d in obj["data"]]
            # distances = np.flip(distances, axis=0)

            # print(' - '.join([str(v).rjust(6, ' ') for v in distances]))

            matrix_x, matrix_y = size_of_the_matrix
            if(len(distances) == matrix_x * matrix_y):
                distances_matrix = np.reshape(distances, (matrix_y, matrix_x))
                


                """
                """
                if 1 < matrix_y:
                    a = distances_matrix[:,0:1]
                    b = distances_matrix[:, 1:matrix_y]
                    # 3| a4, b, b, b,
                    # 2| a3, b, b, b,
                    # 1| a2, b, b, b,
                    # 0|*a1, b, b, b,
                    #   -------------
                    #     0  1  2  3
                    if 1 < matrix_x:
                        a1   = a[0:1, :]
                        a234 = a[1:matrix_x, :]
                        a = np.concatenate( (a234, a1) )

                    distances_matrix = np.concatenate( (b, a), axis=1 )
                    # 3| b, b, b,*a1,
                    # 2| b, b, b, a4,
                    # 1| b, b, b, a3,
                    # 0| b, b, b, a2,
                    #   -------------
                    #     0  1  2  3

                    if matrix_x < 2:
                        distances_matrix = np.flipud(distances_matrix)
                else:
                    distances_matrix = np.flip(distances_matrix)

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
                    txt(x, y, num)
                    for y, _list in enumerate(distances_matrix)
                    for x, num in enumerate(_list)
                ]
                #raise TypeError('test')


    setup()
    anim = animation.FuncAnimation(fig, animate, interval=20, blit=False, repeat=False)

    manager = plt.get_current_fig_manager()
    manager.set_window_title('color mesh')
    manager.resize(800, 650)

    plt.show()

