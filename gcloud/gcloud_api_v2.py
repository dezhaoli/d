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

    @classmethod
    def CopyVersion(self, src_productid, src_app_ver, des_productid, des_app_ver, src_res_ver=None, des_res_ver=None, pub_type=0, diff_app_num=0):
        result = self.GetAllVersion(src_productid, pub_type)

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
            # # not supported creating diff version and creating from history at the same time
            # if diff_app_num > 0:
            #     diff_versions = self.GetDiffVersions(des_productid,diff_app_num,diff_app_num)
            #     version_info = None
            # else:
            #     diff_versions = None
            #     his = self.GetUploadHistory(src_productid, src_app_ver)
            #     if his == None:
            #         raise Exception("version not found in channel: version[%s] channel[%s]" % (src_app_ver, src_productid))
            #         pass
            #     version_info = his["VersionInfo"]
            # self.NewApp(des_productid, des_app_ver, link=src_app_item['PackageUrl'],md5=src_app_item["VersionMd5"], customstr=src_app_item["VersionCustomStr"],versiondes=src_app_item["VersionDes"], diff_list=diff_versions ,version_info=version_info)

            self.NewApp(des_productid, des_app_ver, link=src_app_item['PackageUrl'], customstr=src_app_item['CustomStr'],versiondes=src_app_item['Description'],remark=src_app_item['Remark'])

        if src_res_ver:
            if self.IsVersionExist(des_productid,"res",des_app_ver, des_res_ver):
                raise Exception("Res version already existed: version[%s]" % des_res_ver)
            # his = self.GetUploadHistory(src_productid, src_res_ver)
            # version_info = his["VersionInfo"]

            # self.NewRes(des_productid, des_app_ver, des_res_ver, link=src_res_item['PackageUrl'],md5=src_res_item["VersionMd5"], customstr=src_res_item["VersionCustomStr"],versiondes=src_res_item["VersionDes"] ,version_info=version_info)

            self.NewRes(des_productid, des_app_ver, des_res_ver, link=src_res_item['PackageUrl'], customstr=src_res_item["CustomStr"],versiondes=src_res_item['Description'] ,remark=src_app_item['Remark'])


    #kind:[both|app|res]
    @classmethod
    def IsVersionExist(self, productid, kind, app_ver, res_ver=None, pub_type=0, is_print=False):
        is_app_exit = self.GetVersionInfo(productid, app_ver, pub_type, kind="app") != None
        if res_ver:
            is_res_exit = self.GetVersionInfo(productid, res_ver, pub_type, kind="res") != None
        if kind == "both":
            is_exit = is_app_exit and is_res_exit
        elif kind == "res":
            is_exit = is_res_exit
        else:
            is_exit = is_app_exit
        if is_print : self.output(is_exit)
        return is_exit
            


    @classmethod
    def UpdateVersion(self, productid, version, is_app=True, available_type=None, gray_rule_id=None, customstr=None, versiondes=None, remark=None):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", version)
        ]
        if not available_type == None:
            params.append(("AvailableType", available_type))
            if available_type == 2 or available_type == 3:
                params.append(("GrayRuleID", gray_rule_id))

        if is_app:
            apistr="UpdateApp"
        else:
            apistr="UpdateRes"
        if not customstr == None:
            params.append(("CustomStr", customstr))
        if not versiondes == None:
            params.append(("Description", versiondes))
        if not remark == None:
            params.append(("Remark", remark))
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", apistr,
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
            elif versionstr == item['versionstr']:
                ttt = datetime.datetime.fromtimestamp(int(item['time'])).strftime('%Y-%m-%d %H:%M:%S')
                if isverbose:
                    item['time'] = ttt
                    print item 
                else:
                    print "%s: %s logid[%d], [%s] " % ( ttt, versionstr, item['logid'], item['action'] )

            
        return result

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


