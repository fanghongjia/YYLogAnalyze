# -*- coding: utf-8 -*- 
import xlrd
import urllib,urllib2,gzip,zipfile
import sys,os,os.path
import re
import search
import shutil
import socket


reload(sys)
sys.setdefaultencoding('utf-8')

class AppURLopener(urllib.FancyURLopener):


    version = "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT)";

def open_excel(file= 'list.xlsx'):
	#try:
	data = xlrd.open_workbook(file)
	return data
	#except Exception,e:
		#print('读取xlsx文件异常:',str(e))
	
def parse(data):
	sheetnames = data.sheet_names()
	total_table = []

	for sheetname in sheetnames:
		type = sheettype(sheetname)
		if type != -1:
			index = sheetnames.index(sheetname)
			if type == 1:
				mobile_os = 'ios'
			elif type == 2:
				mobile_os = 'android'

			table = get_table_by_index(data, mobile_os, index)
			total_table.extend(table)

	search.handle_file(total_table)
	
# def parseTableWithRange(data, range):
# 	sheetnames = data.sheet_names()
# 	for sheetname in sheet_names:
# 		index = sheetnames.index(sheetname)
# 		if indexInRange(index, range):
# 			type = sheettype(sheetname)
# 			if type != -1:
# 				index = sheetnames.index(sheetname)
# 				if type == 1:
# 					mobile_os = 'ios'
#
# 				elif type == 2:
# 					mobile_os = 'android'
#
# 				table = get_table_by_index(data, mobile_os, index)
# 				search.handle_file(table, type, sheetname)

def	indexInRange(index, range):
	if index >= range[0] and index < range[0]+range[1]:
		return 1
	else:
		return 0

def sheettype(sheetname):
	searchresult = re.search(r'ios', sheetname, re.M | re.I)
	if searchresult:
		return 1
	else:
		searchresult = re.search(r'android', sheetname, re.M | re.I)
		if searchresult:
			return 2
	return -1

def compare_ios_ver(ver1,ver2):
	#5.4.0 5.3.1
	verArr1 = ver1.split('.')
	verArr2 = ver2.split('.')
	if (int(verArr1[0]) < int(verArr2[0])):
		return 0
	elif (int(verArr1[0]) > int(verArr2[0])):
		return 1
	else:
		#
		if (int(verArr1[1]) < int(verArr2[1])):
			return 0
		elif (int(verArr1[1]) > int(verArr2[1])):
			return 1
		else:
			if (int(verArr1[2]) < int(verArr2[2])):
				return 0
			elif (int(verArr1[2]) > int(verArr2[2])):
				return 1
			else:
				return 1


def get_table_by_index(data,mobile_os,index):
	table_list = []
		
	table = data.sheet_by_index(index)
	nrows = table.nrows

	for row in range(1,nrows):
		
		feedback = table.cell(row,4).value

		if (feedback.find("银联") > 0) or (feedback.find(u"支付宝")>0 or feedback.find("个人账户")>0):

			cell_list = []

			logurl = table.cell(row,6).value
			
			#如果没有日志地址，则不记录这条日志			
			if not logurl == '' and logurl.find('http://') >= 0:

				for col in xrange(1,7):

					value = table.cell(row,col).value
					# 时间转换
					if col == 5:
						t = xlrd.xldate.xldate_as_datetime(value, 0)
						t = t.strftime("%Y-%m-%d %H:%M:%S")
						cell_list.append(t)
					else:
						cell_list.append(table.cell(row,col).value)
				
				#加入日志文件路径	
				ios_ver = table.cell(row,3).value
				logPath = download_logfile(logurl, mobile_os,ios_ver)#'Android'
				cell_list.append(logPath)

				if mobile_os == 'ios':
					cell_list.append(1)
				elif mobile_os == 'android':
					cell_list.append(2)

				table_list.append(cell_list)

	return table_list

