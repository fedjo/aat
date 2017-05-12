from django import forms

class VideoForm(forms.Form):

    CHOICES = [('Yes', 'Yes'),
               ('No', 'No')]

    title = "Please upload your video in zip format"
    video = forms.FileField(required=True, widget=forms.ClearableFileInput())
    recognizer = forms.ChoiceField(choices=[('LBPH', 'Local Binary Patterns Histogram'),
						    ('EF', 'Eighen Faces'),
						    ('FF', 'Fisher Faces'),
						    ('KNN', 'LBPH using K-Nearest Neighbor'),
                            ('No', 'Do not recognize faces')],
                            widget=forms.Select(attrs={'class': 'form-control select select-primary', 'data-toggle': 'select'}))
    Scale = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))
    Neighbors = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    Min_X_dimension = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    Min_Y_dimension = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    iszip = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect(attrs={'data-toggle': 'radio'}))
    #video_dir = forms.CharField(widget=forms.HiddenInput())

class PostForm(forms.Form):
    title = "Please specify the directory containing your videos"
    video_dir = forms.CharField(widget=forms.TextInput(attrs={'class': \
        'form-control'}), required=True)
    recognizer = forms.CharField(widget=forms.HiddenInput(), required=True, \
            initial=False)
    objdetection = forms.CharField(widget=forms.HiddenInput(), required=True, \
            initial=False)


