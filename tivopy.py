#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

from PyQt5.QtCore import QDir, QPoint, QProcess, QSize, Qt, QTime, QUrl
from PyQt5.QtGui import QIcon, QKeySequence, QStandardItem, QStandardItemModel
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QFrame, QHBoxLayout,
                             QLineEdit, QListView, QMenu, QMessageBox,
                             QPushButton, QShortcut, QSizePolicy, QSlider,
                             QStyle, QVBoxLayout, QWidget)


class VideoPlayer(QWidget):

    def __init__(self, aPath, parent=None):
        super(VideoPlayer, self).__init__(parent)

        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAcceptDrops(True)
        
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.mediaPlayer.setVolume(80)
        
        self.videoWidget = QVideoWidget(self)
        self.videoWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.videoWidget.setMinimumSize(QSize(640, 360))
        
        self.lbl = QLineEdit('00:00:00')
        self.lbl.setReadOnly(True)
        self.lbl.setFixedWidth(70)
        self.lbl.setUpdatesEnabled(True)
        self.lbl.setStyleSheet(stylesheet(self))

        self.elbl = QLineEdit('00:00:00')
        self.elbl.setReadOnly(True)
        self.elbl.setFixedWidth(70)
        self.elbl.setUpdatesEnabled(True)
        self.elbl.setStyleSheet(stylesheet(self))

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setFixedWidth(32)
        self.playButton.setStyleSheet("background-color: black")
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal, self)
        self.positionSlider.setStyleSheet(stylesheet(self))
        self.positionSlider.setRange(0, 100)
        self.positionSlider.sliderMoved.connect(self.setPosition)
        self.positionSlider.sliderMoved.connect(self.handleLabel)
        self.positionSlider.setSingleStep(2)
        self.positionSlider.setPageStep(20)
        self.positionSlider.setAttribute(Qt.WA_TranslucentBackground, True)

        self.clip = QApplication.clipboard()
        self.process = QProcess(self)
        self.process.readyRead.connect(self.dataReady)
        self.process.finished.connect(self.playFromURL)

        self.myurl = ""

        # channel list
        self.channelList = QListView(self)
        self.channelList.setMinimumSize(QSize(150, 0))
        self.channelList.setMaximumSize(QSize(150, 4000))
        self.channelList.setFrameShape(QFrame.Box)
        self.channelList.setObjectName("channelList")
        self.channelList.setStyleSheet("background-color: black; color: #585858;")
        self.channelList.setFocus()
        # for adding items to list must create a model
        self.model = QStandardItemModel()
        self.channelList.setModel(self.model)

        self.controlLayout = QHBoxLayout()
        self.controlLayout.setContentsMargins(5, 0, 5, 0)
        self.controlLayout.addWidget(self.playButton)
        self.controlLayout.addWidget(self.lbl)
        self.controlLayout.addWidget(self.positionSlider)
        self.controlLayout.addWidget(self.elbl)

        self.mainLayout = QHBoxLayout()

        # contains video and cotrol widgets to the left side
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.videoWidget)
        self.layout.addLayout(self.controlLayout)
        
        # adds channels list to the right
        self.mainLayout.addLayout(self.layout)
        self.mainLayout.addWidget(self.channelList)

        self.setLayout(self.mainLayout)

        self.myinfo = "©2020\nTIVOpy v1.0"

        self.widescreen = True

        #### shortcuts ####
        self.shortcut = QShortcut(QKeySequence("q"), self)
        self.shortcut.activated.connect(self.handleQuit)
        self.shortcut = QShortcut(QKeySequence("u"), self)
        self.shortcut.activated.connect(self.playFromURL)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self.shortcut.activated.connect(self.play)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_F), self)
        self.shortcut.activated.connect(self.handleFullscreen)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_Escape), self)
        self.shortcut.activated.connect(self.exitFullscreen)
        self.shortcut.activated.connect(self.handleFullscreen)
        self.shortcut = QShortcut(QKeySequence("i"), self)
        self.shortcut.activated.connect(self.handleInfo)
        self.shortcut = QShortcut(QKeySequence("s"), self)
        self.shortcut.activated.connect(self.toggleSlider)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_Right), self)
        self.shortcut.activated.connect(self.forwardSlider)
        self.shortcut = QShortcut(QKeySequence(Qt.Key_Left), self)
        self.shortcut.activated.connect(self.backSlider)

        self.mediaPlayer.setVideoOutput(self.videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.positionChanged.connect(self.handleLabel)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        self.populateChannelList()
        self.selectChannel()
        self.initialPlay()

    def playFromURL(self):
        self.mediaPlayer.pause()
        self.myurl = self.clip.text()
        self.mediaPlayer.setMedia(QMediaContent(QUrl(self.myurl)))
        self.playButton.setEnabled(True)
        self.mediaPlayer.play()
        self.hideSlider()
        print(self.myurl)

    def dataReady(self):
        self.myurl = str(self.process.readAll(), encoding='utf8').rstrip()  ###
        self.myurl = self.myurl.partition("\n")[0]
        print(self.myurl)
        self.clip.setText(self.myurl)
        self.playFromURL()

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)
        mtime = QTime(0, 0, 0, 0)
        mtime = mtime.addMSecs(self.mediaPlayer.duration())
        self.elbl.setText(mtime.toString())

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        print("Error: ", self.mediaPlayer.errorString())

    def handleQuit(self):
        self.mediaPlayer.stop()
        print("Goodbye ...")
        app.quit()

    def contextMenuRequested(self, point):
        menu = QMenu()
        actionURL = menu.addAction(QIcon.fromTheme("browser"), "URL from Clipboard (u)")
        menu.addSeparator()
        actionToggle = menu.addAction(QIcon.fromTheme("next"), "Show / Hide Channels (s)")
        actionFull = menu.addAction(QIcon.fromTheme("view-fullscreen"), "Fullscreen (f)")
        menu.addSeparator()
        actionInfo = menu.addAction(QIcon.fromTheme("help-about"), "About (i)")
        menu.addSeparator()
        actionQuit = menu.addAction(QIcon.fromTheme("application-exit"), "Exit (q)")

        actionQuit.triggered.connect(self.handleQuit)
        actionFull.triggered.connect(self.handleFullscreen)
        actionInfo.triggered.connect(self.handleInfo)
        actionToggle.triggered.connect(self.toggleSlider)
        actionURL.triggered.connect(self.playFromURL)
        menu.exec_(self.mapToGlobal(point))

    def wheelEvent(self, event):
        mscale = event.angleDelta().y() / 13
        self.mediaPlayer.setVolume(self.mediaPlayer.volume() + mscale)
        print("Volume: " + str(self.mediaPlayer.volume()))

    def mouseDoubleClickEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.handleFullscreen()

    def handleFullscreen(self):
        if self.windowState() and Qt.WindowFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()

    def exitFullscreen(self):
        self.showNormal()

    def handleInfo(self):
        QMessageBox.about(self, "About", self.myinfo)

    def toggleSlider(self):
        if self.positionSlider.isVisible():
            self.hideSlider()
        else:
            self.showSlider()

    def hideSlider(self):
        self.channelList.hide()
        self.playButton.hide()
        self.lbl.hide()
        self.positionSlider.hide()
        self.elbl.hide()

    def showSlider(self):
        self.channelList.show()
        self.playButton.show()
        self.lbl.show()
        self.positionSlider.show()
        self.elbl.show()
        self.channelList.setFocus()

    def forwardSlider(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() + 1000 * 60)

    def backSlider(self):
        self.mediaPlayer.setPosition(self.mediaPlayer.position() - 1000 * 60)

    def volumeUp(self):
        self.mediaPlayer.setVolume(self.mediaPlayer.volume() + 10)
        print("Volume: " + str(self.mediaPlayer.volume()))

    def volumeDown(self):
        self.mediaPlayer.setVolume(self.mediaPlayer.volume() - 10)
        print("Volume: " + str(self.mediaPlayer.volume()))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        elif event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        print("drop")
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0].toString()
            print("url = ", url)
            self.mediaPlayer.stop()
            self.mediaPlayer.setMedia(QMediaContent(QUrl(url)))
            self.playButton.setEnabled(True)
            self.mediaPlayer.play()
        elif event.mimeData().hasText():
            mydrop = event.mimeData().text()
            print("generic url = ", mydrop)
            self.mediaPlayer.setMedia(QMediaContent(QUrl(mydrop)))
            self.playButton.setEnabled(True)
            self.mediaPlayer.play()
            self.hideSlider()

    def loadFilm(self, f):
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(f)))
        self.playButton.setEnabled(True)
        self.mediaPlayer.play()

    def populateChannelList(self):
        # file must be in same directory as the script
        FILEPATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "canaletv.txt")
        # lines from file with "channel name" -- "link"
        channelArray = []
        # split file by line and adding it to the array
        with open(FILEPATH) as f:
            for line in f:
                channelArray.append(line.rstrip())
        # dictionary with key = channel name and value = link
        self.channelDict = dict(ch.split(" -- ") for ch in channelArray)
        for channel in self.channelDict.keys():
            item = QStandardItem(channel)
            self.model.appendRow(item)

    def selectedItemBehavior(self, index):
    # gets the link for the selected channel and plays it
        itms = self.channelList.selectedIndexes()
        for it in itms:
            channel = it.data()
            link = self.channelDict[channel]
            self.mediaPlayer.setMedia(QMediaContent(QUrl(link)))
            self.play()

    def selectChannel(self):
    # selecting channel from sidebar calls selectedItemBehavior
        self.selModel = self.channelList.selectionModel()
        self.selModel.selectionChanged.connect(self.selectedItemBehavior)

    def initialPlay(self):
    # play somenting when app opens
        self.mediaPlayer.setMedia(QMediaContent(QUrl("https://vid.hls.protv.ro/proxhdn/proxhd_3_34/index.m3u8?1")))
        self.play()

    def handleLabel(self):
        self.lbl.clear()
        mtime = QTime(0, 0, 0, 0)
        self.time = mtime.addMSecs(self.mediaPlayer.position())
        self.lbl.setText(self.time.toString())

