from collections import defaultdict
from random import sample
import re
from bs4 import BeautifulSoup
import requests

def scrape_additional_courses(url, existing_codes):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the webpage. Status Code: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    additional_courses = []
    unique_course_codes = set(code[:8] for code in existing_codes)  # Create a set of unique course codes

    for tag in soup.find_all(['p', 'strong'], class_='courseblocktitle'):
        course_info = tag.get_text().strip()
        course_parts = course_info.split(". ")
        if len(course_parts) < 3:
            continue

        course_code = course_parts[0]
        # Check if the first 8 characters of the course code are not already in the set
        if course_code[:8] not in unique_course_codes:
            course_name = course_parts[1]
            hours_text = course_parts[2]
            hours = int(re.search(r'\d+', hours_text).group()) if re.search(r'\d+', hours_text) else 0

            additional_courses.append({
                'code': course_code,
                'name': course_name,
                'hours': hours
            })
            unique_course_codes.add(course_code[:8])  # Add the first 8 characters of the course code to the set

    return additional_courses


def scrape_course_data(url):
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to retrieve the webpage. Status Code: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    result_dict = defaultdict(list)
    last_hours = None
    current_section = None
    current_breadth = None
    last_course_data = None
    existing_course_codes = set()

    elements = soup.find_all(['h3', 'tr', 'div'])

    for tag in elements:
        if tag.name == 'div' and tag.get('id') == 'planofstudytextcontainer':
            break

        if tag.name == 'h3':
            current_section = tag.text.strip()
            last_hours = None
            last_course_data = None
            continue

        if 'areaheader' in tag.get('class', []) and 'Breadth Area' in tag.text:
            current_breadth = tag.text.strip()
            print(current_breadth)
            result_dict[current_section].append({current_breadth: {"courses": [], "requirement": 2}})
            continue

        if tag.name == 'tr':
            # Check for alternate class (orclass)
            if 'orclass' in tag.get('class', []):
                if last_course_data:
                    codecol = tag.find('td', {'class': 'codecol orclass'})
                    namecol = tag.find_all('td')[1] if len(tag.find_all('td')) > 1 else None

                    course_code = codecol.text.strip().replace(u'\xa0', u' ') if codecol else last_course_data['code']
                    course_name = namecol.text.strip() if namecol else ''
                    course_data = {
                        'code': course_code,
                        'name': course_name,
                        'hours': last_course_data['hours'],
                        'alternate': last_course_data['name']
                    }
                    if current_breadth and result_dict[current_section] and current_breadth in \
                            result_dict[current_section][-1]:
                        result_dict[current_section][-1][current_breadth]["courses"].append(course_data)
                    else:
                        result_dict[current_section].append(course_data)
                continue

            codecol = tag.find('td', {'class': 'codecol'})
            namecol = tag.find_all('td')[1] if len(tag.find_all('td')) > 1 else None
            hourscol = tag.find('td', {'class': 'hourscol'})

            if codecol and namecol:
                course_code = codecol.text.strip().replace(u'\xa0', u' ')
                if re.match(r'^[A-Za-z]{4}\s\d{3}$', course_code):
                    course_data = {
                        'code': course_code,
                        'name': namecol.text.strip(),
                        'hours': int(
                            hourscol.text.strip()) if hourscol and hourscol.text.strip().isdigit() else last_hours
                    }
                    if current_breadth and result_dict[current_section] and current_breadth in \
                            result_dict[current_section][-1]:
                        result_dict[current_section][-1][current_breadth]["courses"].append(course_data)
                    else:
                        result_dict[current_section].append(course_data)
                    last_course_data = course_data

        if last_course_data:
            existing_course_codes.add(last_course_data['code'])

    additional_courses = scrape_additional_courses("https://bulletin.case.edu/course-descriptions/csds/",
                                                   existing_course_codes)
    # Integrate additional_courses into result_dict
    for course in additional_courses:
        result_dict['Additional Courses'].append(course)

    return dict(result_dict)


