from typing import Tuple

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.colors import BoundaryNorm
from matplotlib.ticker import MaxNLocator
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from gui import GUI
import numpy as np

import datetime
import json
import os
import csv
import subprocess

import time
from time import sleep

import select_serial
import threading

def get_fname(dir: str, ext: str):
    if not os.path.exists(dir):
        os.mkdir(dir)
    d = datetime.date.today()
    n = str(d.year) + str(d.month).zfill(2) + str(d.day).zfill(2)
    i = 1
    while True:
        f = os.path.join(dir, f'{n}_{str(i).zfill(5)}.{ext}')
        if not os.path.exists(f):
            return f
        i += 1

def write_csv_line(path: str, data: list):
    with open(path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)

try:
    con_serial = select_serial.select(115200)
except:
    con_serial = None

if con_serial:
    
    gui = GUI("color mesh")

    blnv = tk.BooleanVar(gui.root, )
    txtv = tk.StringVar(gui.root, value='-')
    
    fig = plt.figure(figsize=(8, 7)) # , facecolor='white'
    ax2 = plt.subplot()

    ms_before = 0
    ms_after  = 0


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


    ser_enable = True
    before_data = {}
    current_data = {}
    fpath = get_fname('Log', 'csv')
    write_csv_line(fpath, ['size_x', 'size_y', ''] + [f'data_{i}' for i in range(16)])

    def ser_worker():
        global ser_enable, current_data, ms_before, ms_after
        while ser_enable:
            # if (con_serial.inWaiting() > 0): #Check if data is on the serial port
            data_receving = con_serial.readline().decode("utf-8").strip()
            try:
                obj = json.loads(data_receving)
                if not current_data == obj:
                    if 'millis' in current_data and 'millis' in obj:
                        ms_before = current_data['millis']
                        ms_after  = obj['millis']
                    current_data = obj
                    write_csv_line(fpath, [obj["size_x"], obj["size_y"], obj["millis"]] + obj['data'])
            except Exception as e:
                print(e, data_receving)


    def animate():
        global distances_matrix, text_list, current_data, before_data

        if not 'size_x' in current_data or current_data == before_data:
            return
        
        before_data = current_data
        obj = current_data
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
                #a = np.flipud(a)
                b = distances_matrix[:, 1:matrix_y]
                #| a4, b, b, b,
                #| a3, b, b, b,
                #| a2, b, b, b,
                #| a1, b, b, b,
                if 1 < matrix_x:
                    a1   = a[0:1, :]
                    a234 = a[1:matrix_x, :]
                    a = np.concatenate( (a234, a1) )

                distances_matrix = np.concatenate( (b, a), axis=1 )
                #| b, b, b, a1,
                #| b, b, b, a4,
                #| b, b, b, a3,
                #| b, b, b, a2,

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



    ser_thread = threading.Thread(target=ser_worker, daemon=True)
    setup()
    # anim = animation.FuncAnimation(fig, animate, interval=20, blit=False, repeat=False)
    # plt.show()

    def gui_setup(root: tk.Tk):
        global blnv, txtv
        root.geometry("1200x850")
        def setflagfalse():
            global ser_enable, blnv
            ser_enable = False
            gui.quit()
            sleep(1)
            nm = os.path.join(os.getcwd(), fpath)
            print(nm)
            # os.startfile(fpath)
            # subprocess.Popen(['start', '', f'{nm}'], shell=True)
            subprocess.run(f'explorer /select,{nm}')
            # subprocess.run(f'"{nm}"')
            sleep(1)
            # ser_thread.terminate()
            print("disconnect")
            con_serial.close()
            ser_thread.join()
        root.protocol("WM_DELETE_WINDOW", setflagfalse)
        frame_plot = tk.Frame(root, width=900, height=800)
        canvas = FigureCanvasTkAgg(fig, frame_plot)
        canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, root, pack_toolbar=False)
        # toolbar.update()
        # button = tk.Button(master=root, text="Quit", command=root.quit)
        # button.pack(side=tk.BOTTOM)
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        # anim = animation.FuncAnimation(fig, animate, fargs=(quad1,), interval=20, blit=True, repeat=False)#, cache_frame_data=True, save_count=100
        # try: anim.save()
        # except: print('anim')
        frame_plot.pack()

        opt_box = tk.Frame(root, width=800, height=300)
        # chk = tk.Checkbutton(opt_box, variable=blnv, text='終了時に作成したログファイルを開く', command=txtv.set(str(blnv.get())))
        # chk.pack()
        lab1 = tk.Label(opt_box, textvariable=txtv, width=100)
        lab1.pack()
        # lab2 = tk.Label(opt_box, text=fpath)
        # lab2.pack()
        opt_box.pack()

        def event():
            try:
                animate()
                canvas.draw()
                txtv.set(f'{ms_after} ms (-> {ms_after - ms_before} ms)')
                root.after(25, event)
            except Exception as e:
                print(e)
                return
        event()

    gui.setup(gui_setup)
    ser_thread.start()
    gui.run()