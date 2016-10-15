from django import forms

class VideoForm(forms.Form):
    title = "Please upload your video in zip format"
    video_dir = "" 
    video = forms.FileField()
    recognizer = forms.MultipleChoiceField(choices=[('LBPH', 'Local Binary Patterns Histogram'),
						    ('EF', 'Eighen Faces'),
						    ('FF', 'Fisher Faces')])

class PostForm(forms.Form):
    title = "Please specify the directory containing your videos"
    video_dir = forms.CharField()
