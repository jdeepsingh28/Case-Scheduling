from collections import defaultdict
from random import sample
import re
from bs4 import BeautifulSoup
import requests
import random

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

        course_code = course_parts[0].replace("\xa0", " ")  # Replace \xa0 with a space
        if course_code[:8] not in unique_course_codes:
            course_name = course_parts[1]
            hours_text = course_parts[2]
            hours = int(re.search(r'\d+', hours_text).group()) if re.search(r'\d+', hours_text) else 0

            additional_courses.append({
                'code': course_code,
                'name': course_name,
                'hours': hours
            })
            unique_course_codes.add(course_code[:8])

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
            schedule.append({
                'code': course['code'],
                'name': course['name'],
                'hours': course['hours']
            })

    # Add up to two most interested classes from each "Breadth Area" that have not been taken
    breadth_requirement = course_data.get("Computer Science Breadth Requirement", [])
    for area_dict in breadth_requirement:
        for area, area_data in area_dict.items():
            # Filter out courses not taken
            not_taken_courses = [c for c in area_data['courses'] if
                                 not user_course_selections.get(c['code'], {}).get('taken', False)]

            # Count the number of courses already taken in this area
            taken_courses_count = len(area_data['courses']) - len(not_taken_courses)

            # Determine the number of courses to add based on taken courses
            courses_to_add = max(0, 2 - taken_courses_count)
            if courses_to_add == 0:
                continue

            # Sort by interest level
            not_taken_courses.sort(key=lambda x: ('interested', 'neutral', 'ignore').index(
                user_course_selections.get(x['code'], {}).get('interest', 'neutral')))
            selected_courses = not_taken_courses[:courses_to_add]
            schedule.extend({
                'code': c['code'],
                'name': c['name'],
                'hours': c['hours']
            } for c in selected_courses)

    # Check if any course in the "Computer Science Secure Computing Requirement" has been taken
    if any(user_course_selections.get(c['code'], {}).get('taken', False) for c in
           course_data.get("Computer Science Secure Computing Requirement", [])):
        # Skip adding a new secure computing course if one has already been taken
        pass
    else:
        # Add one most interested class from "Computer Science Secure Computing Requirement" that has not been taken
        security_courses = [c for c in course_data.get("Computer Science Secure Computing Requirement", []) if
                            not user_course_selections.get(c['code'], {}).get('taken', False)]
        if security_courses:
            security_courses.sort(key=lambda x: ('interested', 'neutral', 'ignore').index(
                user_course_selections.get(x['code'], {}).get('interest', 'neutral')))
            schedule.append({
                'code': security_courses[0]['code'],
                'name': security_courses[0]['name'],
                'hours': security_courses[0]['hours']
            })

    # Check if any course in the "Statistics Requirement" has been taken
    if any(user_course_selections.get(c['code'], {}).get('taken', False) for c in
           course_data.get("Statistics Requirement", [])):
        # Skip adding a new statistics course if one has already been taken
        pass
    else:
        # Add the most interested class from the "Statistics Requirement" that has not been taken
        statistics_courses = [c for c in course_data.get("Statistics Requirement", []) if
                              not user_course_selections.get(c['code'], {}).get('taken', False)]
        if statistics_courses:
            statistics_courses.sort(key=lambda x: ('interested', 'neutral', 'ignore').index(
                user_course_selections.get(x['code'], {}).get('interest', 'neutral')))
            schedule.append({
                'code': statistics_courses[0]['code'],
                'name': statistics_courses[0]['name'],
                'hours': statistics_courses[0]['hours']
            })

    # Mathematics, Science, and Engineering Requirement
    math_sci_eng_courses = course_data.get("Mathematics, Science and Engineering Requirement", [])
    for course in math_sci_eng_courses:
        # Exclude courses with codes starting with 'or'
        if not course['code'].startswith('or') and not user_course_selections.get(course['code'], {}).get('taken', False):
            schedule.append({
                'code': course['code'],
                'name': course['name'],
                'hours': course['hours']
            })

    # Add top two most interested classes from "List of Approved Technical Electives" that have not been taken
    technical_electives = course_data.get("List of Approved Technical Electives", [])
    elective_courses = [course for course in technical_electives if
                        not user_course_selections.get(course['code'], {}).get('taken', False)]
    # Sort by interest level
    elective_courses.sort(key=lambda x: ('interested', 'neutral', 'ignore').index(
        user_course_selections.get(x['code'], {}).get('interest', 'neutral')))
    selected_electives = elective_courses[:2]
    schedule.extend({
        'code': c['code'],
        'name': c['name'],
        'hours': c['hours']
    } for c in selected_electives)

    #add UGER placeholders and out of major classes for breadth
    schedule.append({
        'code': 'UGER 1',
        'name': 'Academic Inquiry Seminar',
        'hours': 3
    })
    schedule.append({
        'code': 'OOM 1',
        'name': 'Out Of Major 1',
        'hours': 3
    })
    schedule.append({
        'code': 'OOM 2',
        'name': 'Out Of Major 2',
        'hours': 3
    })
    schedule.append({
        'code': 'OOM 3',
        'name': 'Out Of Major 3',
        'hours': 3
    })
    schedule.append({
        'code': 'OOM 4',
        'name': 'Out Of Major 4',
        'hours': 3
    })
    schedule.append({
        'code': 'OOM 5',
        'name': 'Out Of Major 5',
        'hours': 3
    })
    schedule.append({
        'code': 'OOM 6',
        'name': 'Out Of Major 6',
        'hours': 3
    })

    # Add courses from "Additional Courses" if total courses are less than 39
    if len(schedule) < 39:
        additional_courses = [c for c in course_data.get("Additional Courses", []) if
                              not user_course_selections.get(c['code'], {}).get('taken', False)]
        # Sort by interest level
        additional_courses.sort(key=lambda x: ('interested', 'neutral', 'ignore').index(
            user_course_selections.get(x['code'], {}).get('interest', 'neutral')))

        # Separate high interest courses
        high_interest_courses = [c for c in additional_courses if
                                 user_course_selections.get(c['code'], {}).get('interest', 'neutral') == 'interested']
        other_courses = [c for c in additional_courses if c not in high_interest_courses][
                        :21]  # Take the first 21 from the rest

    # Add high interest courses first
    for course in high_interest_courses:
        if len(schedule) < 39:
            schedule.append({
                'code': course['code'],
                'name': course['name'],
                'hours': course['hours']
            })
        else:
            break

    # Randomly select from the other courses if there's still space
    while len(schedule) < 39 and other_courses:
        selected_course = random.choice(other_courses)

        # Check if the course is CSDS 296 or CSDS 297 and if the interest level is not 'interested'
        if selected_course['code'] in ['CSDS 296', 'CSDS 297'] and user_course_selections.get(selected_course['code'],
                                                                                              {}).get('interest',
                                                                                                            'neutral') != 'interested':
            continue  # Skip this course

        schedule.append({
            'code': selected_course['code'],
            'name': selected_course['name'],
            'hours': selected_course['hours']
        })
        other_courses.remove(selected_course)  # Remove the selected course to avoid duplicates

    # Return the schedule
    return schedule


