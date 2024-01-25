#!/usr/bin/python2
# -*- coding: utf-8 -*-
###########################################################
# @Author: dezhaoli@tencent.com
# @Date:   
# Please contact dezhaoli if you have any questions.
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

    # TODO: 这个方法应该过期了
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
            # self.NewApp(des_productid, des_app_ver, file_link=src_app_item['PackageUrl'],md5=src_app_item["VersionMd5"], customstr=src_app_item["VersionCustomStr"],versiondes=src_app_item["VersionDes"], diff_list=diff_versions ,version_info=version_info)

            self.NewApp(des_productid, des_app_ver, file_link=src_app_item['PackageUrl'], customstr=src_app_item['CustomStr'],versiondes=src_app_item['Description'],remark=src_app_item['Remark'])

        if src_res_ver:
            if self.IsVersionExist(des_productid,"res",des_app_ver, des_res_ver):
                raise Exception("Res version already existed: version[%s]" % des_res_ver)
            # his = self.GetUploadHistory(src_productid, src_res_ver)
            # version_info = his["VersionInfo"]

            # self.NewRes(des_productid, des_app_ver, des_res_ver, file_link=src_res_item['PackageUrl'],md5=src_res_item["VersionMd5"], customstr=src_res_item["VersionCustomStr"],versiondes=src_res_item["VersionDes"] ,version_info=version_info)

            self.NewRes(des_productid, des_app_ver, des_res_ver, file_link=src_res_item['PackageUrl'], customstr=src_res_item["CustomStr"],versiondes=src_res_item['Description'] ,remark=src_app_item['Remark'])


    #kind:[both|app|res]
    @classmethod
    def IsVersionExist(self, productid, kind, app_ver, res_ver=None, pub_type=0, is_print=False):
        is_app_exit = self.GetApp(productid, app_ver) != None
        if res_ver:
            is_res_exit = self.GetRes(productid, app_version, res_ver) != None
        if kind == "both":
            is_exit = is_app_exit and is_res_exit
        elif kind == "res":
            is_exit = is_res_exit
        else:
            is_exit = is_app_exit
        if is_print : self.output(is_exit)
        return is_exit
            
    ##kind:[both|app|res]
    @classmethod
    def GetVersionInfo(self, productid, versionstr, pub_type=0, kind="both", is_print=False):

        try:
            if kind== "app" or kind== "both":
                result = self.GetApp(productid, versionstr)
                if is_print : self.output(json.dumps(result))
            if kind != "app" :
                # app_version = '.'.join(versionstr.split('.')[0:3]) + '.0';
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

        if pre_num > 0:
            result = self.GetAllVersion(productid, 0)
            for item in result.get('result'):
                if len(diff_list) >= pre_num: break
                if item.get('PackageMd5') and int(item.get('PackageSize')) > 0:
                    app_version = item.get('VersionStr')
                    diff_list.append(app_version)
        if publish_num > 0:
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
    def DeleteVersion(self, productid, app_version, res_version=None):
        if res_version!=None:
            result = self.DeleteRes(productid, res_version)
        else:
            result = self.DeleteApp(productid, app_version)
            return result
        

    # TODO: 这个方法应该过期了
    # @classmethod
    # def DeleteBatch(self, productid, min_res_version, max_res_version):
        # params = [
        #     ("Uin", uin),
        #     ("ProductID", productid),
        #     ("MiniVersionStr", min_res_version),
        #     ("MaxVersionStr", max_res_version)
        # ]

        # result = gcloud_openapi.request_gcloud_api(host4common, gameid,
        #     accessid, accesskey, "update", "DeleteBatch",
        #     params=params, debug=verbose_openapi)

        # return result
        
    # TODO: 这个方法应该过期了
    @classmethod
    def CleanOldAppVersion(self, productid, remain_num_available=60, pub_type=0):
        result = self.GetAllVersion(productid, pub_type)


    @classmethod
    def GetVersionList(self, productid, pub_type=0, is_puffer=False):
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



