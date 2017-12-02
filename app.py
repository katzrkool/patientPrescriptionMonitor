from PyQt5.QtWidgets import (QMainWindow, QApplication, QLabel, QGroupBox, QDesktopWidget, QLineEdit, QPushButton,
                             QProgressBar, QInputDialog, QFileDialog, QCheckBox, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, QCoreApplication, pyqtSlot, Qt
import scraper
import sys
import time
import json
import os
from pathlib import Path

# TODO windows https://github.com/kybu/headless-selenium-for-win

class application(QMainWindow):

    prefs = {}
    defaultValues = {
        "username": "",
        "password": ""
    }

    def __init__(self):
        super().__init__()

        self.mainPage = QGroupBox()

        self.saveLogin = False;

        self.fetchPrefs()

        self.initUI()
        self.pop = None

    def fetchPrefs(self):
        try:
            with open("preferences.json") as f:
                self.prefs = json.load(f)
                if len(self.prefs["username"]) > 0 and len(self.prefs["password"]) > 0:
                    self.toggleLogin(Qt.Checked)
        except:
            self.prefs.update(self.defaultValues)

    def initUI(self):
        mainPage = self.mainPage
        mainPage.setStyleSheet("QGroupBox {background-image: url(img/background.png); margin: -5px;}")

        mainPage.usernameLabel = QLabel("Username:", mainPage)
        mainPage.usernameLabel.move(125, 100)

        mainPage.usernameInput = QLineEdit(mainPage)
        mainPage.usernameInput.move(225, 100)
        mainPage.usernameInput.resize(150, 20)
        mainPage.usernameInput.setText(self.prefs["username"])

        mainPage.passwordLabel = QLabel("Password:", mainPage)
        mainPage.passwordLabel.move(125, 150)

        mainPage.passwordInput = QLineEdit(mainPage)
        mainPage.passwordInput.move(225, 150)
        mainPage.passwordInput.resize(150, 20)
        mainPage.passwordInput.setEchoMode(QLineEdit.Password)
        mainPage.passwordInput.setText(self.prefs["password"])
        mainPage.passwordInput.returnPressed.connect(self.runScraper)

        mainPage.saveLogin = QCheckBox("Save Login", mainPage)
        if self.saveLogin:
            mainPage.saveLogin.setCheckState(Qt.Unchecked)
        else:
            mainPage.saveLogin.setCheckState(Qt.Checked)
        mainPage.saveLogin.move(400, 150)
        mainPage.saveLogin.toggle()
        mainPage.saveLogin.stateChanged.connect(self.toggleLogin)

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
        mainPage.status.setAlignment(Qt.AlignCenter)

        mainPage.progressBar = QProgressBar(mainPage)
        mainPage.progressBar.move(125, 250)
        mainPage.progressBar.resize(350, 15)

        mainPage.setFixedSize(600,400)
        self.center()

        mainPage.setWindowTitle("CheckNarc")
        self.mainPage.show()

    def toggleLogin(self, state):
        if state == Qt.Checked:
            self.saveLogin = True
        else:
            self.saveLogin = False

    @pyqtSlot(str)
    def setStatus(self, status):
        self.mainPage.status.setText(status)
        if status == "Incorrect Login":
            alert = QMessageBox()
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Incorrect Login!")
            alert.setStandardButtons(QMessageBox.Ok)
            alert.exec_()
            self.mainPage.passwordInput.setText("")

    @pyqtSlot(int)
    def updateProgress(self, value):
        self.mainPage.progressBar.setValue(value)

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)

        self.move(qr.topLeft())


    def runScraper(self,):

        username = self.mainPage.usernameInput.text()
        password = self.mainPage.passwordInput.text()

        if len(username) + len(password) == 0:
            self.setStatus("Please enter a username and password!")
            alert = QMessageBox()
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Please enter a username and password!")
            alert.setStandardButtons(QMessageBox.Ok)
            alert.exec_()
            return False
        elif len(username) == 0:
            self.setStatus("Please enter a username!")
            alert = QMessageBox()
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Please enter a username!")
            alert.setStandardButtons(QMessageBox.Ok)
            alert.exec_()
            return False
        elif len(password) == 0:
            self.setStatus("Please enter a password!")
            alert = QMessageBox()
            alert.setIcon(QMessageBox.Critical)
            alert.setText("Please enter a password!")
            alert.setStandardButtons(QMessageBox.Ok)
            alert.exec_()
            return False

        overwrite = False
        if self.saveLogin:
            try:
                with open("preferences.json") as f:
                    data = json.load(f)
                    if data["username"] != username or data["password"] != password:
                        overwrite = True
            except:
                overwrite = True
            finally:
                if overwrite == True:
                    with open("preferences.json", "w") as fp:
                        json.dump({"username": username, "password": password}, fp)

        else:
            try:
                os.remove("preferences.json")
            except:
                pass


        self.setStatus("Pick a file to read from")
        pickFile = QMessageBox()
        pickFile.setIcon(QMessageBox.Question)
        pickFile.setText("Please pick a csv file to get patient names from.")
        pickFile.setStandardButtons(QMessageBox.Ok)
        pickFile.exec_()

        fname = QFileDialog.getOpenFileName(self, 'Open file', str(Path.home()), "CSV (*.csv)")
        if len(fname[0]) > 0:
            self.csvFile = fname[0]
        else:
            self.setStatus("Cancelled")
            return False

        self.setStatus("Pick a folder to save in.")
        pickFolder = QMessageBox()
        pickFolder.setIcon(QMessageBox.Question)
        pickFolder.setText("Please pick a folder to save screenshots in.")
        pickFolder.setStandardButtons(QMessageBox.Ok)
        pickFolder.exec_()

        saveLoc = QFileDialog.getExistingDirectory(self, 'Save Location', str(Path.home()))
        self.saveLoc = saveLoc
        if len(saveLoc[0]) > 0:
            self.csvFile = fname[0]
        else:
            self.setStatus("Cancelled")
            return False

        self.sr = scrapeRemote(username, password, self.csvFile, self.saveLoc)

        self.mainPage.progressBar.setValue(0)

        self.sr.status.connect(self.setStatus)
        self.sr.progress.connect(self.updateProgress)
        self.sr.masterList.connect(self.asker)
        self.mainPage.cancel.clicked.connect(self.sr.stop)

        self.sr.start()

    @pyqtSlot(list)
    def asker(self, masterList):
            self.setStatus("Please select a Master Account")
            asker = QInputDialog.getItem(self, "Master Account Selection", "Pick a Master Account to use", masterList, 0, False)
            self.sr.setMaster([i for i, x in enumerate(masterList) if x == asker[0]][0])
            self.setStatus("Preparing to Download")