def create_random_schedule(data):
    schedule = []

    # Add all classes from "Computer Science Core Requirement"
    schedule.extend({
        'code': c['code'],
        'name': c['name'],
        'hours': c['hours']
    } for c in data['Computer Science Core Requirement'])

    # Add two classes from each "Breadth Area"
    breadth_requirement = data.get("Computer Science Breadth Requirement", [])
    for area_dict in breadth_requirement:
        for area, area_data in area_dict.items():
            breadth_courses = area_data['courses']
            selected_courses = sample(breadth_courses, min(len(breadth_courses), 2))
            schedule.extend({
                'code': c['code'],
                'name': c['name'],
                'hours': c['hours']
            } for c in selected_courses)

    # Add one class from "Computer Science Secure Computing Requirement"
    security_courses = data.get("Computer Science Secure Computing Requirement", [])
    if security_courses:
        schedule.append({
            'code': security_courses[2]['code'],
            'name': security_courses[2]['name'],
            'hours': security_courses[2]['hours']
        })

    # Ensure the schedule contains up to 20 classes with the prefix "CSDS"
    additional_csds_courses = [
        {
            'code': c['code'].replace('\xa0', ' '),
            'name': c['name'],
            'hours': c['hours']
        }
        for c in data.get("Additional Courses", [])
        if c['code'].startswith("CSDS")
    ]

    # Consider only the first 22 courses so that we do not get to graduate courses
    available_courses = additional_csds_courses[:22]

    # Calculate how many courses to add to get to 20
    courses_to_add = 20 - len(schedule)

    if courses_to_add > 0 and available_courses:
        selected_additional_courses = sample(available_courses, min(len(available_courses), courses_to_add))
        # Add only the courses that are not already in the schedule
        for course in selected_additional_courses:
            if not any(c['code'] == course['code'] for c in schedule):
                schedule.append(course)

    # Add classes from "Mathematics, Science and Engineering Requirement", excluding those that start with "or"
    for course in data.get("Mathematics, Science and Engineering Requirement", []):
        course_name = course['name']
        course_code = course['code'].replace('\xa0', ' ')
        course_hours = course['hours']  # Assuming 'hours' is a key in your course data

        if not course_code.startswith('or'):
            schedule.append({
                'code': course_code,
                'name': course_name,
                'hours': course_hours
            })
    
    # Add one class from the "Statistics Requirement"
    statistics_courses = data.get("Statistics Requirement", [])
    if statistics_courses:
        schedule.append({
            'code': statistics_courses[2]['code'],
            'name': statistics_courses[2]['name'],
            'hours': statistics_courses[2]['hours']
        })

        # add UGER placeholders and out of major classes for breadth
        schedule.append({
            'code': 'UGER 1',
            'name': 'Academic Inquiry Seminar',
            'hours': 3
        })
        schedule.append({
            'code': 'OOM 1',
            'name': 'Out Of Major 1',
            'hours': 3
        })
        schedule.append({
            'code': 'OOM 2',
            'name': 'Out Of Major 2',
            'hours': 3
        })
        schedule.append({
            'code': 'OOM 3',
            'name': 'Out Of Major 3',
            'hours': 3
        })
        schedule.append({
            'code': 'OOM 4',
            'name': 'Out Of Major 4',
            'hours': 3
        })
        schedule.append({
            'code': 'OOM 5',
            'name': 'Out Of Major 5',
            'hours': 3
        })
        schedule.append({
            'code': 'OOM 6',
            'name': 'Out Of Major 6',
            'hours': 3
        })

    return schedule


if __name__ == "__main__":
    data = scrape_course_data("https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext")
    print(data)
    print(create_schedule2(data))
    #print(json.dumps(data,indent=4))