######################## QTS 
    @classmethod
    def GetAllProduct(self):
        params = [
            ("PubType", 0),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetAllProduct",
            params=params, debug=verbose_openapi)
        return result


    @classmethod
    def NewUploadAppTask(self, productid, app_version, diff_list=None, category=0):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", app_version),
            ("Category", category),
        ]

        if diff_list and len(diff_list) > 0:
            params.append(('DiffFrom', '|'.join(diff_list)))

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewUploadAppTask",
            params=params, debug=verbose_openapi)
        if verbose : print ("upload task created...")
        print json.dumps(result)
        return result["result"]



    @classmethod
    def NewUploadResTask(self, productid, app_version, res_version, max_diff_num=None):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", res_version),
            ("AppVersionStr", app_version),
            # ("MaxDiff", max_diff_num),
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewUploadResTask",
            params=params, debug=verbose_openapi)
        if verbose : print ("upload task created...")
        print json.dumps(result)
        return result["result"]


    # category:         0 - 正版本式，1 - 灰度版本， 2 - 审版本核
    # gray_rule_id:     灰度规则 ID, 灰度用户可用时必须指定。
    # versiondes:       版本描述
    # customstr:        自定义字符串
    @classmethod
    def NewApp(self, productid, app_version, filepath=None, link=None, md5=None, category=0, gray_rule_id=None, customstr=None, versiondes=None, remark=None, diff_list=None, version_info=None):
        if not version_info:
            # center/NewUploadTask
            result = self.NewUploadAppTask(productid, app_version, diff_list=diff_list)

            TaskInfo = result["TaskInfo"]
            UploadTaskID = result["UploadTaskID"]

            # file/UploadUpdateFile
            self.UploadUpdateFile(UploadTaskID,TaskInfo,filepath=filepath,link=link,md5=md5)

            # center/GetUploadTaskStat
            version_info = self.GetUploadTaskStat(UploadTaskID)


        # update/NewApp
        params=[
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", app_version),
            ("VersionInfo", version_info),
            ("Category", category),
            ("UpgradeType", 1)
        ]
        if category == 1:
            params.append(("GrayRuleID", gray_rule_id))

        if diff_list and len(diff_list) > 0:
            params.append(('DiffFrom', '|'.join(diff_list)))

        if customstr :
            params.append(("CustomStr", customstr))
        if versiondes :
            params.append(("Description", versiondes))
        if remark :
            params.append(("Remark", remark))
            
        # params.append(("EnableP2P", 1))

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
    def NewRes(self, productid, app_version, res_version, filepath=None, link=None, md5=None, customstr=None, versiondes=None, remark=None, version_info=None):
        if not version_info:
            # center/NewUploadTask
            result = self.NewUploadResTask(productid, app_version, res_version, 1)

            TaskInfo = result["TaskInfo"]
            UploadTaskID = result["UploadTaskID"]

            # file/UploadUpdateFile
            self.UploadUpdateFile(UploadTaskID,TaskInfo,filepath=filepath,link=link,md5=md5)

            # center/GetUploadTaskStat
            version_info = self.GetUploadTaskStat(UploadTaskID)


        # update/NewRes
        params=[
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", res_version),
            ("AppVersionStr", app_version),
            ("VersionInfo", version_info)
        ]
        if customstr :
            params.append(("CustomStr", customstr))
        if versiondes :
            params.append(("Description", versiondes))
        if remark :
            params.append(("Remark", remark))

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewRes",
            params=params, debug=verbose_openapi)
        if verbose : print ("new res succeeded...")

        # pre-publish
        self.PrePublish(productid)
        # publish
        # self.Publish(productid)

        if verbose : print ("NewRes done!")



    @classmethod
    def ReuseRes(self, productid, app_version, res_version):
        # update/ReuseRes
        params=[
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", res_version),
            ("AppVersionStr", app_version)
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "ReuseRes",
            params=params, debug=verbose_openapi)
        if verbose : print ("reuse res succeeded...")

        if verbose : print ("ReuseRes done!")



    @classmethod
    def NewChannelPkg(self, productid, res_version, version_info, pkg_name):
        # update/NewChannelPkg
        params=[
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", res_version),
            ("VersionInfo", version_info),
            ("PkgName", pkg_name)
        ]


        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewChannelPkg",
            params=params, debug=verbose_openapi)
        if verbose : print ("reuse res succeeded...")

        if verbose : print ("NewChannelPkg done!")

    @classmethod
    def GetApp(self, productid, app_version):
        params = [
            ("ProductID", productid),
            ("VersionStr", app_version),
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetApp",
            params=params, debug=verbose_openapi)

        return result


    @classmethod
    def GetRes(self, productid, app_version, res_version):
        params = [
            ("ProductID", productid),
            ("VersionStr", res_version),
            ("AppVersionStr", app_version),
            ("PubType", 0)
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetRes",
            params=params, debug=verbose_openapi)

        return result
        


    @classmethod
    def GetResPkg(self, productid, res_version):
        params = [
            ("ProductID", productid),
            ("VersionStr", res_version)
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetResPkg",
            params=params, debug=verbose_openapi)

        return result
        

    # pub_type: 0 未发布 2 正式发布
    @classmethod
    def GetAllVersion(self, productid, pub_type):
        params = [
            ("ProductID", productid),
            ("PubType", 0)
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetAllVersion",
            params=params, debug=verbose_openapi)

        return result

    @classmethod
    def GetVersionList(self, productid, pub_type=0):
        result = self.GetAllVersion(productid, pub_type)

        for app_item in result["result"]:
          print app_item['VersionStr']
          if app_item.has_key( 'ResLine' ):
              for res_item in app_item['ResLine']:
                print "  %s" % res_item['VersionStr']
                if res_item['VersionStr'] == app_item['VersionStr']:
                    break
    @classmethod
    def GetLatestVersionInfo(self, productid, pub_type=0,kind="res"):
        result = self.GetAllVersion(productid, pub_type)

        for app_item in result["result"]:
          if app_item.has_key( 'ResLine' ):
              for res_item in app_item['ResLine']:
                self.PrintVersionInfo(productid, app_item['VersionStr'], res_item['VersionStr'], kind )
                return

    @classmethod
    def UpdateApp(self, productid, app_version, category=None, gray_rule_id=None, upgrade_type=None, customstr=None, versiondes=None, remark=None):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", app_version)
        ]

        if category :
            params.append(("Category", category))
        if category == 1:
            params.append(("GrayRuleID", gray_rule_id))

        if upgrade_type:
            params.append(("UpgradeType", upgrade_type))
        

        if customstr :
            params.append(("CustomStr", customstr))
        if versiondes :
            params.append(("Description", versiondes))
        if remark :
            params.append(("Remark", remark))


        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "UpdateApp",
            params=params, debug=verbose_openapi)

        return result

    @classmethod
    def UpdateRes(self, productid, res_version, customstr=None, versiondes=None, remark=None):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", res_version)
        ]


        if customstr :
            params.append(("CustomStr", customstr))
        if versiondes :
            params.append(("Description", versiondes))
        if remark :
            params.append(("Remark", remark))


        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "UpdateRes",
            params=params, debug=verbose_openapi)

        return result


    @classmethod
    def DeleteApp(self, productid, app_version, customstr=None, versiondes=None, remark=None):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", app_version)
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "DeleteApp",
            params=params, debug=verbose_openapi)

        return result


    @classmethod
    def DeleteRes(self, productid, res_version, customstr=None, versiondes=None, remark=None):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", res_version)
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "DeleteRes",
            params=params, debug=verbose_openapi)

        return result

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


    @classmethod
    def GetUploadTaskStat(self, upload_task_id):
        # center/GetUploadTaskStat
        task_state = ""
        version_info = None
        while task_state != "succeeded" and task_state != "failed":
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


    # filepath      本地待上传文件，与link互斥，UploadUpdateFile
    # link          文件下载链接,UploadUpdateFileWithLink
    @classmethod
    def UploadUpdateFile(self, uploadtaskid, taskinfo, filepath=None, link=None, md5=None):
        # file/UploadUpdateFile
        params = [
            ('UploadTaskID', uploadtaskid),
            ("TaskInfo", taskinfo)
        ]
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

    ##kind:[both|app|res]
    @classmethod
    def GetVersionInfo(self, productid, versionstr, pub_type=0, kind="both", is_print=False):

        try:
            if kind== "app" or kind== "both":
                result = self.GetApp(productid, versionstr)
                if is_print : self.output(json.dumps(result))
            if kind != "app" :
                app_version = '.'.join(versionstr.split('.')[0:3]) + '.0';
                result = self.GetRes(productid, app_version, versionstr)
                if is_print : self.output(json.dumps(result))

        except gcloud_openapi.GCloudError, e:
            if e._message == 'version does not exist':
                if is_print : self.output(e._message)
                return None

        
        return result

    ##kind:[both|app|res]
    @classmethod
    def PrintVersionInfo(self, productid, app_version, res_version, kind="both"):

        try:
            if kind== "app" or kind== "both":
                result = self.GetApp(productid, app_version)
                self.output(json.dumps(result))
            if kind != "app" :
                result = self.GetRes(productid, app_version, res_version)
                self.output(json.dumps(result))

        except gcloud_openapi.GCloudError, e:
            if e._message == 'version does not exist':
                self.output(e._message)
                return None

        
        return result
        


    @classmethod
    def GetDiffVersions(self, productid, pre_num=1, publish_num=2):
        diff_list = []
        result = self.GetAllVersion(productid, 0)
        for item in result.get('result'):
            if len(diff_list) >= pre_num: break
            if item.get('PackageMd5') and int(item.get('PackageSize')) > 0:
                app_version = item.get('VersionStr')
                diff_list.append(app_version)
        result = self.GetAllVersion(productid, 2)
        for item in result.get('result'):
            if len(diff_list) >= pre_num + publish_num: break
            if item.get('PackageMd5') and int(item.get('PackageSize')) > 0:
                app_version = item.get('VersionStr')
                if app_version not in diff_list:
                    diff_list.append(app_version)
        if len(diff_list) == 0: return None
        return diff_list

    @classmethod
    def GetNewestVersion(self, productid, formatstr=None, is_print=False):
        result = self.GetAllVersion(productid, 0)
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
    def DeleteVersion(self, productid, versionstr):
        if self.GetVersionInfo(productid, versionstr, kind="res"):
            result = self.DeleteRes(productid, versionstr)

        app_version = '.'.join(versionstr.split('.')[0:3]) + '.0';
        app_item = self.GetVersionInfo(productid, versionstr, kind="app")
        if app_item and not app_item.has_key( 'ResLine' ):
            result = self.DeleteApp(productid, versionstr)
        return result
        
    @classmethod
    def DeleteBatch(self, productid, min_res_version, max_res_version):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("MiniVersionStr", min_res_version),
            ("MaxVersionStr", max_res_version)
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "DeleteBatch",
            params=params, debug=verbose_openapi)

        return result
        

    @classmethod
    def CleanOldAppVersion(self, productid, remain_num_available=60, pub_type=0):
        result = self.GetAllVersion(productid, pub_type)

        app_list = result["result"]
        result=None
        res_to_del_list = []
        if len(app_list)>0:
            for app_item in app_list:
                if app_item.has_key( 'ResLine' ) and self.GetVersionInfo(productid,app_item['VersionStr'],pub_type,'res'):
                    res_list=app_item['ResLine']
                    while len(res_list) > remain_num_available:
                        res_item = res_list[-1]
                        print 'total (%d) available res versions. exceeded %d. pedding del %s' % (len(res_list), remain_num_available, res_item['VersionStr'])
                        del res_list[-1]
                        res_to_del_list.append(res_item['VersionStr'])
                    break
                else:
                    # we should delete the app_item whose resline are empty
                    result = self.DeleteApp(productid, app_item['VersionStr'])
        if len(res_to_del_list) > 1:
            result = self.DeleteBatch(productid, res_to_del_list[0], res_to_del_list[-1])
        elif len(res_to_del_list) == 1:
            result = self.DeleteVersion(productid,res_to_del_list[0])
        if result and result[u'code'] == 0:
            self.PrePublish(productid)






