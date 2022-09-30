
#이마이카나성우기원

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, QTime, Qt, QEventLoop
from PyQt5.QtGui import QIcon
import requests,re
import pandas as pd
from gtts import gTTS
from playsound import playsound
bstop = ''
selstop = []


class MainWindow(QWidget):
    
    def __init__(self):
        global bstop, selstop
        self.key='Cp3kRtnkoRgEPXMSK65TjzIV+BoUmqc/0ARtjUjeovb8Qd5kxqn76oCModae8nTAnYAHBfLcXE9iwyWBFyk7UQ=='
        self.url0 = 'http://apis.data.go.kr/6260000/BusanBIMS/busStopList'
        self.timeron = 0
        super().__init__()
        self.timer = QTimer(self)
        self.setWindowTitle('BUSanBIS')
        self.setGeometry(100, 100, 640, 480)
        self.label1 = QLabel('정류장명을 입력해 주세요:', self)
        self.label1.setAlignment(Qt.AlignCenter)
        self.label2 = QLabel('현재 선택된 정류장:')
        self.label2.setAlignment(Qt.AlignCenter)

        self.bstopin = QLineEdit(self)
        self.bstopin.textChanged.connect(self.onChanged)

        self.pbar = QProgressBar(self)
        self.pbar.setValue(0)
        self.pbar.setFormat("")

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(64)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setHorizontalHeaderLabels(['번호', '도착시간', '다음 도착시간'])

        layout = QVBoxLayout()
        subLayout = QHBoxLayout()


        self.set = QPushButton()
        self.set.setText('검색(&S)')
        self.set.pressed.connect(self.submit)

        subLayout.addStretch(1)
        subLayout.addWidget(self.label1)
        subLayout.addWidget(self.bstopin)
        subLayout.addWidget(self.set)
        subLayout.addStretch(1)
        layout.addLayout(subLayout)
        layout.addWidget(self.label2)
        layout.addWidget(self.tableWidget)
        layout.addWidget(self.pbar)
 
        self.setLayout(layout)

    def onChanged(self, text):
        global bstop
        bstop = text

    def submit(self):
        self.timer.stop()
        self.pbar.setMaximum(0)
        if not bstop:
            nostop = QMessageBox.warning(self, '정류장명 없음', '정류장명을 입력해 주세요.', QMessageBox.Ok, QMessageBox.Ok)
        else:
            self.tableWidget.clear()
            self.dialog = SelDialog(self)
            self.dialog.setAttribute(Qt.WA_DeleteOnClose)
            loop = QEventLoop()
            self.dialog.destroyed.connect(loop.quit)
            loop.exec()
            print(selstop)
            self.pbar.setMaximum(15)
            self.label2.setText('현재 선택된 정류장:%s(%s)'%(selstop[1], selstop[2]))
            self.aftersel()
            if self.timeron == 0:
                self.loopreset()
            self.timer.start(1000)

    def aftersel(self):
        url = 'http://apis.data.go.kr/6260000/BusanBIMS/stopArrByBstopid'
        params ={'serviceKey' : self.key, 'bstopid' : selstop[0] }
        response = requests.get(url, params=params)
        result = response.content
        result = bytes.decode(result)
        #print(result)
        p = re.compile( '<item>.*?</item>' , re.DOTALL )
        p1 = re.compile( r'<lineno>((?:[가-힣]+)?\d+(?:-1)?(?:-2)?(?:A)?(?:\(A\))?(?:\(심야\))?)?</lineno>' )
        p2 = re.compile( r'<min1>(\d+)</min1>' )
        p3 = re.compile( r'<min2>(\d+)</min2>' )
        m = p.findall(result)

        m1=[]


        for i in m :
            if p2.findall(i):
                if p3.findall(i):
                    m1.append([p1.findall(i)[0], p2.findall(i)[0], p3.findall(i)[0]])
                else:
                    m1.append( [p1.findall(i)[0], p2.findall(i)[0], ''] )
            else:
                m1.append( [p1.findall(i)[0], '', ''] )
        
        for i in m1 :
            i[1] = int(i[1]) if i[1] else 1000
            i[2] = int(i[2]) if i[2] else 1000
            i[0] = '88' if i[0] == '88(A)' else i[0]
            i[0] = '88-1' if i[0] == '88-1A' else i[0]
        self.df = pd.DataFrame (m1, columns = ['번호', '도착시간1', '도착시간2'])
        self.df = self.df.sort_values('도착시간1', ascending=True)
        self.df = self.df.transpose()
        self.df = self.df.to_dict()
        #print(self.df)
        self.j = 0
        for i in self.df.values():
            self.tableWidget.setItem(self.j, 0, QTableWidgetItem(str(i['번호'])))
            self.j += 1
        self.j = 0
        for i in self.df.values():
            if i['도착시간1'] != 1000:
                self.tableWidget.setItem(self.j, 1, QTableWidgetItem(str(i['도착시간1'])+'분'))
            elif i['도착시간1'] == 1:
                self.tableWidget.setItem(self.j, 1, QTableWidgetItem(''))
            else:
                self.tableWidget.setItem(self.j, 1, QTableWidgetItem('도착정보 없음'))
            self.j += 1
        self.j = 0
        for i in self.df.values():
            if i['도착시간2'] != 1000:
                self.tableWidget.setItem(self.j, 2, QTableWidgetItem(str(i['도착시간2'])+'분'))
            else:
                self.tableWidget.setItem(self.j, 2, QTableWidgetItem('도착정보 없음'))
            self.j += 1
    def loopreset(self):
        self.timeron = 1
        self.time = 0
        self.pbar.setFormat("%d초 후 갱신"%(15-self.time))
        self.timer.timeout.connect(self.afterloop)
        self.timer.start(1000)
            

    def afterloop(self):
        self.soon = []
        self.j = 0
        for i in self.df.values():
            if i['도착시간1'] == 1:
                self.soon.append(i['번호'])
                if self.time % 2 == 0:
                    self.tableWidget.setItem(self.j, 1, QTableWidgetItem('잠시 후 도착'))
                else:
                    self.tableWidget.setItem(self.j, 1, QTableWidgetItem(''))
            self.j += 1
        print(self.soon)
        self.time += 1
        self.pbar.setValue(self.time)
        self.pbar.setFormat("%d초 후 갱신"%(15-self.time))
        if self.time == 15:
            self.aftersel()
            self.time = 0

