import requests
try:
	from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
	TOOLBELT_AVAILABLE = True
except ImportError:
	TOOLBELT_AVAILABLE = False
import uuid
import json
import time
import os
import hashlib
import sys
import struct
import binascii

# Change the values below:
SKEY = '@changeme';
UIN = '29changeme';
PTCZ = '97changeme'
PGV_INFO = 'ssid=s9changeme'
PGV_PVID = 'changeme'
EMAIL = 'changeme@changeme.changeme'

current_milli_time = lambda: int(round(time.time() * 1000))
file_size = lambda x: os.stat(x).st_size 
get_ordered_tuple = lambda x,y: next(a[1] for a in x if a[0] == y)
md5 = lambda x: hashlib.md5(open(x, 'rb').read()).hexdigest()
sha1 = lambda x: hashlib.sha1(open(x, 'rb').read()).hexdigest()
jsonprint = lambda x: json.dumps(x, sort_keys=True, indent=2, separators=(',', ': '))
def get_token(skey, md5key='tencentQQVIP123443safde&!%^%1282', salt=5381):
	thash = []
	num = salt<<5
	thash.append(str(num))
	for i in range(0, len(skey)):
		ac = ord(skey[i])
		num = (salt<<5)+ac
		thash.append(str(num))
		salt = ac
	return hashlib.md5(''.join(thash)+md5key).hexdigest()
def get_tk(skey, salt=5381):
	for i in range(0, len(skey)):
		ac = ord(skey[i])
		salt += (salt<<5)+ac
	return salt&0x7fffffff;
def get_chunk(filename, offset, length=131072):
	f = open(filename)
	f.seek(offset)
	chunk = f.read(length)
	f.close()
	return chunk
def encode_chunk(ukey, filekey, filename, offset, chunk):
	data = ''
	data = data + struct.pack('>I', 2882377846)
	data = data + struct.pack('>I', 1000)
	data = data + struct.pack('>I', 0)
	hlen = 2*2 + 4*3 + len(ukey)/2 + len(filekey)/2 + len(chunk)
	data = data + struct.pack('>I', hlen)
	data = data + struct.pack('>H', len(ukey)/2)
	data = data + binascii.unhexlify(ukey)
	data = data + struct.pack('>H', len(filekey)/2)
	data = data + binascii.unhexlify(filekey)
	data = data + struct.pack('>I', file_size(filename))
	data = data + struct.pack('>I', offset)
	data = data + struct.pack('>I', len(chunk))
	data = data + chunk
	return data

TOKEN = get_token(SKEY)
GTK = get_tk(SKEY)
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36' \
			' (KHTML, like Gecko) Chrome/37.0.2062.94 Safari/537.36',
			'Referer': 'http://www.weiyun.com/disk/index-en.html'}
COOKIES = {'pgv_info': PGV_INFO,
			'pgv_pvid': PGV_PVID, 
			'ptui_loginuin': EMAIL,
			'pt2gguin': 'o'+UIN,
			'uin': 'o'+UIN,
			'skey': SKEY,
			'ptisp': 'os',
			'ptcz': PTCZ}
REQ_HEADER = {"cmd":"",
				"main_v":11,
				"proto_ver":10006,
				"sub_v":1,
				"encrypt":0,
				"msg_seq":1,
				"source":30234,
				"appid":30234,
				"client_ip":"127.0.0.1",
				"token":TOKEN}

class BaseWeiyun(object):
	def __init__(self, endpoint, cmd):
		self.base = 'http://web.cgi.weiyun.com'
		self.endpoint = endpoint
		self.cmd = cmd
		self.data = {"req_header":REQ_HEADER,
					"req_body":{}}
		self.data["req_header"]["cmd"] = cmd

	def get_response(self):
		url = self.base + self.endpoint
		payload = self.get_payload()
		r = requests.get(url, cookies=COOKIES, params=payload, headers=HEADERS)
		response = r.text\
			.replace('try{'+get_ordered_tuple(payload,"callback")+'(', '')\
			.replace(')} catch(e){};', '')\
			.replace(')}catch(e){};', '');
		return json.loads(response)

	def get_payload(self, isPost=False):
		ruuid = str(uuid.uuid4()).upper().replace('-', '_')
		prefix = 'post_callback' if isPost else 'get'
		payload = (('cmd', self.cmd),
			('g_tk', GTK),
			('callback', prefix+'_'+ruuid),
			('data', json.dumps(self.data)),
			('_', str(current_milli_time())))
		return payload;

class QueryUser(BaseWeiyun):
	def __init__(self):
		endpoint = '/wy_web_jsonp.fcg'
		cmd = 'query_user'
		super(QueryUser, self).__init__(endpoint, cmd)

class RootDirList(BaseWeiyun):
	def __init__(self):
		endpoint = '/weiyun_web_root_dir_list_cgi.fcg'
		cmd = 'root_dir_list'
		super(RootDirList, self).__init__(endpoint, cmd)

