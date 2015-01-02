import requests
import json
import os
import sys
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


def get_face(uid, itype=5):
	payload = (
			('appid', str(527020901)),
			('imgtype', str(itype)),
			('encrytype', '0'),
			('devtype', '0'),
			('keytpye', '0'),
			('uin', str(uid)))
	r = requests.get(url='http://ptlogin2.weiyun.com/getface', params=payload)
	response = r.text\
			.replace('pt.setHeader(', '')\
			.replace(');', '');
	return json.loads(response)

def parse(i):
	url = get_face(i)[str(i)]
	if '&t=0' in url: return
	r = requests.get(url=url)
	if r.status_code == 200:
		with open('./images/'+str(i)+'.jpeg', 'wb') as f:
			f.write(r.content)
		print str(i),url

pool = ThreadPool(8)
start = 2756810000
length = 10000
uids = range(start, start+length)
results = pool.map(parse, uids)
pool.close()
pool.join()