#######################################################################################################################################
########################  QTS  ########################################################################################################
#######################################################################################################################################

    # is_noapp 是否需要上传 App 包，可选值 0/1, 缺省为 0. 用于 iOS 或 Google Play Store 等渠道，因为这 些渠道不支持游戏内更新 App
    # is_disabledowngrade 是否禁止版本回退，可选值 0/1, 缺省为 0. 由 于版本回退可能产生难以预测的问题，通过指定 该选项，当高版本检查更新要回退到低版本是， version_server 返回特殊标识禁止回退升级。
    @classmethod
    def NewProduct(self, productname, customcfg, is_noapp=0, is_disabledowngrade=0):
        params = [
            ("Uin", uin),
            ("ProductName", productname),
            ("CustomCfg", customcfg),
            ("NoAppPkg", is_noapp),
            ("DisableDowngrade", is_disabledowngrade),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewProduct",
            params=params, debug=verbose_openapi)
        self.output(json.dumps(result))
        return result


    @classmethod
    def GetProduct(self, productid, pub_type=0):
        params = [
            ("ProductID", productid),
            ("PubType", pub_type),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetProduct",
            params=params, debug=verbose_openapi)
        self.output(json.dumps(result))
        return result


    @classmethod
    def GetAllProduct(self, pub_type=0):
        params = [
            ("PubType", pub_type),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetAllProduct",
            params=params, debug=verbose_openapi)
        self.output(json.dumps(result))
        return result

    @classmethod
    def UpdateProduct(self, productid, productname):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("ProductName", productname),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "UpdateProduct",
            params=params, debug=verbose_openapi)
        self.output(json.dumps(result))
        return result

    @classmethod
    def DeleteProduct(self, productid):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "DeleteProduct",
            params=params, debug=verbose_openapi)
        self.output(json.dumps(result))
        return result


    @classmethod
    def WipeProduct(self, productid):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "WipeProduct",
            params=params, debug=verbose_openapi)
        self.output(json.dumps(result))
        return result

    @classmethod
    def CloneProduct(self, src_productid, des_productid):
        params = [
            ("Uin", uin),
            ("SrcProductID", src_productid),
            ("DestProductID", des_productid),
        ]
        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "CloneProduct",
            params=params, debug=verbose_openapi)
        self.output(json.dumps(result))
        return result


    @classmethod
    def NewUploadAppAttachmentTask(self, productid, app_version, diff_list=None, category=0):
        params = [
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", app_version),
            ("Category", category),
        ]

        # if diff_list and len(diff_list) > 0:
        #     params.append(('DiffFrom', '|'.join(diff_list)))

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewUploadAppAttachmentTask",
            params=params, debug=verbose_openapi)
        if verbose : print ("upload app attachment task created...")
        print json.dumps(result)
        return result["result"]

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
        if verbose : print ("upload app task created...")
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
        if verbose : print ("upload res task created...")
        print json.dumps(result)
        return result["result"]


    # category:         0 - 正版本式，1 - 灰度版本， 2 - 审版本核
    # gray_rule_id:     灰度规则 ID, 灰度用户可用时必须指定。
    # versiondes:       版本描述
    # customstr:        自定义字符串
    @classmethod
    def NewApp(self, productid, app_version, file_path=None, file_link=None, md5=None, category=0, gray_rule_id=None, customstr=None, versiondes=None, remark=None, diff_list=None, version_info=None):
        if not version_info:
            # center/NewUploadTask
            result = self.NewUploadAppTask(productid, app_version, diff_list=diff_list)

            TaskInfo = result["TaskInfo"]
            UploadTaskID = result["UploadTaskID"]

            # file/UploadUpdateFile
            self.UploadUpdateFile(UploadTaskID,TaskInfo,file_path=file_path,file_link=file_link,md5=md5)

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

    # maybe not need: gray_rule_id=None, customstr=None, versiondes=None, remark=None, diff_list=None
    @classmethod
    def NewAppAttachment(self, productid, app_version, file_path=None, file_link=None, md5=None, category=0, gray_rule_id=None, customstr=None, versiondes=None, remark=None, diff_list=None, version_info=None):
        if not version_info:
            # update/NewUploadAppAttachmentTask
            result = self.NewUploadAppAttachmentTask(productid, app_version)

            TaskInfo = result["TaskInfo"]
            UploadTaskID = result["UploadTaskID"]

            # file/UploadUpdateFile
            self.UploadUpdateFile(UploadTaskID,TaskInfo,file_path=file_path,file_link=file_link,md5=md5)

            # center/GetUploadTaskStat
            version_info = self.GetUploadTaskStat(UploadTaskID)



        # update/NewUploadAppAttachmentTask
        params=[
            ("Uin", uin),
            ("ProductID", productid),
            ("VersionStr", app_version),
            ("VersionInfo", version_info),
            ("Category", category),
            ("UpgradeType", 2),
            ("EnableP2P", 1),
        ]
        # if category == 1:
        #     params.append(("GrayRuleID", gray_rule_id))

        # if diff_list and len(diff_list) > 0:
        #     params.append(('DiffFrom', '|'.join(diff_list)))

        # if customstr :
        #     params.append(("CustomStr", customstr))
        # if versiondes :
        #     params.append(("Description", versiondes))
        # if remark :
        #     params.append(("Remark", remark))
            
        # params.append(("EnableP2P", 1))

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "NewAppAttachment",
            params=params, debug=verbose_openapi)
        if verbose : print ("new app attachment succeeded...")

        # pre-publish
        self.PrePublish(productid)
        # publish
        # self.Publish(productid)

        if verbose : print ("NewAppAttachment done!")


    
    @classmethod
    def NewRes(self, productid, app_version, res_version, file_path=None, file_link=None, md5=None, customstr=None, versiondes=None, remark=None, version_info=None):
        if not version_info:
            # center/NewUploadTask
            result = self.NewUploadResTask(productid, app_version, res_version, 1)

            TaskInfo = result["TaskInfo"]
            UploadTaskID = result["UploadTaskID"]

            # file/UploadUpdateFile
            self.UploadUpdateFile(UploadTaskID,TaskInfo,file_path=file_path,file_link=file_link,md5=md5)

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
    def GetRes(self, productid, app_version, res_version, pub_type=0):
        params = [
            ("ProductID", productid),
            ("VersionStr", res_version),
            ("AppVersionStr", app_version),
            ("PubType", pub_type)
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
        self.output(json.dumps(result))

        return result
        

    # pub_type: 0 未发布 2 正式发布
    @classmethod
    def GetAllVersion(self, productid, pub_type=0):
        params = [
            ("ProductID", productid),
            ("PubType", pub_type)
        ]

        result = gcloud_openapi.request_gcloud_api(host4common, gameid,
            accessid, accesskey, "update", "GetAllVersion",
            params=params, debug=verbose_openapi)

        return result

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
    def PrePublish(self, productid, is_puffer=False):
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
        print( "version_info: [" + version_info + "]")
        return version_info


    # file_path      本地待上传文件，与file_link互斥，UploadUpdateFile
    # file_link          文件下载链接,UploadUpdateFileWithLink
    @classmethod
    def UploadUpdateFile(self, uploadtaskid, taskinfo, file_path=None, file_link=None, md5=None):
        # file/UploadUpdateFile
        params = [
            ('UploadTaskID', uploadtaskid),
            ("TaskInfo", taskinfo)
        ]
        if file_link:
            params.append(("Link", file_link))
            result = gcloud_openapi.request_gcloud_api(host4file, gameid,
                accessid, accesskey, "file", "UploadUpdateFileWithLink",
                params=params, file=None, debug=verbose_openapi)
        elif file_path:
            filename = os.path.basename(file_path)
            file = open(file_path, "rb")
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









#######################################################################################################################################
#######################################################################################################################################
#######################################################################################################################################






