import requests
import base64
import pprint
import pandas as pd
import time
import track
import re
import datetime
import json
import logging
import os
import params

logger = logging.getLogger("root")
logging.basicConfig(
    format = "\033[1;36m%(levelname)s: %(filename)s (def %(funcName)s %(lineno)s): \033[1;37m %(message)s",
    level=logging.DEBUG
)

#### Step 1: # Obtaining StubHub User Access Token ####

#### Credentials #####
app_token = params.app_token
consumer_key = params.consumer_key
consumer_secret = params.consumer_secret
stubhub_username = params.stubhub_username 
stubhub_password = params.stubhub_password


#### Generate authorization token ####
combo = consumer_key + ':' + consumer_secret
basic_authorization_token = base64.b64encode(combo.encode('utf-8'))


#### POST parameters for API call ####
url = 'https://api.stubhub.com/login'
HEADERS = {
        'Content-Type':'application/x-www-form-urlencoded',
        'Authorization':'Basic '+basic_authorization_token,}
body = {
        'grant_type':'password',
        'username':stubhub_username,
        'password':stubhub_password,
        'scope':'PRODUCTION'}

#### Variables for the looping function ####
Data = {
    'eventid': '',
    'sort': 'quantity desc',
    'start': 0,
    'rows': 100
}

#### Get the time of the data pull ####
time = time.strftime("%Y-%m-%d-%H-%M")



#### Make the call ####
class StuHubEventSearch(object):
	url = 'https://api.stubhub.com/login'
	inventory_url = 'https://api.stubhub.com/search/inventory/v2'

	def _init(self, *args, **kwargs):
		r = requests.post(url, headers=HEADERS, data=body)
		token_response = r.json()
		user_GUID = r.headers['X-StubHub-User-GUID']
		HEADERS['Authorization'] = 'Bearer ' + token_response['access_token']
		HEADERS['Accept'] = 'application/json'
		HEADERS['Accept-Encoding'] = 'application/json'
		HEADERS['User-agent'] = "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.53 Safari/525.19"
		inventory = requests.get(self.inventory_url, headers=HEADERS, params=Data)


#### Import the games to track ####
		tag = None
		tracks = track.tags

#### Collect for each game ####
		for x in range(len(tracks)):
			tag = tracks[x]
			if tag == tracks[x]:
				inventory_url = 'https://api.stubhub.com/search/inventory/v2'
				eventid = tag
				data = {'eventid':tag, 'rows':1000}
				HEADERS['Authorization'] = 'Bearer ' + token_response['access_token']
				HEADERS['Accept'] = 'application/json'
				HEADERS['Accept-Encoding'] = 'application/json'

				inventory = requests.get(inventory_url, headers=HEADERS, params=data)

				#### Here's the raw JSON return for each game ####
				inv = inventory.json()


				#### Declare some variables of interest from the raw return and setup the loop ####
				totalTix = inv['totalTickets']
				totalList = inv['totalListings']
				eventid = inv['eventId']
				rows = inv['rows']
				start = inv['start']

				#### Pass the number of rows, starting listing, etc and run the loop ####
				listings = self.make_request_to_url(self.inventory_url, rows, start, totalList, tag)


				#### Add the snapshot time and organize the JSON by data pull ####
				for listing in listings:
					listing['snapshot_time'] = time
				#d = {}
				#d['data_pull'] = {'eventId':eventid, 'snapshot_time':time, 'totalTickets':totalTix, 'aggListings':totalList, 'listings':listings}
				

				#### Dump the organized JSON file ####
				#with open('/home/ec2-user/collections/' + tag + '.json', 'a') as file:
				#	file.write(json.dumps(d,indent=4))

				#### Get event info from eventinfo.csv ####
				df = pd.read_csv('eventinfo.csv')
				df['ID'] = df['ID'].astype(str)
				event_df= df[df['ID'] == tag]
				eventID = event_df.iloc[0]['ID']
				eventTime = event_df.iloc[0]['gameTime']
				eventhomeTeam = event_df.iloc[0]['homeTeam']
				eventawayTeam = event_df.iloc[0]['awayTeam']

				for listing in listings:
					listing['eventTime'] = eventTime
					listing['homeTeam'] = eventhomeTeam
					listing['awayTeam'] = eventawayTeam
					listing['snapshot_time'] = time

				#### Create an organized excel file  ####	
				listing_df = pd.DataFrame(listings)
				listing_df['current_price'] = listing_df.apply(lambda x: x['currentPrice']['amount'], axis=1)
				listing_df['listed_price'] = listing_df.apply(lambda x: x['listingPrice']['amount'], axis=1)

				my_col = [
					'snapshot_time',
					'eventTime',
					'homeTeam',
					'awayTeam',
					'listingId',
					'quantity',						
					'sectionName',									
					'row',
					'seatNumbers',
					'current_price',
					'listed_price',
					'sellerSectionName',
					'sellerOwnInd',					
					'sectionId',
					'splitOption',
					'splitVector',
					'ticketSplit',
					'zoneName',
					'deliveryMethodList',
					'deliveryTypeList',
				]
				final_df = listing_df[my_col]

				if os.path.exists('/home/ec2-user/collections/' + tag + '.csv'):
					with open('/home/ec2-user/collections/' + tag + '.csv', 'a') as f1:
						final_df.to_csv(f1, mode='a', header=False)

				else:
					with open('/home/ec2-user/collections/' + tag + '.csv', 'w') as f2:
						final_df.to_csv(f2, header=True)


			

	def make_request_to_url(self, url, rows, start, total, tag):
#### increment the starting point of the listings based on the total number of listings ####

		all_listings = []
		Data = {
			'eventid': tag,
			'sort':'quantity desc',
			'start':start,
			'rows':'100'
		}

		while Data['start'] < total:
			inventory = requests.get(self.inventory_url, headers = HEADERS, params=Data)
			inv = inventory.json()
			all_listings = all_listings + inv['listing']
			logger.debug("Retrieving listings starting at %s" % (Data['start']))
			Data['start'] = Data['start'] + inv['rows']
		return all_listings


if __name__ == '__main__':
	task_run = StuHubEventSearch()
	task_run._init()
	print "\nTask finished at %s\n" % str(datetime.datetime.now())

