from django import forms
from django.core.exceptions import ValidationError

from stats.models import Account


class DateInput(forms.DateField):
    input_type = 'date'


def validate_account_id(value: int):
    try:
        Account.objects.get(pk=value)
    except Account.DoesNotExist:
        raise ValidationError(f'Konta z ID {value} nie ma w bazie!')


class SearchAccountForm(forms.Form):
    account_id = forms.IntegerField(
        label='ID konta',
        widget=forms.TextInput,
        required=True,
        min_value=1,
        error_messages={
            'required': 'Wpisz ID konta!',
            'invalid': 'ID konta musi być liczbą!',
            'min_value': 'ID konta musi być większe od 0!'
        },
        validators=[validate_account_id]
    )
    activity_date = forms.DateField(
        label='Dzień',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    no_date_option = forms.ChoiceField(
        label='Gdy nie ma aktywności tego dnia',
        choices=(
            ('last', 'zwróć najnowszą'),
            ('first', 'zwróć najstarszą')
        )
    )
    follow = forms.BooleanField(
        label='Dodaj do listy obserwowanych',
        required=False
    )
