from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from stats.models import Account


class DateInput(forms.DateField):
    input_type = 'date'


def validate_account_id(value: int):
    try:
        Account.objects.get(pk=value)
    except Account.DoesNotExist:
        raise ValidationError(f'Konta z ID {value} nie ma w bazie!')


class AccountIdField(forms.IntegerField):
    def __init__(self, **kwargs):
        super().__init__(
            label='ID konta',
            widget=forms.TextInput,
            required=True,
            min_value=1,
            error_messages={
                'required': 'Wpisz ID konta!',
                'invalid': 'ID konta musi być liczbą!',
                'min_value': 'ID konta musi być większe od 0!'
            },
            validators=[validate_account_id], **kwargs
        )


class SearchAccountForm(forms.Form):
    account_id = AccountIdField()
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


class FollowAccountForm(forms.Form):
    account_id = AccountIdField()


class MyAuthenticationForm(AuthenticationForm):
    username = UsernameField(
        label='Login',
        widget=forms.TextInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label='Hasło',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )


class RegistrationForm(UserCreationForm):
    password1 = forms.CharField(
        label='Hasło',
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Powtórz hasło",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'email')
        labels = {
            'username': 'Login',
            'email': 'Email',
        }
        help_texts = {
            'username': None,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
