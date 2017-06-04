import requests
import json
import boto3	
import datetime
from itertools import islice
from decimal import *



urlIGDict = { 'getSelfInfo' : 'https://api.instagram.com/v1/users/self/?access_token={0}',
			  'getUserInfo' : 'https://api.instagram.com/v1/users/{0}/?access_token={1}',
			  'getSelfMedia' : 'https://api.instagram.com/v1/users/self/media/recent/?access_token={0}&count=-1{1}',
			  'getUserMedia' : 'https://api.instagram.com/v1/users/{0}/media/recent/?access_token={1}',
			  'getSelfMediaLiked' : 'https://api.instagram.com/v1/users/self/media/liked?access_token={0}',
			  'getUserSearch' : 'https://api.instagram.com/v1/users/search?q={0}&access_token={1}'
			 }

def chunks(data, size=10):
	'''
		This method takes in dictionary data and splits it in to chunks of specified size
		usage: chunks(dictdata, 10)
	'''
	it = iter(data)
	for i in xrange(0, len(data), size):
		yield {k:data[k] for k in islice(it, size)}


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
	url = urlIGDict['getSelfInfo']

	url = url.format(access_token)

	print(url)

	resp = getIGData(url)

	if(resp['meta']['code'] == 200):
		#get the data from the response
		userid = resp['data']['id']
		username = resp['data']['username']
		profilepicture = resp['data']['profile_picture']
		fullname = resp['data']['full_name']
		bio = resp['data']['bio']
		website = resp['data']['website']
		mediacount = resp['data']['counts']['media']
		followscount = resp['data']['counts']['follows']
		followedbycount = resp['data']['counts']['followed_by']

		#get dynamodb resource
		dyndb = boto3.resource('dynamodb')

		#get dynamodb table
		igUserSelfTable = dyndb.Table('IGUserSelf')

		#build the item object
		item = {}
		item['userid'] = int(userid)
		item['username'] = username
		if profilepicture: item['profilepicture'] = profilepicture
		if fullname: item['fullname'] = fullname
		if bio: item['bio'] = bio
		if website: item['website'] = website
		if mediacount: item['mediacount'] = int(mediacount)
		if followscount: item['followscount'] = int(followscount)
		if followedbycount: item['followedbycount'] = int(followedbycount)

		r = igUserSelfTable.put_item(Item = item)

		print(json.dumps(r))
	else:
		raise 'Unable to get the data'

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
		if resp['pagination']:
			if 'next_max_id' in resp['pagination']: nextmaxid = resp['pagination']['next_max_id']

		#get dynamodb resource
		dyndb = boto3.resource('dynamodb')

		#get dynamodb table
		igUserSelfMediaTable = dyndb.Table('IGUserSelfMedia')

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
	










