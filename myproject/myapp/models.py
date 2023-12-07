from django.db import models
from django.contrib.auth.models import User

class SavedSchedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    schedule = models.JSONField() # Or any other appropriate field type
    # Add other fields as needed, e.g., saved data, timestamp, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Schedule for {self.user.username}"
