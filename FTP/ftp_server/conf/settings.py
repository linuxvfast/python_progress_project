__author__ = 'progress'
import os,sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_HOME = '%s/%s'%(os.path.dirname(BASE_DIR),'ftp_client')
USER_DIR = '%s/%s'%(BASE_DIR,'db')    #数据目录
USER_HOME = '%s/%s'%(BASE_DIR,'home')  #用户家目录存放目录
LOG_DIR = '%s/%s'%(BASE_DIR,'log')     #日志存放目录
ACCOUNT_FILE = '%s/%s/%s'%(BASE_DIR,'conf','accounts.cfg') #ftp用户信息
LOG_LEVEL = 'DEBUG'     #日志级别
HOST = '0.0.0.0'        #所有的ip地址
PORT = 9999             #端口