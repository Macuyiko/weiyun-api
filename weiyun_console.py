from weiyun import *
import os.path

def get_user_info():
	o = QueryUser()
	r = o.get_response()
	return r

user = get_user_info()
KEY_ROOT = user['rsp_body']['root_key']
KEY_MAIN = user['rsp_body']['main_dir_key']
DIR_DICTIONARY = {}
DIR_DICTIONARY[KEY_ROOT] = ('ROOT', '')
DIR_DICTIONARY[KEY_MAIN] = ('MAIN', KEY_ROOT)

def get_files_from_json(r):
	files = []
	if 'files' not in r['rsp_body'].keys() or r['rsp_body']['files'] is None:
		return files
	for d in r['rsp_body']['files']:
		name = d['file_name'] if 'file_name' in d.keys() else d['file_attr']['file_name']
		files.append((name, d['file_id'], d['file_md5'], d['file_sha'], d))
	return files

def get_dirs_from_json(r):
	dirs = []
	if 'dirs' not in r['rsp_body'].keys() or r['rsp_body']['dirs'] is None:
		return dirs
	for d in r['rsp_body']['dirs']:
		name = d['dir_name'] if 'dir_name' in d.keys() else d['dir_attr']['dir_name']
		dirs.append((name, d['dir_key'], d))
	return dirs

def handle_dir_list(r, dirkey, parentdirkey):
	print
	print "Listing of %s (%s):" % (DIR_DICTIONARY[dirkey][0], dirkey)
	dirs = get_dirs_from_json(r)
	files = get_files_from_json(r)
	print "    ..  %s: %s" % (DIR_DICTIONARY[parentdirkey][0], parentdirkey)
	for d in xrange(0, len(dirs)):
		print "    DIR [%s] %s: %s" % (d, dirs[d][0], dirs[d][1])
	print
	for f in xrange(0, len(files)):
		print "    [%s] %s: %s" % (f, files[f][0], files[f][1])
	return (dirkey,parentdirkey,dirs,files)

def make_dir(dirname, dirkey, parentdirkey):
	o = DirCreate(ocommand[1], dirkey, parentdirkey)
	o.get_response()
	return (dirkey, parentdirkey)

def delete_dir(name, key, dirkey, parentdirkey):
	o = BatchFolderDelete([name], [key], [dirkey], [parentdirkey])
	o.get_response()
	return (dirkey, parentdirkey)

def get_dir_list(dirkey=KEY_MAIN, parentdirkey=KEY_ROOT):
	if parentdirkey is None:
		if dirkey in DIR_DICTIONARY.keys():
			parentdirkey = DIR_DICTIONARY[dirkey][1]
		else:
			parentdirkey = KEY_ROOT
	if dirkey==KEY_MAIN or parentdirkey==KEY_ROOT:
		o = RootDirList()
		dirkey = KEY_MAIN
		parentdirkey = KEY_ROOT
	else:
		o = GetDirList(dirkey, parentdirkey)
	r = o.get_response()
	for d in get_dirs_from_json(r):
		DIR_DICTIONARY[d[1]] = (d[0], dirkey)
	return (dirkey, parentdirkey, r)

def delete_file(name, id, ver, dirkey, parentdirkey):
	o = BatchFileDelete([name], [id], [ver], [dirkey], [parentdirkey])
	o.get_response()
	return (dirkey, parentdirkey)

def upload_file(name, dirkey, parentdirkey):
	o = FileUpload(name, file_size(name), dirkey, parentdirkey, md5(ocommand[1]), sha1(ocommand[1]))
	o.send_file(ocommand[1])
	return (dirkey, parentdirkey)

def download_file(fid, name, dirkey):
	user = get_user_info()
	checksum = user['rsp_body']['checksum']
	o = DownloadFile(fid, name, dirkey, checksum)
	o.get_file(files[int(command[1])][0])
	return (dirkey, parentdirkey)

def handle_command(dirkey, parentdirkey, dirs, files):
	print
	ocommand = ''
	while ocommand == '':
		ocommand = raw_input("?> ")
		command = ocommand
		while '  ' in command:
			command = command.replace('  ',' ')
		command = command.strip().split(' ');
		if command[0] == "cd":
			if command[1] == '..':
				d,p,r = get_dir_list(parentdirkey, None)
			else:
				d,p,r = get_dir_list(dirs[int(command[1])][1], dirkey)
			return (d,p)
		elif command[0] == "mkdir":
			return make_dir(ocommand[1], dirkey, parentdirkey)
		elif command[0] == "delfile":
			return delete_file(files[int(command[1])][1], 
				files[int(command[1])][0],
				files[int(command[1])][4]['file_ver'], 
				dirkey, parentdirkey)
		elif command[0] == "deldir":
			return delete_dir(dirs[int(command[1])][0], 
				dirs[int(command[1])][1],
				dirkey, parentdirkey)
			return (dirkey, parentdirkey)
		elif command[0] == "upload":
			print "Uploading file..."
			ocommand = ocommand.strip().split('"');
			if os.path.isfile(ocommand[1]):
				return download_file(ocommand[1], dirkey, parentdirkey)
			print "File does not exist"
		elif command[0] == "download":
			print "Downloading file..."
			return download_file(files[int(command[1])][1], files[int(command[1])][0], dirkey)
		elif command[0] == "exit":
			exit()
		ocommand = ''
		print "Valid commands: cd, deldir, delfile, mkdir, upload, download"
	
d,p,r = get_dir_list()
while True:
	d,p,dirs,files = handle_dir_list(r,d,p)
	d,p = handle_command(d, p, dirs, files)
	d,p,r = get_dir_list(d,p)

