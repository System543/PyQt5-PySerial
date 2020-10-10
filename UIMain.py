import Saver
import SerialPort
import sys
import time
import datetime
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QFileDialog, QGraphicsScene
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from myui import Ui_MainWindow

import matplotlib
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

matplotlib.use("Qt5Agg")

dataList = []
displayList = []
# graphicList = []
displayLimit = 20
manulSaveFlag = False


# graphicLimit = 20


class MainWindow(QDialog, Ui_MainWindow):
    """
    UI界面，主窗口
    """

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/icon/picture/icon.ico"))

        self.spThread = ""
        self.autoSaveThread = ""
        self.upDateFlag = False
        self.serialPort = ""

        self.startSample.clicked.connect(self.start_sample)
        self.stopSample.clicked.connect(self.stop_sample)
        self.openPathButton.clicked.connect(self.get_save_path)
        self.saveManul.clicked.connect(self.save_manul)
        self.cleanDataDisplay.clicked.connect(self.clean_data_display)

        self.figure_show = FigureShow()
        self.figure_show.plot()
        # self.line = self.figure_show.get_line()
        self.graphic_scene = QGraphicsScene()
        self.graphic_scene.addWidget(self.figure_show)
        self.graphicsDisplay.setScene(self.graphic_scene)
        # self.graphicsDisplay.fitInView()
        self.graphicsDisplay.show()
        self.ani = FuncAnimation(self.figure_show.figure, self.update_plot, interval=1000, blit=False)
        # self.updateThread = UpDataThread(self.figure_show, updateTime=1000)
        # self.updateThread.start()

    def start_sample(self):
        baudrate = self.baudRateSelect.currentText()
        sampleTime = self.sampleTime.text()
        saveCount = self.count.currentText()
        comIndex = self.comSelect.currentIndex()
        try:
            sampleTime = int(sampleTime)
            baudrate = int(baudrate)
            saveCount = int(saveCount)
            if baudrate != 9600:
                msg_box = QMessageBox()
                msg_box.warning(self, "提示", "波特率需9600", QMessageBox.Ok)
                return 0
        except:
            msg_box = QMessageBox()
            msg_box.warning(self, "提示", "请填入整数", QMessageBox.Ok)
            return 0

        try:
            if not self.spThread.isRunning():
                self.serialPort = SerialPort.open_port(comIndex, baudrate)
                if not self.serialPort:
                    msg_box = QMessageBox()
                    msg_box.warning(self, "提示", "打开串口失败", QMessageBox.Ok)
                    return 0
                self.spThread = SerialPortThread(sampleTime, self.serialPort)
                self.spThread.get_data_signal.connect(self.display_text)
                self.spThread.start()

                self.autoSaveThread = SaveThread(self.savePath.currentText(), saveCount)
                self.autoSaveThread.save_error_flag.connect(self.save_error_box)
                self.autoSaveThread.start()
        except:
            if self.serialPort == "" or self.serialPort is False:
                self.serialPort = SerialPort.open_port(comIndex, baudrate)
            elif not self.serialPort.is_open:
                self.serialPort = SerialPort.open_port(comIndex, baudrate)
            if not self.serialPort:
                msg_box = QMessageBox()
                msg_box.warning(self, "提示", "打开串口失败.", QMessageBox.Ok)
                return 0
            self.spThread = SerialPortThread(sampleTime, self.serialPort)
            self.spThread.get_data_signal.connect(self.display_text)
            self.autoSaveThread = SaveThread(self.savePath.currentText(), saveCount)
            self.autoSaveThread.save_error_flag.connect(self.save_error_box)
            self.spThread.start()
            self.autoSaveThread.start()

        self.spThread.sampleFlag = True
        self.autoSaveThread.sampleFlag = True
        print("采样开始：", self.spThread.isRunning())

    def stop_sample(self):
        try:
            self.spThread.quitFlag = True
            self.autoSaveThread.quitFlag = True
            time.sleep(0.2)
            self.serialPort.close()
            # print(self.spThread.isFinished())
        except:
            msg_box = QMessageBox()
            msg_box.warning(self, "警告", "没有开始采集", QMessageBox.Ok)

    def display_text(self):

        global displayList
        string = ""
        for i in range(len(displayList) - 1, -1, -1):
            string = string + displayList[i][0] + '\t' + "%.3f ppm" % displayList[i][1] + '\n'
        self.textDisplay.setText(string)

    def update_plot(self, frame):
        global displayList
        y = []
        for i in displayList:
            y.append(i[1])
        x = list(range(len(displayList)))
        ln = self.figure_show.axes.lines
        ln[0].set_data(x, y)
        # self.figure_show.axes.plot(y)

    def clean_data_display(self):
        global displayList
        displayList = []
        self.textDisplay.setText("")

    def get_save_path(self):
        get_dir = QFileDialog()
        path = get_dir.getExistingDirectory(self, "选择保存文件夹", "./", options=QFileDialog.ShowDirsOnly)
        self.savePath.setCurrentText(path)
        # print(path)

    def save_manul(self):
        try:
            self.autoSaveThread.manulSaveFlag = True
        except:
            msg_box = QMessageBox()
            msg_box.warning(self, "提示", "保存错误，请先开始采样", QMessageBox.Ok)

    def save_error_box(self):
        msg_box = QMessageBox()
        msg_box.warning(self, "提示", "保存错误，检查保存路径文件是否损坏或被占用", QMessageBox.Ok)


