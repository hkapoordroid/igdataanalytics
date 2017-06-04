from app import app	
from flask import redirect, request
import requests
import json 
import boto3
import datacollectors


clientID = '26d2405a54464c8d93cc2cc786401246'
clientSecret = '3f6f68e1ab2841a9831f10bf6a13bcfd'
redirectUrl = 'http://127.0.0.1:5000/index'


@app.route('/')
def authenticate():
	igAuthUrl = 'https://api.instagram.com/oauth/authorize/?client_id='+clientID+'&redirect_uri='+redirectUrl+'&response_type=code&scope=basic+public_content+follower_list+comments+relationships+likes'

	#initialize the global variables and settings

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
	print('Got the access tokens, lets start pulling data...')

	#get user's info
	print('Getting user''s self info')
	datacollectors.gatherSelfData(accessToken)

	#get user's own media data
	print('Getting user self media data')
	datacollectors.gatherSelfMediaData(accessToken)

	return accessToken



