import requests
from bs4 import BeautifulSoup, NavigableString
import csv

def format_course_codes(prereq_element):
    if not prereq_element:
        return "None"
    if not prereq_element.find('a'):
        return prereq_element.get_text().replace('Prerequisite(s): ', '').strip()
    groups = []
    current_group = []
    for child in prereq_element.children:
        if child.name == 'a':
            course_code = child.get_text().replace(u'\xa0', u' ')
            current_group.append(course_code)
        elif isinstance(child, NavigableString) and ';' in child:
            if current_group:
                groups.append('/'.join(current_group))
                current_group = []
    if current_group:
        groups.append('/'.join(current_group))
    return ', '.join(groups)

# Step 1: Fetch the list of course categories
categories_url = 'https://catalog.ucdavis.edu/courses-subject-code/'
response = requests.get(categories_url)
soup = BeautifulSoup(response.text, 'html.parser')
category_links = []
for category in soup.find_all('h2', class_='letternav-head'):
    for a in category.find_next_sibling('ul').find_all('a', href=True):
        category_links.append((a.text, 'https://catalog.ucdavis.edu' + a['href']))

# Step 2: Visit each category URL to extract courses, including prerequisites
courses = []

for name, url in category_links:
    resp = requests.get(url)
    category_soup = BeautifulSoup(resp.text, 'html.parser')

    print(f"Extracting courses for {name}")

    for courseblock in category_soup.find_all('div', class_='courseblock'):
        subject_code = courseblock.find('span', class_='detail-code').b.text.split()[0]
        course_code = courseblock.find('span', class_='detail-code').b.text
        course_name = courseblock.find('span', class_='detail-title').b.text.strip('— ').strip()
        course_units = courseblock.find('span', class_='detail-hours_html').b.text.strip('()')

        # Extract course description
        course_desc_element = courseblock.find('p', class_='courseblockextra')
        course_desc = ""
        if course_desc_element:
            course_desc_full_text = course_desc_element.text.strip()
            prefix = "Course Description:"
            course_desc = course_desc_full_text[len(prefix):].strip() if course_desc_full_text.startswith(prefix) else course_desc_full_text

        # Extract prerequisites
        prereq_element = courseblock.find('p', class_='detail-prerequisite')
        prerequisites = format_course_codes(prereq_element)

        courses.append([subject_code, name, course_code, course_name, course_desc, course_units, prerequisites])

# Step 3: Write the data to a CSV file
with open('ucdavis_courses.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Subject Code', 'Subject Name', 'Course Code', 'Course Name', 'Course Description', 'Course Units', 'Prerequisites'])
    writer.writerows(courses)

print("CSV file has been created with prerequisites.")
