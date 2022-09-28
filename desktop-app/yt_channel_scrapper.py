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


def load_chanel_list(filename):
    global channel_data

    with open(filename, "r") as f:
        channel_data = json.load(f)
        return channel_data


def downloadChromeDriver():

    latest_chrome_driver_link = "{}LATEST_RELEASE".format(chrome_driver_repository)

    latest_chrome_driver_version = urllib.request.urlopen(latest_chrome_driver_link).read().decode('utf-8')
    latest_chrome_driver_downlodable_link = "{}{}/{}".format(chrome_driver_repository,
                                                                latest_chrome_driver_version,
                                                                chrome_driver_win_binary_zip)

    print ("No Chromedriver found, downloading latest driver.. hope that fits with browser version.")

    try:
        if os.path.exists(chrome_driver_win_binary_zip):
            os.remove(chrome_driver_win_binary_zip)
        else:
            print("Thankfully no Old Zip Found, downloading new chrome diver binary zip now..")
        
        wget.download(latest_chrome_driver_downlodable_link)
        
        try:
            with ZipFile("chromedriver_win32.zip","r") as zip_ref:
                zip_ref.extractall(driver_dir)   
        except:
            print("error extracting zip package") 
    except:
        print("Error fetcing URL")


def validateChromeDriver():

    global chrome_driver_repository
    global chrome_driver_win_binary_zip
    chrome_driver_repository = "https://chromedriver.storage.googleapis.com/"
    chrome_driver_win_binary_zip = "chromedriver_win32.zip"

    if "chromedriver.exe" not in os.listdir():
        downloadChromeDriver()

    chrome_binary_version = {}
    try:
        Webdriver = Service(webdriver_location)
        driv_options = Options()
        driv_options.headless = True
        driver = webdriver.Chrome(service=Webdriver, options=driv_options)
        chrome_binary_version.update({"browser_version": driver.capabilities['browserVersion'].split(".")[0]} )
        chrome_binary_version.update({"driver_version": driver.capabilities['chrome']['chromedriverVersion'].split(' ')[0].split(".")[0]} )
        
    except SessionNotCreatedException as error:
        chrome_binary_version.update({"driver_version": error.msg.split()[11]})
        chrome_binary_version.update({"browser_version": error.msg.split()[16].split(".")[0]})

    try:
        if chrome_binary_version['driver_version'] != chrome_binary_version['browser_version']:
            print("Incompaitable chmore driver/browser version", chrome_binary_version)
            chrome_binary_version.update({"update_required": "true"})
        else:
            chrome_binary_version.update({"update_required": "false"})
    except:
        pass        
    
    return chrome_binary_version


def initDriverSession():

    

    try:
        Webdriver = Service(webdriver_location)
        driv_options = Options()
        driv_options.headless = True
        driver = webdriver.Chrome(service=Webdriver, options=driv_options)
    except Exception as error:
        print(error)
    return driver


def updateChromeDriver():

    global driver_dir
    global webdriver_location

    driver_dir = os.getcwd()
    webdriver_location = driver_dir+"\\chromedriver.exe"
 
    try:
        installed_version = validateChromeDriver()

        if installed_version['update_required'] == "true":        
            browser_version = installed_version['browser_version']
            get_driver_version_for_url_1 = re.search('\w*.\w*.\w*', browser_version)[0]
            construct_download_url_step_1 = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_"+get_driver_version_for_url_1
            try:

                browser_request_1 = urllib.request.urlopen(construct_download_url_step_1)
                get_driver_version_for_url_2 = browser_request_1.read().decode('utf-8')
                construct_download_url_step_2 = "https://chromedriver.storage.googleapis.com/"+get_driver_version_for_url_2+"/chromedriver_win32.zip"
                print("downloading from :", construct_download_url_step_2)

                if os.path.exists(chrome_driver_win_binary_zip):
                    os.remove(chrome_driver_win_binary_zip)

                else:
                    print("Thankfully no Old Zip Found, downloading new chrome diver binary zip now..")

                wget.download(construct_download_url_step_2)

                try:
                    with ZipFile("chromedriver_win32.zip","r") as zip_ref:
                        zip_ref.extractall(driver_dir)   
                except:
                    print("error extracting zip package")
            except:
                print("Error fetcing URL")
        else:
            print("Chrome driver Versions already updated, no need to update.")

    except:
        pass


def scrapper():

    driver = initDriverSession()
    for val in channel_data.keys():

        youtube_pages = channel_data[val]['link']
        csv_file = open(driver_dir+"\\"+channel_data[val]['fname'], 'w', encoding="utf-8", newline="")
        writer = csv.writer(csv_file)


        # write header names
        writer.writerow(
            ['video_title', 'no_of_views', 'time_uploaded'])

        driver.get(youtube_pages)
        time.sleep(2)

        print("Scrapting data for :", youtube_pages)
        video_posted_in_48h=0

        while video_posted_in_48h >= 0:
            driver.execute_script("window.scrollTo(0,Math.max(document.documentElement.scrollHeight,document.body.scrollHeight,document.documentElement.clientHeight))")
            time.sleep(1)
            try:
                video_posted_in_24h=len(driver.find_elements(By.XPATH,'//*[contains(text(),"hour")]'))

            except:
                video_posted_in_24h=0
            try:
                video_posted_in_48h=len(driver.find_elements(By.XPATH,'//*[contains(text(),"1 day")]'))
            except:
                video_posted_in_48h=0
            
            print("Videos posted in 24hours", video_posted_in_24h)
            print("Videos posted in 48hours", video_posted_in_48h)

            if len(driver.find_elements(By.XPATH,'//*[contains(text(),"2 day")]')) > 0:
                break

        print("Total Videos in last 48 hours :", video_posted_in_48h)

        yt_title=[]
        yt_views=[]
        yt_posted=[]
        youtube_dict = {}

        for count in range(0,video_posted_in_48h):
            video_title=driver.find_elements(By.ID, 'video-title')[count].text
            video_views=driver.find_elements(By.XPATH, '//*[@id="metadata-line"]/span[1]')[count].text.rstrip('views')
            video_posted=driver.find_elements(By.XPATH, '//*[@id="metadata-line"]/span[2]')[count].text
            #time.sleep(1)
            yt_title.append(video_views)

            youtube_dict['yt_title'] = video_title
            youtube_dict['yt_views'] = video_views
            youtube_dict['yt_posted'] = video_posted

            print(video_title, video_views, video_posted)
            writer.writerow(youtube_dict.values())
    
    driver.close()
        

load_chanel_list("channel_list.json")
updateChromeDriver()
scrapper()
