from datetime import date

from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.contrib.auth.views import LoginView
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.mail import send_mail
from django.db.models import Min, Max
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View

from .forms import SearchAccountForm, FollowAccountForm, MyAuthenticationForm, RegistrationForm
from .models import Account, Character, Activity, Following


def index(request):
    if request.method == 'POST':
        form = SearchAccountForm(request.POST)
        if form.is_valid():
            account_id = form.cleaned_data['account_id']
            activity_date = form.cleaned_data['activity_date']
            no_date_option = form.cleaned_data['no_date_option']
            follow = form.cleaned_data['follow']
            request.session["follow"] = follow
            request.session["no_date_option"] = no_date_option
            return redirect('stats:detail', aid=account_id, activity_date=activity_date)
    else:
        # przekierowanie z błędnego 'details'
        if 'account_not_exists' in request.session:
            aid, activity_date = request.session["account_not_exists"].values()
            form = SearchAccountForm({'account_id': aid, 'activity_date': activity_date, 'no_date_option': 'last'})
            form.add_error('account_id', f'Konta z ID {aid} nie ma w bazie!')
            request.session.pop('account_not_exists', None)
        # normalne wejście na stronę
        else:
            form = SearchAccountForm(initial={'account_id': 390135, 'activity_date': date(2022, 12, 28)})
            # form = SearchAccountForm(initial={'activity_date': date(2022, 12, 28)})
        form.fields['activity_date'].widget.attrs.update({
            'min': '2022-12-28',
            'max': date.today()
        })

    # ranking
    latest_activity_date = Activity.objects.aggregate(Max('date')).get('date__max')
    activity_query_set = Activity.objects.filter(date=latest_activity_date)
    top_activity = sorted(activity_query_set, key=lambda a: a.total_minutes, reverse=True)[:5]
    top_character_activity = [(activity.character, activity) for activity in top_activity]
    top_ranking = {
        'date': latest_activity_date,
        'character_activity_list': top_character_activity
    }

    context = {'form': form, 'top': top_ranking}
    return render(request, 'stats/index.html', context)


class FollowingView(View):
    http_method_names = ['get', 'post']

    def get(self, request):
        context = self.get_context_data(request)
        return render(request, 'stats/following.html', context)

    def post(self, request):
        form = FollowAccountForm(request.POST)
        if form.is_valid():
            account_id = form.cleaned_data['account_id']
            Following.objects.get_or_create(user=request.user, account_id=account_id)
            form = None
        context = self.get_context_data(request, form)
        return render(request, 'stats/following.html', context)

    @staticmethod
    def get_context_data(request, form: FollowAccountForm = None):
        context = {
            'form': form if form is not None else FollowAccountForm()
        }
        if request.user.is_authenticated:
            following_list = Following.objects.filter(user=request.user)
            account_with_last_activity_date_list = []
            for following in following_list:
                account_activity = Activity.objects.filter(character__account=following.account)
                latest_activity_date = account_activity.aggregate(Max('date')).get('date__max')
                account_with_last_activity_date_list.append((following.account, latest_activity_date))
            context['account_with_last_activity_date_list'] = account_with_last_activity_date_list
        return context


class UnfollowView(View):
    http_method_names = ['get']

    def get(self, request, aid: int):
        Following.objects.filter(user=request.user, account_id=aid).delete()
        return redirect('stats:following')


