from django import forms

from .models import UploadedCSV


class CSVUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedCSV
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(
                attrs={
                    "class": "block w-full text-sm text-slate-300 "
                    "file:mr-4 file:py-2 file:px-4 file:rounded-lg "
                    "file:border-0 file:text-sm file:font-semibold "
                    "file:bg-gold file:text-primary-900 "
                    "hover:file:bg-amber-400 cursor-pointer",
                    "accept": ".csv",
                }
            ),
        }
