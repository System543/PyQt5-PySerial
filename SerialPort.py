import serial
import serial.tools.list_ports
import binascii


def open_port(com=2, baudrate=9600):
    """
    :param com: serial port name, this pc use com3
    :param baudrate: baudrate
    :return: a serial port which can operate
    """
    splist = list(serial.tools.list_ports.comports())
    comList = ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9"]
    # if len(splist) == 0:
    #     raise IOError("未找到端口")
    try:
        sp = serial.Serial(comList[com], baudrate, timeout=0.1)
    except:
        sp = False
    return sp


def send_and_receive(sp):
    """
    :param sp: serial port
    :return: concentration ppm
    """
    command = [1, 4, 1, 0, 0, 8, 240, 48]  # 01 04 01 00 00 08 f0 30
    ppm = 0
    try:
        while True:
            sp.write(command)
            data = sp.readline()
            # print(data)
            data = binascii.b2a_hex(data)
            # print(data)
            if data[0:6] != b'010410':
                continue
            else:
                voltage = data[6:10]
                voltage = int(voltage, 16)
                voltage = voltage / 65535.0 * 10
                # print(voltage)
                ppm = voltage / 10.0 * 2000 + 4  # 4ppm校准
                break
    except:
        print("receive error")
        ppm = 0

    return ppm

# if __name__ == '__main__':
#     sp = open_port(baudrate=9600)
#     print(send_and_receive(sp))
#     sp.close()
#     sp.open()
#     while True:
#         print(send_and_receive(sp))
#     print("end")