# 下载日志
def download_logfile(url, mobile_os='ios',ios_ver='3.3.0'):

	print('down file:'+url+',version:'+ios_ver)

	strArr = url.split('/')
	
	big_than_key_ver = compare_ios_ver(ios_ver,'5.3.1')

	gz_filename = ''
	if (mobile_os == 'ios'):
		if (big_than_key_ver == 1):
			#5.4.0以后，ios的日志压缩文件是zip，同android一样
			gz_filename = mobile_os+"_logs"+"/"+strArr[-1]+".zip"
		else:
			gz_filename = mobile_os+"_logs"+"/"+strArr[-1]+".gz"
	else:
		gz_filename = mobile_os+"_logs"+"/"+strArr[-1]+".zip"

	unziptodir = mobile_os+"_logs"+"/"+strArr[-1]

	if not os.path.exists(unziptodir):
		print('dir:'+unziptodir+',zipfile:'+gz_filename)
		#创建解压目录
		os.makedirs(unziptodir, 0777)
	else:
		shutil.rmtree(unziptodir)

	urllib._urlopener = AppURLopener()

	if (mobile_os == 'ios'):

		if (big_than_key_ver == 1):
			#5.4.0以后，ios的日志是多个文件形式，同android一样
			if not os.path.exists(gz_filename):
				try:
					print('down zip')
					urllib.urlretrieve(url, gz_filename)
				except urllib.ContentTooShortError:
					urllib.urlretrieve(url, gz_filename)
			else:
				print('zip did download')

			#解压到指定文件夹下
			unzip(gz_filename, unziptodir)

			log_file_name = unziptodir
		else:
			log_file_name = unziptodir+'/'+strArr[-1]+'.txt'
			if not os.path.exists(gz_filename):
				try:
					print('down gz')
					urllib.urlretrieve(url, gz_filename)
				except urllib.ContentTooShortError:
					urllib.urlretrieve(url, gz_filename)
			else:
				print('gz did download')

			if not os.path.exists(log_file_name):
				untar(gz_filename,log_file_name)
			else:
				print('gz did untar')
	else:
		# log_file_name = unziptodir+'/log_description'+'.txt'

		if not os.path.exists(gz_filename):
			try:
				urllib.urlretrieve(url, gz_filename)
			except urllib.ContentTooShortError:
				urllib.urlretrieve(url, gz_filename)
		else:
			print('zip did download')

		if not os.path.exists(unziptodir):
			unzip(gz_filename,unziptodir)
		else:
			print('zip did unzip')

		log_file_name = unziptodir

	print('log_path',log_file_name)
	return log_file_name

# 解压日志包
def untar(gz_fname,unziptodir):
	print('untar', gz_fname)
	try:
		g = gzip.GzipFile(mode="rb", fileobj=open(gz_fname, 'rb'))
		open(unziptodir, "wb").write(g.read())
	except Exception, e:
		print('gz 解压失败', e)

def unzip(zip_fname, unziptodir):
    print('unzip', zip_fname)
    try:
    	zfobj = zipfile.ZipFile(zip_fname)
    	for name in zfobj.namelist():
	        name = name.replace('\\','/')

	        if name.endswith('/'):
	            os.mkdir(os.path.join(unziptodir, name))
	        else:            
	            ext_filename = os.path.join(unziptodir, name)
	            ext_dir= os.path.dirname(ext_filename)
	            if not os.path.exists(ext_dir) : os.mkdir(ext_dir,0777)
	            outfile = open(ext_filename, 'wb')
	            outfile.write(zfobj.read(name))
	            outfile.close()
    except Exception,e:
    	print('zip 解压失败',e)

	    

# 主函数	
def main():

	# socket.setdefaulttimeout(120.0)
	
	data = open_excel("data.xlsx")
	
	#parse函数会解析所有的sheet
	parse(data)
	
	#parseTableWithRange函数只会解析给定Range内sheet
	# tableRange = [12,6]
	# parseTableWithRange(data,tableRange)
	

if __name__ == "__main__":
	main()
