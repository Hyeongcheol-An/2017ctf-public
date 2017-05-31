import os
import sys
import time
import ConfigParser
from selenium import webdriver
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

POSTING_XPATH = '/html/body/div/table/tbody/tr/td/a'
FLAG_FILE = '/tmp/flag'
LOGIN_URI = '/bbs/login/'
CONFIG_FILE = 'config.conf'
SECTION = 'government'
#Below global variables will be set after reading a config file
ADMIN_ID = ''
ADMIN_PW = ''
SITE = ''
DOMAIN_NAME = ''

READ_TIMEOUT = 3

def read_posting(driver):
    # Get post's links by inspecting html
    links = driver.find_elements_by_xpath(POSTING_XPATH)
    link_num = len(links)

    if(link_num == 0):
        print "Cannot read any post."

    # Read each post and go back to bbs list page 
    else:
        for i in range(len(links)):
            try:
                WebDriverWait(driver, 5).until(EC.title_contains('list'))
                links[i].click()
                # Wait 1 second to load an posting
                time.sleep(1)
                s_time = time.time()
                while True:
                    WebDriverWait(driver, 1).until(EC.alert_is_present())
                    if time.time() - s_time > READ_TIMEOUT:
                        raise
                    alert = driver.switch_to_alert()
                    alert.accept()
                    time.sleep(0.1)
            except:
                driver.execute_script('window.history.go(-1)')
 

def bbs_login(driver):
    # Visit login page and login
    visit_website(driver, SITE + LOGIN_URI)
    login_id = driver.find_element_by_id('username')
    login_id.send_keys(ADMIN_ID)

    login_pw = driver.find_element_by_id('password')
    login_pw.send_keys(ADMIN_PW)

    login_form = driver.find_element_by_class_name('form-inline')
    login_form.submit()
    try:
        element = WebDriverWait(driver, 5).until(EC.title_contains('list'))
    except:
        print "[Fail] Cannot login"
        driver.quit()
        exit(1)
   

def set_cookie(driver, domain):
    # Get a flag from the file which a flag updater is generated
    try:
        f = open(FLAG_FILE, 'r')
        flag = f.readline()
        f.close()
    except:
        print "[Fail] Cannot read a flag file, " + FLAG_FILE
        driver.quit()
        exit(1)

    # Check flag size
    flag = flag.strip()
    if len(flag) != 32:
        print "[Fail] Invalid length of the flag value, %d" % len(flag)
        driver.quit()
        exit(1)

    # Set a cookie with the flag value
    try:
        driver.add_cookie({'name': 'flag', 'value': flag, 'domain': domain,
            'path': '/', 'expires': None})
        print "Set-cookie: flag=" + flag + ", domain=" + domain
    except:
        print "Cannot set a cookie."


def visit_website(driver, domain):
    driver.get('http://' + domain)
    time.sleep(2)


def set_driver(driver):
    # Doesn't work in the is521 box, dont know why..
    #driver.implicitly_wait(3)
    driver.set_window_size(1000, 600)
   

def write_config():
    # Write a config file
    print "Making config file..."
    global ADMIN_ID, ADMIN_PW, SITE, DOMAIN_NAME
    config = ConfigParser.RawConfigParser()
    config.add_section(SECTION)
  
    ADMIN_ID  = raw_input("Enter government website admin ID: ")
    ADMIN_PW = raw_input("Enter government website admin PW: ")
    SITE = raw_input("Enter government website address: http://")
    DOMAIN_NAME = raw_input("Enter domain of bank.com: http://")
    config.set(SECTION, 'ADMIN_ID', ADMIN_ID)
    config.set(SECTION, 'ADMIN_PW', ADMIN_PW)
    config.set(SECTION, 'SITE', SITE)
    config.set(SECTION, 'DOMAIN_NAME', DOMAIN_NAME)

    with open(CONFIG_FILE, 'wb') as conf_file:
        config.write(conf_file)
  

def read_config(conf_file):
    # Read a config file. If not exist, write it.
    global ADMIN_ID, ADMIN_PW, SITE, DOMAIN_NAME
    if os.path.isfile(conf_file):
        try:
            config = ConfigParser.ConfigParser()
            config.read(conf_file)
            ADMIN_ID = config.get(SECTION, 'ADMIN_ID')
            ADMIN_PW = config.get(SECTION, 'ADMIN_PW')
            SITE = config.get(SECTION, 'SITE')
            DOMAIN_NAME = config.get(SECTION, 'DOMAIN_NAME')            
        except:
            print conf_file + " is an invalid config file."
            write_config()
    else:
        print "Config file is not exist."
        write_config()


if __name__ == '__main__':
    read_config(CONFIG_FILE)
    while True:
        driver = webdriver.Firefox()
        try:
            set_driver(driver)

            visit_website(driver, DOMAIN_NAME)
            #set_cookie(driver, DOMAIN_NAME)

            visit_website(driver, SITE)
            bbs_login(driver)
            read_posting(driver)
            driver.quit()
        except:
            driver.quit()
        time.sleep(5)
