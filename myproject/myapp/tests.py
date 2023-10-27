from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
class LoginTestCase(TestCase):

    def setUp(self):
        # Create a test user with correct login credentials
        self.username = 'testuser'
        self.correct_password = 'testpassword'
        self.user = User.objects.create_user(username=self.username, password=self.correct_password)

        # URL for the login view
        self.login_url = reverse('login')  # Replace 'login' with the actual name of your login view

    def test_login_page_loads(self):
        # Use the reverse function to get the URL of the login page
        url = reverse('login')  # Use the name 'login' associated with the login URL

        # Perform an HTTP GET request to the login page
        response = self.client.get(url)

        # Check that the response status code is 200, indicating a successful page load
        self.assertEqual(response.status_code, 200)

        # Check that the login form is present on the page
        self.assertContains(response, '<form method="post">')

        # Check for the presence of the CSRF token input field
        self.assertContains(response, '<input type="hidden" name="csrfmiddlewaretoken"')

    def test_incorrect_login(self):
        # Simulate a POST request with incorrect login credentials
        incorrect_password = 'incorrectpassword'
        response = self.client.post(self.login_url, {'username': self.username, 'password': incorrect_password})

        # Check that the response status code indicates a failed login (e.g., 200 for displaying the login page)
        self.assertEqual(response.status_code, 200)

        # Check that the response contains an error message or specific text indicating a failed login
        self.assertContains(response, 'Please enter a correct username and password. Note that both fields may be case-sensitive.')

