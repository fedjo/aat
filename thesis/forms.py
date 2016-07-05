from django import forms

class VideoForm(forms.Form):
    title = "Please upload your video"
    video = forms.FileField()
