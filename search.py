#coding=utf-8

__author__ = 'liusilan'

import os
import re

import xlwt


# 读取文件
def read_file(os_type, filepath):

    if os.path.isfile(filepath):
        print('is file:'+filepath)
        #该路径为文件路径
        fp = open(filepath)
        try:
            content = fp.read()
        finally:
            fp.close()
        return content
    else:
        print('is dir:'+filepath)
        #该路径为目录路径
        #fo 大文件，当前目录下的所有Log文件集合
        fo = open(filepath+'/all.txt', 'w+')
        for root, dirs, files in os.walk(filepath):

            print root,dirs,files

            for log in files:
                print('file :'+log)
                #如果是.log后缀则将文本拼接起来
                didfind = log.find('.log')
                if didfind != -1 :
                    logfilepath = filepath+'/'+log
                    #打开这个日志文件，写入到大文件离去
                    print('will open file:'+logfilepath)
                    fi = open(logfilepath)
                    lines = fi.readlines()
                    fo.write(lines)
                    fi.close()
        try:
            content = fo.read()
        finally:
            fo.close()

        return content


# 是否是appstore
def is_appstore(content):
    result = re.search(r'appstore', content, re.M | re.I)
    if result:
        print "is_appstore"
        return True
    else:
        print "jail"
        return False

#进入支付中心页面
def search_enter_recharge_center(os_type, content):
    if os_type == 1:
        searchresult =  re.search(r'begin query products', content, re.M | re.I)
        if searchresult:
            print('进入支付中心')
            return True
        else:
            print('未进入支付中心')
            return False
    else:
        return  True

#获取充值列表失败
def search_products_failed(os_type, content):
    if os_type == 1:
        searchresult = re.search(r'Search productList fail',content, re.M | re.I)
        if searchresult:
            print('拉取充值列表失败')
            return  True
        else:
            print('拉取充值列表成功')
            return False
    else:
        return False

#点击支付按钮失败
def search_click_pay_failed(os_type, content):
    if os_type == 1:
        print('点击按钮成功')
        return False
    else:
        return False

#发起支付请求失败
def search_pay_req_failed(os_type, content):

    if os_type == 1:
        pay_req_result = re.search(r'verifyReceiptAtServer with url', content, re.M | re.I)
        pay_rsp_result = re.search(r'parserVerifyResult isSignValid:', content, re.M | re.I)
        pay_rsp_fail_result = re.search(r'after verifyReceiptAtServer failed, current retry verify purchase', content, re.M | re.I)

        if pay_req_result:

            if pay_rsp_fail_result :
                #如果有after verifyReceiptAtServer failed, current retry verify purchase关键字,则意味请求返回http级别的错误，请求失败
                print('发起支付请求失败')
                return True
            elif pay_rsp_result:
                print('发起支付请求成功')
                return False

        else:
            print('发起支付请求失败')
            return True
    else:
        return False

# 支付网关处理失败
def search_pay_rsp_failed(os_type, content):

    if os_type == 1:
        success_result = re.search(r'pay successfully', content, re.M | re.I)
        pending_result = re.search(r'after parserVerifyResult, current processing orders',content, re.M | re.I)

        if not success_result and not pending_result:
            print('支付网关处理失败')

            failed_result = re.search(r'(\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*parserVerifyResult isSignValid:([\S\s]*?)\d{4}-\d{2}-\d{2}',content, re.M | re.I)
            if failed_result:
                # 请求参数
                match = failed_result.group(2)

                result = (True,match)
                return  result
            return (True,'')
        else:
            print('支付网关处理成功')
            return  (False,'')
    elif os_type == 2:
        #android
        rsp_result = re.search(r'(onRecharge payType[\s\S]*?)(\d{4}-\d{2}-\d{2})', content, re.M | re.I)
        if rsp_result:
            rsp_str =  rsp_result.group(1)
            code_result = re.search(r'code: ([\S\s]*?)orderId',rsp_str,re.M | re.I)
            if code_result:
                result = code_result.group(1)
                list = result.split(',')
                code = list[0]
                if code == '-1':
                    print('支付网关处理失败')
                    return  (True,rsp_str)
                else:
                    print('支付网关处理成功')
                    return (False, '')

        else:
            return (False,'')

# excel表头
def add_header(sheet):
    col_list = ["反馈量", "进入支付页面", "拉取充值列表失败", "点击支付按钮失败", "发起支付请求失败",
            "支付网关处理失败"]
    coloumn = 1
    for value in col_list:
        sheet.write(0, coloumn, value)
        coloumn += 1

    row_list = ["Android","iOS(AppStore)","iOS(越狱)"]
    row = 1
    for value in row_list:
        sheet.write(row,0,value)
        row += 1

def del_file(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)

