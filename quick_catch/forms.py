from django import forms

from .models import ENERGY_LEVELS, BrainDump


class BrainDumpForm(forms.ModelForm):
    """Form for brain dump entry: input text and energy level."""

    energy_level = forms.ChoiceField(
        choices=[(x, x.capitalize()) for x in ENERGY_LEVELS],
        widget=forms.RadioSelect(attrs={"class": "radio"}),
    )

    class Meta:
        model = BrainDump
        fields = ("input_text", "energy_level")
        widgets = {
            "input_text": forms.Textarea(
                attrs={
                    "class": "textarea textarea-bordered w-full min-h-[12rem]",
                    "placeholder": "Type or paste everything on your mind...",
                    "rows": 12,
                }
            ),
        }

    def clean_input_text(self):
        value = self.cleaned_data.get("input_text") or ""
        value = value.strip()
        if not value:
            raise forms.ValidationError("Please enter some text before processing.")
        return value
