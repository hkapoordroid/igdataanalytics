from app import app
from flask import redirect, request
import requests
import json 
import boto3

#glabal values
clientID = '26d2405a54464c8d93cc2cc786401246'
clientSecret = '3f6f68e1ab2841a9831f10bf6a13bcfd'
redirectUrl = 'http://127.0.0.1:5000/index'



urlIGDict = { 'getSelfInfo' : 'https://api.instagram.com/v1/users/self/?access_token={0}',
			  'getUserInfo' : 'https://api.instagram.com/v1/users/{0}/?access_token={1}',
			  'getSelfMedia' : 'https://api.instagram.com/v1/users/self/media/recent/?access_token={0}',
			  'getUserMedia' : 'https://api.instagram.com/v1/users/{0}/media/recent/?access_token={1}',
			  'getSelfMediaLiked' : 'https://api.instagram.com/v1/users/self/media/liked?access_token={0}',
			  'getUserSearch' : 'https://api.instagram.com/v1/users/search?q={0}&access_token={1}'
			 }

@app.route('/')
def authenticate():
	igAuthUrl = 'https://api.instagram.com/oauth/authorize/?client_id='+clientID+'&redirect_uri='+redirectUrl+'&response_type=code&scope=basic+public_content+follower_list+comments+relationships+likes'
	return redirect(igAuthUrl)

@app.route('/index')
def index():
	code = request.args.get('code')
	r = requests.post('https://api.instagram.com/oauth/access_token', data={ 'client_id' : clientID, 
																			'client_secret' : clientSecret, 
																			'grant_type' : 'authorization_code', 
																			'redirect_uri' : redirectUrl,
																			'code' : code })


	resObj = json.loads(r.text)
	
	accessToken = resObj['access_token']
	userID = resObj['user']['id']
	userName = resObj['user']['username']
	userProfilePic = resObj['user']['profile_picture']
	userFullName = resObj['user']['full_name']
	userBio = resObj['user']['bio']
	userWebsite = resObj['user']['website']

	#start gathering data
	return gatherSelfData(accessToken)

	

def gatherSelfData(access_token):
	'''
		This method gather all data related user self and save it to dynamodb 
	'''
	url = urlIGDict['getSelfInfo'].format(access_token)

	resp = getIGData(url)

	print resp
	
	#if resp:
	#	dynamodb = boto3.resource('dynamodb')
	#	igUserSelfTable = dynamodb.Table('IGUserSelf')

	#	r = igUserSelfTable.put_item(Item=resp)		
		
	return resp


def getIGData(url):
	'''
		This method takes in url and return the response as json object
	'''
	try:
		r = requests.get(url)
		return json.loads(r.text)
	except e:
		#TODO: logging
		raise e
	