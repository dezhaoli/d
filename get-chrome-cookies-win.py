import os
import json
import base64
import sqlite3
import shutil
import sys
from urllib.parse import urlparse

# python.exe -m pip install pypiwin32
import win32crypt
# python.exe -m pip install pycryptodomex
from Cryptodome.Cipher import AES


def parse_domain(hostname):
    parsed_url = urlparse(hostname)
    if parsed_url.scheme:
        domain = parsed_url.netloc
    else:
        raise ValueError('You must include a scheme with your hostname')
    labels = domain.split('.')
    for i in range(2, len(labels) + 1):
        domain = '.'.join(labels[-i:])
        yield domain
        yield '.' + domain

def fetch_cookies(hostname):
	# Copy Cookies and Local State to current folder
	cookies_file=os.getenv("USERPROFILE") + '/Desktop/Cookies'
	try:
		shutil.copyfile(os.getenv("USERPROFILE") + "/AppData/Local/Google/Chrome/User Data/Default/Network/Cookies", cookies_file)
	except Exception as e:
		pass
	

	# Load encryption key
	encrypted_key = None
	with open(os.getenv("USERPROFILE") + "/AppData/Local/Google/Chrome/User Data/Local State", 'r') as file:
		encrypted_key = json.loads(file.read())['os_crypt']['encrypted_key']
	encrypted_key = base64.b64decode(encrypted_key)
	encrypted_key = encrypted_key[5:]
	decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]


	# Connect to the Database
	conn = sqlite3.connect(cookies_file)
	conn.text_factory = lambda b: b.decode(errors="ignore")
	cursor = conn.cursor()

	# Get the results
	cookies = dict()
	# cursor.execute('SELECT host_key, name, value, encrypted_value FROM cookies ')
	
	for host_key in parse_domain(hostname):
		cursor.execute('SELECT host_key, name, value, encrypted_value FROM cookies WHERE host_key = ?', (host_key,))
		for host_key, name, value, encrypted_value in cursor.fetchall():
			# Decrypt the encrypted_value
			try:
				# Try to decrypt as AES (2020 method)
				cipher = AES.new(decrypted_key, AES.MODE_GCM, nonce=encrypted_value[3:3+12])
				decrypted_value = cipher.decrypt_and_verify(encrypted_value[3+12:-16], encrypted_value[-16:])
			except:
				# If failed try with the old method
				decrypted_value = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8') or value or 0
			cookies[name] = decrypted_value.rstrip().decode('utf8')

	conn.commit()
	conn.close()
	return cookies


if __name__ == '__main__':
    url = sys.argv[1]
    cookies = fetch_cookies(url)
    for key in cookies:
        print(key + '=' + cookies[key])