# -*- coding: utf-8 -*-
import datetime
import os.path
import time
import pandas as pd
import sys
import logging
import getpass
import signal
import socket
from pandas.tseries.offsets import BDay
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.common import exceptions
from selenium.webdriver.support.wait import WebDriverWait

__version__ = "1.0.0"

if sys.version_info[0] < 3:
    raise Exception("Must be run using Python 3")

PROXIES = {'http': '192.168.1.2:3128',
           'https': '192.168.1.2:3128', }

URL = "https://www.szse.cn/English/disclosures/announcements/"


########################################################################################
# logging constants
LOGFORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
LOG_DEBUG = 10
LOG_INFO = 20
LOG_WARNING = 30
LOG_ERROR = 40
LOG_CRITICAL = 50
# current logging minimum level for the run
LOG_CURRENT_MINIMUM = LOG_DEBUG


########################################################################################################################
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


########################################################################################################################
def log(level: int, message: str):
    """logger"""
    logger.log(level, message, extra={'clientip': get_ip(), 'user': getpass.getuser()})


########################################################################################################################
def signal_handler(sig, frame):
    """the interrupt handler"""
    log(LOG_INFO, 'Interrupt received, stopping')
    sys.exit(0)


########################################################################################################################
def create_webdriver_instance():
    """ Initialise driver settings """
    try:
        options = Options()
        options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
        options.headless = False
        driver = webdriver.Firefox(executable_path='C:/Users/Gare/Downloads/geckodriver.exe', options=options)
        return driver
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error create_webdriver_instance(): {0} at line {1}".format(str(exc_value),
                                                                                      str(exc_traceback.tb_lineno)))


########################################################################################################################
def visit_site(driver, url):
    """Navigate to webpage"""
    try:
        driver.get(str(url))
        return driver
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error visit_site(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))


########################################################################################################################
def change_tab(driver):
    """Click accept button using the text from the button name"""
    try:
        xpath_search = '//div[@class="c-loading-overlay"]'
        WebDriverWait(driver, 10).until(expected_conditions.invisibility_of_element((By.XPATH, xpath_search)))
        buttons = driver.find_elements_by_xpath('//a[text()="ChiNext" and @class="tab"]')
        buttons[0].click()

        WebDriverWait(driver, 10).until(expected_conditions.visibility_of_element_located((By.XPATH, xpath_search)))
        WebDriverWait(driver, 10).until(expected_conditions.invisibility_of_element((By.XPATH, xpath_search)))
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error change_tab(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))

########################################################################################################################
def get_date_range():
    """Get current date and previous date excluding weekends"""
    try:
        today_date = datetime.datetime.today()
        previous_date = today_date - BDay(1)
        print(today_date)
        return str(previous_date.date()), str(today_date.date())
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error get_date_range(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))


########################################################################################################################
def set_page_date_range(driver, other_tab=False):
    """Set value for date range in page"""
    try:
        start_date, end_date = get_date_range()
        xpath_search = '//table[@class="table table-responsive table-tab1"]'
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_search)))

        # Sets the date form boxes
        if other_tab:
            xpath_search = '//input[@id="1845_tab2_startDate"]'
            start_date_box = driver.find_elements_by_xpath(xpath_search)[0]
        else:
            xpath_search = '//input[@id="1845_tab1_startDate"]'
            start_date_box = driver.find_elements_by_xpath(xpath_search)[0]
        start_date_box.clear()
        start_date_box.send_keys(start_date)

        if other_tab:
            xpath_search = '//input[@id="1845_tab2_endDate"]'
            end_date_box = driver.find_elements_by_xpath(xpath_search)[0]
        else:
            xpath_search = '//input[@id="1845_tab1_endDate"]'
            end_date_box = driver.find_elements_by_xpath(xpath_search)[0]
        end_date_box.clear()
        end_date_box.send_keys(end_date)

        xpath_search = '//button[@class="confirm-query btn-query-primary"]'
        if other_tab:
            search_button = driver.find_elements_by_xpath(xpath_search)[1]
        else:
            search_button = driver.find_elements_by_xpath(xpath_search)[0]
        search_button.click()

        xpath_search = '//div[@class="c-loading-overlay"]'
        WebDriverWait(driver, 15).until(expected_conditions.invisibility_of_element((By.XPATH, xpath_search)))
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error set_page_date_range(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))


########################################################################################################################
def get_page_rows(driver, other_tab=False):
    """Click accept button using the text from the button name"""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        driver.implicitly_wait(10)
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        if other_tab:
            tables = soup.find_all("table", class_="table table-responsive table-tab1")
            for tab in tables:
                if len(tab.find_all("td", class_="text-center")) > 0:
                    table = tab
        else:
            tables = soup.find_all("table", class_="table table-responsive table-tab1")
            for tab in tables:
                if len(tab.find_all("td", class_="text-center")) > 0:
                    table = tab
        col_extra = table.find_all("colgroup")[0]
        table = str(table).replace(str(col_extra), "")
        converters = {'Stock Code': lambda x: str(x)}
        dataframe = pd.read_html(table, converters=converters)[0]
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        return dataframe
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error get_page_rows(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))


########################################################################################################################
def get_page_current_number(driver, other_tab=False):
    """Click accept button using the text from the button name"""
    try:
        xpath_search = '//div[@class="current-page"]'
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_search)))
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        if other_tab:
            current_page = soup.find_all("div", {"id": "1845_nav2"})[0]
        else:
            current_page = soup.find_all("div", {"id": "1845_nav1"})[0]
        current_page = current_page.find_all("div", class_="current-page")[0]
        current_page = current_page.find_all("span", class_="num-cur")[0].getText()
        return current_page
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error get_page_current_number(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))


