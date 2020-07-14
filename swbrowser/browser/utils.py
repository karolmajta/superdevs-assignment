from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import math
import requests
from petl.transform.basics import addfields, cutout
from petl.transform.conversions import convert
from petl.io.json import fromdicts
from petl.transform.basics import cat
from django.conf import settings

PEOPLE_HEADER = [
    'name', 'height', 'mass', 'hair_color', 'skin_color', 'eye_color',
    'birth_year', 'gender', 'homeworld', 'edited'
]


def fetch_people_table():
    planet_fetcher = CachedPlanetFetcher()

    first_page_response = _fetch_people_page(1).json()
    total_count = first_page_response['count']
    fetched_results = first_page_response['results']
    fetched_count = len(fetched_results)
    remaining_count = total_count - fetched_count
    remaining_pages = math.ceil(remaining_count / fetched_count)

    table = fromdicts(fetched_results, header=PEOPLE_HEADER)

    with ThreadPoolExecutor(max_workers=8) as executor:
        response_futures = [
            executor.submit(_fetch_people_page, page_number)
            for page_number in range(2, 2 + remaining_pages)
        ]
        for future in as_completed(response_futures):
            page_response = future.result().json()
            table = cat(
                table, fromdicts(page_response['results'],
                                 header=PEOPLE_HEADER))

    table = addfields(table, [('date', lambda rec: datetime.fromisoformat(rec[
        'edited'].replace('Z', '+00:00')).date().isoformat())])
    table = cutout(table, 'edited')
    table = convert(
        table, 'homeworld', lambda homeworld_url: planet_fetcher.fetch(
            homeworld_url).json()['name'])

    return table


def _fetch_people_page(page_number):
    response = requests.get('{0}/people/?page={1}'.format(
        settings.SWAPI_ROOT, page_number))
    return response


class CachedPlanetFetcher(object):
    def __init__(self):
        self.url_to_response = {}
        self.lock = Lock(
        )  # better safe than sorry, idk if petl is single or multi-threaded

    def fetch(self, url):
        self.lock.acquire()
        if url in self.url_to_response:
            self.lock.release()
            return self.url_to_response[url]
        else:
            response = requests.get(url)
            self.url_to_response[url] = response
            self.lock.release()
            return self.url_to_response[url]
