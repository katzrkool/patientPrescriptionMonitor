import datetime
import urllib

import pandas as pd

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

# TODO windows https://github.com/kybu/headless-selenium-for-win

# Initializing browsers and virtual displays
try:
    def setup():
        global driver
        global date

        # Display(visible=0, size=(1920, 1080)).start()
        # driver = webdriver.Firefox()
        # driver.set_window_size(1920, 1080)
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(chrome_options=options)
        driver.set_window_size(1920, 1080)

        # Getting date 100 days back
        date = (datetime.datetime.today().date() - datetime.timedelta(days=100)).strftime("%m/%d/%Y")
        date = str(date)


    # Goes to the login site and authenticates
    def pushTheButton(username, password):
        driver.get("https://arkansas.pmpaware.net/login")

        usernameCenter = driver.find_element_by_id("auth_key")
        usernameCenter.send_keys(username)

        passwordCenter = driver.find_element_by_id("password")
        passwordCenter.send_keys(password)

        buttonCenter = driver


    def fetchData(csvLocation):
        global lastNames
        global firstNames
        global dob

        # grabs the patient data
        data = pd.read_csv(csvLocation)

        # renames columns so python can read it
        data = data.rename(
            columns={'Patient Last Name': 'Patient_Last_Name', 'Patient First Name': 'Patient_First_Name',
                     "Patient DOB": "Patient_DOB"})

        # grabs data
        lastNames = list(data.Patient_Last_Name)
        firstNames = list(data.Patient_First_Name)
        dob = list(data.Patient_DOB)


    def getMasterAccounts():
        driver.get("https://arpmp-ph.hidinc.com/arappl/bdarpdmq/pmqrecipqry.html?a=0&page=recipqry&accept-box=yes")

        if len(driver.find_elements_by_id("suplist")) > 0:
            masterList = Select(driver.find_element_by_id("suplist"))
            masterOptions = masterList.options
            for i in range(0, len(masterOptions)):
                masterOptions[i] = masterOptions[i].text
            return masterOptions
        else:
            return False


    def downloadData(date, lastName, firstName, dob):

        # formats the date of birth so the website will take it
        dob = datetime.datetime.strptime(dob, "%m/%d/%Y")
        dob = dob.date().strftime("%m/%d/%Y")

        driver.get("https://arpmp-ph.hidinc.com/arappl/bdarpdmq/pmqrecipqry.html?a=0&page=recipqry&accept-box=yes")

        # fills in boxes with patient names
        lastNameBox = driver.find_element_by_id("recip-name")
        lastNameBox.send_keys(lastName)

        firstNameBox = driver.find_element_by_id("recip-fname")
        firstNameBox.send_keys(firstName)

        dobBox = driver.find_element_by_id("recip-dob")
        dobBox.send_keys(dob)

        beginDate = driver.find_element_by_id("disp-bdate")
        beginDate.clear()
        beginDate.send_keys(date)

        # checks for master account; if exists, it asks user which one to use, then selects it
        if len(driver.find_elements_by_id("suplist")) > 0:
            masterList = Select(driver.find_element_by_id("suplist"))
            masterOptions = masterList.options
            global masterChoice
            masterAccount = masterOptions[masterChoice]
            masterAccount.click()

        # selects next button twice, one for each page
        submitButton = driver.find_element_by_xpath("//button[@type='submit']")
        submitButton.click()

        submitButton = driver.find_element_by_xpath("//button[@type='submit']")
        submitButton.click()

        # grabs first inital
        firstInitial = firstName[:1]
        fileName = lastName + firstInitial

        global saveLoc
        # now that we are on the prescription page, we take a screenshot
        driver.get_screenshot_as_file("{}/{}.png".format(saveLoc, fileName))
        return lastName


    def killTheBrowser():
        driver.quit()


    def initSession(username, password, csvFile):
        setup()
        pushTheButton(username, password)
        fetchData(csvFile)


    def setMasterAccount(choice):
        global masterChoice
        masterChoice = choice

    def setSaveLocation(choice):
        global saveLoc
        saveLoc = choice

except:
    driver.quit()
