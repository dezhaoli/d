#!/usr/bin/python2
import random
import time
import hashlib
import hmac
import base64
import requests
if hasattr(requests, "packages") and requests.adapters.HTTPResponse is requests.packages.urllib3.response.HTTPResponse:
    import requests.packages.urllib3 as urllib3
else:
    import urllib3
if hasattr(urllib3, "disable_warnings"):
    urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
    urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import json
import urlparse
import urllib

from form_file import FormFile


class ConstError(Exception): pass

class _const(object):
    def __setattr__(self, k, v):
        if k in self.__dict__:
            raise ConstError
        else:
            self.__dict__[k] = v

CFG = _const()

CFG.URI_PREFIX = "/v1/openapi"
CFG.SPECIAL_POST_API = [
    "UploadApp",
    "UploadRes",
    "UploadDynamicRes",
    "UploadUpdateFile",
    "UpdateGrayRule",
]


class GCloudError(Exception):
    def __init__(self, code, message):
        self._code = code
        self._message = message
    def __str__(self):
        return "code=[%s], message=[%s]" % (
            self._code,
            self._message,
        )


def request_gcloud_api(host, gameid, accessid, accesskey, module, action, params=None, data=None, file=None, debug=False, proxy=None):
    """Request gcloud openapi with HTTP POST.
    Parameters:
      - params: parameters apart from the common parameters(*ts*, *nonce*, *accessid*, etc.)
                and *gameid*. It's a 2-tuple list, like:
                    [
                        ("productid", 1),
                        ("versionstr", "1.1.1.1"),
                        ...
                    ]
      - data: data in body, can be bytes(string) or file-like object
      - file: only used when uploading a file(form-based file upload, see rfc 1867).
              It's a ("filename", file-like object) tuple, e.g.
                ("1.1.1.1.apk", open("1.1.1.1/1.1.1.1.apk", "rb"))
    """
    if data and file:
        raise Exception("invalid parameters: #data and #file can NOT exist at the same time")
    
    proxies = None
    if proxy: proxies = {"http": "http://" + proxy, "https": "http://" + proxy}
    
    comm_params = [
        # common parameters
        ("gameid", gameid),
        ("ts", int(time.time())),
        ("nonce", random.randint(0, 0x7FFFFFFF)),
        ("accessid", accessid),
    ]
    
    if params:
        gcloud_params = comm_params + params
    else:
        gcloud_params = comm_params

    # sort parameters by key
    gcloud_params.sort(key=lambda x:x[0])
    
    # generate signature
    uri = CFG.URI_PREFIX + "/" + module + "/" + action
    req_url = "http://" + host + uri
    if debug: print "req_url=%s" % req_url
    sig = uri + "?" + list_to_param_str(gcloud_params, False)
    if debug: print "sig=%s" % sig
    sig = base64.b64encode(hmac.new(accesskey, sig, hashlib.sha1).digest())
    
    # replace "+" with "-", and "/" with "_"
    sig = sig.replace("+", "-")
    sig = sig.replace("/", "_")
    if debug: print "sig2=%s" % sig

    # add signature
    gcloud_params.append(("signature", sig))

    # send request
    try:
        if file:
            data = FormFile(file[1], formname="file", filename=file[0])
            headers = {"Content-Type": data.content_type}

        query_string = list_to_param_str(gcloud_params)
        if debug: print "query_string=%s" % query_string
        if data or action in CFG.SPECIAL_POST_API:
            rsp = requests.post(req_url, params=query_string, data=data, headers=headers, proxies=proxies, timeout=60)
        else:
            rsp = requests.post(req_url, data=query_string, proxies=proxies, timeout=60)
    except Exception, e:
        raise Exception("%s: req_url[%s]" % (e, req_url))
    
    if rsp.status_code < 200 or rsp.status_code >= 300:
        raise Exception("request failed: req_url[%s], status[%d], response[%s]" % (req_url, rsp.status_code, rsp.content))
        
    try:
        result = json.loads(rsp.content)
    except Exception, e:
        raise Exception("request failed: req_url[%s], status[%d], response[%s]" % (req_url, rsp.status_code, rsp.content))
    
    if result.get("code") < 0:
        raise GCloudError(result.get("code"), result.get("message"))
    
    return result

def list_to_param_str(lst, encode=True):
    param_str = ""
    first = True
    for key, value in lst:
        if first:
            first = False
        else:
            param_str += "&"
        
        if encode:
            param_str += key + "=" + urllib.quote_plus(str(value))
        else:
            param_str += key + "=" + str(value)

    return param_str


