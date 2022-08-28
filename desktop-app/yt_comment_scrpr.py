#imports here
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import WebDriverWait
import time
import random

#code by pythonjar, not me


chrome_options = webdriver.ChromeOptions()
prefs = {"profile.default_content_setting_values.notifications" : 2}
chrome_options.add_experimental_option("prefs",prefs)

#specify the path to chromedriver.exe (download and save on your computer)
driver = webdriver.Chrome('D:\\Work\\Ajgar\\yt-scrapper\\chromedriver.exe', chrome_options=chrome_options)
driver.get("https://www.youtube.com/watch?v=J4FM1-CICTE&t=750s")

time.sleep(20)
while True:
    scroll_height = 100
    document_height_before = driver.execute_script("return document.documentElement.scrollHeight")
    driver.execute_script(f"window.scrollTo(0, {document_height_before + scroll_height});")
    time.sleep(random.randint(3,6))
    document_height_after = driver.execute_script("return document.documentElement.scrollHeight")
    if document_height_after == document_height_before:
        break

