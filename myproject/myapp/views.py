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
            breadth_requirements = defaultdict(list)
            for item in scraped_data.get('Computer Science Breadth Requirement', []):
                for breadth_area, details in item.items():
                    for course in details['courses']:
                        course['breadth_area'] = breadth_area
                        course['requirement'] = f"Number of classes needed: {details['requirement']}"
                        breadth_requirements[breadth_area].append(course)

            # Convert defaultdict to regular dict for template
            breadth_requirements = dict(breadth_requirements)

    return render(request, 'home.html', {
        'majors': major_urls.keys(),
        'scraped_data': scraped_data,
        'core_requirements': core_requirements,
        'breadth_requirements': breadth_requirements
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
        # Dictionaries to store course data
        course_data = {}

        for key, value in request.POST.items():
            if 'interest_' in key:
                course_code = key.split('_')[1]
                # Initialize the course data entry if not present
                if course_code not in course_data:
                    course_data[course_code] = {'interest': None, 'taken': False}
                # Update interest level
                course_data[course_code]['interest'] = value
            elif 'taken_' in key:
                course_code = key.split('_')[1]
                # Initialize the course data entry if not present
                if course_code not in course_data:
                    course_data[course_code] = {'interest': None, 'taken': False}
                # Update taken status
                course_data[course_code]['taken'] = (value == 'on')

        course_data = scrape_course_data("https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext")

        # Generate the schedule using the create_schedule function
        schedule = create_schedule2(course_data)

        # Pass course_data and schedule to your template
        return render(request, 'schedule_page.html', {'course_data': course_data, 'schedule': schedule})

    return redirect('home')  # Redirect to home page if not a POST request

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
