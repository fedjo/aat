from django import forms

class VideoForm(forms.Form):

    CHOICES = [('Yes', 'Yes'),
               ('No', 'No')]

    title = "Please upload your video in zip format"
    video_dir = "" 
    video = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
    recognizer = forms.MultipleChoiceField(choices=[('LBPH', 'Local Binary Patterns Histogram'),
						    ('EF', 'Eighen Faces'),
						    ('FF', 'Fisher Faces')],
                            widget=forms.Select(attrs={'class': 'form-control select select-primary', 'data-toggle': 'select'}))
    iszip = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(attrs={'data-toggle': 'radio'}))

class PostForm(forms.Form):
    title = "Please specify the directory containing your videos"
    video_dir = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    video_path = forms.FilePathField(path='/home/yiorgos/',  allow_folders=True)


