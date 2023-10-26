from django.shortcuts import render, redirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .scraping import scrape_course_data

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
            print(scraped_data)  # Printing the scraped data to console

    return render(request, 'home.html', {
        'majors': major_urls.keys(),
        'scraped_data': scraped_data
    })


def get_major_info(major):
    # Your logic to get and return major-related information
    if major == "major1":
        return "Information related to Major 1"
    elif major == "major2":
        return "Information related to Major 2"