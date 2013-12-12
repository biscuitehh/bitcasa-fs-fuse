# BitcasaFS - A FUSE Filesystem Driver for BitcasaFS
# Michael Thomas, 2013

# Imports
import os
import errno
import fuse
import stat
import time
from bitcasa import Bitcasa

fuse.fuse_python_api = (0, 2)

# Since Bitcasa API doesn't have real "permissions", lie.
class BitcasaStat(fuse.Stat):
	def __init__(self, item = ""):
		fuse.Stat.__init__(self)
		print 'called BitcasaStat:',item

		# Check to see if item is file or folder
		if(item['Type'] == 'folders'):
			self.st_mode = stat.S_IFDIR | 0755
			self.st_nlink = 2
			self.st_size = 4096
		else:
			self.st_mode = stat.S_IFREG | 0666
			self.st_nlink = 1
			self.st_size = item['Size']
		# TODO: Find something to set these with.
		self.st_uid = os.geteuid()
		self.st_gid = os.getgid()

		# TODO: Bitcasa needs to save other times. Also, /1000 since they use microtime
		self.st_atime = int(item['mtime']) / 1000;
		self.st_mtime = int(item['mtime']) / 1000;
		self.st_ctime = int(item['mtime']) / 1000;

class BitcasaFS(fuse.Fuse):
	def __init__(self, *args, **kw):
		fuse.Fuse.__init__(self, *args, **kw)
		
		# Python FUSE Options
		self.bitcasa = Bitcasa('config.json')
		if(self.bitcasa == None):
			sys.exit("Failed to authenticate Bitcasa Client.")
		# Bitcasa Encoded Path (for things like rename/create/delete)
		self.bpath = ""
		# Breadcrumbs to how we got where we are.
		self.breadcrumbs = {}
		# Files/Folders in Current Path
		self.dir = {}

	def getattr(self, path):
		print 'called getattr:', path
		if (path == '/'):
			t = [0,]*10
			t[0] =  0755
			t[3] = 2; t[6] = 2048
			return t
		# Else pass File/Folder Object
		# mkdir Check
		elif(path.split('/')[-1] in self.dir):
			return BitcasaStat(self.dir[path.split('/')[-1]])
		else:
			# DNE
			return -errno.ENOENT

	# Directory Methods
	def readdir(self, path, offset):
		# Turn English into Bitcasa Base64
		# Root Path - This clears our breadcrumbs @ preps
		if(path == "/"):
			# Get Files/Folders for Root
			bdir = self.bitcasa.list_folder(path)
			# Clear Breadcrumbs
			self.breadcrumbs = { }
			# Add Root Breadcrumb
			self.breadcrumbs['/'] = { 'Name':'', 'Path':'/', 'Type':'folders', 'mtime':'0'}
			# Reset Path
			self.bpath = ""
		else:
			# Load next round of Files/Folders from Bitcasa
			bdir = self.bitcasa.list_folder(self.dir[path.split('/')[-1]]['Path'])
			# Add our new Breadcrumb
			# TODO - add logic to check and see if we have this breadcrumb already.
			self.breadcrumbs[path.split('/')[-1]] = self.dir[path.split('/')[-1]]
			# Current Bitcasa Path
			self.bpath = self.dir[path.split('/')[-1]]['Path']
			print(self.bpath)
		for b in bdir:
			# Get Extra File Stuff
			if(b['category'] == 'folders'):
				item = { 'Name':b['name'].encode('utf-8'), 'Path':b['path'].encode('utf-8'), 'Type':b['category'], 'mtime':b['mtime'] }
			else:
				item = { 'Name':b['name'].encode('utf-8'), 'Path':b['path'].encode('utf-8'), 'Type':b['category'], 'mtime':b['mtime'], 'ID':b['id'].encode('utf-8'), 'Size':b['size'] }
			self.dir[b['name'].encode('utf-8')] = item
			# Now yield to FUSE
			yield fuse.Direntry(b['name'].encode('utf-8'))

	def mkdir(self, path, mode):
		result = self.bitcasa.add_folder(self.bpath, path.split('/')[-1])
		if(result['error'] == None):
			new = result['result']['items'][0]
			item = { 'Name':new['name'].encode('utf-8'), 'Path':new['path'].encode('utf-8'), 'Type':new['category'], 'mtime':new['mtime'] }
			self.dir[new['name'].encode('utf-8')] = item
			return 0
		else:
			return -errno.ENOSYS

	# WIP - Doesn't report "file not found"
	def rmdir(self, path):
		print("Removing " + path + ";CurrentPath: " + self.bpath)
		result = self.bitcasa.delete_folder(self.dir[path.split('/')[-1]]['Path'])
		if(result['error'] == None):
			return 0
		else:
			return -errno.ENOSYS

	# File Methods
	def open(self, path, flags):
		print "Trying to open: ", path + "/" + self.dir[path.split('/')[-1]]['ID']
		print "Filename is: ", self.dir[path.split('/')[-1]]['Name']
		temp_file = self.bitcasa.download_file(self.dir[path.split('/')[-1]]['ID'], self.dir[path.split('/')[-1]]['Path'], self.dir[path.split('/')[-1]]['Name'], self.dir[path.split('/')[-1]]['Size'])
		if temp_file != None:
			return open(temp_file, "rb")
		else:
			return -errno.EACCESS

	# Read from Cached File
	# @todo - Consider adding "streaming" mode, we could do it.
	def read(self, path, size, offset, fh):
		fh.seek(offset)
		return fh.read(size)


# return -errno.ENOENT
if __name__ == '__main__':
	fs = BitcasaFS()
	fs.parse(errex=1)
	fs.main()