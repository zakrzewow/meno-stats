from typing import List, Tuple

import numpy as np
from django.db import models


class Account(models.Model):
    """
    Reprezentuje konto gracza
    aid - account id - id konta
    """
    aid = models.IntegerField(primary_key=True)

    def __str__(self):
        return f"[{self.aid}]"


class Character(models.Model):
    """
    Reprezentuje postać (bohatera którym porusza się gracz)
    Wiele postaci może być przypisanych do jednego konta
    account
    cid - character id - id postaci
    world - nazwa świata (gracz może mieć postacie na różnych światach, czyli serwerach)
    nick
    lvl - poziom doświadczenia (dodatni, mniejszy niż 500)
    prof - profesja (klasa postaci); wojownik (w), mag (m), łowca (h), tropiciel (t), paladyn (p), tancerz ostrzy (b)
    avatar_url - link (końcówka linku) do avatara postaci
    """

    class Profession(models.TextChoices):
        WARRIOR = 'w'
        MAGE = 'm'
        HUNTER = 'h'
        TRACKER = 't'
        PALADIN = 'p'
        BLADE_DANCER = 'b'

    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    cid = models.IntegerField()
    world = models.CharField(max_length=10)
    nick = models.CharField(max_length=40, blank=True)
    lvl = models.SmallIntegerField(blank=True, null=True)
    prof = models.CharField(max_length=1, choices=Profession.choices, default=Profession.WARRIOR)
    avatar_url = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.account}[{self.cid}] {self.nick_or_null} {self.lvl_prof_or_null} {self.world}"

    @property
    def nick_or_null(self) -> str:
        return "????" if len(self.nick) == 0 else self.nick

    @property
    def lvl_prof_or_null(self) -> str:
        return "??" if self.lvl is None else f"{self.lvl}{self.prof}"


def activity_default():
    return bytearray(180)


class Activity(models.Model):
    """
    Reprezentuje aktywność gracza na danej postaci w ciągu jednego dnia
    Gracz w jednym momencie może być grać tylko na jednej postaci
    Aktywność jest pobierana ze strony pokazującej aktualnie zalogowanych graczy: https://www.margonem.pl/stats
    Ta strona aktualizuje się co minutę
    Aktywność gracza w ciągu dnia jest reprezenowana jako ciąg 180 bajtów (1440 minut) - jeden dzień zawiera 1440 minut,
    1 oznacza że gracz był zalogowny i grał na danej postaci, natomiast 0 że nie był
    """
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    activity = models.BinaryField(max_length=180, default=activity_default)  # 60 * 24 / 8

    def __str__(self):
        return f"[{self.date}]{self.character}"

    @property
    def total_minutes(self) -> int:
        """
        :return: czas aktywności w minutach
        """
        return self.__bits_unpacked.sum()

    @property
    def activity_time(self) -> str:
        """
        :return: reprezentację aktywności w postaci napisu X godz. Y min.
        """
        total_minutes = self.total_minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60
        str_ = f"{minutes} min."
        if hours > 0:
            str_ = f"{hours} godz. " + str_
        return str_

    @property
    def activity_plot(self):
        plot_width = 600
        bits = self.__bits_unpacked
        start_end_list = self.__get_start_end_list(bits)

        # tworzenie div-ów oznaczających godziny (ticki na wykresie)
        div_list = []
        for i in range(60, 1440, 60):
            left = round(i * plot_width / 1440, 4) + 10
            div_line = f"""<div class="activity-plot-hour-line" style="left: {left}px;"></div>"""
            div_list.append(div_line)

            hour = f"{i // 60:02d}"
            div_hour = f"""<div class="activity-plot-hour" style="left: {left - 6}px;">{hour}</div>"""
            div_list.append(div_hour)

        # tworzenie div-ów oznaczających aktywność gracza
        for (start, end) in start_end_list:
            left = round(start * plot_width / 1440, 4) + 10
            width = round((end - start) * plot_width / 1440, 4)
            div = f"""<div class="activity-plot-line" style="left: {left}px; width: {width}px;"></div>"""
            div_list.append(div)

        return "\n".join(div_list)

    @property
    def __bits_unpacked(self) -> np.ndarray:
        return np.unpackbits(np.asarray(bytearray(self.activity)))

    @staticmethod
    def __get_start_end_list(bits: np.ndarray) -> List[Tuple[int, int]]:
        """
        Listę bitów transformuje na listę par indeksów określających położenie podciągów jedynek w ciągu bitów
        """
        start_end_list = []
        start = None
        for i in range(0, len(bits)):
            if bits[i] == 1 and start is None:
                start = i
            if bits[i] == 0 and start is not None:
                start_end_list.append((start, i))
                start = None
        if start is not None:
            start_end_list.append((start, len(bits)))
        return start_end_list
