from buildings.models import Building

from django import forms

from django_select2.forms import Select2MultipleWidget

from tasks.models import Task, TaskComment

from users.models import CmmsUser


class TaskCommentForm(forms.ModelForm):
    comment_text = forms.CharField(
        label="", widget=forms.Textarea(attrs={"class": "form-control", "rows": "3"})
    )

    class Meta:
        model = TaskComment
        fields = ["comment_text"]


class CustomClearableFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class MultipleFileField(forms.FileField):
    def to_python(self, data):
        if not data:
            return []
        if isinstance(data, list):
            return data
        return [data]


class TaskForm(forms.ModelForm):
    attachments = MultipleFileField(
        widget=CustomClearableFileInput(),
        required=False,
    )
    assigned_person = forms.ModelMultipleChoiceField(
        queryset=CmmsUser.objects.all(),
        widget=Select2MultipleWidget(
            attrs={"class": "form-control", "data-placeholder": "---------"}
        ),
        required=True,
    )
    building = forms.ModelMultipleChoiceField(
        queryset=Building.objects.all(),
        widget=Select2MultipleWidget(
            attrs={"class": "form-control", "data-placeholder": "---------"}
        ),
        required=True,
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "deadline",
            "category",
            "priority",
            "description",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Wpisz tytuł zadania"}
            ),
            "deadline": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "placeholder": "Wybierz termin wykonania",
                },
            ),
            "category": forms.Select(
                attrs={"class": "form-control", "placeholder": "Wybierz kategorię"}
            ),
            "priority": forms.Select(
                attrs={"class": "form-control", "placeholder": "Wybierz priorytet"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "placeholder": "Wpisz opis zadania"}
            ),
        }


class TaskFilterForm(forms.Form):
    assigned_person = forms.ModelChoiceField(
        queryset=CmmsUser.objects.all(),
        required=False,
        label="Przypisana osoba",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    status_field = forms.ChoiceField(
        choices=[("", "---------")] + Task.STATUS_CHOICES,
        required=False,
        label="Status",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    category = forms.ChoiceField(
        choices=[("", "---------")] + Task.CATEGORY_CHOICES,
        required=False,
        label="Kategoria",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    priority = forms.ChoiceField(
        choices=[("", "---------")] + Task.PRIORITY_CHOICES,
        required=False,
        label="Priorytet",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    start_date = forms.DateField(
        required=False,
        label="Data utworzenia (od)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    end_date = forms.DateField(
        required=False,
        label="Data utworzenia (do)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    closed_start = forms.DateField(
        required=False,
        label="Data zamknięcia (od)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    closed_end = forms.DateField(
        required=False,
        label="Data zamknięcia (do)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    deadline_start = forms.DateField(
        required=False,
        label="Deadline (od)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    deadline_end = forms.DateField(
        required=False,
        label="Deadline (do)",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