def stylesheet(self):
    return """

QSlider::handle:horizontal 
{
background: transparent;
width: 8px;
}

QSlider::groove:horizontal {
border: 1px solid #444444;
height: 8px;
     background: qlineargradient(y1: 0, y2: 1,
                                 stop: 0 #2e3436, stop: 1.0 #000000);
}

QSlider::sub-page:horizontal {
background: qlineargradient( y1: 0, y2: 1,
    stop: 0 #729fcf, stop: 1 #2a82da);
border: 1px solid #777;
height: 8px;
}

QSlider::handle:horizontal:hover {
background: #2a82da;
height: 8px;
width: 8px;
border: 1px solid #2e3436;
}

QSlider::sub-page:horizontal:disabled {
background: #bbbbbb;
border-color: #999999;
}

QSlider::add-page:horizontal:disabled {
background: #2a82da;
border-color: #999999;
}

QSlider::handle:horizontal:disabled {
background: #2a82da;
}

QLineEdit
{
background: black;
color: #585858;
border: 0px solid #076100;
font-size: 8pt;
font-weight: bold;
}
    """


if __name__ == '__main__':

    app = QApplication(sys.argv)
    player = VideoPlayer('')
    player.setAcceptDrops(True)
    player.setWindowTitle("TIVOpy")
    player.setWindowIcon(QIcon.fromTheme("multimedia-video-player"))
    player.setGeometry(100, 300, 1366, 768)
    # player.setGeometry(50, 50, 640, 480)
    player.setContextMenuPolicy(Qt.CustomContextMenu)
    player.customContextMenuRequested[QPoint].connect(player.contextMenuRequested)
    player.show()
    if len(sys.argv) > 1:
        print(sys.argv[1])
        if sys.argv[1].startswith("http"):
            player.myurl = sys.argv[1]
            player.playFromURL()
        else:
            player.loadFilm(sys.argv[1])
sys.exit(app.exec_())
