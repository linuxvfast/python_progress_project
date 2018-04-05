import socketserver
import json
import os
import configparser
from conf import settings
import hashlib

STATUS_CODE = {
    250:"invalid cmd format e.g:{'action':'get','filename':'test.py','size':400}",
    251:"invalid cmd ",
    252:"invalid auth data ",
    253:"Invalid user name and password",
    254:"passed authentication",
    255:"filename not provided",
    256:"file not exist",
    257:"you can send a file...",
    258:"md5 verification",
    259:"Server disk space is insufficient",
}
class Mytcpclass(socketserver.BaseRequestHandler):
    def cmd_put(self,*args,**kwargs):
        '''上传文件'''
        data = args[0]
        print('put from server', data)
        if data.get('filename') is None:  # 没有提供文件名
            self.send_response(255)

        # 拼接文件存储路径
        user_home_dir = '%s/%s' % (settings.USER_HOME, self.user['username'])
        file_abs_path = '%s/%s' % (user_home_dir, data.get('filename'))
        print('file abs path', file_abs_path)

        # print('接收的文件大小为:',data.get('file_size'))
        file_total_size = data.get('file_size')
        print('文件总大小:',file_total_size)
        recv_size = 0

        #检查磁盘大小
        config = configparser.ConfigParser()
        config.read(settings.ACCOUNT_FILE)
        username = self.user['username']
        disk_size = int(config[username]['quotation'])
        print('磁盘大小:',disk_size)
        if disk_size < file_total_size:
            self.send_response(259)
        else:
            self.send_response(257)
            file_obj = open(file_abs_path, 'wb')
            if data.get('md5'):
                m = hashlib.md5()
                progress = self.show_progress(file_total_size)  # generator生成器
                progress.__next__()
                while recv_size < file_total_size:
                    if file_total_size - recv_size > 1024:
                        size = 1024
                    else:
                        size = file_total_size - recv_size
                    data = self.request.recv(size)
                    recv_size += len(data)
                    m.update(data)
                    file_obj.write(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print('100%')
                else:
                    print('\033[33m---file upload success---\033[0m')
                    file_obj.close()

                    # 验证MD5值是否一致
                    file_md5 = self.get_repsone() # 接收的md5
                    print('接收到的md5:', file_md5)
                    new_md5 = m.hexdigest()  # 客户端的文件md5值
                    print('本机md5:', new_md5)
                    if file_md5['status_code'] == 258:
                        if file_md5['md5'] == new_md5:
                            print('%s 文件一致性校验成功' % file_abs_path)
            else:
                # 就收文件
                progress = self.show_progress(file_total_size)  # generator生成器
                progress.__next__()
                while recv_size < file_total_size:
                    if file_total_size - recv_size > 1024:
                        size = 1024
                    else:
                        size = file_total_size - recv_size
                    data = self.request.recv(size)
                    recv_size += len(data)
                    print('recv data size:',recv_size)
                    file_obj.write(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print('100%')
                else:
                    print('\033[33m---file upload success---\033[0m')
                    file_obj.close()

        #修改磁盘大小
        remaining_disk = disk_size - file_total_size
        config.set(username,'quotation',remaining_disk )
        config.write(open(settings.ACCOUNT_FILE, 'w'))

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

    def cmd_get(self,*args,**kwargs):
        '''下载文件'''
        data = args[0]
        print('cmd_get from server',data)
        if data.get('filename') is None:  #没有提供文件名
            self.send_response(255)

        #拼接文件下载路径,防止下载其它目录下的文件
        user_home_dir = '%s/%s'%(settings.USER_HOME,self.user['username'])
        file_abs_path = '%s/%s'%(user_home_dir,data.get('filename'))
        print('file abs path',file_abs_path)

        #判断文件是否存在
        if os.path.isfile(file_abs_path):
            # print('you can send a file...')
            file_obj = open(file_abs_path,'rb')
            file_size = os.path.getsize(file_abs_path)
            print('文件大小',file_size)
            self.send_response(257,data={'file_size':file_size})
            res = self.request.recv(1024) #防止粘包
            print(res.decode())

            #发送文件
            if data.get('md5'):
                m = hashlib.md5()
                for line in file_obj:
                    self.request.send(line)  #发送文件内容
                    m.update(line)

                print('send file done...')
                file_obj.close()
                file_md5 = m.hexdigest()
                self.send_response(258,data={'md5':file_md5})
            else:
                for line in file_obj:
                    self.request.send(line)
                print('\033[33msend file done...\033[0m')
                file_obj.close()
        else:
            self.send_response(256)

    def cmd_cd(self,*args,**kwargs):
        '''切换目录'''
        current_dir = '%s/%s' % (settings.USER_HOME, self.user['username'])
        print(current_dir)
        self.request.send(json.dumps(current_dir).encode())

    def cmd_ls(self,*args,**kwargs):
        '''列出当前目录下的文件和目录'''
        current_dir = '%s/%s' % (settings.USER_HOME, self.user['username'])
        print(current_dir)
        self.request.send(json.dumps(current_dir).encode())

    def cmd_pwd(self,*args,**kwargs):
        '''显示当前的目录'''
        current_dir = '%s/%s'%(settings.USER_HOME,self.user['username'])
        print(current_dir)
        self.request.send(json.dumps(current_dir).encode())

    def get_repsone(self):
        '''接受客户端的返回结果'''
        data = self.request.recv(1024)
        data = json.loads(data.decode())
        return data

    def authenticate(self,username,password):
        '''验证用户合法性'''
        config = configparser.ConfigParser()
        config.read(settings.ACCOUNT_FILE)
        if username in config.sections():  #检查用户名是否在配置文件中
            _password = config[username]['password']  #临时保存密码
            if _password == password:
                print('pass auth...',username)

                # config[username]只包含用户名下面的信息，不包含用户名，需要添加用户名信息
                config[username]['username'] = username
                return config[username]

    def send_response(self,status_code,data=None):
        '''向客户端返回数据'''
        response = {'status_code':status_code,'status_msg':STATUS_CODE[status_code]}
        if data:
            response.update(data)
        self.request.send(json.dumps(response).encode())

    def cmd_auth(self,*args,**kwargs):
        '''检查接收参数合法性'''
        data = args[0]
        print('cmd_auth',data)
        if data.get('username') is None or data.get('password') is None:
            self.send_response(252)
        ret = self.authenticate(data.get('username'),data.get('password'))
        if ret is None:
            self.send_response(253)
        else:
            print('passed authentication',ret)
            self.user = ret   #保留用户信息
            self.send_response(254)

    def handle(self):
        '''与客户端交互'''
        while True:
            print('等待客户端响应...')
            self.data = self.request.recv(1024).strip()
            print('{} wrote:'.format(self.client_address[0]))
            # print('handle', self.data)
            if not self.data:
                print('客户端已经断开...')
                break

            data = json.loads(self.data.decode())
            if data.get('action') is not None:
                if hasattr(self,'cmd_%s'%data.get('action')):
                    func = getattr(self,'cmd_%s'%data.get('action'))
                    func(data)
                else:
                    print('\033[31m invalid cmd \033[0m')
                    self.send_response(251)
            else:
                print('\033[31m invalid cmd format\033[0m')
                self.send_response(250)


if __name__ == '__main__':
    HOST,PORT = 'localhost',9999