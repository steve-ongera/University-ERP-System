from django import forms
from .models import StudentComment


class StudentCommentForm(forms.ModelForm):
    class Meta:
        model = StudentComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter your comment or question here...'
            })
        }
