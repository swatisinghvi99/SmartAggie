import requests
from bs4 import BeautifulSoup
import csv

# Step 1: Fetch the list of course categories
categories_url = 'https://catalog.ucdavis.edu/courses-subject-code/'
response = requests.get(categories_url)
soup = BeautifulSoup(response.text, 'html.parser')
category_links = []
for category in soup.find_all('h2', class_='letternav-head'):
    for a in category.find_next_sibling('ul').find_all('a', href=True):
        category_links.append((a.text, 'https://catalog.ucdavis.edu' + a['href']))

# Step 2: Visit each category URL to extract courses
courses = []

for name, url in category_links:
    resp = requests.get(url)
    category_soup = BeautifulSoup(resp.text, 'html.parser')

    print(f"Extracting courses for {name}")

    # Extract courses
    for courseblock in category_soup.find_all('div', class_='courseblock'):
        subject_code = courseblock.find('span', class_='detail-code').b.text.split()[0]
        course_code = courseblock.find('span', class_='detail-code').b.text
        course_name = courseblock.find('span', class_='detail-title').b.text.strip('— ').strip()
        course_units = courseblock.find('span', class_='detail-hours_html').b.text.strip('()')
        course_desc_element = courseblock.find('p', class_='courseblockextra')
        if course_desc_element:
            course_desc_full_text = course_desc_element.text.strip()
            prefix = "Course Description:"
            if course_desc_full_text.startswith(prefix):
                course_desc = course_desc_full_text[len(prefix):].strip()
            else:
                course_desc = course_desc_full_text
    
        courses.append([subject_code, name, course_code, course_name, course_desc, course_units])

# Step 3: Write the data to a CSV file
with open('ucdavis_courses.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Subject Code', 'Subject Name', 'Course Code', 'Course Name', 'Course Description', 'Course Units'])
    writer.writerows(courses)

print("CSV file has been created.")
