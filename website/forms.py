from django import forms
from . import models

class MemberUpdateForm(forms.ModelForm):
    picture = forms.ImageField(widget=forms.FileInput, required=False)
    del_pic = forms.BooleanField(required=False)

    class Meta:
        model = models.Member
        fields = ['email', 'thesis', 'picture', 'del_pic']
