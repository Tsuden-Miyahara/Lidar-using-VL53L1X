import serial
from serial.tools import list_ports

def select(bau: int = 9600):
    ports = list_ports.comports()
    devices = [v.device for v in ports]
    if not len(devices):
        raise IndexError('no detected serial')
    for i, d in enumerate(devices):
        print(f'{i}. {d}')
    try:
        num = int(input('select index: '))
    except ValueError:
        num = 0
    return serial.Serial(devices[num], bau)