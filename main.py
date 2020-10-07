import Saver
import SerialPort
import sys
import time
import timer
import datetime
import threading

dataList = []
count = 20


class SpThread(threading.Thread):
    def __init__(self, name, sample_time, sp):
        super(SpThread, self).__init__()
        self.name = name
        self.sample_time = float(sample_time)
        self.sp = sp

    def run(self):
        print(self.name + " start")
        old_time = datetime.datetime.now()
        while True:
            error = time_delta(old_time)
            if error > self.sample_time:
                # old_time = datetime.datetime.now()
                ppm = SerialPort.send_and_receive(sp=self.sp)
                dataList.append([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ppm])
                print(ppm)
                old_time = old_time + datetime.timedelta(seconds=self.sample_time / 1000)


class SaveThread(threading.Thread):
    def __init__(self, path):
        super(SaveThread, self).__init__()
        self.path = path

    def run(self):
        global dataList
        while True:
            time.sleep(10)
            try:
                if len(dataList) > count:
                    Saver.save_data(path=self.path, newData=dataList)
                    dataList = []
            except:
                print("excel write error")


def time_delta(old_time):
    """
    :param old_time: 上次采样时间
    :return: 据上次采样时间差值 ms
    """
    new_time = datetime.datetime.now()
    error = new_time - old_time
    return error.total_seconds() * 1000


def main():
    path = r"G:\WXB\Datas\test.xlsx"
    sp = SerialPort.open_port()
    spThread = SpThread("serial port thread", 20000, sp)
    spThread.start()
    saveThread = SaveThread(path)
    saveThread.start()


if __name__ == '__main__':
    main()