def create_schedule2(course_data, user_course_selections):
    schedule = []

    # Add all classes from "Computer Science Core Requirement" that have not been taken
    for course in course_data.get("Computer Science Core Requirement", []):
        if not user_course_selections.get(course['code'], {}).get('taken', False):
            schedule.append(course['name'])

    # Add two most interested classes from each "Breadth Area" that have not been taken
    breadth_requirement = course_data.get("Computer Science Breadth Requirement", [])
    for area_dict in breadth_requirement:
        for area, area_data in area_dict.items():
            breadth_courses = [c for c in area_data['courses'] if not user_course_selections.get(c['code'], {}).get('taken', False)]
            # Sort by interest level
            breadth_courses.sort(key=lambda x: ('interested', 'neutral', 'ignore').index(user_course_selections.get(x['code'], {}).get('interest', 'neutral')))
            selected_courses = breadth_courses[:2]
            schedule.extend(c['name'] for c in selected_courses)

    # Add one most interested class from "Computer Science Secure Computing Requirement" that has not been taken
    security_courses = [c for c in course_data.get("Computer Science Secure Computing Requirement", []) if not user_course_selections.get(c['code'], {}).get('taken', False)]
    if security_courses:
        security_courses.sort(key=lambda x: ('interested', 'neutral', 'ignore').index(user_course_selections.get(x['code'], {}).get('interest', 'neutral')))
        schedule.append(security_courses[0]['name'])

    # Add the most interested class from the "Statistics Requirement" that has not been taken
    statistics_courses = [c for c in course_data.get("Statistics Requirement", []) if not user_course_selections.get(c['code'], {}).get('taken', False)]
    if statistics_courses:
        statistics_courses.sort(key=lambda x: ('interested', 'neutral', 'ignore').index(user_course_selections.get(x['code'], {}).get('interest', 'neutral')))
        schedule.append(statistics_courses[0]['name'])

    # Return the schedule
    return schedule


def create_random_schedule(data):
    schedule = []

    # Add all classes from "Computer Science Core Requirement"
    schedule.extend(c['code'] for c in data['Computer Science Core Requirement'])

    # Add two classes from each "Breadth Area"
    breadth_requirement = data.get("Computer Science Breadth Requirement", [])
    for area_dict in breadth_requirement:
        for area, area_data in area_dict.items():
            breadth_courses = area_data['courses']
            selected_courses = sample(breadth_courses, min(len(breadth_courses), 2))
            schedule.extend(c['code'] for c in selected_courses)

    # Add one class from "Computer Science Secure Computing Requirement"
    security_courses = data.get("Computer Science Secure Computing Requirement", [])
    if security_courses:
        schedule.append(security_courses[0]['code'])

    # Ensure the schedule contains up to 25 classes with the prefix "CSDS"
    additional_csds_courses = [c['code'].replace('\xa0', ' ') for c in data.get("Additional Courses", []) if c['code'].startswith("CSDS")]
    available_courses = additional_csds_courses[:49]  # Consider only the first 54 courses so that we do not get to graduate courses
    courses_to_add = 23 - len(schedule)  # Calculate how many courses to add to get to 20

    if courses_to_add > 0 and available_courses:
        selected_additional_courses = sample(available_courses, min(len(available_courses), courses_to_add))
        schedule.extend(course for course in selected_additional_courses if course not in schedule)

    # Add classes from "Mathematics, Science and Engineering Requirement", excluding those that start with "or"
    for course in data.get("Mathematics, Science and Engineering Requirement", []):
        course_name = course['name'].lower()
        course_code = course['code'].replace('\xa0', ' ')
        if not course_code.startswith('or'):
            schedule.append(course_code)
    
    # Add one class from the "Statistics Requirement"
    statistics_courses = data.get("Statistics Requirement", [])
    if statistics_courses:
        schedule.append(statistics_courses[2]['code'])
   
    schedule.append("UGER 1")
    schedule.append("UGER 2")
    schedule.append("UGER 3")
    schedule.append("UGER 4")
    schedule.append("OOM 1")
    schedule.append("OOM 2")
    schedule.append("OOM 3")
    schedule.append("OOM 4")
    schedule.append("OOM 5")
    schedule.append("OOM 6")
    return schedule


if __name__ == "__main__":
    data = scrape_course_data("https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext")
    print(data)
    print(create_schedule2(data))
    #print(json.dumps(data,indent=4))