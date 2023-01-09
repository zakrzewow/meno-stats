from django.contrib import admin

from .models import Account, Character, Activity, Following

admin.site.register(Account)
admin.site.register(Character)
admin.site.register(Activity)
admin.site.register(Following)
