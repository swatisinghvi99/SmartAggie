import requests_cache
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import timedelta
from ratelimit import limits, sleep_and_retry
import requests_cache
import time
import pandas as pd
import os.path

requests_cache.install_cache("RMP")


def close_popup(driver,xpath):
    close_button = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.XPATH, xpath ))
        )
    close_button.click()

@sleep_and_retry
@limits(calls=3, period=timedelta(seconds=5).total_seconds())
def scrape_professor_info(prof_url,prof_name):

    commnet_df = pd.DataFrame(
        columns=['Name','Link', 'Quality Rating', 'Difficulty', 'Course', 'Comment'])
    comment_xpath = '/html/body/div[2]/div/div/div[3]/div[4]/div/div/ul/li'
    load_more_ratings_xpath = '/html/body/div[2]/div/div/div[3]/div[4]/div/div/button'
    while True:
        try:
            load_more_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, load_more_ratings_xpath))
            )
            load_more_button.click()
        except Exception as e:
            print(f"No more pages to load")
            break
    comment_elements = driver.find_elements(By.XPATH, comment_xpath)

    for comment in comment_elements:
        comment_dat = comment.text
        if not comment_dat == '':
            course_quality_rating=comment_dat.split('\n')[1]
            course_difficulty=comment_dat.split('\n')[3]
            course_title = comment_dat.split('\n')[4]
            if comment_dat.split('\n')[7] != 'Helpful' and 'Grade:' not in comment_dat.split('\n')[7] and 'Textbook:' not in comment_dat.split('\n')[7]:
                if 'Attendance:'not in comment_dat.split('\n')[7]:
                    comment_text=comment_dat.split('\n')[7]
                elif 'Helpful' in comment_dat.split('\n')[10]:
                    comment_text = comment_dat.split('\n')[9]
                elif 'Helpful' in comment_dat.split('\n')[11]:
                    comment_text = comment_dat.split('\n')[10]
                else:
                    comment_text = comment_dat.split('\n')[11]
            elif comment_dat.split('\n')[7] != 'Helpful':
                if 'Textbook:' not in comment_dat.split('\n')[8]:
                    comment_text = comment_dat.split('\n')[8]
                else:
                    comment_text = comment_dat.split('\n')[9]
            else:
                comment_text = comment_dat.split('\n')[6]
            print(f"Course {course_title} has a rating of {course_quality_rating}")
            # Add the professor data to the DataFrame
            commnet_df = pd.concat([commnet_df, pd.DataFrame([{'Name': prof_name,'Link':prof_url, 'Quality Rating': course_quality_rating,
                                               'Difficulty': course_difficulty, 'Course': course_title,
                                               'Comment': comment_text, }],
                                             index=[0])], ignore_index=True)

    return commnet_df

temp_data="/Users/ktujwal/PycharmProjects/SmartAggie/prof_dat.csv"
df= pd.read_csv(temp_data)
all_comments_file = '/Users/ktujwal/PycharmProjects/SmartAggie/all_comments.csv'
if os.path.isfile(all_comments_file):
    all_comment_df = pd.read_csv(all_comments_file)
else:
    all_comment_df = pd.DataFrame()
count=0
new_df =df[count:]
try:
    options = webdriver.ChromeOptions()
    path_to_adblocker = '/Users/ktujwal/PycharmProjects/SmartAggie/extensions/Adblock.crx'
    options.add_extension(path_to_adblocker)
    options.add_argument('--disable-extensions-first-run')
    driver = webdriver.Chrome(options=options)  # Set the correct path
    original_window = driver.current_window_handle
    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            break

    driver.close()
    driver.switch_to.window(original_window)
    cookie_disclaimer_xpath = '/html/body/div[5]/div/div/button'
    rmp_popup_xpath = '/html/body/div[17]/div[2]/div/button'

    try:
        close_popup(driver, cookie_disclaimer_xpath)
        time.sleep(3)
        close_popup(driver, rmp_popup_xpath)
        time.sleep(3)
    except Exception as e:
        print(f"Error closing cookie popup, manual effort maybe needed")
    for url,name in zip(new_df['Link'],new_df['Name']):
        try:
            driver.get(url)
            comment_df = scrape_professor_info(url,name)
            all_comment_df = pd.concat([all_comment_df,comment_df],ignore_index=True)
            count = count+1
            print(f'Processed {count}/{df.shape[0]} comment data for {name}')
            all_comment_df.to_csv(all_comments_file, mode='w')
        finally:
            pass
finally:
    driver.quit()