def handle_file(loglist_info):

    workbook = xlwt.Workbook(encoding='utf-8')

    sheetLog = workbook.add_sheet("统计结果")
    pay_rsp_failed_sheet = workbook.add_sheet("iOS网关处理失败")
    android_pay_rsp_failed_sheet = workbook.add_sheet("android网关处理失败")

    result_dir = 'result'

    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    filename ='result/result.xls'
    del_file(filename)

    #添加头部
    add_header(sheetLog)

    #反馈总量
    android_total = 0
    appStore_total = 0
    jail_total = 0

    #进入支付页面
    android_enter_total = 0
    appStore_enter_total = 0
    jail_enter_total = 0

    #获取充值列表失败
    android_products_failed_total = 0
    appStore_products_failed_total = 0
    jail_products_failed_total = 0

    #点击支付按钮失败
    android_pay_click_failed_total = 0
    appStore_pay_click_failed_total = 0
    jail_pay_click_failed_total = 0

    #发起支付请求失败
    android_pay_req_failed_total = 0
    appStore_pay_req_failed_total = 0
    jail_pay_req_failed_total = 0

    #网关返回失败
    android_pay_rsp_failed_total = 0
    appStore_pay_rsp_failed_total = 0
    jail_pay_rsp_failed_total = 0

    appStore_pay_rsp_failed_row = 0
    android_pay_rsp_failed_row = 0

    #遍历解析log
    for log_info in loglist_info:

        print('日志信息',log_info)

        if len(log_info) == 0:
            continue

        #系统
        type = log_info[-1]
        # if type == 2:
        #     print('1111')
        # else:
        #     continue

        #日志路径
        filepath = log_info[-2]
        if os.path.exists(filepath):

            #判断该路径是否为目录路径，ios 手y5.4版本之后，解压出来的是个目录，里面有多个文件 
            if not os.path.isfile(filepath):

                for root, dirs, files in os.walk(filepath):
                    #只处理根目录下的logs文件，其他的子目录是SDK的log
                    if  not root == filepath:
                        continue

                    loglist = []
                    for log in files:
                        #如果是.log后缀则将文本拼接起来
                        if type == 1:
                            didfind = log.find('.log')
                        elif type == 2:
                            didfind = 1#log.find('logs_')
                    
                        if didfind != -1 :
                            logstr = read_file(type, filepath+'/'+log)
                            loglist.append(logstr)
                    content = '\n'.join(loglist)

            else:
                content = read_file(type, filepath)

            # 反馈总量
            if type == 1:
                appstore_flag = is_appstore(content)
                if appstore_flag:
                    appStore_total += 1
                else:
                    jail_total += 1
            else:
                android_total += 1

            #进入支付中心
            has_enter = search_enter_recharge_center(type, content)
            if has_enter:
                if type == 1:
                    if appstore_flag:
                        appStore_enter_total += 1
                    else:
                        jail_enter_total += 1
                else:
                    #android
                    android_enter_total += 0
            else:
                continue
            #获取充值列表失败
            products_failed = search_products_failed(type, content)
            if products_failed:
                if type == 1:
                    if appstore_flag:
                        appStore_products_failed_total += 1
                    else:
                        jail_products_failed_total += 1
                else:
                    android_products_failed_total += 0

                continue

            #点击支付按钮失败
            click_pay_failed = search_click_pay_failed(type,content)
            if click_pay_failed:
                if type == 1:
                    if appstore_flag:
                        appStore_pay_click_failed_total += 1
                    else:
                        jail_pay_click_failed_total += 1
                else:
                    android_pay_click_failed_total +=0

                continue

            #发起支付请求失败
            pay_req_failed = search_pay_req_failed(type, content)
            if pay_req_failed:
                if type == 1:
                    if appstore_flag:
                        appStore_pay_req_failed_total += 1
                    else:
                        jail_pay_req_failed_total += 1
                else:
                    android_pay_req_failed_total += 0

                continue

            # 网关返回失败
            pay_rsp_failed_tuple = search_pay_rsp_failed(type, content)

            pay_rsp_failed = pay_rsp_failed_tuple[0]

            if pay_rsp_failed:

                if type == 1:
                    if appstore_flag:
                        appStore_pay_rsp_failed_total += 1
                        if not pay_rsp_failed_tuple[1] == '':
                            pay_rsp_failed_sheet.write(appStore_pay_rsp_failed_row, 0,pay_rsp_failed_tuple[1] )
                            appStore_pay_rsp_failed_row += 1
                    else:
                        jail_pay_rsp_failed_total += 1
                else:
                    if not pay_rsp_failed_tuple[1] == '':
                        android_pay_rsp_failed_sheet.write(android_pay_rsp_failed_row,0,pay_rsp_failed_tuple[1] )
                        android_pay_rsp_failed_row += 1
                    android_pay_rsp_failed_total += 1


    # 反馈总量
    sheetLog.write(1, 1, android_total)
    sheetLog.write(2, 1, appStore_total)
    sheetLog.write(3, 1, jail_total)

    # 进入支付中心
    sheetLog.write(1, 2, android_enter_total)
    sheetLog.write(2, 2, appStore_enter_total)
    sheetLog.write(3, 2, jail_enter_total)

    # 获取充值列表失败
    sheetLog.write(1, 3, android_products_failed_total)
    sheetLog.write(2, 3, appStore_products_failed_total)
    sheetLog.write(3, 3, jail_products_failed_total)

    # 点击支付按钮失败
    sheetLog.write(1, 4, android_pay_click_failed_total)
    sheetLog.write(2, 4, appStore_pay_click_failed_total)
    sheetLog.write(3, 4, jail_pay_click_failed_total)

    # 发起支付请求失败
    sheetLog.write(1, 5, android_pay_req_failed_total)
    sheetLog.write(2, 5, appStore_pay_req_failed_total)
    sheetLog.write(3, 5, jail_pay_req_failed_total)

    # 网关返回失败
    sheetLog.write(1, 6, android_pay_rsp_failed_total)
    sheetLog.write(2, 6, appStore_pay_rsp_failed_total)
    sheetLog.write(3, 6, jail_pay_rsp_failed_total)

    print("save ", filename)
    workbook.save(filename)