def detail(request, aid: int, activity_date: date):
    try:
        account = Account.objects.get(pk=aid)
    except Account.DoesNotExist:
        request.session['account_not_exists'] = {'aid': aid, 'activity_date': activity_date.strftime("%Y-%m-%d")}
        return redirect('stats:index')

    unauthenticated_follow_attempt = False
    if request.session.get('follow', False):
        request.session.pop('follow', None)
        if request.user.is_authenticated:
            Following.objects.get_or_create(user=request.user, account=account)
        else:
            unauthenticated_follow_attempt = True

    characters = Character.objects.filter(account=account)
    activity_query_set = Activity.objects.filter(character__account=account, date=activity_date)

    real_activity_date = activity_date
    if not activity_query_set.exists():
        activity_query_set = Activity.objects.filter(character__account=account)

        no_date_option = request.session.get("no_date_option", "last")
        if no_date_option == 'first':
            agg_func, agg_field = Min, 'date__min'
        else:
            agg_func, agg_field = Max, 'date__max'
        request.session.pop('no_date_option', None)

        real_activity_date = activity_query_set.aggregate(agg_func('date')).get(agg_field)
        activity_query_set = activity_query_set.filter(date=real_activity_date)

    character_activity_list = []
    for character in characters:
        try:
            activity = activity_query_set.get(character=character)
        except Activity.DoesNotExist:
            activity = None
        character_activity_list.append((character, activity))

    all_activity_dates = (
        Activity.objects.filter(character__account=account)
        .values_list('date', flat=True)
        .distinct()
        .order_by('date')
    )

    context = {
        'account': account,
        'unauthenticated_follow_attempt': unauthenticated_follow_attempt,
        'character_activity_list': character_activity_list,
        'activity_date': activity_date,
        'real_activity_date': real_activity_date,
        'all_activity_dates': all_activity_dates
    }

    return render(request, 'stats/detail.html', context)


class ExportAsXmlView(View):
    http_method_names = ['get']
    ACTIVITY_FORMAT = """<activity date="{}">\n\t{}</activity>"""
    CHARACTER_FORMAT = """<character><cid>{}</cid><world>{}</world>{}</character>"""
    XML_FORMAT = """<?xml version="1.0" encoding="ISO-8859-1" ?>\n<?xml-stylesheet type="text/xsl" href="meno-stats.xsl"?>\n<stats>\n\t<account>\n\t\t<aid>{}</aid>\n\t</account>\n\t{}\n</stats>"""

    def get(self, request, aid: int):
        try:
            account = Account.objects.get(pk=aid)
        except Account.DoesNotExist:
            return Http404(f"Konta z ID {aid} nie ma w bazie")

        activity_query_set = Activity.objects.filter(character__account=account)
        cid_world_list = activity_query_set.values_list('character__cid', 'character__world').distinct()
        character_xml_list = []
        for cid, world in cid_world_list:
            activity_xml_list = []
            for activity in activity_query_set.filter(character__cid=cid):
                activity_xml_list.append(
                    self.ACTIVITY_FORMAT.format(activity.date.strftime("%d-%m-%Y"), activity.bits_str)
                )

            character_xml_list.append(
                self.CHARACTER_FORMAT.format(cid, world, "\n".join(activity_xml_list))
            )

        xml = self.XML_FORMAT.format(account.aid, "\n\t".join(character_xml_list))
        return HttpResponse(xml, headers={
            'Content-Type': 'application/xml',
            'Content-Disposition': f'attachment; filename="account_{aid}.xml"',
        })


class MyLoginView(LoginView):
    authentication_form = MyAuthenticationForm
    next_page = '/stats/following'


def logout(request):
    auth.logout(request)
    return redirect('stats:index')


class RegistrationView(View):
    http_method_names = ['get', 'post']

    def get(self, request):
        context = self.get_context_data(request)

        current_site = get_current_site(request)
        site_name = current_site.name
        domain = current_site.domain
        print(site_name, domain)
        return render(request, 'registration/registration.html', context)

    def post(self, request):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            activation_link = self.__get_activation_link(user, request)
            send_mail(
                'Aktywacja konta Meno Stats',
                f'Aby aktywować konto, kliknij w link: {activation_link}\nPo aktywacji konta będzie można się zalogować.',
                'meno.stats@gmail.com',
                [user.email],
                fail_silently=False,
            )

        context = self.get_context_data(request, form)
        return render(request, 'registration/registration.html', context)

    @staticmethod
    def get_context_data(request, form: RegistrationForm = None):
        return {
            'form': form if form is not None else RegistrationForm()
        }

    def __get_activation_link(self, user: User, request):
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        domain = get_current_site(request).domain
        return f"http://{domain}/stats/accounts/activate/{uidb64}/{token}"


class AccountActivationView(View):
    http_method_names = ['get']
    token_generator = PasswordResetTokenGenerator()

    def get(self, request, uidb64, token):
        print(uidb64, token)
        user = self.get_user(uidb64)

        if user is not None:
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
        return redirect('stats:login')

    def get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except (
                TypeError,
                ValueError,
                OverflowError,
                User.DoesNotExist,
                ValidationError,
        ):
            user = None
        return user
