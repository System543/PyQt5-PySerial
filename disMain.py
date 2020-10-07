import Saver
import SerialPort
import sys
import time
import timer
import datetime
import threading
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from myui import Ui_MainWindow

dataList = []
displayList = []
displayLimit = 10
sampleFlag = False
printFlag = False


class MainWindow(QDialog, Ui_MainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.sp = ""

        self.startSample.clicked.connect(self.start_sample)
        self.stopSample.clicked.connect(self.stop_sample)
        self.thread.ok.connect(self.print_ppm)

    def start_sample(self):
        global sampleFlag
        if not sampleFlag:
            baudrate = self.baudRateSelect.currentText()
            sampleTime = self.sampleTime.text()
            comIndex = self.comSelect.currentIndex()
            try:
                sampleTime = int(sampleTime)
                baudrate = int(baudrate)
            except:
                msg_box = QMessageBox()
                msg_box.warning(self, "提示", "输入整数", QMessageBox.Ok)
                return 0
            path = r"G:\WXB\Datas\test.xlsx"
            try:
                self.sp.open()
            except:
                self.sp = SerialPort.open_port(comIndex, baudrate)
            spThread = SpThread("serial port thread", sampleTime, self.sp)

            saveThread = SaveThread(path)

            spThread.start()
            saveThread.start()

        sampleFlag = True
        # self.textDisplay.setText("sadafag")

    def stop_sample(self):
        app = QApplication.instance()
        app.quit()
        global sampleFlag
        sampleFlag = False
        # try:
        #     self.sp.close()
        # except:
        #     msg_box = QMessageBox()
        #     msg_box.warning(self, "警告", "未开始采集", QMessageBox.Ok)

    def print_ppm(self):
        self.textDisplay.setText("asgfag")


class SpThread(threading.Thread):
    ok = pyqtSignal()

    def __init__(self, name, sample_time, sp):
        super(SpThread, self).__init__()
        self.name = name
        self.sample_time = float(sample_time)
        self.sp = sp

    def run(self):
        print(self.name + " start")
        global displayList
        old_time = datetime.datetime.now()
        if sampleFlag:
            ppm = SerialPort.send_and_receive(sp=self.sp)
            dataList.append([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ppm])
            print(ppm)
        while True:
            error = time_delta(old_time)
            if error > self.sample_time:
                # old_time = datetime.datetime.now()
                if sampleFlag:
                    ppm = SerialPort.send_and_receive(sp=self.sp)
                    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    dataList.append([now_time, '%.3f' % ppm])
                    if len(displayList) <= 10:
                        displayList.append([now_time, '%.3f' % ppm])
                    else:
                        mid = displayList[1:]
                        displayList = mid + [[now_time, '%.3f' % ppm]]
                    print([now_time, '%.3f ppm' % ppm])
                old_time = old_time + datetime.timedelta(seconds=self.sample_time / 1000)


class DisplayThread(threading.Thread):
    def __init__(self):
        super(DisplayThread, self).__init__()

    def run(self):

        while True:
            if printFlag:
                print()


class SaveThread(threading.Thread):
    def __init__(self, path, saveCount=20):
        super(SaveThread, self).__init__()
        self.path = path
        self.saveCount = saveCount

    def run(self):
        global dataList
        while True:
            time.sleep(10)
            if sampleFlag:
                try:
                    if len(dataList) > self.saveCount:
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
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
