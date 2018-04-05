import socket,os,json
import sys,time

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file_dir = '%s/%s'%(base_dir,'ftp_server')
sys.path.append(file_dir)
print(base_dir)
from conf import settings
import optparse
import getpass
import hashlib

STATUS_CODE = {
    250:"invalid cmd format e.g:{'action':'get','filename':'test.py','size':400}",
    251:"invalid cmd ",
    252:"invalid auth data ",
    253:"Invalid user name and password",
    254:"passed authentication",
    255: "filename not provided",
    256: "file not exist",
    257: "you can send a file...",
    258:"md5 verification",
}

class Ftpclient(object):
    def __init__(self):
        '''智能读取参数'''
        self.parse = optparse.OptionParser()
        self.parse.add_option('-s','--host',dest='host',help='Binding the address of the server')
        self.parse.add_option('-P','--port',type='int',dest='port',help='Binding server port')
        self.parse.add_option('-u','--username',dest='username',help='user name')
        self.parse.add_option('-p','--password',dest='password',help='user pasword')
        self.parse.add_option('-m','--md5',dest='file_md5',help='Validation file md5 value')
        (self.options, self.args) = self.parse.parse_args()
        # print(self.option.host,self.option.port)
        self.verify_args(self.options, self.args)
        self.make_connect()

    def verify_args(self,options, args):
        '''校验参数合法性'''
        if options.username is not None and options.password is not None:
            pass
        elif options.username is None and options.password is None:
            pass
        else:
            exit('\033[31m The user name and password must be appearing together or not\033[0m')

        if options.host and options.port:
            if options.port > 0 and options.port < 65535:
                return True
            else:
                exit('\033[31m 端口无效，范围为0-65535')

    def make_connect(self):
        '''连接服务器'''
        self.client = socket.socket()
        self.client.connect((self.options.host,self.options.port))

    def help(self):
        #命令帮助
        msg = '''
        ----------命令操作如下----------
        ls             查看当前目录下的文件和目录
        pwd            查看当前路径
        cd   dir       切换目录
        get  filename  下载文件
        put  filename  上传文件
        '''
        print(msg)

    def show_progress(self,total):
        '''显示进度条'''
        recv_size = 0  #接收到数据大小
        current_percent = 0  #当前的百分比
        while recv_size < total:
            if int((recv_size / total)*100) > current_percent:
                print('#',end='',flush=True)
                current_percent = int((recv_size / total)*100)
            new_size = yield
            recv_size += new_size

    def cmd_md5_required(self,cmd_list):
        '''检测命令是否需要md5值验证'''
        if '--md5' in cmd_list:
            return True

    def cmd_put(self,cmd_list):
        '''上传文件'''
        if len(cmd_list) == 1:
            print('Did not provide a file name...')
            return
        put_dic = {
            'action': 'put',
            'filename': cmd_list[1],
        }
        if self.cmd_md5_required(cmd_list):  # 如果客户端get命令中包含--md5为get_dic添加md5值
            put_dic['md5'] = True

        # 拼接上传文件路径
        if '/' not in cmd_list[1]:
            file_abs_path = '%s/%s' % (settings.CLIENT_HOME, cmd_list[1])
            put_dic['file_size'] = os.path.getsize(file_abs_path)
        else:
            file_abs_path = cmd_list[1]
            put_dic['file_size'] = os.path.getsize(file_abs_path)
        print('put file path:', file_abs_path)

        self.client.send(json.dumps(put_dic).encode())
        response = self.get_repsone()
        print('put response', response)

        # 发送文件
        if response['status_code'] == 257:
            if os.path.isfile(file_abs_path):
                file_obj = open(file_abs_path,'rb')
                if self.cmd_md5_required(cmd_list):
                    m = hashlib.md5()
                    for line in file_obj:
                        self.client.send(line)  # 发送文件内容
                        m.update(line)

                    print('\033[33msend file done...\033[0m')
                    file_obj.close()
                    file_md5 = m.hexdigest()
                    self.send_response(258, data={'md5': file_md5})
                else:
                    for line in file_obj:
                        self.client.send(line)
                    print('\033[33msend file done...\033[0m')
                    file_obj.close()
            else:
                print('\033[31m file not exist...\033[0m')
        else:
            print('\033[31mServer disk space is insufficient\033[0m')

    def cmd_get(self,cmd_list):
        #下载文件
        if len(cmd_list) == 1:
            print('no filename follows...')
            return
        get_dic = {
            'action':'get',
            'filename':cmd_list[1],
        }
        if self.cmd_md5_required(cmd_list):  #如果客户端get命令中包含--md5为get_dic添加md5值
            get_dic['md5'] = True

        self.client.send(json.dumps(get_dic).encode())
        response = self.get_repsone()
        print('response',response)
        if response['status_code'] == 257: #准备接收数据
            self.client.send('已经可以接收文件...'.encode())
            base_filename = cmd_list[1].split('/')[-1]  #去除下载时的传入的路径,获取文件名
            file_total_size = response['file_size']
            recv_size = 0
            file_obj = open(base_filename, 'wb')

            if self.cmd_md5_required(cmd_list): #判断是否使用md5加密传输
                m = hashlib.md5()
                progress = self.show_progress(file_total_size) #generator生成器
                progress.__next__()
                #接收文件
                while recv_size < file_total_size:
                    if file_total_size - recv_size > 1024:
                        size = 1024
                    else:
                        size = file_total_size - recv_size
                    data = self.client.recv(size)
                    recv_size += len(data)
                    m.update(data)
                    file_obj.write(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print('100%')
                else:
                    print('---file download success---')
                    file_obj.close()
                    #验证MD5值是否一致
                    file_md5 = self.get_repsone()  # 接收的md5
                    print('接收到的md5:', file_md5)
                    new_md5 = m.hexdigest()  # 客户端的文件md5值
                    print('本机md5:', new_md5)
                    if file_md5['status_code'] == 258:
                        if file_md5['md5'] == new_md5:
                            print('%s 文件一致性校验成功'%base_filename)

            else:
                progress = self.show_progress(file_total_size)  # generator生成器
                progress.__next__()

                # 接收文件
                while recv_size < file_total_size:
                    if file_total_size - recv_size > 1024:
                        size = 1024
                    else:
                        size = file_total_size - recv_size
                    data = self.client.recv(size)
                    recv_size += len(data)
                    file_obj.write(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print('100%')
                else:
                    print('---file download success---')
                    file_obj.close()

    def cmd_pwd(self,cmd_list):
        '''显示当前所在的目录'''
        data = cmd_list
        print(data)
        pwd_dic = {
            'action':'pwd',
        }
        self.client.send(json.dumps(pwd_dic).encode())
        print('当前所在目录:', self.get_repsone())

    def cmd_ls(self,cmd_list):
        '''列出当前目录下的文件和目录'''
        # data = cmd_list
        # print(data)
        ls_dic = {
            'action': 'ls',
        }
        self.client.send(json.dumps(ls_dic).encode())

        res = self.get_repsone() #接收服务器返回的当前所在的目录

        print('当前目录下的文件和目录'.center(30, '-'))
        ret = os.listdir(res)  #列出目录下的文件和目录
        # print('ret:',ret)
        for i in ret:
            if os.path.isfile('%s/%s'%(res,i)):
                print('%s 文件' % i)
            else:
                print('%s 目录' % i)

    def cmd_cd(self,cmd_list):
        '''切换目录'''
        if len(cmd_list) ==1:
            print('no dir follows...')
            return
        cd_dic ={
            'action':'cd',
            'switch_dir':cmd_list[1],
        }
        self.client.send(json.dumps(cd_dic).encode())
        current_dir = self.get_repsone()
        print('需要切换的目录:', cmd_list[1])
        if cmd_list[1] == '..':
            new_dir = os.path.dirname(current_dir)
            print(new_dir)
            if len(new_dir) <len(current_dir):
                print('没有权限切换到该目录[%s]'%new_dir)
                return
            current_dir = new_dir
            print('已经切换到 [%s]' % new_dir)
        else:
            new_dir = '%s/%s' % (current_dir,cmd_list[1])
            print(new_dir)
            if len(new_dir) <len(current_dir):
                print('没有权限切换到该目录[%s]'%new_dir)
                return
            current_dir = new_dir
            print('已经切换到 [%s]' % new_dir)
        return current_dir

    def get_repsone(self):
        '''接受服务器的返回结果'''
        data = self.client.recv(1024)
        data = json.loads(data.decode())
        # print('get_repsone', data)
        return data

    def send_response(self,status_code,data=None):
        '''向服务器返回数据'''
        response = {'status_code':status_code,'status_msg':STATUS_CODE[status_code]}
        if data:
            response.update(data)
        self.client.send(json.dumps(response).encode())

    def get_auth_result(self,username,password):
        '''验证用户密码'''
        data = {
            'action':'auth',
            'username':username,
            'password':password,
        }
        self.client.send(json.dumps(data).encode())
        response = self.get_repsone()
        if response.get('status_code') == 254:
            print('passed authentication...')
            self.user = username
            return True
        else:
            print('get_auth_result:',response.get('status_msg'))

    def authenticate(self):
        '''用户验证'''
        if self.options.username:
            print(self.options.username,self.options.password)
            return self.get_auth_result(self.options.username,self.options.password)
        else:
            retry_count = 0
            while retry_count < 3:
                username = input('username>>').strip()
                # password = input('password>>').strip()
                password = getpass.getpass('password>>').strip()
                return self.get_auth_result(username,password)

    def interactive(self):
        #交互
        if self.authenticate():
            print('---Begin to interact---')
            while True:
                choice = input('[%s]:'%self.user).strip()   #显示当前的登录用户
                if len(choice) == 0:continue
                if choice == 'exit':break
                cmd_list = choice.split()
                if hasattr(self,'cmd_%s'%cmd_list[0]):
                    func = getattr(self,'cmd_%s'%cmd_list[0])
                    func(cmd_list)
                else:
                    print('invalid cmd...')



if __name__ == '__main__':
    obj = Ftpclient()
    obj.interactive()