########################################################################################################################
def scroll_to_bottom(driver):
    try:
        reached_page_end = False
        last_height = driver.execute_script("return document.body.scrollHeight")

        while not reached_page_end:
            driver.find_element_by_xpath('//body').send_keys(Keys.END)
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if last_height == new_height:
                reached_page_end = True
            else:
                last_height = new_height

    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error scroll_to_bottom(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))


########################################################################################################################
def go_to_next_page(driver, other_tab=False):
    """Scroll to bottom of the page and click button to go to next page"""
    try:
        scroll_to_bottom(driver)

        xpath_search = '//li[@class="next"]'
        WebDriverWait(driver, 15).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_search)))

        if other_tab:
            button_number = int(get_page_current_number(driver, True))
            button_path = '//div[@id="1845_nav2"]//li[@class="next"]'
            buttons = driver.find_elements_by_xpath(button_path)
            buttons[0].click()
            next_page_loaded = '//div[@id="1845_nav2"]//span[text()= ' + str(button_number) + 'and @class="num-cur"]'
        else:
            button_number = int(get_page_current_number(driver))
            button_path = '//li[@class="next"]'
            buttons = driver.find_elements_by_xpath(button_path)
            buttons[0].click()
            next_page_loaded = '//span[text()= ' + str(button_number) + 'and @class="num-cur"]'

        WebDriverWait(driver, 15).until(expected_conditions.visibility_of_element_located((By.XPATH, next_page_loaded)))

        xpath_search = '//div[@class="report-container c-loading"]'
        WebDriverWait(driver, 10).until(expected_conditions.visibility_of_element_located((By.XPATH, xpath_search)))
        WebDriverWait(driver, 10).until(expected_conditions.invisibility_of_element((By.XPATH, xpath_search)))
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error go_to_next_page(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))


#######################################################################################################################
def get_total_page(driver, other_tab=False):
    """Click accept button using the text from the button name"""
    try:
        html_source = driver.page_source
        soup = BeautifulSoup(html_source, 'html.parser')
        if other_tab:
            total_page = soup.find_all("div", {"id": "1845_nav2"})[0]
        else:
            total_page = soup.find_all("div", {"id": "1845_nav1"})[0]

        total_page = total_page.find_all("div", class_="current-page")[0]
        total_page = int(total_page.find_all("span", class_="num-all")[0].getText())

        return total_page
    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error get_total_page(): {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))



#######################################################################################################################
def get_main_tab(URL):
    log(LOG_INFO, 'Starting Shenzhen 1st Tab'.format(__version__))
    driver = create_webdriver_instance()

    # navigate to the site

    driver = visit_site(driver, URL)

    # Set date range to produce html tables
    set_page_date_range(driver)
    driver.implicitly_wait(10)


    tab_1_df = []
    data = get_page_rows(driver)
    tab_1_df.append(data)
    log(LOG_INFO, 'In progress Shenzhen 1st tab pages'.format(__version__))
    while int(get_page_current_number(driver)) < get_total_page(driver):

        go_to_next_page(driver)
        tab_1_df.append(get_page_rows(driver))

    tab_1_df = pd.concat(tab_1_df)

    driver.close()
    log(LOG_INFO, 'Shenzhen 1st tab complete'.format(__version__))
    return tab_1_df


#######################################################################################################################
def get_other_tab(URL):
    log(LOG_INFO, 'Starting Shenzhen 2nd Tab'.format(__version__))
    driver = create_webdriver_instance()
    driver = visit_site(driver, URL)
    change_tab(driver)

    # Set date range to produce html tables
    set_page_date_range(driver, True)
    driver.implicitly_wait(10)
    tab_2_df = []
    data = get_page_rows(driver, True)
    tab_2_df.append(data)
    log(LOG_INFO, 'In progress Shenzhen 2nd tab pages'.format(__version__))
    while int(get_page_current_number(driver, True)) < get_total_page(driver, True):
        go_to_next_page(driver, True)
        tab_2_df.append(get_page_rows(driver, True))
    tab_2_df = pd.concat(tab_2_df)

    driver.close()
    log(LOG_INFO, 'Shenzhen 2nd tab complete'.format(__version__))
    return tab_2_df


#######################################################################################################################
def clean_dataframe(dataframe):
    dataframe.rename(columns={'0': 'Stock Code', '1': 'Stock Name', '2': 'Date', '3': 'Title',  '4': 'Memo'}, inplace=True)
    dataframe.drop(['Stock Name'], axis=1)

    return dataframe
    

###################################################################################################################
if __name__ == '__main__':
    try:
        # set up logging
        logging.basicConfig(format=LOGFORMAT)
        logger = logging.getLogger('scrape_shenzhen')
        logger.setLevel(LOG_CURRENT_MINIMUM)
        log(LOG_INFO, 'Starting scrape_shenzhen'.format(__version__))

        # set up interrupt catcher
        signal.signal(signal.SIGINT, signal_handler)

        attempts = 0

        while attempts < 4:
            try:
                df = get_main_tab(URL)
                df2 = get_other_tab(URL)
                df = pd.concat([df, df2])
                df = clean_dataframe(df)
                
                df.to_csv('shenzhen_announcement.csv', index=False)
                log(LOG_INFO, 'Scrape complete'.format(__version__))
                attempts = 4
            except Exception as exception:
                attempts = attempts + 1
                log(LOG_INFO, 'Failed Shenzhen scrape attempting again try number: {0}'.format(str(attempts)))

    except Exception as exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        log(LOG_CRITICAL, "Error main: {0} at line {1}".format(str(exc_value), str(exc_traceback.tb_lineno)))
        log(LOG_INFO, 'Shenzhen Scrape Failed'.format(__version__))
        exit(4)
