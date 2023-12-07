from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .scraping import scrape_course_data
from .forms import CreateAccountForm
from collections import defaultdict
from .scraping import create_schedule2
from .scraping import create_random_schedule
import re
from .models import SavedSchedule
import json


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

        semester_blocks = [schedule[i:i + 5] for i in range(0, len(schedule), 5)]

        # Render your schedule page with the generated schedule
        return render(request, 'schedule_page.html', {'schedule': semester_blocks})

from django.shortcuts import render

def random_schedule_view(request):
    if request.method == 'POST':

        course_data = scrape_course_data("https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext")
        # Logic to create a random schedule
        random_schedule = create_random_schedule(course_data)

        semester_blocks = [random_schedule[i:i + 5] for i in range(0, len(random_schedule), 5)]

        # Render a template with the random schedule
        return render(request, 'random_schedule_template.html', {'schedule': semester_blocks})
    
    # Redirect or show an error if the request is not POST
    return redirect('home')

@login_required
def saved_schedules_view(request):
    if request.method == 'POST':
        schedule_data = request.POST.get('schedule_data')
        if schedule_data:
            schedule = json.loads(schedule_data)

            # Save the schedule to the database
            saved_schedule = SavedSchedule(user=request.user, schedule=schedule)
            saved_schedule.save()

            # Redirect to a confirmation page or back to the schedule page
            return redirect('saved_schedules')

        # If not POST request, show saved schedules
    saved_schedules = SavedSchedule.objects.filter(user=request.user)
    return render(request, 'saved_schedules.html', {'saved_schedules': saved_schedules})


from django.shortcuts import get_object_or_404
from .models import SavedSchedule
from .scraping import scrape_course_data
from collections import defaultdict

def edit_schedule_view(request, schedule_id):
    saved_schedule = get_object_or_404(SavedSchedule, pk=schedule_id, user=request.user)

    if request.method == 'POST':
        # Retrieve the updated schedule data from the POST request
        schedule_data_json = request.POST.get('schedule_data')
        if schedule_data_json:
            # Update the saved schedule with new data
            schedule_data = json.loads(schedule_data_json)
            saved_schedule.schedule = schedule_data
            saved_schedule.save()
            return redirect('saved_schedules') # Redirect to saved schedules page or other confirmation page

    # Load the existing schedule for editing
    existing_schedule = saved_schedule.schedule
    # Convert your existing schedule format to the format expected by your HTML template
    # For example, if your existing schedule is a list of semesters with courses, you might need to reformat it
    # to match the structure expected by the front-end. This step depends on how your front-end expects the data.
    formatted_schedule = convert_to_frontend_format(existing_schedule)

    return render(request, 'schedule_page.html', {'schedule': formatted_schedule, 'schedule_id': schedule_id})

def convert_to_frontend_format(schedule):
    # Implement this function based on how your front-end expects the data
    # For instance, if your front-end expects a list of semesters with courses, format the data accordingly
    formatted_schedule = []
    # Example conversion logic
    for semester in schedule:
        semester_courses = [{'code': course['code'], 'name': course['name'], 'hours': course['hours']} for course in semester['courses']]
        formatted_schedule.append(semester_courses)
    return formatted_schedule

