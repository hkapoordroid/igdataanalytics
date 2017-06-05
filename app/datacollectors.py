import requests
import json
import boto3	
import datetime
from itertools import islice
from decimal import *
from boto3.dynamodb.conditions import Key, Attr



urlIGDict = { 'getSelfInfo' : 'https://api.instagram.com/v1/users/self/?access_token={0}',
			  'getUserInfo' : 'https://api.instagram.com/v1/users/{0}/?access_token={1}',
			  'getSelfMedia' : 'https://api.instagram.com/v1/users/self/media/recent/?access_token={0}&count=-1{1}',
			  'getUserMedia' : 'https://api.instagram.com/v1/users/{0}/media/recent/?access_token={1}',
			  'getSelfMediaLiked' : 'https://api.instagram.com/v1/users/self/media/liked?access_token={0}',
			  'getUserSearch' : 'https://api.instagram.com/v1/users/search?q={0}&access_token={1}',
			  'getMediaComments' : 'https://api.instagram.com/v1/media/{0}/comments?access_token={1}{2}'
			 }

def chunks(data, size=10):
	'''
		This method takes in dictionary data and splits it in to chunks of specified size
		usage: chunks(dictdata, 10)
	'''
	it = iter(data)
	for i in xrange(0, len(data), size):
		yield {k:data[k] for k in islice(it, size)}


def collectAllUserData(username, access_token):
	#get user's info
	print('Getting user''s self info')
	gatherSelfData(access_token)

	#get user's own media data
	print('Getting user self media data')
	gatherSelfMediaData(access_token)

	#query the dynamodb table to get list of all media ids for the user and get collect all comments for each mediaid
	print('Getting user self media comments data')
	#get dynamodb resource
	dyndb = boto3.resource('dynamodb')
	#get dynamodb table
	igUserSelfMediaTable = dyndb.Table('IGUserSelfMedia')

	#query the table to get list of mediaids
	responseMediaIDs = igUserSelfMediaTable.query(
						ProjectionExpression="mediaid",
						KeyConditionExpression=Key('username').eq(username)
					)

	mediaids = { x['mediaid'] for x in responseMediaIDs['Items'] }

	for media_id in mediaids:
		gatherMediaComments(access_token, media_id)



##############################################################################
# Data Collection Methods to call IG API, get the data and save it in the dynamodb tables
##############################################################################
def getIGData(url):
	'''
	#	This method takes in url and return the response as json object
	'''
	try:
		r = requests.get(url)
		return json.loads(r.text)
	except:
		#TODO: logging
		raise

def gatherSelfData(access_token):
	'''
	#	This method gather all data related user self and save it to dynamodb 
	'''
	try:
		url = urlIGDict['getSelfInfo']

		url = url.format(access_token)

		print(url)

		resp = getIGData(url)

		if(resp['meta']['code'] == 200):
			#get the data from the response
			item = {}

			#build the item object
			item['userid'] = int(resp['data']['id'])
			item['username'] = resp['data']['username']
			if resp['data']['profile_picture']: item['profilepicture'] = resp['data']['profile_picture']
			if resp['data']['full_name']: item['fullname'] = resp['data']['full_name']
			if resp['data']['bio']: item['bio'] = resp['data']['bio']
			if resp['data']['website']: item['website'] = resp['data']['website']
			if resp['data']['counts']['media']: item['mediacount'] = int(resp['data']['counts']['media'])
			if resp['data']['counts']['follows']: item['followscount'] = int(resp['data']['counts']['follows'])
			if resp['data']['counts']['followed_by']: item['followedbycount'] = int(resp['data']['counts']['followed_by'])

			#get dynamodb resource
			dyndb = boto3.resource('dynamodb')

			#get dynamodb table
			igUserSelfTable = dyndb.Table('IGUserSelf')

			#save the dynamodb
			r = igUserSelfTable.put_item(Item = item)

			print(json.dumps(r))
		else:
			raise 'Unable to get the user info data'
	except:
		raise

def gatherSelfMediaData(access_token, max_id = ''):
	'''
	#	This method gather all media data of the user 
	'''
	try:
		url = urlIGDict['getSelfMedia']
		maxid = '&max_id='+max_id if max_id else ''

		url = url.format(access_token, maxid)
		print(url)

		#make the api call to get the media json data
		resp = getIGData(url)

		#check to see if the media has next max_id set
		nextmaxid = None
		if 'pagination' in resp and resp['pagination']:
			if 'next_max_id' in resp['pagination']: nextmaxid = resp['pagination']['next_max_id']

		#get dynamodb resource
		dyndb = boto3.resource('dynamodb')

		#get dynamodb table
		igUserSelfMediaTable = dyndb.Table('IGUserSelfMedia')

		#save the data to dynamodb 
		with igUserSelfMediaTable.batch_writer() as batch:
			for data in resp['data']:
				item = {}

				item['username'] = data['user']['username']
				item['mediaid'] = data['id']
				item['createdtime'] = int(data['created_time'])
				if data['tags']: item['tags'] = data['tags']
				if data['user_has_liked']: item['selfliked'] = bool(data['user_has_liked'])
				if data['likes']['count']: item['likescount'] = int(data['likes']['count'])
				if data['filter']: item['filterused'] = data['filter']
				if data['comments']['count']: item['commentscount'] = int(data['comments']['count'])
				if data['type']: item['mediatype'] = data['type']
				if data['link']: item['linktomedia'] = data['link']
				#if data['location']: item['location'] = data['location']
				#if data['location']['latitude']: item['locationlat'] = Decimal(data['location']['latitude'])
				#if data['location']['latitude']: item['locationlon'] = Decimal(data['location']['longitude'])
				#if data['location']['name']: item['locationname'] = data['location']['name']
				#if data['location']['id']: item['locationid'] = data['location']['id']
		
				batch.put_item(item)


		#make a recursive call to the method if nextmaxid is set
		if nextmaxid:
			gatherSelfMediaData(access_token, nextmaxid)
	except:
		raise

def gatherMediaComments(access_token, mediaid, max_id=''):
	'''
		This method gathers all the comments related to a particular media
	'''
	try:
		url = urlIGDict['getMediaComments']
		maxid = '&max_id='+max_id if max_id else ''

		url = url.format(mediaid, access_token, maxid)
		print(url)

		#make the api call to get the media comments json data
		resp = getIGData(url)

		#check to see if the media has next max_id set
		nextmaxid = None
		if 'pagination' in resp and resp['pagination']:
			if 'next_max_id' in resp['pagination']: nextmaxid = resp['pagination']['next_max_id']

		#get dynamodb resource
		dyndb = boto3.resource('dynamodb')

		#get dynamodb table
		igUserSelfMediaCommentsTable = dyndb.Table('IGUserSelfMediaComments')

		#save the data to dynamodb
		with igUserSelfMediaCommentsTable.batch_writer() as batch:
			for data in resp['data']:
				item = {}

				item['mediaid'] = mediaid
				item['commentid'] = data['id']
				item['createdtime'] = int(data['created_time'])
				if data['text']: item['commenttext'] = data['text']
				if data['from']: 
					if data['from']['username']: item['fromusername'] = data['from']['username']
					if data['from']['profile_picture']: item['fromprofilepicture'] = data['from']['profile_picture']
					if data['from']['id']: item['fromuserid'] = data['from']['id']
					if data['from']['full_name']: item['fromfullname'] = data['from']['full_name']

				batch.put_item(item)

		#make a recursive call to the method if nextmaxid is set
		if nextmaxid:
			gatherMediaComments(access_token, mediaid, nextmaxid)

	except:
		raise

##############################################################################
# end of section
##############################################################################