class scrapeRemote(QThread):
    progress = pyqtSignal(int, name="Updated Progress")
    status = pyqtSignal(str, name="Status")
    masterList = pyqtSignal(list, name="Master Account Choices")

    def __init__(self, username, password, csvFile, saveLoc, parent=None):
        super(scrapeRemote, self).__init__(parent)
        self.username = username
        self.password = password
        self.csvFile = csvFile
        self.saveLoc = saveLoc
        self._isRunning = True
        self.partTwo = False

    def run(self):
        self.status.emit("Initializing")
        if scraper.initSession(self.username, self.password, self.csvFile) == False:
            scraper.killTheBrowser()
            self.status.emit("Incorrect Login")
            self._isRunning = False
            self.partTwo = True

        if self.partTwo == False:
            masterAccounts = scraper.getMasterAccounts()
            if masterAccounts != False:
                self.masterList.emit(masterAccounts)
            else:
                self.status.emit("Incorrect Login Credentials! Try Again")
                scraper.killTheBrowser()
                self._isRunning = False
                self.partTwo = True
        while self.partTwo == False:
            time.sleep(0.1)
        if self._isRunning:
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

    def setMaster(self, master):
        self.masterChoice = master
        self.partTwo = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ct = application()
    sys.exit(app.exec_())
