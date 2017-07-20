from django import forms

class PublicationImportForm(forms.Form):
    keywords = forms.CharField(required=True, widget=forms.Textarea,
        label='Keywords',
        help_text='Enter keywords for many papers. One paper per line.'
    )
