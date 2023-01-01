from django.contrib import admin

from .models import Account, Character, Activity

admin.site.register(Account)
admin.site.register(Character)
admin.site.register(Activity)
