import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from stats.models import Account, Character, Activity


class Command(BaseCommand):
    """
    Komenda służąca do aktualizacji:
    - tabeli *stats_activity* z aktywnością graczy
    - tabeli *stats_character* z danymi o postaciach

    Uruchomienie: `py .\manage.py sstats`
    """
    def handle(self, *args, **options):
        last_now = None
        while True:
            now = datetime.now().replace(second=0, microsecond=0)
            # nowa minuta - pobieramy statystyki
            if last_now != now:
                last_now = now
                minute = now.hour * 60 + now.minute

                r = requests.get("https://www.margonem.pl/stats")
                soup = BeautifulSoup(r.text, 'html.parser')
                text = "".join([str(s) for s in soup.find_all("div", attrs={"class": "news-body"})[1:9:7]])
                profiles = re.findall(r'/profile/view,(\d+)#char_(\d+),(\w+)', text)

                for (aid, cid, world) in profiles:
                    account, _ = Account.objects.get_or_create(aid=aid)
                    char, _ = Character.objects.get_or_create(account=account, cid=cid, world=world)
                    activity, _ = Activity.objects.get_or_create(character=char, date=now.date())
                    a = bytearray(activity.activity)
                    a[minute // 8] += 2 ** (8 - minute % 8 - 1)
                    activity.activity = a
                    activity.save()
                print(f"Minuta {minute} - {len(profiles)} aktywnych graczy")
            # w międzyczasie uzupełniamy dane o profilach
            else:
                char = Character.objects.filter(lvl=None)[0]
                aid = char.account.aid
                cid = char.cid
                world = char.world
                r2 = requests.get(f"https://www.margonem.pl/profile/view,{aid}#char_{cid},{world}")
                soup = BeautifulSoup(r2.text, 'html.parser').find_all(attrs={"data-id": cid})[0]
                avatar_url = soup.find("span", attrs={"class": "cimg"})["style"][70:-3]
                nick = soup.find("input", attrs={"class": "chnick"})["value"]
                lvl = soup.find("input", attrs={"class": "chlvl"})["value"]
                prof = soup.find("input", attrs={"class": "chprof"})["value"]

                char.avatar_url = avatar_url
                char.nick = nick
                char.lvl = lvl
                char.prof = prof
                char.save()
            time.sleep(1)
