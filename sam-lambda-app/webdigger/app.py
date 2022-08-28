from asyncio import events
from selenium.webdriver import Chrome
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import json
import os
import csv
from math import ceil
import json
import boto3

# Credits -  https://www.youtube.com/watch?v=Xajg_kvdA0c&list=PLC5qe4rQ-j1h-DktBYkeJto7rsEZAfTMl

def lambda_handler(event, context):
    
    def initialize_driver():

        global driver

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

        return driver

    def initiale_data(filename):

        global channel_data
        global data_dir
        global today

        dt = datetime.now()
        today = dt.strftime('%m%d%y')
        print(len(event.keys()))
        data_dir="/tmp/data/"

        os.mkdir(data_dir)

        with open(filename, "r") as f:
            channel_data = json.load(f)
            return channel_data

    def scrapper():


        
        for val in channel_data.keys():

            youtube_page = channel_data[val]['link']
            channel_name = channel_data[val]['link'].split('/')[4].lower()
            file_name = "report_{}_{}_data.csv".format(today,channel_name)
            file_name_with_dir = "{}{}".format(data_dir,file_name)

            csv_file = open(file_name_with_dir, 'w', encoding="utf-8", newline="")
            writer = csv.writer(csv_file)


            # write header names
            writer.writerow(
                ['video_title', 'no_of_views', 'time_uploaded'])

            driver.get(youtube_page)
            time.sleep(2)

            print("Scrapting data for :", youtube_page)
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
            
            upload_file_to_s3(file_name_with_dir, "9-bucket", file_name)
                
        driver.close()
        # close the driver

    def upload_file_to_s3(local_filename, s3_bucket_name, s3_filename):
        
        s3 = boto3.client('s3')

        '''
        Function is meant to upload locally downloaded files to s3 bucket.
        # Reference
        # https://medium.com/analytics-vidhya/aws-s3-multipart-upload-download-using-boto3-python-sdk-2dedb0945f11
        # https://stackoverflow.com/questions/34303775/complete-a-multipart-upload-with-boto3
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/customizations/s3.html
        '''

        try:
            print("Uploading file: {}".format(local_filename))

            tc = boto3.s3.transfer.TransferConfig()
            t = boto3.s3.transfer.S3Transfer(client=s3, config=tc)

            t.upload_file(local_filename, s3_bucket_name, s3_filename)

        except Exception as fileUploadtoS3error:
            print("Error uploading: {}".format(fileUploadtoS3error))

    
    def print_data():
        '''
        This function can be used to get a list of items in current working directory
        # Debugging function, not called within script.
        '''
        os.chdir(data_dir)
        get_list = os.listdir()
        for file in get_list:
            print(file)
    
    initiale_data("channel_list.json")
    initialize_driver()
    scrapper()
    #print_data()

