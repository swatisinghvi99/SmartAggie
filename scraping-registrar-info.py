from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import csv
import time

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=chrome_options)

search_url = 'https://registrar-apps.ucdavis.edu/courses/search/index.cfm'

# Read course codes from the CSV
course_codes = []
with open('ucdavis_courses.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row['Course Code'] not in course_codes:
            course_codes.append(row['Course Code'])

# Quarters to search through
quarters = {
    'Winter Quarter 2024': '202401',
    'Spring Semester 2024': '202402',
    'Spring Quarter 2024': '202403',
    'Summer Session 1 2024': '202405',
    'Summer Special Session 2024': '202406',
    'Summer Session 2 2024': '202407',
    'Summer Quarter 2024': '202408',
    'Fall Quarter 2024': '202410',
}

with open('course_details_selenium.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Course Code', 'Term', 'Instructor', 'Prerequisite'])

    for course_code in course_codes:
        print(f"Extracting info for {course_code}")
        for quarter_name, quarter_code in quarters.items():
            driver.get(search_url)
            
            # Select the quarter
            select = Select(driver.find_element(By.NAME, 'termCode'))
            select.select_by_value(quarter_code)

            # Input the course code
            driver.find_element(By.NAME, 'course_number').send_keys(course_code)

            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Search']"))
            )
            search_button.click()

            try:

                view_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.cs-view-course'))
                )
                driver.execute_script("arguments[0].click();", view_link)

                # Extract course details
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'cs-modal-body'))
                )
                term = quarter_name
                instructor_element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//strong[contains(text(), 'Instructor:')]/ancestor::td[1]"))
                )
                # Extracting the full text and then processing it might be necessary if the name is not directly accessible
                instructor_full_text = instructor_element.text
                instructor = instructor_full_text.split('Instructor:')[-1].split('\n')[0].strip()

                prerequisite_element = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//strong[contains(text(), 'Prerequisite:')]/ancestor::td"))
                )
                
                # Checking if there's a link for prerequisites or direct text
                prerequisite_link_elements = prerequisite_element.find_elements(By.TAG_NAME, "a")
                
                if prerequisite_link_elements:
                    # If there's a link present, extract the href attribute or link text
                    prerequisite_links = [link.get_attribute('href') for link in prerequisite_link_elements]
                    prerequisite_text = "See links: " + ", ".join(prerequisite_links)
                else:
                    # If there's no link, extract the text directly
                    prerequisite_full_text = prerequisite_element.text
                    prerequisite_text = prerequisite_full_text.split('Prerequisite:')[-1].strip()

                prerequisite = prerequisite_text

                # Write to CSV
                print(f"Course {course_code} found for {quarter_name}")
                writer.writerow([course_code, term, instructor, prerequisite])

            except Exception as e:
                pass

driver.quit()