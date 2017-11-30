import datetime
import time

import pandas as pd

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

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

        buttonCenter = driver.find_element_by_class_name("btn-primary")
        buttonCenter.click()

        warningText = '''Warning\nAuthentication failed, please try again.\nDISMISS'''

        try:
            if driver.find_element_by_id("alert-alert").text == warningText:
                return False
        except:
            pass

        try:
            screenTitle = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="content"]/h2')))
        except:
            usernameCenter = driver.find_element_by_id("auth_key")
            usernameCenter.send_keys(username)

            passwordCenter = driver.find_element_by_id("password")
            passwordCenter.send_keys(password)

            buttonCenter = driver.find_element_by_class_name("btn-primary")
            buttonCenter.click()


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
        driver.get("https://arkansas.pmpaware.net/rx_search_requests/new")
        try:
            testName = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "rx_search_request_last_name")))
        except:
            pass

        if len(driver.find_element_by_id("rx_search_request_delegator_id").find_elements_by_tag_name("option")) > 0:
            masterList = Select(driver.find_element_by_id("rx_search_request_delegator_id"))
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

        driver.get("https://arkansas.pmpaware.net/rx_search_requests/new")

        # fills in boxes with patient names
        try:
            testName = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, "rx_search_request_last_name")))
        except:
            driver.get("https://arkansas.pmpaware.net/rx_search_requests/new")

        lastNameBox = driver.find_element_by_id("rx_search_request_last_name")
        lastNameBox.send_keys(lastName)

        firstNameBox = driver.find_element_by_id("rx_search_request_first_name")
        firstNameBox.send_keys(firstName)

        dobBox = driver.find_element_by_id("rx_search_request_birthdate")
        dobBox.clear()
        dobBox.send_keys(dob)

        beginDate = driver.find_element_by_id("rx_search_request_filled_at_begin")
        beginDate.clear()
        beginDate.send_keys(date)

        # checks for master account; if exists, it asks user which one to use, then selects it
        if len(driver.find_element_by_id("rx_search_request_delegator_id").find_elements_by_tag_name("option")) > 0:
            masterList = Select(driver.find_element_by_id("rx_search_request_delegator_id"))
            masterOptions = masterList.options
            global masterChoice
            masterAccount = masterOptions[masterChoice]
            masterAccount.click()


        # selects next button
        submitButton = driver.find_element_by_name("commit")
        submitButton.click()

        # grabs first inital
        firstInitial = firstName[:1]
        fileName = lastName + firstInitial

        global saveLoc
        # now that we are on the prescription page, we take a screenshot
        #WebDriverWait(driver, 1).until(wait_for_display((By.CSS_SELECTOR, ".indeterminate_progress .small")))
        #TODO style not display. maybe style.display or something
        time.sleep(0.1)
        try:
            spinner = driver.find_element_by_class_name("rx_request_new_spinner")
            while "none" != spinner.find_element_by_tag_name("i").value_of_css_property("display"):
                time.sleep(0.1)
                spinner = driver.find_element_by_class_name("rx_request_new_spinner")
            while not popup(True):
                time.sleep(0.1)
            time.sleep(0.5)
            if "false" == driver.find_element_by_id("multiple_patient_confirmation_modal").get_attribute("aria-hidden"):
                WebDriverWait(driver, 100)
                patientChoices = driver.find_elements_by_class_name("patient_group_table")
                for i in patientChoices:
                    i.find_element_by_xpath(".input[@type=checkbox]").click()
                driver.find_element_by_xpath('//*[@id="multiple_patient_confirmation"]/div[4]/div/button[2]').click()
        except:
            pass
        finally:
            driver.get_screenshot_as_file("{}/{}.png".format(saveLoc, fileName))

        #float: right; display: block;

        '''if "false" == driver.find_element_by_id("patients_found_but_no_results_modal").get_attribute("aria-hidden"):
            try:
                cat = WebDriverWait(driver, 2).until(EC.url_changes)
            except:
                pass
            finally:
                driver.get_screenshot_as_file("{}/{}.png".format(saveLoc, fileName))
        else:
            driver.get_screenshot_as_file("{}/{}.png".format(saveLoc, fileName))'''


        return lastName

    def killTheBrowser():
        driver.quit()


    def initSession(username, password, csvFile):
        setup()
        if pushTheButton(username, password) == False:
            return False
        fetchData(csvFile)

    def popup(bool):
        if driver.find_element_by_id("multiple_patient_confirmation_modal").get_attribute("aria-hidden") == "true":
            if bool:
                return True
            else:
                return "multiple"
        elif driver.find_element_by_id("patients_found_but_no_results_modal").get_attribute("aria-hidden") ==  "true":
            if bool:
                return True
            else:
                return "no results"
        else:
            if bool:
                return False
            else:
                return "no"


    def setMasterAccount(choice):
        global masterChoice
        masterChoice = choice

    def setSaveLocation(choice):
        global saveLoc
        saveLoc = choice

except:
    driver.quit()
