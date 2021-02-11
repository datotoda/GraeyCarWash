from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import F, Sum, ExpressionWrapper, DecimalField, Count, Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from user.models import User
from wash.forms import ContactForm, CarForm
# @TODO: Add Manager Method For Washer Listing
from wash.forms import OrderForm
from wash.models import Order, Car


def washer_list_view(request: WSGIRequest) -> HttpResponse:
    washer_q = Q()
    order_q = Q()
    q = request.GET.get('q')

    if q:
        washer_q &= Q(first_name__icontains=q[-1]) | Q(last_name__icontains=q[-1])
        order_q &= Q(employee__first_name__icontains=q[-1]) | Q(employee__last_name__icontains=q[-1])

    profit_q = ExpressionWrapper(
        F('price') * (1 - F('employee__salary') / Decimal('100.0')),
        output_field=DecimalField()
    )
    order_info: Dict[str, Optional[Decimal]] = Order.objects.filter(end_date__isnull=False).filter(order_q) \
        .annotate(profit_per_order=profit_q) \
        .aggregate(profit=Sum('profit_per_order'), total=Count('id'))

    context = {
        'washers': User.objects.filter(status=User.Status.washer.value).filter(washer_q).annotate(
            washed_count=Count('orders')),
        # **order_info
    }
    context.update(order_info)

    return render(request=request, template_name='wash/washer-list.html', context=context)


# Dispatch (type) -> view

def washer_detail(request: WSGIRequest, pk: int) -> HttpResponse:
    order_form = OrderForm()
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        if order_form.is_valid():
            order: Order = order_form.save(commit=False)
            order.employee_id = pk
            try:
                start_date = datetime.strptime(
                    " ".join([
                        order_form.cleaned_data['start_date_day'],
                        order_form.cleaned_data['start_date_time']
                    ]),
                    '%d/%m/%Y %H:%M'
                )
                order.start_date = start_date
                order.save()
            except ValueError:
                order_form.add_error('start_date_day', 'პაპს ნუ ატყუებ')


    washer: User = get_object_or_404(
        User.objects.filter(status=User.Status.washer.value),
        pk=pk
    )
    earned_money_q = ExpressionWrapper(
        F('price') * F('employee__salary') / Decimal('100.0'),
        output_field=DecimalField()
    )
    now = timezone.now()
    washer_salary_info: Dict[str, Optional[Decimal]] = washer.orders.filter(end_date__isnull=False) \
        .annotate(earned_per_order=earned_money_q) \
        .aggregate(
        earned_money_year=Sum(
            'earned_per_order',
            filter=Q(end_date__gte=now - timezone.timedelta(days=365))
        ),
        washed_last_year=Count(
            'id',
            filter=Q(end_date__gte=now - timezone.timedelta(days=365))
        ),
        earned_money_month=Sum(
            'earned_per_order',
            filter=Q(end_date__gte=now - timezone.timedelta(weeks=4))
        ),
        washed_last_month=Count(
            'id',
            filter=Q(end_date__gte=now - timezone.timedelta(weeks=4))
        ),
        earned_money_week=Sum(
            'earned_per_order',
            filter=Q(end_date__gte=now - timezone.timedelta(days=7))
        ),
        washed_last_week=Count(
            'id',
            filter=Q(end_date__gte=now - timezone.timedelta(days=7))
        )
    )

    return render(request, template_name='wash/washer-detail.html', context={
        'washer': washer,
        **washer_salary_info,
        'order_form': order_form
    })


def contact(request: WSGIRequest):
    contact_form = ContactForm()
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            print(contact_form.cleaned_data.get('phone'))
            # contact_form.errors.as_json()
        # send_mail()
    return render(request, template_name='wash/contact.html', context={
        'contact_form': contact_form
    })


def make_order(request: WSGIRequest, pk: int):
    order_form = OrderForm()
    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        if order_form.is_valid():
            order: Order = order_form.save(commit=False)
            order.employee_id = pk
            order.start_date = timezone.now()
            order.save()

        return redirect('wash:washer-detail')

    return render(request, template_name='wash/contact.html', context={
        'contact_form': order_form
    })


def car_list_view(request: WSGIRequest) -> HttpResponse:
    car_form = CarForm()
    if request.method == 'POST':
        car_form = CarForm(request.POST)
        if car_form.is_valid():
            car: Car = car_form.save(commit=False)
            car.save()

    car_q = Q()
    q = request.GET.get('q')
    car_list = Car.objects.all()
    if q:
        car_q &= Q(licence_plate__icontains=q[-1])
        car_list = Car.objects.filter(car_q)

    cars_info = Car.objects.filter(car_q).aggregate(total=Count('id'))

    page = request.GET.get('page', 1)
    print(request.GET)

    paginator = Paginator(car_list, 4)
    try:
        cars = paginator.page(page)
    except PageNotAnInteger:
        cars = paginator.page(1)
    except EmptyPage:
        cars = paginator.page(paginator.num_pages)

    context = {
        'cars': cars,
        # **order_info
        'car_form': car_form
    }
    context.update(cars_info)

    return render(request=request, template_name='wash/car-list.html', context=context)


def car_detail(request: WSGIRequest, pk: int) -> HttpResponse:
    car: Car = get_object_or_404(
        Car.objects,
        pk=pk
    )
    context = {

        'car': car,
    }
    return render(request, template_name='wash/car-detail.html', context=context)


def homepage_view(request: WSGIRequest) -> HttpResponse:

    return render(request, template_name='wash/homepage.html')

