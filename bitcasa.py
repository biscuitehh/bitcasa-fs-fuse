# Bitcasa Python Class (Unofficial)
# Michael Thomas, 2013 
# TODO #
########
# Test for Python2 & Python3
# Error Handling that works well.
# Implement File Methods
# DONE: download file to cache
# upload file from cache

# Import Section
import urllib2, urllib
import json
import base64
import sys
import os

# Upload Progress Helper
# @todo - May switch Download to this as well.
class Progress(object):
	def __init__(self):
		self._seen = 0.0

	def update(self, total, size, name):
		self._seen += size
		pct = (self._seen / total) * 100.0
		print '%s progress: %.2f' % (name, pct)

class file_with_callback(file):
	def __init__(self, path, mode, callback, *args):
		file.__init__(self, path, mode)
		self.seek(0, os.SEEK_END)
		self._total = self.tell()
		self.seek(0)
		self._callback = callback
		self._args = args

	def __len__(self):
		return self._total

	def read(self, size):
		data = file.read(self, size)
		self._callback(self._total, len(data), *self._args)
		return data
# e.g.
# path = 'large_file.txt'
# progress = Progress()
# stream = file_with_callback(path, 'rb', progress.update, path)
# req = urllib2.Request(url, stream)
# res = urllib2.urlopen(req)

# Bitcasa Class
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
		
		# Adding support for File Cache
		self.cache_dir = self.config['cache_dir'].encode('utf-8')
		# Check to see if cache_dir is valid & exists
		if(self.cache_dir == None):
			self.cache_dir = os.path.dirname(os.path.realpath(__file__)) + ".cache"
			self.save_config()
		# Now Make sure it exists
		if not os.path.exists(self.cache_dir):
			os.makedirs(self.cache_dir)
		
		# See if we need our tokens
		if(self.auth_token == "") or (self.access_token == ""):
			return self.authenticate()
		else:
			return None

	def save_config (self):
		with open(self.config_path, 'w') as outfile:
			json.dump(self.config, outfile, indent=4)

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

	def add_folder (self, path, folder_name):
		payload = {"folder_name":folder_name}
		request = urllib2.Request(self.api_url + "/folders/" + path + "?access_token=" + self.access_token, urllib.urlencode(payload))
		try:
			response = json.load(urllib2.urlopen(request))
		except urllib2.HTTPError, e:
			response = e.read()
		return response

	def delete_folder (self, path):
		payload = {"path":path}
		request = urllib2.Request(self.api_url + "/folders/?access_token=" + self.access_token, urllib.urlencode(payload))
		request.get_method = lambda: 'DELETE'
		response = json.load(urllib2.urlopen(request))
		return response

	# File API Methods
	def download_file (self, file_id, path, file_name, file_size):
		f = open(self.cache_dir + "/" + file_name, 'wb')
		print "Downloading file from: " + self.api_url + "/files/"+file_id+"/"+ file_name +"?access_token=" + self.access_token + "&path=/" + path
		u = urllib2.urlopen(self.api_url + "/files/"+file_id+"/"+file_name+"?access_token=" + self.access_token + "&path/" + path)
		print "Downloading: %s Bytes: %s" % (file_name, file_size)
		file_size_dl = 0
		block_sz = 8192
		
		while True:
			buffer = u.read(block_sz)
			if not buffer:
				break
			file_size_dl += len(buffer)
			f.write(buffer)
			status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
			status = status + chr(8)*(len(status)+1)
			print status
		print "Closing new File"
		f.close()
		return self.cache_dir + "/" + file_name

	def upload_file (self, path, file_name, file_size):
		return
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
