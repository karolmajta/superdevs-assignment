import uuid
import os
from petl.io.csv import tocsv, fromcsv
from petl.util.base import header, data
from petl.transform.sorts import sort
from petl.transform.basics import head, cutout
from petl.util.counting import valuecounts
from django.http import HttpResponseNotFound, HttpResponseBadRequest
from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect, render
from .utils import fetch_people_table
from .models import CSVDownload


def csv_list(request):
    csvdownloads = CSVDownload.objects.order_by('-downloaded_at').all()
    return render(request, 'csv_list.html', {'csvdownloads': csvdownloads})


def fetch(request):
    people = fetch_people_table()
    uid = uuid.uuid4()
    fname = '{0}.csv'.format(uid)
    full_fname = os.path.join(settings.CSV_DIR, fname)
    tocsv(people, full_fname)
    CSVDownload.objects.create(uuid=uid)
    return redirect(to=reverse('csv_list'))


def people_list(request, uuid):
    try:
        csvdownload = CSVDownload.objects.get(uuid=uuid)
    except CSVDownload.DoesNotExist:
        return HttpResponseNotFound("Not found.")

    fname = '{0}.csv'.format(csvdownload.uuid)
    full_fname = os.path.join(settings.CSV_DIR, fname)
    people = fromcsv(full_fname)

    sortby = request.GET.get('sortby', 'name')
    ordering = request.GET.get('ordering', 'asc')
    count_str = request.GET.get('count', '10')

    if sortby not in header(people):
        return HttpResponseBadRequest('Bad request.')
    if ordering not in ('asc', 'desc'):
        return HttpResponseBadRequest('Bad request.')
    try:
        count = int(count_str)
    except ValueError:
        return HttpResponseBadRequest('Bad request.')
    if count < 1:
        return HttpResponseBadRequest('Bad request.')

    people = sort(people, sortby, reverse=ordering == 'desc')
    people = head(people, count)

    return render(
        request, 'people_list.html', {
            'csvdownload': csvdownload,
            'headers': header(people),
            'people': data(people),
            'has_more': len(people) > count,
            'queryparams': {
                'sortby': sortby,
                'ordering': ordering,
                'count': str(count + 10)
            }
        })


def counts(request, uuid):
    try:
        csvdownload = CSVDownload.objects.get(uuid=uuid)
    except CSVDownload.DoesNotExist:
        return HttpResponseNotFound("Not found.")

    fname = '{0}.csv'.format(csvdownload.uuid)
    full_fname = os.path.join(settings.CSV_DIR, fname)
    people = fromcsv(full_fname)

    columns_str = request.GET.get('columns', '')
    columns = sorted([c for c in columns_str.split(',') if c.strip()])
    for column in columns:
        if column not in header(people):
            return HttpResponseBadRequest('Bad request.')
    if not columns:
        return redirect(to=reverse('people_list', kwargs={'uuid': uuid}))

    counts = valuecounts(people, *columns)
    counts = cutout(counts, 'frequency')

    return render(
        request, 'counts.html', {
            'csvdownload': csvdownload,
            'columns': header(people),
            'headers': header(counts),
            'counts': data(counts),
            'queryparams': {
                'columns': columns
            }
        })
