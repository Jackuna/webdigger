from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import SessionNotCreatedException
import time
import os
import csv
from math import ceil
import urllib.request
import json
import re
import wget
from zipfile import ZipFile
from datetime import datetime


def load_variables():

    global chrome_driver_repository
    global chrome_driver_win_binary_zip
    global chrome_driver_win_binary
    global driver_dir
    global webdriver_location
    global today
    global data_dir

    chrome_driver_repository = "https://chromedriver.storage.googleapis.com/"
    chrome_driver_win_binary_zip = "chromedriver_win32.zip"
    chrome_driver_win_binary = "chromedriver.exe"
    driver_dir = os.getcwd()
    data_dir = driver_dir
    webdriver_location = "{}\\{}".format(driver_dir, chrome_driver_win_binary)
    dt = datetime.now()
    today = dt.strftime('%m%d%y')



def load_chanel_list(filename):
    
    global channel_urls

    with open(filename, "r") as f:
        channel_urls = json.load(f)
        return channel_urls

    

def downloadChromeDriver(chrome_driver_version):

    chrome_driver_downlodable_link = "{}{}/{}".format(chrome_driver_repository,
                                                                chrome_driver_version,
                                                                chrome_driver_win_binary_zip)
    try:
        if os.path.exists(chrome_driver_win_binary_zip):
            os.remove(chrome_driver_win_binary_zip)
        else:
            print("Thankfuly no Old Zip Found, downloading new chrome driver binary zip now..")
        
        wget.download(chrome_driver_downlodable_link)
        
        try:
            with ZipFile(chrome_driver_win_binary_zip,"r") as zip_ref:
                zip_ref.extractall(driver_dir)   
        except:
            print("error extracting zip package") 
    except:
        print("Error reported while downloading chrome driver")

    

def downloadLatestChromeDriver():

    print("No Chromedriver binary found in system, downloading latest one..\n")

    latest_chrome_driver_link = "{}LATEST_RELEASE".format(chrome_driver_repository)
    latest_chrome_driver_version = urllib.request.urlopen(latest_chrome_driver_link).read().decode('utf-8')
    downloadChromeDriver(latest_chrome_driver_version)



def getChromeBinaryVersions():

    chrome_binary_versions = {}
    try:
        Webdriver = Service(webdriver_location)
        driv_options = Options()
        driv_options.headless = True
        driver = webdriver.Chrome(service=Webdriver, options=driv_options)
        chrome_binary_versions.update(
                                        {"browser_version": driver.capabilities['browserVersion'].split(".")[0]} )
        chrome_binary_versions.update(
                                        {"driver_version": driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0].split(".")[0]} )
        
    except SessionNotCreatedException as error:
        chrome_binary_versions.update({"driver_version": error.msg.split()[11]})
        chrome_binary_versions.update({"browser_version": error.msg.split()[16].split(".")[0]})

    try:
        if chrome_binary_versions['driver_version'] != chrome_binary_versions['browser_version']:
            print("Incompaitable chmore driver/browser version", chrome_binary_versions)
            chrome_binary_versions.update({"update_required": "true"})
        else:
            chrome_binary_versions.update({"update_required": "false"})
    except:
        pass        
    
    return chrome_binary_versions


def validateChromeDriver():

    if  chrome_driver_win_binary not in os.listdir():
        downloadLatestChromeDriver()
    
    try:
        installed_version = getChromeBinaryVersions()

        if installed_version['update_required'] == "true":        
            browser_version = installed_version['browser_version']
            get_driver_version_for_url_1 = re.search('\w*.\w*.\w*', browser_version)[0]
            construct_download_url_step_1 = "{}LATEST_RELEASE_{}".format(chrome_driver_repository, 
                                                                            get_driver_version_for_url_1)

            browser_request_1 = urllib.request.urlopen(construct_download_url_step_1)
            get_driver_version_for_url_2 = browser_request_1.read().decode('utf-8')

            downloadChromeDriver(get_driver_version_for_url_2)
        else:
            print("Chrome driver Versions already updated, no need to update.")
    except:
        print("Something went wromg while validating chrome driver")
    

def initDriverSession():

    try:
        Webdriver = Service(webdriver_location)
        driv_options = Options()
        driv_options.headless = False
        driver = webdriver.Chrome(service=Webdriver, options=driv_options)
    except Exception as error:
        print(error)
    return driver


def yt_channel_scrapper(channel_urls, scrap_posts_count_limit, scrap_post_day_age ):

    driver = initDriverSession()

    
    for val in channel_urls.keys():

        youtube_pages = channel_urls[val]['link']
        channel_name = channel_urls[val]['link'].split('/')[4].lower()
        file_name = "report_{}_{}_data.csv".format(today,channel_name)
        file_name_with_dir = "{}//{}".format(data_dir,file_name)

        csv_file = open(file_name_with_dir, 'w', encoding="utf-8", newline="")
        writer = csv.writer(csv_file)


        # write header names
        writer.writerow(
            ['video_title', 'no_of_views', 'time_uploaded'])

        driver.get(youtube_pages)
        time.sleep(2)

        print("\n Scrapting data for :", youtube_pages)
        video_posted_in_requested_age=0

        while video_posted_in_requested_age >= 0:
            driver.execute_script("window.scrollTo(0,Math.max(document.documentElement.scrollHeight,document.body.scrollHeight,document.documentElement.clientHeight))")
            time.sleep(1)

            if scrap_post_day_age == 24:
                construct_xpath_string_start = '//*[contains(text(),"hour")]'
                construct_xpath_string_end = '//*[contains(text(),"{} day")]'.format('1')
                day_or_hour = "hour"
            else:
                construct_xpath_string_start = '//*[contains(text(),"{} day")]'.format(scrap_post_day_age)
                construct_xpath_string_end = '//*[contains(text(),"{} day")]'.format(scrap_post_day_age+1)
                day_or_hour = "day"

            try:
                video_posted_in_requested_age=len(driver.find_elements(By.XPATH,construct_xpath_string_start))
            except:
                video_posted_in_requested_age=0
        
            if len(driver.find_elements(By.XPATH,construct_xpath_string_end)) > 0:
                break

        

        total_post_to_write = len(driver.find_elements(By.ID, 'video-title'))
        print("Total video posted by {} {} : {} \n".format(scrap_post_day_age, day_or_hour, total_post_to_write))


        yt_title=[]
        yt_views=[]
        yt_posted=[]
        youtube_dict = {}
        negative_counter = 0
        for count in range(0,total_post_to_write):
            
            video_title=driver.find_elements(By.ID, 'video-title')[count].text
            video_views=driver.find_elements(By.XPATH, '//*[@id="metadata-line"]/span[1]')[count].text

            youtube_dict['yt_title'] = video_title
            youtube_dict['yt_views'] = video_views

            if video_views.split()[1] == "watching":
                video_posted = "Stream ongoing.."
                youtube_dict['yt_posted'] = video_posted
                negative_counter = negative_counter + 1
            else:
                new_count = count - negative_counter
                video_posted=driver.find_elements(By.XPATH, '//*[@id="metadata-line"]/span[2]')[new_count].text
                youtube_dict['yt_posted'] = video_posted


            print(video_title, video_views, video_posted)
            writer.writerow(youtube_dict.values())
    
    driver.close()

def main():
    load_variables()
    load_chanel_list("channel_list.json")
    validateChromeDriver()
    yt_channel_scrapper(channel_urls,101,24)


if __name__ == "__main__":
    main()