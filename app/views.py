from app import app	
from flask import redirect, request
import requests
import json 
import boto3
import datacollectors


clientID = ''
clientSecret = ''
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

	#invoke the data collection main function
	datacollectors.collectAllUserData(userName, accessToken)


	return accessToken




