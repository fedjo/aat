from django import forms


class DefaultDetectionForm(forms.Form):
    title = "Please specify the directory containing your videos"
    video = forms.FileField(required=True, widget=forms.ClearableFileInput())
    #video_dir = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}),
    #                            required=True)

    detection = forms.CharField(widget=forms.HiddenInput(),
                                    required=True, initial=False)
    recognizer = forms.CharField(widget=forms.HiddenInput(),
                                 required=True, initial=False)
    objdetection = forms.CharField(widget=forms.HiddenInput(),
                                   required=True, initial=False)
    transcription = forms.CharField(widget=forms.HiddenInput(),
                                    required=True, initial=False)


class ComplexDetectionForm(forms.Form):

    CHOICES = [('Yes', 'Yes'),
               ('No', 'No')]

    title = "Please upload your video in zip format"
    video = forms.FileField(required=True, widget=forms.ClearableFileInput())
    #video_dir = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}),
    #                            required=True)

    detection = forms.CharField(widget=forms.HiddenInput(),
                                    required=True, initial=False)
    recognizer = forms.ChoiceField(choices=[('LBPH', 'Local Binary Patterns Histogram'),
						                    ('EF', 'Eighen Faces'),
						                    ('FF', 'Fisher Faces'),
						                    #('KNN', 'LBPH using K-Nearest Neighbor'),
                                            ('false', 'Do not recognize faces')],
                                            widget=forms.Select(attrs={'class': 'form-control '
                                                'select select-primary', 'data-toggle': 'select'}))
    objdetection = forms.CharField(widget=forms.HiddenInput(),
                                   required=True, initial=False)
    transcription = forms.CharField(widget=forms.HiddenInput(),
                                    required=True, initial=False)

    iszip = forms.ChoiceField(choices=CHOICES,
                              widget=forms.RadioSelect(attrs={'data-toggle': 'radio'}))

    scale = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}))
    neighbors = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    min_x_dimension = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))
    min_y_dimension = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control'}))

    bounding_boxes = forms.BooleanField(required=False)

    # facesdb = forms.FileField(required=False, widget=forms.ClearableFileInput())
