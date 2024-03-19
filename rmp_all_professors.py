import re
import requests
import requests_cache
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import timedelta
from ratelimit import limits, sleep_and_retry
import requests_cache
import time
import pandas as pd

requests_cache.install_cache("RMP")

def fetch_uni_info(school_id =1073):
    url="https://www.ratemyprofessors.com/school/1073"
    cur_list_xpath ='/html/body/div[2]/div/div/div[3]/div[5]/ul'
    driver = webdriver.Chrome(executable_path="/opt/homebrew/bin/chromedriver")
    driver.get(url)
    url = f'https://www.ratemyprofessors.com/campusRatings.jsp?sid={school_id}'
    driver.get(url)

    #professor_elements = driver.find_elements(By.CLASS_NAME, 'TeacherCard__StyledTeacherCard-syjs0d-0 dLJIlx')

    try:
        while True:
            # wait = WebDriverWait(driver, 10)
            # wait.until(EC.presence_of_element_located((By.CLASS_NAME, "schoolRatingList")))
            professor_elements = driver.find_elements(By.CLASS_NAME, 'schoolRatingList')
            tree = html.fromstring(driver.page_source)
            print(tree)
    except:
        pass

def close_popup(driver,xpath):
    close_button = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.XPATH, xpath ))
        )
    close_button.click()
def scrape_professors(school_id =1073):
    # Initialize Chrome WebDriver
    options = webdriver.ChromeOptions()
    path_to_adblocker = '/Users/ktujwal/PycharmProjects/SmartAggie/extensions/Adblock.crx'
    options.add_extension(path_to_adblocker)
    options.add_argument('--disable-extensions-first-run')
    #options.add_argument('load-extension=/path/to/extension')
    driver = webdriver.Chrome(options=options)  # Set the correct path
    df = pd.DataFrame(
        columns=['Name', 'Quality Rating', 'Total Ratings', 'Department', 'University', 'Would Take Again',
                 'Level of Difficulty', 'Link'])
    try:
        url = f'https://www.ratemyprofessors.com/search/professors/{school_id}?q=*'
        driver.get(url)
        original_window = driver.current_window_handle

        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        driver.close()
        driver.switch_to.window(original_window)
        cookie_disclaimer_xpath = '/html/body/div[5]/div/div/button'
        rmp_popup_xpath='/html/body/div[17]/div[2]/div/button'
        prof_xpath ='/html/body/div[2]/div/div/div[4]/div[1]/div[1]/div[3]/a'
        show_more_xpath = '/html/body/div[2]/div/div/div[4]/div[1]/div[1]/div[4]/button'

        try:
            close_popup(driver,cookie_disclaimer_xpath)
            time.sleep(3)
            close_popup(driver,rmp_popup_xpath)
            time.sleep(3)
        except Exception as e:
            print(f"Error closing cookie popup, manual effort maybe needed")

        while True:
            try:
                show_more_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, show_more_xpath))
                )
                show_more_button.click()
            except Exception as e:
                print(f"No more pages to load")
                break
        professor_elements = driver.find_elements(By.XPATH, prof_xpath)

        for professor in professor_elements:
            professor_dat = professor.text
            prof_quality_rating=professor_dat.split('\n')[1]
            prof_total_rating=professor_dat.split('\n')[2].split(' ratings')[0]
            prof_name = professor_dat.split('\n')[3]
            prof_dept = professor_dat.split('\n')[4]
            prof_uni = professor_dat.split('\n')[5]
            would_take_again=professor_dat.split('\n')[6]
            level_of_difficulty=professor_dat.split('\n')[8]
            professor_link=professor.get_attribute('href')
            print(f"Professor {prof_name} has a rating of {prof_quality_rating}")
            # Add the professor data to the DataFrame
            df = pd.concat([df, pd.DataFrame([{'Name': prof_name, 'Quality Rating': prof_quality_rating,
                                               'Total Ratings': prof_total_rating, 'Department': prof_dept,
                                               'University': prof_uni, 'Would Take Again': would_take_again,
                                               'Level of Difficulty': level_of_difficulty, 'Link': professor_link}],
                                             index=[0])], ignore_index=True)

        df.to_csv("prof_dat.csv")

    finally:
        driver.quit()



def get_remaining_professors():
    rmp_gql_endpoint = 'https://www.ratemyprofessors.com/graphql'
    rmp_gql_headers = {
        "Authorization": "Basic dGVzdDp0ZXN0",
    }

    query = {
        "query": "query TeacherSearchPaginationQuery(\n  $count: Int!\n  $cursor: String\n  $query: TeacherSearchQuery!\n) {\n  search: newSearch {\n    ...TeacherSearchPagination_search_1jWD3d\n  }\n}\n\nfragment TeacherSearchPagination_search_1jWD3d on newSearch {\n  teachers(query: $query, first: $count, after: $cursor) {\n    didFallback\n    edges {\n      cursor\n      node {\n        ...TeacherCard_teacher\n        id\n        __typename\n      }\n    }\n    pageInfo {\n      hasNextPage\n      endCursor\n    }\n    resultCount\n    filters {\n      field\n      options {\n        value\n        id\n      }\n    }\n  }\n}\n\nfragment TeacherCard_teacher on Teacher {\n  id\n  legacyId\n  avgRating\n  numRatings\n  ...CardFeedback_teacher\n  ...CardSchool_teacher\n  ...CardName_teacher\n  ...TeacherBookmark_teacher\n}\n\nfragment CardFeedback_teacher on Teacher {\n  wouldTakeAgainPercent\n  avgDifficulty\n}\n\nfragment CardSchool_teacher on Teacher {\n  department\n  school {\n    name\n    id\n  }\n}\n\nfragment CardName_teacher on Teacher {\n  firstName\n  lastName\n}\n\nfragment TeacherBookmark_teacher on Teacher {\n  id\n  isSaved\n}\n",
        "variables": {
            "count": 10000,
            "query": {
                "text": "",
                "schoolID": "U2Nob29sLTEwNzM=",
                "fallback": True
            }
        }
    }

    response = requests.post(rmp_gql_endpoint, headers = rmp_gql_headers, json=query)

    result = response.json()
    prof_list = result['data']['search']['teachers']['edges']
    print(response)

    def fetch_info(dic):
        name = dic['node']['firstName'] + " " + dic['node']['lastName']
        link = "https://www.ratemyprofessors.com/professor/" + str(dic['node']['legacyId'])
        return [name, dic['node']['avgRating'], dic['node']['numRatings'], dic['node']['department'],
                dic['node']['school']['name'], dic['node']['wouldTakeAgainPercent'], dic['node']['avgDifficulty'], link]

    remaining_profs_df = pd.DataFrame([fetch_info(prof) for prof in prof_list], columns=['Name', 'Quality Rating', 'Total Ratings', 'Department', 'University', 'Would Take Again',
                                                                                         'Level of Difficulty', 'Link'])
    remaining_profs_df.to_csv('prof_dat.csv', index=False)


get_remaining_professors()

school_id = 1073
scrape_professors(school_id)
#get_remaining_professors()

