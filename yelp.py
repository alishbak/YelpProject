"""
This program requires the Python oauth2 library, which you can install via:
`pip install -r requirements.txt`.

Also:
pip install lxml 
pip install requests

Go to https://www.yelp.com/developers/manage_api_keys 
to get your api manage_api_keys and save them under yelpKeys.py

Sample usage of the program:
python yelp.py
"""
import argparse
import json
import pprint
import sys
import urllib
import urllib2
import csv
from lxml import html # pip install lxml 
import requests #pip install requests
import oauth2

import yelpKeys # CREATE THIS FILE YOURSELF

API_HOST = 'api.yelp.com'
DEFAULT_TERM = 'food' # Not using this
DEFAULT_LOCATION = 'University of Maryland College Park, 20740'
SORT = 0 # Sort mode: 0=Best matched (default), 1=Distance, 2=Highest Rated
DEFAULT_CATEGORY = 'restaurants'
SEARCH_LIMIT = 20 # this is the max per API call
SEARCH_PATH = '/v2/search/'
BUSINESS_PATH = '/v2/business/'

FIELDNAMES = ['id','name','categories','latitude','longitude', 'state', 'college', 'distance_from_college','rating','review_count','permanently_closed']

FEATNAMES = ['TakesReservations', 'Delivery','Take-out','AcceptsCreditCards','AcceptsBitcoin','GoodFor','Parking','BikeParking','WheelchairAccessible','GoodforKids','GoodforGroups','Attire','Ambience','NoiseLevel','Alcohol','OutdoorSeating','Wi-Fi','HasTV','DogsAllowed','WaiterService','Caters','Drive-Thru']


# OAuth credential placeholders that must be filled in by users.
CONSUMER_KEY = yelpKeys.CONSUMER_KEY
CONSUMER_SECRET = yelpKeys.CONSUMER_SECRET
TOKEN = yelpKeys.TOKEN
TOKEN_SECRET = yelpKeys.TOKEN_SECRET

def request(host, path, url_params=None):
    """Prepares OAuth authentication and sends the request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        dict: The JSON response from the request.

    Raises:
        urllib2.HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = 'http://{0}{1}?'.format(host, urllib.quote(path.encode('utf8')))

    consumer = oauth2.Consumer(CONSUMER_KEY, CONSUMER_SECRET)
    oauth_request = oauth2.Request(method="GET", url=url, parameters=url_params)

    oauth_request.update(
        {
            'oauth_nonce': oauth2.generate_nonce(),
            'oauth_timestamp': oauth2.generate_timestamp(),
            'oauth_token': TOKEN,
            'oauth_consumer_key': CONSUMER_KEY
        }
    )
    token = oauth2.Token(TOKEN, TOKEN_SECRET)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()

    # print 'urls:',url_params
    # print u'Querying {0} ...'.format(url)

    conn = urllib2.urlopen(signed_url, None)
    try:
        response = json.loads(conn.read())
    finally:
        conn.close()

    return response

def search(term, location, offset):
    """Query the Search API by a search term and location.

    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.

    Returns:
        # dict: The JSON response from the request.
    """
    
    url_params = {
        # 'term': term.replace(' ', '+'),
        'location': location.replace(' ', '+'),
        'sort' : SORT,
        'category_filter': DEFAULT_CATEGORY,
        'offset': offset,
        'limit': SEARCH_LIMIT
 
    }
    return request(API_HOST, SEARCH_PATH, url_params=url_params)

def get_business(business_id):
    """Query the Business API by a business ID.

    Args:
        business_id (str): The ID of the business to query.

    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path)

# http://docs.python-guide.org/en/latest/scenarios/scrape/
def scrape_page(url):
    page = requests.get(url)
    tree = html.fromstring(page.text)
    info = {}

    try:
        info['price'] = len(tree.xpath('//span[@class="business-attribute price-range"]/text()')[0]) # number of dollar signs (1-4)
    except:
        pass 

    try:
        business_info = tree.xpath('//div[@class="bordered-rail"]//div[@class="ywidget"]//div[@class="short-def-list"]')[0] # right hand "more business info" list

        for r in business_info:
            attrKey = r.xpath('.//dt[@class="attribute-key"]/text()')[0].strip().replace(" ", "")
            attrVal = r.xpath('.//dd/text()')[0].strip()
            info[attrKey] = attrVal
    except:
        pass

    return info


def query_api(term, location, offset):
    """Queries the API by the input values from the user.

    Args:
        term (str): The search term to query.
        location (str): The location of the business to query.
    """
    response = search(term, location, offset)

    # pprint.pprint(response)

    businesses = response.get('businesses')

    if not businesses:
        print u'No businesses for {0} in {1} found. Offset: {2}'.format(term, location, offset)
        return

    print u'{0} businesses found...'.format(len(businesses))
    
    with open('restaurants' + DEFAULT_LOCATION.replace(' ', '') + '.csv', 'a') as csvfile:
        all_fields = FIELDNAMES + FEATNAMES
        writer = csv.DictWriter(csvfile, fieldnames=all_fields)

        for business in businesses:
            business_id = business['id']
            response = get_business(business_id)
            print u'Result for business "{0}" found:'.format(business_id)
            # pprint.pprint(response, indent=2)

            # ex: response['categories'] = [[u'Coffee & Tea', u'coffee'], [u'Tea Rooms', u'tea']]]
            categories = [row[1] for row in response['categories']]
            categories = [c.encode('ascii', 'ignore') for c in categories] # get rid of u'
            # apparently 'hotdogs' links to the fast food category

            restaurant_id = response['id'].encode('utf8')
            features = scrape_page("http://www.yelp.com/biz/" + restaurant_id)

            row = {'id': restaurant_id, # id used for url: http://www.yelp.com/biz/{id}
                'name': response['name'].encode('utf8'), 
                'categories': categories,
                'latitude': response['location']['coordinate']['latitude'],
                'longitude': response['location']['coordinate']['longitude'], 
                'state': response['location']['state_code'],
                'college': DEFAULT_LOCATION,
                'distance_from_college': business['distance'],
                'rating': response['rating'], 
                'review_count': response['review_count'],
                'permanently_closed': response['is_closed']
                }

            for f in FEATNAMES:
                if f in features:
                    row[f] = features[f]

            writer.writerow(row)


def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM, type=str, help='Search term (default: %(default)s)')
    # parser.add_argument('-l', '--location', dest='location', default=DEFAULT_LOCATION, type=str, help='Search location (default: %(default)s)')
    # input_values = parser.parse_args()

    # write head only once
    with open('restaurants' + DEFAULT_LOCATION.replace(' ', '') + '.csv', 'a') as csvfile:
        all_fields = FIELDNAMES + FEATNAMES
        writer = csv.DictWriter(csvfile, fieldnames=all_fields)
        writer.writeheader()

    try:
        offset = 0
         # Cause yelp only lets you get 20 at a time
        while offset < 300:
            query_api(DEFAULT_TERM, DEFAULT_LOCATION, offset) 
            offset += 20 # array index offset for results to get next 20
    except urllib2.HTTPError as error:
        sys.exit('Encountered HTTP error {0}. Abort program.'.format(error.code))


if __name__ == '__main__':
    main()