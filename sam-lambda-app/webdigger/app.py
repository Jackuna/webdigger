from selenium.webdriver import Chrome
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import json
import os
import csv
from math import ceil
import urllib.request
import json


def lambda_handler(event, context):
    # ----------------------------------web driver setup---------------------------------------------------
    # path to chromedriver. while testing locally, 'var/task/' is the temporary path where files and dependencies of the function are mounted.
    # 'var/task/' path stays the same for files and dependencies in aws lambda environment, when you upload the function as a zip file.
    driver_path = '/var/task/chromedriver'
    
    # path to headless-chromium
    binary_path = '/var/task/headless-chromium'

    # we'll use an instance of Options to specify certain things, while initializing the driver
    # https://www.selenium.dev/selenium/docs/api/rb/Selenium/WebDriver/Chrome/Options.html
    options = Options()

    # location(path) of headless-chromium binary file
    options.binary_location = binary_path

    # will start chromium in headless-mode
    options.add_argument('--headless')

    # below argument is for testing only;not recommended to be used in production.
    # https://chromium.googlesource.com/chromium/src/+/HEAD/docs/linux/sandboxing.md
    options.add_argument('--no-sandbox')

    # not using the below argument can limit resources.
    # https://www.semicolonandsons.com/code_diary/unix/what-is-the-usecase-of-dev-shm
    options.add_argument('--disable-dev-shm-usage')

    # "unable to discover open window in chrome" error pops up if u dont add the below argument
    # https://www.techbout.com/disable-multiple-chrome-processes-in-windows-10-26897/
    options.add_argument('--single-process')

    # initialize the driver
    driver = Chrome(executable_path=driver_path, options=options)

    print("driver initialized successfully..")

    # ----------------------------------web driver setup done----------------------------------------------------


    def load_chanel_list(filename):
        global channel_data

        with open(filename, "r") as f:
            channel_data = json.load(f)
            return channel_data

    def scrapper():

        driver_dir="/tmp/"
        for val in channel_data.keys():

            youtube_pages = channel_data[val]['link']
            csv_file = open(driver_dir+channel_data[val]['fname'], 'w', encoding="utf-8", newline="")
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
        # close the driver

    def uploda_to_s3():
        pass

    load_chanel_list("channel_list.json")
    scrapper()