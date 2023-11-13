import json
from collections import defaultdict
from bs4 import BeautifulSoup
import requests
import re


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

    return dict(result_dict)


if __name__ == "__main__":
    data = scrape_course_data("https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext")
    print(json.dumps(data,indent=4))