# Bitcasa Python Class (Unofficial)
# Michael Thomas, 2013 

# Import Section
import urllib2, urllib
import json
import base64
import sys

class Bitcasa:
	# Start Client & Load Config
	def __init__ (self, config_path):
		# Config file
		self.config_path = config_path
		try:
			with open(self.config_path, 'r') as config_file:
				self.config = json.load(config_file)
		except:
			sys.exit("Could not find configuration file.")
		# Set configuation variables
		self.api_url = self.config['api_url'].encode('utf-8')
		self.client_id = self.config['client_id'].encode('utf-8')
		self.secret = self.config['secret'].encode('utf-8')
		self.redirect_url = self.config['redirect_url'].encode('utf-8')
		self.auth_token = self.config['auth_token'].encode('utf-8')
		self.access_token = self.config['access_token'].encode('utf-8')
		# See if we need our tokens
		if(self.auth_token == "") or (self.access_token == ""):
			return self.authenticate()
		else:
			return None

	def save_config (self):
		with open(self.config_path, 'w') as outfile:
			json.dump(self.config, outfile)

	def authenticate (self):
		print("### ENTER THE FOLLOWING URL IN A BROWSER AND AUTHORIZE THIS APPLICATION ###")
		print(self.api_url + "/oauth2/authenticate?client_id=" + self.client_id + "&redirect=" + self.redirect_url)
		print("### ONCE YOU HAVE AUTHORIZED THE APPLICATION, ENTER THE AUTH TOKEN HERE (WILL BE IN URL) ###")
		auth = raw_input("Auth Token: ")
		self.auth_token = auth
		self.config['auth_token'] = self.auth_token
		request = urllib2.Request("https://developer.api.bitcasa.com/v1/oauth2/access_token?secret="+ self.secret +"&code=" + self.auth_token)
		try:
			response = json.load(urllib2.urlopen(request))
			self.access_token = response['result']['access_token']
			self.config['access_token'] = self.access_token
			self.save_config()
			return True
		except urllib2.HTTPError, e:
			error = e.read()
			return error

	def list_folder (self, path = ""):
		request = urllib2.Request(self.api_url + "/folders" + path + "?access_token=" + self.access_token)
		try:
			response = json.load(urllib2.urlopen(request))
		except urllib2.HTTPError, e:
			error = e.read()
			response = json.loads(error)
		if(response['result'] == None):
			return response
		else:
			return response['result']['items']

	def add_folder (self, folder_name, path = ""):
		payload = {"folder_name":folder_name}
		print(self.api_url + "/folders/" + path + "?access_token=" + self.access_token, urllib.urlencode(payload))
		request = urllib2.Request(self.api_url + "/folders/" + path + "?access_token=" + self.access_token, urllib.urlencode(payload))
		try:
			response = json.load(urllib2.urlopen(request))
		except urllib2.HTTPError, e:
			response = e.read()
		return response

	def delete_folder (self, path):
		if(path != ""):
			path = base64.b64encode(path)
		request = urllib2.Request(self.api_url + "/folders/" + path + "?access_token=" + self.access_token, data)
		request.get_method = lambda: 'DELETE'
		response = json.load(urllib2.urlopen(request))
		return response

	# def rename_folder (self, path, new_filename, exists = "rename"):
	# 	# Encode path
	# 	if(path != ""):
	# 		path = base64.b64encode(path)
	# 	else:
	# 		return "You must specify a file to rename."
		
	# 	payload = { "operation" = "" }
	# 	data = urllib.urlencode(payload)

	# 	request = urllib2.Request(Bitcasa.api_url + "/folders/" + path + "?access_token=" + self.access_token, data)
	# 	response = json.load(urllib2.urlopen(request))
	# 	return response;
