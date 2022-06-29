#encoding:utf-8
###########################################################
# @Author: dezhaoli@tencent.com
# @Date:   2020-08-19 11:54:47
# Please contact dezhaoli if you have any questions.


# Live GCloud OpenAPI Reference: https://iwiki.woa.com/pages/viewpage.action?pageId=151866342
###########################################################
import random
import time
import datetime
import json
import os

import gcloud_openapi


class GCAPI():
    
    @classmethod
    def Init(self, _uin, _gameid, _accessid, _accesskey, _host4common, _host4file, _regionid, _verbose=True, _verbose_openapi=False):
        global verbose_openapi, verbose
        verbose_openapi = _verbose_openapi
        verbose = _verbose

        global uin, gameid, accessid, accesskey, host4common, host4file, regionid
        uin = _uin
        gameid = _gameid
        accessid = _accessid
        accesskey = _accesskey
        host4common = _host4common
        host4file = _host4file
        regionid = _regionid
        if verbose_openapi : print("GCAPI.Init:", uin, gameid, accessid, accesskey, host4common, host4file, regionid, _verbose, _verbose_openapi)

    @classmethod
    def output(self, msg):
        if isinstance(msg, bool):
            print ("result::true" if msg == True else "result::false" )
        else:
            print "result::%s" % msg

    # 0 PrePublish, 2 Publish, default:0
    @classmethod
    def QueryVersion(self, productid,pub_type=0):
        params = [
            ("PubType", pub_type),
            ("ProductID", productid),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "QueryVersion",
            params=params, debug=verbose_openapi)
        return result

    @classmethod
    def CopyVersion(self, src_productid, src_app_ver, des_productid, des_app_ver, src_res_ver=None, des_res_ver=None, pub_type=0, diff_app_num=0):
        result = self.QueryVersion(src_productid, pub_type)

        src_app_item=None
        src_res_item=None
        for app_item in result["result"]:
            if app_item['VersionStr'] != src_app_ver: continue
            src_app_item = app_item
            break
        if not src_app_item:
            raise Exception("version not found: version[%s]" % (src_app_ver))
        if src_res_ver:
            for res_item in src_app_item['ResLine']:
                if res_item['VersionStr'] == src_res_ver:
                    src_res_item = res_item
            if not src_res_item:
                raise Exception("version not found: version[%s]" % (src_res_ver))

        if self.IsVersionExist(des_productid,"app",des_app_ver):
            print ("Skipping. App version already existed: version[%s]" % des_app_ver)
        else:
            # not supported creating diff version and creating from history at the same time
            if diff_app_num > 0:
                diff_versions = self.GetDiffVersions(des_productid,diff_app_num,diff_app_num)
                version_info = None
            else:
                diff_versions = None
                his = self.GetUploadHistory(src_productid, src_app_ver)
                if his == None:
                    raise Exception("version not found in channel: version[%s] channel[%s]" % (src_app_ver, src_productid))
                    pass
                version_info = his["VersionInfo"]
            
            self.NewApp(des_productid, des_app_ver, link=src_app_item['PackageUrl'],md5=src_app_item["VersionMd5"], customstr=src_app_item["VersionCustomStr"],versiondes=src_app_item["VersionDes"], diff_list=diff_versions ,version_info=version_info)

        if src_res_ver:
            if self.IsVersionExist(des_productid,"res",des_app_ver, des_res_ver):
                raise Exception("Res version already existed: version[%s]" % des_res_ver)
            his = self.GetUploadHistory(src_productid, src_res_ver)
            version_info = his["VersionInfo"]
            self.NewRes(des_productid, des_app_ver, des_res_ver, link=src_res_item['PackageUrl'],md5=src_res_item["VersionMd5"], customstr=src_res_item["VersionCustomStr"],versiondes=src_res_item["VersionDes"] ,version_info=version_info)


    #kind:[both|app|res]
    @classmethod
    def IsVersionExist(self, productid, kind, app_ver, res_ver=None, pub_type=0, is_print=False):
        is_app_exit = self.GetVersionInfo(productid, app_ver, pub_type)
        if res_ver:
            is_res_exit = self.GetVersionInfo(productid, res_ver, pub_type)
        if kind == "both":
            is_exit = is_app_exit and is_res_exit
        elif kind == "res":
            is_exit = is_res_exit
        else:
            is_exit = is_app_exit
        if is_print : self.output(is_exit)
        return is_exit
            

    @classmethod
    def GetVersionInfo(self, productid, versionstr, pub_type=0, is_print=False):
        result = self.QueryVersion(productid, pub_type)

        for app_item in result["result"]:
            if app_item['VersionStr'] == versionstr:
                if is_print : self.output(json.dumps(app_item)) 
                return True
            else:
                for res_item in app_item['ResLine']:
                    if res_item['VersionStr'] == versionstr:
                        if is_print : self.output(json.dumps(res_item)) 
                        return True
        return False

    @classmethod
    def UpdateVersion(self, productid, version, available_type=None, gray_rule_id=None, customstr=None, versiondes=None):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", version)
        ]
        if not available_type == None:
            params.append(("AvailableType", available_type))
            if available_type == 2 or available_type == 3:
                params.append(("GrayRuleID", gray_rule_id))
            
        if not customstr == None:

            params.append(("CustomStr", customstr))
        if not versiondes == None:
            params.append(("VersionDes", versiondes))
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "UpdateVersion",
            params=params, debug=verbose_openapi)
        return result

    @classmethod
    def CleanOldAppVersion(self, productid, remain_num_reserve=13, remain_num_available=37, pub_type=0):
        result = self.QueryVersion(productid, pub_type)

        available_list = result["result"]
        reserve_list = []
        for i in reversed(range(len(available_list))):
            app_item=available_list[i]
            if app_item['VersionDes'] == 'RESERVE':
                reserve_list.append(available_list[i])
                del available_list[i]
        while len(available_list) > remain_num_available:
            app_item = available_list[-1]
            print 'total (%d) available app versions. exceeded %d. del %s' % (len(available_list), remain_num_available, app_item['VersionStr'])
            del available_list[-1]
            self.DeleteVersion(productid, app_item['VersionStr'])
        while len(reserve_list) > remain_num_reserve:
            app_item = reserve_list[0]
            print 'total (%d) reserve app versions. exceeded %d. del %s' % (len(reserve_list), remain_num_reserve, app_item['VersionStr'])
            del reserve_list[0]
            self.DeleteVersion(productid, app_item['VersionStr'])

    @classmethod
    def GetNewestVersion(self, productid, formatstr=None, pub_type=0, is_print=False):
        result = self.QueryVersion(productid, pub_type)
        vvv=[]
        if formatstr:
            v=formatstr.split('.')[:3]
            for x in xrange(0,2):
                if "X" not in str(v[x]):
                    vvv.append(v[x])
            # print vvv
        for app_item in result["result"]:

            if len(app_item['ResLine'])> 0:
              versionstr = app_item['ResLine'][0]['VersionStr']
            else:
              versionstr = app_item['VersionStr']
            # print versionstr
            if len(vvv) > 0:
                vv=versionstr.split('.')[:len(vvv)]
                math = True
                for x in xrange(0,len(vvv)):
                    if vv[x] != vvv[x]:
                        math = False
                        break
                if math:
                    if is_print : self.output(versionstr)
                    return versionstr
            else:
                if is_print : self.output(versionstr)
                return versionstr


    @classmethod
    def GetVersionList(self, productid, pub_type=0):
        result = self.QueryVersion(productid, pub_type)

        for app_item in result["result"]:
          print app_item['VersionStr']
          for res_item in app_item['ResLine']:
            print "  %s" % res_item['VersionStr']

    @classmethod
    def DeleteVersion(self, productid, versionstr):
        params = [
            ("Uin", uin ),
            ("ProductID", productid),
            ("VersionStr", versionstr),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "DeleteVersion",
            params=params, debug=verbose_openapi)
        return result

    @classmethod
    def RestoreVersion(self, productid, versionstr, logid=None):
        params = [
            ("Uin", uin ),
            ("ProductID", productid),
            ("VersionStr", versionstr),
        ]
        if logid:
            params.append(("LogID", logid))
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "RestoreVersion",
            params=params, debug=verbose_openapi)
        return result

    @classmethod
    def GetLog(self, productid, versionstr=None, isverbose=False):
        params = [
            ("Uin", uin ),
            ("ProductIDList", productid),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetLog",
            params=params, debug=verbose_openapi)

        for item in result["result"]:
            if not versionstr:
                print item
            elif versionstr == item['versionname']:
                ttt = datetime.datetime.fromtimestamp(int(item['time'])).strftime('%Y-%m-%d %H:%M:%S')
                if isverbose:
                    item['time'] = ttt
                    print item 
                else:
                    print "%s: %s logid[%d], [%s] " % ( ttt, versionstr, item['logid'], item['action'] )

            
        return result

    @classmethod
    def GetDiffVersions(self, productid, pre_num=1, publish_num=2):
        diff_list = []
        result = self.QueryVersion(productid, 0)
        for item in result.get('result'):
            if len(diff_list) >= pre_num: break
            if item.get('VersionMd5') and int(item.get('PackageSize')) > 0:
                app_version = item.get('VersionStr')
                diff_list.append(app_version)
        result = self.QueryVersion(productid, 2)
        for item in result.get('result'):
            if len(diff_list) >= pre_num + publish_num: break
            if item.get('VersionMd5') and int(item.get('PackageSize')) > 0:
                app_version = item.get('VersionStr')
                if app_version not in diff_list:
                    diff_list.append(app_version)
        if len(diff_list) == 0: return None
        return diff_list
    @classmethod
    def NewUploadTask(self, productid, versionstr, versiontype, diff_list=None):
        # center/NewUploadTask
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", versionstr),
            ("VersionType", versiontype),
            ("RegionID", regionid),
        ]
        if diff_list and len(diff_list) > 0:
            params.append(('DiffVersions', '|'.join(diff_list)))

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "center", "NewUploadTask",
            params=params, debug=verbose_openapi)

        if verbose : print ("upload task created...")
        return result

    # filepath      本地待上传文件，与link互斥，UploadUpdateFile
    # link          文件下载链接,UploadUpdateFileWithLink
    # baseversion   若为增量资源，则需指定基线版本号
    @classmethod
    def UploadUpdateFile(self, uploadtaskid, taskinfo, filepath=None, link=None, md5=None, baseversion=None):
        # file/UploadUpdateFile
        params = [
            ('UploadTaskID', uploadtaskid),
            ("TaskInfo", taskinfo)
        ]
        if baseversion:
            params.append(("ResType", 2))
            params.append(("BaseVersion", baseversion))
        if link:
            params.append(("Link", link))
            result = gcloud_openapi.request_gcloud_api(host4file, gameid,
                accessid, accesskey, "file", "UploadUpdateFileWithLink",
                params=params, file=None, debug=verbose_openapi)
        elif filepath:
            filename = os.path.basename(filepath)
            file = open(filepath, "rb")
            result = gcloud_openapi.request_gcloud_api(host4file, gameid,
                accessid, accesskey, "file", "UploadUpdateFile",
                params=params, file=(filename, file), debug=verbose_openapi)
        else:
            result = gcloud_openapi.request_gcloud_api(host4file, gameid,
                accessid, accesskey, "file", "MakeEmptyUpdateFile",
                params=params, file=None, debug=verbose_openapi)
        if md5:
            params.append(("MD5", md5))

        if verbose : print ("upload task started...")
        return result

    @classmethod
    def GetUploadTaskStat(self, upload_task_id):
        # center/GetUploadTaskStat
        task_state = ""
        version_info = None
        while task_state != "succeeded":
            params = [
                ('UploadTaskID', upload_task_id)
            ]
            result = gcloud_openapi.request_gcloud_api(host4common, gameid,
                accessid, accesskey, "center", "GetUploadTaskStat",
                params=params, debug=verbose_openapi)
            task_state = result["result"]["State"]
            version_info = result["result"].get("VersionInfo", None)
            if verbose : print ("state=%s" % task_state)

            time.sleep(1)
        if verbose : print ("upload task finished")
        assert version_info,'error: Failed to get version info form GetUploadTaskStat with task id [%s].'%(upload_task_id)
        return version_info

    @classmethod
    def PrePublish(self, productid):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "PrePublish",
            params=params, debug=verbose_openapi)
        return result

    @classmethod
    def Publish(self, productid):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("Force", 1),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "Publish",
            params=params, debug=verbose_openapi)
        return result

    # available_type:   版本目标用户。可选值:0 - 不可用，1 - 普通用户可用，2 - 灰度用户可用，3 - 普通用户和灰度用户都可用，4 - 审核版本，缺省 1
    # gray_rule_id:     灰度规则 ID, 灰度用户可用时必须指定。
    # versiondes:       版本描述
    # customstr:        自定义字符串
    @classmethod
    def NewApp(self, productid, versionstr, filepath=None, link=None,md5=None, available_type=1, gray_rule_id=None, customstr=None, versiondes=None, diff_list=None, version_info=None):

        if not version_info:
            # center/NewUploadTask
            result = self.NewUploadTask(productid, versionstr, 0, diff_list=diff_list)

            TaskInfo = result["result"]["TaskInfo"]
            UploadTaskID = result["result"]["UploadTaskID"]

            # file/UploadUpdateFile
            self.UploadUpdateFile(UploadTaskID,TaskInfo,filepath=filepath,link=link,md5=md5)

            # center/GetUploadTaskStat
            version_info = self.GetUploadTaskStat(UploadTaskID)


        # update/NewApp
        params=[
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", versionstr),
            ("AvailableType", available_type),
            ("VersionInfo", version_info),
            ("FromHistory", 0) # regardless of the documemtation, always be 0
        ]
        if available_type == 2 or available_type == 3:
            params.append(("GrayRuleID", gray_rule_id))
        if diff_list and len(diff_list) > 0:
            params.append(('DiffVersions', '|'.join(diff_list)))

        if customstr :
            params.append(("CustomStr", customstr))
        if versiondes :
            params.append(("VersionDes", versiondes))
            
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewApp",
            params=params, debug=verbose_openapi)
        if verbose : print ("new app succeeded...")

        # pre-publish
        self.PrePublish(productid)
        # publish
        # self.Publish(productid)

        if verbose : print ("NewApp done!")

    
    @classmethod
    def NewRes(self, productid, appversionstr, versionstr, filepath=None,link=None,md5=None, available_type=1, gray_rule_id=None, baseversion=None, customstr=None, versiondes=None, version_info=None):
        

        if not version_info:
            # center/NewUploadTask
            result = self.NewUploadTask(productid, versionstr, 1)

            TaskInfo = result["result"]["TaskInfo"]
            UploadTaskID = result["result"]["UploadTaskID"]

            # file/UploadUpdateFile
            self.UploadUpdateFile(UploadTaskID,TaskInfo,filepath=filepath,link=link,md5=md5,baseversion=baseversion)

            # center/GetUploadTaskStat
            version_info = self.GetUploadTaskStat(UploadTaskID)


        # update/NewRes
        params=[
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", versionstr),
            ("AvailableType", available_type),
            ("VersionInfo", version_info),
            ("AppVersionStr", appversionstr),
            ("FromHistory", 0) # regardless of the documemtation, always be 0
        ]
        if available_type == 2 or available_type == 3:
            params.append(("GrayRuleID", gray_rule_id))
        if customstr :
            params.append(("CustomStr", customstr))
        if versiondes :
            params.append(("VersionDes", versiondes))

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewRes",
            params=params, debug=verbose_openapi)
        if verbose : print ("new res succeeded...")

        # pre-publish
        self.PrePublish(productid)
        # publish
        # self.Publish(productid)

        if verbose : print ("NewRes done!")

    def NewWorldListRule(self):
        params = [
            ("Uin", uin),
            ("GrayRuleName", "world_list_rule"),
        ]

        data = [
            {
                "id": 1,
                "world": "world1",
            },
            {
                "id": 2,
                "world": "world2",
            }
        ]
        data = json.dumps(data)
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewWorldListRule",
            params=params, data=data)
        return result["result"]["GrayRuleID"]

    def NewUserListRule(self):
        params = [
            ("Uin", uin),
            ("GrayRuleName", "user_list_rule"),
        ]

        data = [
            "user1",
            "user2",
            "user3",
        ]
        data = json.dumps(data)
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewUserListRule",
            params=params, data=data)
        return result["result"]["GrayRuleID"]

    @classmethod
    def NewProduct(self):
        # update/NewProduct
        params = [
            ("Uin", uin),
            ("ProductName", "test_Init"),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewProduct",
            params=params, debug=verbose_openapi)

        productid = result["result"]["ProductID"]
        return productid

    def get_md5(self, filesvr_path):
        params = [
            ("filepath", filesvr_path)
        ]
        result = gcloud_openapi.request_gcloud_api(host4file, gameid, 
            accessid, accesskey, "file", "Md5", 
            params=params, debug=verbose_openapi)

        return result["result"]["md5"]


    @classmethod
    def GetUploadHistory(self, productid, versionstr):
        version_type = 0 if versionstr.split('.')[3] == '0' else 1
        
        state_type=0
        page_size=100
        for page_num in xrange(1,20):
            params = [
                ("VersionType", version_type),
                ("PageNum", page_num),
                ("StateType", state_type),
                ("PageSize", page_size),
            ]
            result = gcloud_openapi.request_gcloud_api(host4common, gameid,
                accessid, accesskey, "center", "GetUploadHistoryList",
                params=params, debug=verbose_openapi)
            for item in result["result"]:
                if item['ProductID'] == productid and item['VersionStr'] == versionstr :
                    print json.dumps(item)
                    return item














