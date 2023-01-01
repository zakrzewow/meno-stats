from datetime import date

from django.db.models import Min, Max
from django.shortcuts import render, redirect

from .forms import SearchAccountForm
from .models import Account, Character, Activity


def index(request):
    if request.method == 'POST':
        form = SearchAccountForm(request.POST)
        if form.is_valid():
            account_id = form.cleaned_data['account_id']
            activity_date = form.cleaned_data['activity_date']
            no_date_option = form.cleaned_data['no_date_option']
            follow = form.cleaned_data['follow']
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


def following(request):
    return render(request, 'stats/following.html', {})


def detail(request, aid: int, activity_date: date):
    try:
        account = Account.objects.get(pk=aid)
    except Account.DoesNotExist:
        request.session['account_not_exists'] = {'aid': aid, 'activity_date': activity_date.strftime("%Y-%m-%d")}
        return redirect('stats:index')
    characters = Character.objects.filter(account=account)
    activity_query_set = Activity.objects.filter(character__account=account, date=activity_date)

    real_activity_date = activity_date
    if not activity_query_set.exists():
        activity_query_set = Activity.objects.filter(character__account=account)

        no_date_option = request.session.get("no_date_option", "last")
        if no_date_option == "first":
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
        'character_activity_list': character_activity_list,
        'activity_date': activity_date,
        'real_activity_date': real_activity_date,
        'all_activity_dates': all_activity_dates
    }

    return render(request, 'stats/detail.html', context)
