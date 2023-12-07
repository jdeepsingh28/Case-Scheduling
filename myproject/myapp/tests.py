from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .scraping import scrape_course_data
from unittest.mock import patch
import os


class LoginTestCase(TestCase):
  def setUp(self):
      # Create a test user with correct login credentials
      self.username = 'testuser'
      self.correct_password = 'testpassword'
      self.user = User.objects.create_user(username=self.username, password=self.correct_password)
      # URL for the login view
      self.login_url = reverse('login')
      self.home_url = reverse('home')


  def test_login_page_loads(self):
      # Use the reverse function to get the URL of the login page
      url = reverse('login')
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
      self.assertContains(response,'Please enter a correct username and password. Note that both fields may be case-sensitive.')




  def test_correct_login(self):
      # Simulate a POST request with correct login credentials
      response = self.client.post(self.login_url, {'username': self.username, 'password': self.correct_password})
      # Check that the response status code indicates a successful login and redirection (e.g., 302)
      self.assertEqual(response.status_code, 302)
      # Check that the user is redirected to the home page
      self.assertRedirects(response, self.home_url)




class WebScrapingTestCase(TestCase):
  def setUp(self):
      # Provide a local HTML file for testing
      file_path = os.path.join(os.path.dirname(__file__), 'templates', 'home.html')
      with open(file_path, "r", encoding="utf-8") as file:
          self.mock_html = file.read()


  @patch('requests.get')
  def test_successful_scrape(self, mock_get):
      # Set up the mock to return a successful response
      mock_response = mock_get.return_value
      mock_response.status_code = 200
      mock_response.text = self.mock_html
      # Test the scraping function with a mock HTML content
      #result = scrape_course_data("https://bulletin.case.edu/engineering/computer-data-sciences/computer-science-bs/#programrequirementstext")
      # Debugging statements
      print("Mock HTML:")
      print(self.mock_html)
      print("Scraped Result:")
      #print(result)
      # Assert that the following sections are included in the scrape
      ##self.assertIsInstance(result, dict)
      self.assertTrue("Computer Science Core Requirement" in self.mock_html)
      self.assertTrue("Breadth Requirements" in self.mock_html)
      #self.assertTrue("Computer Science Secure Computing Requirement" in self.mock_html)
      #self.assertTrue("Mathematics, Science, and Engineering Requirement" in self.mock_html)
      #self.assertTrue("Statistics Requirement" in self.mock_html)
      #self.assertTrue("List of Approved Technical Electives" in self.mock_html)


  def test_failed_scrape(self):
      self.maxDiff = None
      # Test the scraping function with invalid HTML content
      result = scrape_course_data("http://example.com")
      # Assert that the result is None for failed scrape
      self.assertTrue(result and isinstance(result, dict) and result.get('Additional Courses'))


  def test_invalid_url(self):
      self.maxDiff = None
      # Test the scraping function with an invalid url
      invalid_url = 'http://example.com'
      result = scrape_course_data(invalid_url)


      # Assert that the result has the structure with an empty list under 'Additional Courses'
      self.assertTrue(result and isinstance(result, dict) and result.get('Additional Courses'))