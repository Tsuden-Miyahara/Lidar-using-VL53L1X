import serial
from serial.tools import list_ports
import questionary

def select(bau: int = 9600):
    ports = list_ports.comports()
    if not len(ports):
        raise IndexError('no detected serial')
    obj = {}
    for v in ports: obj[v.description] = v.device
    key = questionary.select("select", choices=obj).ask()
    if not key:
        raise IndexError('serial unselected')
    ser = serial.Serial(obj[key], bau)
    ser.set_buffer_size(rx_size = 12800, tx_size = 12800)
    return ser