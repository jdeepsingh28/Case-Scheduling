import json
from collections import defaultdict
from bs4 import BeautifulSoup
import requests


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
    current_breadth_requirement = None

    for tag in soup.find_all(['h3', 'tr']):
        if tag.name == 'h3':
            current_section = tag.text.strip()
            last_hours = None  # Reset the last_hours whenever a new section starts
            continue

        if 'areaheader' in tag.get('class', []) and 'Breadth Area' in tag.text:
            current_breadth = tag.text.strip()
            result_dict[current_section].append({current_breadth: {"courses": [], "requirement": None}})
            continue

        if 'areasubheader' in tag.get('class', []) and 'Choose' in tag.text:
            current_breadth_requirement = tag.find('td').get('colspan')
            if current_breadth and result_dict[current_section] and current_breadth in result_dict[current_section][-1]:
                result_dict[current_section][-1][current_breadth][
                    "requirement"] = f"Number of classes needed: {current_breadth_requirement}"
            continue

        if tag.name == 'tr' and 'areaheader' not in tag.get('class', []):
            course_data = {}

            codecol = tag.find('td', {'class': 'codecol'})
            if codecol:
                course_data['code'] = codecol.text.strip().replace(u'\xa0', u' ')

            namecol = tag.find_all('td')[1] if len(tag.find_all('td')) > 1 else None
            if namecol:
                course_data['name'] = namecol.text.strip()

            hourscol = tag.find('td', {'class': 'hourscol'})
            if hourscol and hourscol.text.strip().isdigit():
                last_hours = int(hourscol.text.strip())
                course_data['hours'] = last_hours
            else:
                course_data['hours'] = last_hours

            if course_data['hours']:  # only append if hours is not None
                if current_breadth and result_dict[current_section] and current_breadth in result_dict[current_section][-1]:
                    result_dict[current_section][-1][current_breadth]["courses"].append(course_data)
                else:
                    result_dict[current_section].append(course_data)

    return dict(result_dict)


