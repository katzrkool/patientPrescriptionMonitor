from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QGroupBox, QDesktopWidget, QLineEdit, QPushButton,
                             QProgressBar, QInputDialog, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, QCoreApplication, pyqtSlot
import scraper
import sys


# TODO windows https://github.com/kybu/headless-selenium-for-win

class application(QMainWindow):
    def __init__(self):
        super().__init__()

        self.mainPage = QGroupBox()

        self.initUI()
        self.pop = None

    def initUI(self):
        mainPage = self.mainPage
        mainPage.setStyleSheet("QGroupBox {background-image: url(img/background.png); margin: -5px;}")

        mainPage.usernameLabel = QLabel("Username:", mainPage)
        mainPage.usernameLabel.move(125, 100)

        mainPage.usernameInput = QLineEdit(mainPage)
        mainPage.usernameInput.move(225, 100)
        mainPage.usernameInput.resize(150, 20)

        mainPage.passwordLabel = QLabel("Password:", mainPage)
        mainPage.passwordLabel.move(125, 150)

        mainPage.passwordInput = QLineEdit(mainPage)
        mainPage.passwordInput.move(225, 150)
        mainPage.passwordInput.resize(150, 20)
        mainPage.passwordInput.setEchoMode(QLineEdit.Password)
        mainPage.passwordInput.returnPressed.connect(self.runScraper)

        mainPage.submit = QPushButton("Submit", mainPage)
        mainPage.submit.resize(mainPage.submit.sizeHint())
        mainPage.submit.move(200, 200)
        mainPage.submit.clicked.connect(self.runScraper)

        mainPage.cancel = QPushButton("Cancel", mainPage)
        mainPage.cancel.resize(mainPage.submit.sizeHint())
        mainPage.cancel.move(300, 200)

        mainPage.status = QLabel("", mainPage)
        mainPage.status.move(150, 300)
        mainPage.status.resize(300,20)

        mainPage.progressBar = QProgressBar(mainPage)
        mainPage.progressBar.move(125, 250)
        mainPage.progressBar.resize(350, 15)

        mainPage.resize(600, 400)
        self.center()

        mainPage.setWindowTitle("Patient Prescription Monitor")
        self.mainPage.show()

    @pyqtSlot(str)
    def setStatus(self, status):
        self.mainPage.status.setText(status)

    @pyqtSlot(int)
    def updateProgress(self, value):
        self.mainPage.progressBar.setValue(value)

    def runScraper(self):
        self.setStatus("Pick a file to read from")
        fname = QFileDialog.getOpenFileName(self, 'Open file', "~")
        self.csvFile = fname[0]

        saveLoc = QFileDialog.getExistingDirectory(self, 'Save Location', "~")
        self.saveLoc = saveLoc

        self.mainPage.progressBar.setValue(0)

        username = self.mainPage.usernameInput.text()
        password = self.mainPage.passwordInput.text()

        self.setStatus("Initializing")

        self.sgm = scrapeGrabMaster(username, password, self.csvFile)
        self.sgm.masterList.connect(self.chooser)
        self.sgm.status.connect(self.setStatus)
        self.sgm.start(QThread.NormalPriority)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

        self.move(qr.topLeft())

    @pyqtSlot(list)
    def chooser(self, masterList):

        username = self.mainPage.usernameInput.text()
        password = self.mainPage.passwordInput.text()
        self.setStatus("Please select a Master Account")
        asker = QInputDialog.getItem(self, "Master Account Selection", "Pick a Master Account to use", masterList, 0, False)
        self.setStatus("Preparing to Download")
        self.sr = scrapeRemote(username, password, [i for i,x in enumerate(masterList) if x == asker[0]][0], self.csvFile, self.saveLoc)

        self.sr.status.connect(self.setStatus)
        self.sr.progress.connect(self.updateProgress)
        self.mainPage.cancel.clicked.connect(self.sr.stop)
        self.sr.start()

class scrapeRemote(QThread):
    progress = pyqtSignal(int, name="Updated Progress")
    goGoGo = False
    status = pyqtSignal(str, name="Status")

    def __init__(self, username, password, masterChoice, csvFile, saveLoc, parent=None):
        super(scrapeRemote, self).__init__(parent)
        self.username = username
        self.password = password
        self.masterChoice = masterChoice
        self.csvFile = csvFile
        self.saveLoc = saveLoc
        self._isRunning = True

    def run(self):
        scraper.initSession(self.username, self.password, self.csvFile)
        scraper.setSaveLocation(self.saveLoc)
        scraper.setMasterAccount(self.masterChoice)
        for i in range(0, len(scraper.lastNames)):
            QCoreApplication.processEvents()
            if self._isRunning:
                self.status.emit("Downloaded " + scraper.downloadData(scraper.date, scraper.lastNames[i], scraper.firstNames[i],
                                     scraper.dob[i]))
                self.progress.emit(int(((i + 1) * 100) / len(scraper.lastNames) - 1))
            else:
                scraper.killTheBrowser()
                self.status.emit("Canceled")
                break
        scraper.killTheBrowser()
        if self._isRunning:
            self.progress.emit(100)
            self.status.emit("Finished!")
    def stop(self):
        self._isRunning = False
        self.status.emit("Cancelling")

class scrapeGrabMaster(QThread):

    masterList = pyqtSignal(list, name="Master Account Choices")
    status = pyqtSignal(str, name = "Status change")

    def __init__(self, username, password, csvFile):
        super(scrapeGrabMaster, self).__init__()
        self.username = username
        self.password = password
        self.csvFile = csvFile

    def run(self):
        scraper.initSession(self.username, self.password, self.csvFile)
        masterAccounts = scraper.getMasterAccounts()
        scraper.killTheBrowser()
        if masterAccounts != False:
            self.masterList.emit(masterAccounts)
        else:
            self.status.emit("Incorrect Login Credentials! Try Again")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ct = application()
    sys.exit(app.exec_())
