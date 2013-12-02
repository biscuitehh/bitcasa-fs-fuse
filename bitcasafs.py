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
			self.st_size = item['size']
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
		else: return BitcasaStat(self.dir[path.split('/')[-1]])

	def readdir(self, path, offset):
		print "readir: ",path
		# Turn English into Bitcasa Base64
		# Root Path - This clears our breadcrumbs @ preps
		if(path == "/"):
			# Get Files/Folders for Root
			bdir = self.bitcasa.list_folder(path)
			# Clear Breadcrumbs
			self.breadcrumbs = { }
			# Add Root Breadcrumb
			self.breadcrumbs['/'] = { 'Name':'', 'Path':'/', 'Type':'folders', 'mtime':'0'}
		else:
			# Load next round of Files/Folders from Bitcasa
			bdir = self.bitcasa.list_folder(self.dir[path.split('/')[-1]]['Path'])
			# Add our new Breadcrumb
			# TODO - add logic to check and see if we have this breadcrumb already.
			self.breadcrumbs[path.split('/')[-1]] = self.dir[path.split('/')[-1]]
		for b in bdir:
			item = { 'Name':b['name'].encode('utf-8'), 'Path':b['path'].encode('utf-8'), 'Type':b['category'], 'mtime':b['mtime'] }
			# But wait, there's more!
			if('size' in b):
				item['size'] = b['size']
			self.dir[b['name'].encode('utf-8')] = item
			# Now yield to FUSE
			yield fuse.Direntry(b['name'].encode('utf-8'))

	# WIP #
	def mkdir(self, path, mode):
		self.bitcasa.add_folder(self.current_item['Path'], "Test")
		return 0

if __name__ == '__main__':
	fs = BitcasaFS()
	fs.parse(errex=1)
	fs.main()