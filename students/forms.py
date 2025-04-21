from django import forms
from club_dashboard.models import Review

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, f"{i}⭐") for i in range(1, 6)],
        label="التقييم",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    comment = forms.CharField(
        label="التعليق",
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
