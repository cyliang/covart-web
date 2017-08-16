from django import forms
from . import models

class PublicationImportForm(forms.Form):
    keywords = forms.CharField(required=True, widget=forms.Textarea,
        label='Keywords',
        help_text='Enter keywords for many papers. One paper per line.'
    )


class MemberUpdateForm(forms.ModelForm):
    picture = forms.ImageField(widget=forms.FileInput, required=False)
    del_pic = forms.BooleanField(required=False)

    class Meta:
        model = models.Member
        fields = ['email', 'picture', 'del_pic']
