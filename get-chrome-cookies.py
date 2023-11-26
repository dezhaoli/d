import keyring
import sys
from hashlib import pbkdf2_hmac
import os
import sqlite3
from urlparse import urlparse
from Crypto.Cipher import AES


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

def decrypt(encrypt_string, cookies_erncrypt_key):
    encrypt_string = encrypt_string[3:]
    cipher = AES.new(cookies_erncrypt_key , AES.MODE_CBC, IV=b' ' * 16)
    decrypted_string = cipher.decrypt(encrypt_string)
    return decrypted_string.rstrip().decode('utf8')
    
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

    with sqlite3.connect(cookie_file_path) as conn:
        secure_column_name = 'is_secure'
        for column_names in conn.execute('PRAGMA table_info(cookies)'):
            if column_names[1] == 'secure':
                secure_column_name = 'secure'
                break
            elif column_names[1] == 'is_secure':
                break
        
        sql_str = ('select host_key, path, ' + secure_column_name +
                   ', expires_utc, name, value, encrypted_value '
                   'from cookies where host_key like ?')
        cookies = dict()

        for host_key in parse_domain(hostname):
            for hk, path, is_secure, expires_utc, cookie_key, val, enc_val \
                in conn.execute(sql_str, (host_key,)):
                if val or (enc_val[:3] not in (b'v10', b'v11')):
                    pass
                else:
                    val = decrypt(enc_val, cookies_erncrypt_key)
                cookies[cookie_key] = val

    return cookies
            

if __name__ == '__main__':
    url = sys.argv[1]
    cookies = fetch_cookies(url)
    for key in cookies:
        print key + '=' + cookies[key]