class FigureShow(FigureCanvasQTAgg):
    def __init__(self, parent=None, figureSize=(5, 3), dpi=100):
        """
        内部显示figure
        :param parent: none
        :param figureSize: none
        :param dpi: none
        """
        fig = Figure(figsize=figureSize, dpi=dpi)
        super(FigureShow, self).__init__(fig)
        self.setParent(parent)
        self.axes = fig.add_subplot(111)
        self.axes.set_xlim(0, displayLimit)
        self.axes.set_ylim(0, 2000)
        self.axes.set_ylabel("Concentration(ppm)")

    def plot(self):
        self.axes.plot([], [], color='r')


class UpDataThread(QThread):
    def __init__(self, fig, updateTime):
        super(UpDataThread, self).__init__()
        self.fig_show = fig
        self.updateTime = updateTime

    def run(self):
        ani = FuncAnimation(self.fig_show.figure, self.update_plot, interval=self.updateTime)

    def update_plot(self, frame):
        global displayList
        y = []
        for i in displayList:
            y.append(i[1])
        x = list(range(len(displayList)))
        ln = self.fig_show.axes.lines
        ln[0].set_data(x, y)


class SerialPortThread(QThread):
    get_data_signal = pyqtSignal()

    def __init__(self, sampleTime, sp):
        """
        串口数据采集线程
        :param sampleTime: 采样时间
        :param sp: 打开的串口类
        """
        super(SerialPortThread, self).__init__()
        self.sampleTime = sampleTime
        self.sp = sp
        self.sampleFlag = False
        self.quitFlag = False

    def run(self):
        global dataList
        global displayList
        # global graphicList
        # global graphicLimit
        global displayLimit
        old_time = datetime.datetime.now()
        if self.sampleFlag:
            ppm = SerialPort.send_and_receive(sp=self.sp)
            dataList.append([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%.3f' % ppm])
        self.get_data_signal.emit()
        while True:
            error = time_delta(old_time)
            if error > self.sampleTime:
                if self.sampleFlag:
                    ppm = SerialPort.send_and_receive(sp=self.sp)
                    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    dataList.append([now_time, '%.3f' % ppm])
                    if len(displayList) <= displayLimit:
                        displayList.append([now_time, ppm])
                    else:
                        mid = displayList[1:]
                        displayList = mid + [[now_time, ppm]]
                    # if len(graphicList) <= graphicLimit:
                    #     graphicList.append(ppm)
                    # else:
                    #     mid = graphicList[1:]
                    #     graphicList = mid + [ppm]
                    self.get_data_signal.emit()
                old_time = old_time + datetime.timedelta(seconds=self.sampleTime / 1000.0)
            if self.quitFlag:
                break


class SaveThread(QThread):
    save_error_flag = pyqtSignal()

    def __init__(self, path, saveCount=20):
        """
        数据保存线程
        :param path: 保存路劲
        :param saveCount: 自动保存间隔数据数
        """
        super(SaveThread, self).__init__()
        self.path = path
        self.saveCount = saveCount
        self.sampleFlag = False
        self.quitFlag = False
        self.manulSaveFlag = False

    def run(self):
        global dataList
        while True:
            if self.sampleFlag:
                try:
                    if len(dataList) > self.saveCount:
                        saveDataList = dataList
                        dataList = []
                        Saver.save_data(self.path, saveDataList)
                except:
                    try:
                        saveDataList = dataList
                        dataList = []
                        Saver.save_data("", saveDataList)
                    except:
                        self.save_error_flag.emit()
                        print("error")

            if self.manulSaveFlag:
                try:
                    saveDataList = dataList
                    dataList = []
                    Saver.save_data(self.path, saveDataList)
                except:
                    try:
                        saveDataList = dataList
                        dataList = []
                        Saver.save_data("", saveDataList)
                    except:
                        self.save_error_flag.emit()
                        print("error")
                self.manulSaveFlag = False
            if self.quitFlag:
                break


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
