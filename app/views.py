from app import app
from flask import redirect, request
import requests

#glabal values
clientID = 'bc3fe815409344ccb43f57c662a498d0'
clientSecret = '3d18fb13207649f68933d34311acca61'
redirectUrl = 'http://127.0.0.1:5000/index'


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





	return r.text