class GetDirList(BaseWeiyun):
	def __init__(self, dirkey, parentdirkey):
		endpoint = '/wy_web_jsonp.fcg'
		cmd = 'get_dir_list'
		super(GetDirList, self).__init__(endpoint, cmd)
		self.data["req_body"] = {
				"pdir_key":parentdirkey,
				"dir_key":dirkey,
				"dir_mtime":"2000-01-01 01:01:01",
				"only_dir":0}

class DirCreate(BaseWeiyun):
	def __init__(self, dirname, parentdirkey, parentparentdirkey):
		endpoint = '/wy_web_jsonp.fcg'
		cmd = 'dir_create'
		super(DirCreate, self).__init__(endpoint, cmd)
		self.data["req_body"] = {"ppdir_key": parentparentdirkey,
			"pdir_key": parentdirkey,
			"dir_attr": {"dir_name":dirname, "dir_note":""}}

	def get_response(self):
		url = self.base + self.endpoint
		payload = self.get_payload(True)
		r = requests.post(url, cookies=COOKIES, params=payload, data=payload, headers=HEADERS)
		response = r.text\
			.replace('<script>document.domain="weiyun.com";'+\
				'try{parent.'+get_ordered_tuple(payload,"callback")+'(', '')\
			.replace(')} catch(e){};</script>', '');
		return json.loads(response)

class BatchFolderDelete(BaseWeiyun):
	def __init__(self, dirnames, dirkeys, parentdirkeys, parentparentdirkeys):
		endpoint = '/wy_web_jsonp.fcg'
		cmd = 'batch_folder_delete'
		super(BatchFolderDelete, self).__init__(endpoint, cmd)
		dellist = []
		for i in range(0, len(dirnames)):
			dellist.append({"ppdir_key":parentparentdirkeys[i],
							"pdir_key":parentdirkeys[i],
							"dir_key":dirkeys[i],
							"flag":1,
							"dir_name":dirnames[i]})
		self.data["req_body"] = {"del_folders": dellist}

	def get_response(self):
		url = self.base + self.endpoint
		payload = self.get_payload(True)
		r = requests.post(url, cookies=COOKIES, params=payload, data=payload, headers=HEADERS)
		response = r.text\
			.replace('<script>document.domain="weiyun.com";'+\
				'try{parent.'+get_ordered_tuple(payload,"callback")+'(', '')\
			.replace(')} catch(e){};</script>', '');
		return json.loads(response)

class BatchFileDelete(BaseWeiyun):
	def __init__(self, fileids, filenames, filevers, parentdirkeys, parentparentdirkeys):
		endpoint = '/wy_web_jsonp.fcg'
		cmd = 'batch_file_delete'
		super(BatchFileDelete, self).__init__(endpoint, cmd)
		dellist = []
		for i in range(0, len(fileids)):
			dellist.append({"ppdir_key":parentparentdirkeys[i],
							"pdir_key":parentdirkeys[i],
							"file_id":fileids[i],
							"file_name":filenames[i],
							"file_ver":filevers[i]})
		self.data["req_body"] = {"del_files": dellist}

	def get_response(self):
		url = self.base + self.endpoint
		payload = self.get_payload(True)
		r = requests.post(url, cookies=COOKIES, params=payload, data=payload, headers=HEADERS)
		response = r.text\
			.replace('<script>document.domain="weiyun.com";'+\
				'try{parent.'+get_ordered_tuple(payload,"callback")+'(', '')\
			.replace(')} catch(e){};</script>', '');
		return json.loads(response)

class DownloadFile(BaseWeiyun):
	def __init__(self, fileid, filename, parentdirkey, checksum):
		endpoint = '/wy_down.fcg'
		cmd = None
		super(DownloadFile, self).__init__(endpoint, cmd)
		self.base = 'http://download.cgi.weiyun.com'
		self.data = None
		self.fileid = fileid
		self.filename = filename
		self.parentdirkey = parentdirkey
		self.checksum = checksum

	def get_response(self, stream=True):
		url = self.base + self.endpoint
		payload = self.get_payload()
		headers = HEADERS.copy()
		headers['origin'] = 'http://www.weiyun.com'
		r = requests.post(url, cookies=COOKIES, params=payload, headers=headers, stream=stream)
		return r

	def callback(self, ds, sofar, total):
		w = 80
		sys.stdout.write( "\b" * (w+10) )
		speed = ds / ((current_milli_time() - self.tb)/1000)
		sys.stdout.write( "[%s%s] %s" %
			("#" * (int(w * float(sofar) / float(total))),
			 " " * (w-(int(w * float(sofar) / float(total)))),
			 speed) )

	def get_file(self, filename, stream=True, callback=None):
		if callback is None:
			callback = self.callback
		a = self.get_response()
		self.tb = current_milli_time()-1000
		if stream:
			total = 0
			with open(filename, 'wb') as fd:
				ds = 1024*100
				for chunk in a.iter_content(ds):
					total += len(chunk)
					fd.write(chunk)
					callback(ds, total, str(a.headers['content-length']))
			print
			a.close()
		else:
			with open(filename, 'wb') as fd:
				fd.write(a.content)
				fd.close()

	def get_payload(self):
		payload = (('fid', self.fileid),
					('pdir', self.parentdirkey),
					('fn', self.filename),
					('uuin', UIN),
					('skey', SKEY),
					('appid', REQ_HEADER["appid"]),
					('token', TOKEN),
					('checksum', self.checksum),
					('err_callback', 'http://www.weiyun.com/web/callback/iframe_disk_down_fail.html'),
					('ver', REQ_HEADER["main_v"]))
		return payload

