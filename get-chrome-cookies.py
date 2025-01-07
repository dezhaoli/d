import keyring
import sys
from hashlib import pbkdf2_hmac
import os
import sqlite3
from urlparse import urlparse
from Crypto.Cipher import AES
import binascii

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

    
def fetch_cookies(hostname, isChrome=True):
    if not (sys.platform == 'darwin'):
        raise ValueError('This script only works on macOS')


    if isChrome:
        cookies_filepath = '~/Library/Application Support/Google/Chrome/Default/Cookies'
        browser = 'Chrome'
    else:
        cookies_filepath = '~/Library/Application Support/Chromium/Default/Cookies'
        browser = 'Chromium'

    password = keyring.get_password(browser + ' Safe Storage', browser)
    cookies_erncrypt_key = pbkdf2_hmac(hash_name='sha1',
                   password=password.encode('utf8'),
                   salt=b'saltysalt',
                   iterations=1003,
                   dklen=16)


    cookie_file_path = str(os.path.expanduser(cookies_filepath))
    print(cookie_file_path)
    print(hostname)
    with sqlite3.connect(cookie_file_path) as conn:
        cookies = dict()

        for domain in parse_domain(hostname):
            print(domain)
            for name, value, encrypted_value_hex in conn.execute("SELECT name, value, HEX(encrypted_value) FROM cookies WHERE host_key LIKE ?", (domain,)) :
                encrypted_value = binascii.unhexlify(encrypted_value_hex)
                if value or (encrypted_value[:3] not in (b'v10', b'v11')):
                    pass
                else:
                    cipher = AES.new(cookies_erncrypt_key , AES.MODE_CBC, IV=b' ' * 16)
                    decrypted_value = cipher.decrypt(encrypted_value[3:])
                    value = decrypted_value[32:].rstrip().decode('utf8')
                cookies[name] = value

    return cookies
            

if __name__ == '__main__':
    url = sys.argv[1]
    cookies = fetch_cookies(url)
    for key in cookies:
        print key + '=' + cookies[key]