def main():
    from optparse import OptionParser
    import os
    import sys

    class MyParser(OptionParser):
        def format_description(self, formatter):
            if self.description:
                return self.description
            else:
                return ""

        def format_epilog(self, formatter):
            if self.epilog:
                return "\n" + self.epilog
            else:
                return ""


    example1 = "--host=127.0.0.1:2107 --debug --gameid=123 --module=dir --action=GetAllPlatform " + \
               "--accessid='7Ayv7z1PZa2RGzq9bZHhth3gdcoE' --accesskey='rv0gyosjnaHYJS5Q5ZHeouc8yM0E'"
    example2 = "--host=127.0.0.1:2107 --debug --gameid=123 --module=dir --action=NewPlatform " + \
               "--more='platformname=openapi_test&uin=francishe' " + \
               "--accessid='7Ayv7z1PZa2RGzq9bZHhth3gdcoE' --accesskey='rv0gyosjnaHYJS5Q5ZHeouc8yM0E'"
    example3 = "--host=127.0.0.1:2107 --debug --gameid=123 --module=update --action=NewWorldListRule " + \
               "--more='Uin=francishe&GrayRuleName=user_rule' " + \
               """--data='[{"id":1,"world":"world1"},{"id":2,"world":"world2"}]' """ + \
               "--accessid='7Ayv7z1PZa2RGzq9bZHhth3gdcoE' --accesskey='rv0gyosjnaHYJS5Q5ZHeouc8yM0E'"
    example4 = "--host=127.0.0.1:2107 --debug --gameid=123 --module=update --action=UpdateGrayRule " + \
               "--more='Uin=francishe&GrayRuleID=3&GrayRuleName=new_user_rule' " + \
               "--accessid='7Ayv7z1PZa2RGzq9bZHhth3gdcoE' --accesskey='rv0gyosjnaHYJS5Q5ZHeouc8yM0E'"
    example5 = "--host=127.0.0.1:2107 --debug --gameid=123 --module=file --action=UploadApp " + \
               "--more='productid=1&versionstr=1.0.0.0' --filepath=test.apk " + \
               "--accessid='7Ayv7z1PZa2RGzq9bZHhth3gdcoE' --accesskey='rv0gyosjnaHYJS5Q5ZHeouc8yM0E'"
    example6 = "--host=127.0.0.1:2107 --debug --gameid=123 --module=file --action=UploadApp " + \
               "--more='productid=1&versionstr=1.0.0.0&skipupload=1' " + \
               "--accessid='7Ayv7z1PZa2RGzq9bZHhth3gdcoE' --accesskey='rv0gyosjnaHYJS5Q5ZHeouc8yM0E'"
    example7 = "--host=127.0.0.1:2107 --debug --gameid=123 --module=file --action=UploadRes " + \
               "--more='productid=1&versionstr=1.0.0.0&downloadlink=someurl' " + \
               "--accessid='7Ayv7z1PZa2RGzq9bZHhth3gdcoE' --accesskey='rv0gyosjnaHYJS5Q5ZHeouc8yM0E'"

    examples = "Examples:\n" + \
               "  %s %s\n" % (sys.argv[0], example1) + \
               "  %s %s\n" % (sys.argv[0], example2) + \
               "  %s %s\n" % (sys.argv[0], example3) + \
               "  %s %s\n" % (sys.argv[0], example4) + \
               "  %s %s\n" % (sys.argv[0], example5) + \
               "  %s %s\n" % (sys.argv[0], example6) + \
               "  %s %s\n" % (sys.argv[0], example7)
    parser = MyParser(epilog=examples)

    parser.add_option(
        "--host",
        action="store",
        type="string",
        dest="host",
        help="host, e.g. 127.0.0.1:2107",
        metavar="HOST"
    )
    parser.add_option(
        "--gameid",
        action="store",
        type="string",
        dest="gameid",
        help="gameid, e.g. 123",
        metavar="GAMEID"
    )
    parser.add_option(
        "--accessid",
        action="store",
        type="string",
        dest="accessid",
        help="accessid, e.g. 7Ayv7z1PZa2RGzq9bZHhth3gdcoE",
        metavar="ACCESSID"
    )
    parser.add_option(
        "--accesskey",
        action="store",
        type="string",
        dest="accesskey",
        help="accesskey, e.g. rv0gyosjnaHYJS5Q5ZHeouc8yM0E",
        metavar="ACCESSKEY"
    )
    parser.add_option(
        "--module",
        action="store",
        type="string",
        dest="module",
        help="module, e.g. dir",
        metavar="MODULE"
    )
    parser.add_option(
        "--action",
        action="store",
        type="string",
        dest="action",
        help="action, e.g. Publish",
        metavar="ACTION"
    )
    parser.add_option(
        "--filepath",
        action="store",
        type="string",
        dest="filepath",
        default=None,
        help="path of the file to be uploaded",
        metavar="FILEPATH"
    )
    parser.add_option(
        "--more",
        action="store",
        type="string",
        dest="more",
        default=None,
        help="other parameters in the query string, e.g. key1=value1&key2=value2",
        metavar="PARAMS"
    )
    parser.add_option(
        "--data",
        action="store",
        type="string",
        dest="data",
        default=None,
        help="data to be sent in HTTP body",
        metavar="DATA"
    )
    parser.add_option(
        "--debug",
        action="store_true",
        dest="debug",
        default=False
    )
    parser.add_option(
        "--proxy",
        action="store",
        type="string",
        dest="proxy",
        default=None,
        help="proxy host, e.g. 127.0.0.1:8080",
        metavar="PROXY"
    )
    (options, args) = parser.parse_args()
    if not options.host:
        parser.error("option --host not supplied")
    if not options.gameid:
        parser.error("option --gameid not supplied")
    if not options.accessid:
        parser.error("option --accessid not supplied")
    if not options.accesskey:
        parser.error("option --accesskey not supplied")
    if not options.module:
        parser.error("option --module not supplied")
    if not options.action:
        parser.error("option --action not supplied")
    
    more = None
    if options.more:
        more_list = []
        more_dict = urlparse.parse_qs(options.more)
        for key, value in more_dict.iteritems():
            more_list.append((key, value[0]))
        if more_list: more = more_list

    if options.filepath:
        filename = os.path.basename(options.filepath)
        file = open(options.filepath, "rb")
        result = request_gcloud_api(options.host, options.gameid, options.accessid, options.accesskey,
            options.module, options.action, params=more, data=options.data,
            file=(filename, file), debug=options.debug, proxy=options.proxy)
    else:
        result = request_gcloud_api(options.host, options.gameid, options.accessid, options.accesskey,
            options.module, options.action, params=more, data=options.data, debug=options.debug, proxy=options.proxy)

    print result

if __name__ == "__main__":
    main()