class FileUpload(BaseWeiyun):
	def __init__(self, filename, filesize, parentdirkey, parentparentdirkey, md5="", sha=""):
		endpoint = '/upload.fcg'
		cmd = 'file_upload'
		super(FileUpload, self).__init__(endpoint, cmd)
		utype = 1 if md5 == "" else 0
		self.data["req_body"] = {"ppdir_key":parentparentdirkey,
				"pdir_key":parentdirkey,
				"upload_type": utype,
				"file_md5":md5,
				"file_sha":sha,
				"file_size":str(filesize),
				"file_attr":{"file_name":filename}}
		self.parentdirkey = parentdirkey
		self.parentparentdirkey = parentparentdirkey

	def send_file(self, filename):
		a = self.get_response()
		if (a['rsp_body']['file_exist']):
			return True
		else:
			self.data["req_body"]["file_md5"] = ''
			self.data["req_body"]["file_sha"] = ''
			self.data["req_body"]["upload_type"] = 1
			# Delete broken old file
			o = BatchFileDelete(
				[self.data["req_body"]["file_attr"]["file_name"]], 
				[a['rsp_body']['file_id']],
				[a['rsp_body']['file_ver']], 
				[self.parentdirkey], [self.parentparentdirkey])
			o.get_response()
			a = self.get_response()
		#print a
		url = 'http://' + a['rsp_body']['upload_svr_host']+':'+\
			str(a['rsp_body']['upload_svr_port']) + '/ftn_handler/'+\
			'?ver=12345&ukey='+a['rsp_body']['upload_csum']+\
			'&filekey='+a['rsp_body']['file_key']+'&'
		headers = HEADERS.copy()
		headers['origin'] = 'http://www.weiyun.com'
		data = {'Filename': self.data["req_body"]["file_attr"]["file_name"],
				'mode': 'flashupload',
				'Upload': 'Submit Query',
				'file': ('filename', open(filename, 'rb'), 'application/octet-stream')}
		r = requests.post(url, headers=headers, files={'file':data['file']})
		return r

class ChunkedFileUpload(BaseWeiyun):
	def __init__(self, filename, filesize, parentdirkey, parentparentdirkey, fmd5, fsha):
		utype = 1 if fmd5 == "" else 0
		self.base = 'http://user.weiyun.com/newcgi'
		self.endpoint = '/qdisk_upload.fcg'
		self.cmd = '2301'
		self.data = {"req_header":{
						"cmd":int(self.cmd),
						"appid":30013,
						"version":2,
						"major_version":2},
					"req_body":{
						"ReqMsg_body":{
							"weiyun.DiskFileUploadMsgReq_body":{
								"ppdir_key":parentparentdirkey,
								"pdir_key":parentdirkey,
								"upload_type":utype,
								"file_md5":fmd5,
								"file_sha":fsha,
								"file_size":filesize,
								"filename":filename,
								"file_exist_option":4}}}}
		self.parentdirkey = parentdirkey
		self.parentparentdirkey = parentparentdirkey

	def get_response(self):
		url = self.base + self.endpoint
		payload = self.get_payload()
		headers = HEADERS.copy()
		headers['Referer'] = 'http://user.weiyun.com/cdr_proxy.html'
		r = requests.get(url, cookies=COOKIES, params=payload, headers=headers)
		response = r.text\
			.replace('try{X_GET(', '')\
			.replace(')}catch(e){};', '');
		return json.loads(response)

	def get_payload(self):
		payload = (('cmd', self.cmd),
			('g_tk', GTK),
			('data', json.dumps(self.data)), 
			('callback', 'X_GET'),
			('_', str(current_milli_time())))
		return payload;

	def callback(self, send, total):
		print send, total

	def send_file(self, filename, callback=None):
		if callback is None:
			callback = self.callback
		a = self.get_response()
		rspbody = a['rsp_body']['RspMsg_body']['weiyun.DiskFileUploadMsgRsp_body']
		print rspbody
		if rspbody['file_exist'] and False:
			return True
		else:
			print ''
			url = 'http://' + rspbody['server_name']+':'+\
				str(rspbody['server_port']) + '/ftn_handler/'+\
				self.data['req_body']['ReqMsg_body']['weiyun.DiskFileUploadMsgReq_body']['file_md5']
			headers = HEADERS.copy()
			headers['origin'] = 'http://img.weiyun.com'
			length = 131072
			filekey = rspbody['file_key']
			ukey = rspbody['check_key']
			for start in range(0, file_size(filename), 131072):
				chunk = get_chunk(filename, start, length)
				encch = encode_chunk(ukey, filekey, filename, start, chunk)
				bmd5 = '?' # TODO: requires conversion of crypto
				print bmd5
				r = requests.post(url+ '?bmd5=' + bmd5, headers=headers, data = encch)
				if callback is not None:
					callback(start + length, file_size(filename))
