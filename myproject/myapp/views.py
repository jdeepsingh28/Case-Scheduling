from django.shortcuts import render, redirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .scraping import scrape_course_data
from .forms import CreateAccountForm
from .breadth_reformat import reformat_breadth_requirements
from collections import defaultdict
from .scraping import create_schedule2
from .scraping import create_random_schedule
import re

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def home_view(request):
    scraped_data = None
    core_requirements = None
    breadth_requirements = None
    math_requirements = None

    # Define the majors and corresponding URLs
    major_urls = {
        "Computer Science": "https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext",
        "Mechanical Aerospace Engineering": "https://bulletin.case.edu/engineering/mechanical-aerospace-engineering/aerospace-engineering-bse/#programrequirementstext",
    }

    if request.method == "POST":
        selected_major = request.POST.get('major')
        url = major_urls.get(selected_major)
        if url:
            scraped_data = scrape_course_data(url)
            core_requirements = scraped_data.get('Computer Science Core Requirement', [])
            math_requirements = scraped_data.get("Mathematics, Science and Engineering Requirement", [])
            breadth_requirements = defaultdict(list)
            for item in scraped_data.get('Computer Science Breadth Requirement', []):
                for breadth_area, details in item.items():
                    for course in details['courses']:
                        course['breadth_area'] = breadth_area
                        course['requirement'] = f"Number of classes needed: {details['requirement']}"
                        breadth_requirements[breadth_area].append(course)
            for course in math_requirements:
                course['show_interest'] = 'or' in course['name'].lower() and re.search(r'or [A-Z]{4}',course['name']) is not None
            # Convert defaultdict to regular dict for template
            breadth_requirements = dict(breadth_requirements)

    return render(request, 'home.html', {
        'majors': major_urls.keys(),
        'scraped_data': scraped_data,
        'core_requirements': core_requirements,
        'breadth_requirements': breadth_requirements,
        'math_requirements': math_requirements
    })


def create_account_view(request):
    if request.method == 'POST':
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # Redirect to the login page or any other page you prefer
    else:
        form = CreateAccountForm()
    return render(request, 'createnewaccount.html', {'form': form})


def schedule_view(request):
    if request.method == 'POST':
        user_course_selections = {}

        course_data = scrape_course_data("https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext")
        core_requirements = course_data.get('Computer Science Core Requirement', [])
        breadth_requirements = defaultdict(list)
        for item in course_data.get('Computer Science Breadth Requirement', []):
            for breadth_area, details in item.items():
                for course in details['courses']:
                    course['breadth_area'] = breadth_area
                    course['requirement'] = f"Number of classes needed: {details['requirement']}"
                    breadth_requirements[breadth_area].append(course)

        for key, value in request.POST.items():
            if key.startswith('interest_') or key.startswith('taken_'):
                course_code = key.split('_')[1]
                if course_code not in user_course_selections:
                    user_course_selections[course_code] = {'interest': 'neutral', 'taken': False}

                if key.startswith('interest_'):
                    user_course_selections[course_code]['interest'] = value
                elif key.startswith('taken_'):
                    user_course_selections[course_code]['taken'] = (value == 'on')

        # Call your create_schedule2 function here with the user_course_selections
        schedule = create_schedule2(course_data, user_course_selections)

        # Render your schedule page with the generated schedule
        return render(request, 'schedule_page.html', {'schedule': schedule})

from django.shortcuts import render

def random_schedule_view(request):
    if request.method == 'POST':

        course_data = scrape_course_data("https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext")
        # Logic to create a random schedule
        random_schedule = create_random_schedule(course_data)

        # Render a template with the random schedule
        return render(request, 'random_schedule_template.html', {'schedule': random_schedule})
    
    # Redirect or show an error if the request is not POST
    return redirect('home') 
