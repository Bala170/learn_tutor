
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
	ROLE_CHOICES = (
		('teacher', 'Teacher'),
		('student', 'Student'),
	)
	role = models.CharField(max_length=10, choices=ROLE_CHOICES)
	department = models.CharField(max_length=100)
	year = models.PositiveIntegerField(null=True, blank=True)

	def __str__(self):
		return f"{self.username} ({self.role})"


class Subject(models.Model):
	name = models.CharField(max_length=200)
	department = models.CharField(max_length=100)
	year = models.PositiveIntegerField()
	description = models.TextField(blank=True, null=True)
	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subjects')

	def __str__(self):
		return self.name


class Notes(models.Model):
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name="notes")
    file = models.FileField(upload_to='notes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # NEW FIELDS
    faiss_index_path = models.CharField(max_length=255, blank=True, null=True)
    chunks_path = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.subject.name} - Notes {self.id}"

# Create your models here.