class SelDialog(QWidget):
    def __init__(self,parent):
        super(SelDialog, self).__init__()
        global bstop, selstop
        self.setWindowTitle('정류장 선택')
        self.setGeometry(120, 120, 640, 10)
        self.key='Cp3kRtnkoRgEPXMSK65TjzIV+BoUmqc/0ARtjUjeovb8Qd5kxqn76oCModae8nTAnYAHBfLcXE9iwyWBFyk7UQ=='
        self.url0 = 'http://apis.data.go.kr/6260000/BusanBIMS/busStopList'
        
        self.initUI()

    def initUI(self):
        global bstop, selstop
        self.params0 ={'serviceKey' : self.key, 'pageNo' : '1', 'numOfRows' : '10000', 'bstopnm' : bstop }
        self.response0 = requests.get(self.url0, params=self.params0)
        self.result0 = self.response0.content
        self.result0 = bytes.decode(self.result0)
        #print(self.result0)

        self.p = re.compile( '<item>.*?</item>' , re.DOTALL ) #각각의 항목을 분리
        self.p01 = re.compile( r'<bstopid>(\d+)</bstopid>' )
        self.p02 = re.compile( r'<bstopnm>(.+)</bstopnm>' )
        self.p03 = re.compile( r'<arsno>(\d+)</arsno>' )
        self.p0 = re.compile( r'<bstopid>.*?</arsno>' , re.DOTALL )
        self.m0 = self.p0.findall(self.result0)
        self.m01=[]
        
        for i in self.m0 :
            self.m01.append( [self.p01.findall(i)[0],self.p02.findall(i)[0], self.p03.findall(i)[0]] )
        
        if self.m01:
            #print(self.m01)
            layout = QVBoxLayout()
            self.rbtns = []
            self.selbtn = 0
            for i in range(len(self.m01)):
                self.rbtns.append(QRadioButton('%s(%s)'%(self.m01[i][1], self.m01[i][2]), self))
                self.rbtns[i].move(10, 10+10*i)
            for i in self.rbtns:
                layout.addWidget(i)
        

            self.submitbtn = QPushButton('확인(&C)')
            self.submitbtn.pressed.connect(self.submit)

            layout.addWidget(self.submitbtn)
            self.setLayout(layout)
            self.show()
        else:
            nostop = QMessageBox.critical(self, '정류장 없음', '해당하는 정류장이 없습니다.', QMessageBox.Ok, QMessageBox.Ok)

    def submit(self):
        global selstop
        for i in range(len(self.rbtns)):
            if self.rbtns[i].isChecked():
                selstop = self.m01[i]
                #print(selstop)
                self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MainWindow()
    myWindow.show()
    sys.exit(app.exec_())

    #이마이카나성우기원