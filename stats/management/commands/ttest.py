from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.first()
        token = PasswordResetTokenGenerator().make_token(user)
        print(token)
        print(PasswordResetTokenGenerator().check_token(user, token))