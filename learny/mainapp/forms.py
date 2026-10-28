from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Subject, Notes

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'department', 'year', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].required = False

class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'department', 'year', 'description']

class NotesForm(forms.ModelForm):
    class Meta:
        model = Notes
        fields = ['subject', 'file']
