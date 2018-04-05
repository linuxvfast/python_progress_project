import optparse    #智能读取参数
import socketserver
from core.ftp_server import Mytcpclass
from conf import settings

class run(object):
    def __init__(self):
        '''智能获取参数'''
        self.parse = optparse.OptionParser()
        self.parse.add_option('-s','--start',dest='start ftp',help='start ftp server')
        (self.options,self.args) = self.parse.parse_args()
        self.verify_args(self.options,self.args)

    def verify_args(self,options,args):
        '''校验args并调用相应的功能'''
        if hasattr(self,args[0]):
            func = getattr(self,args[0])
            func()
        else:
            self.parse.print_help()


    def start(self):
        '''启动ftp服务'''
        print('---Start the FTP service---')
        server = socketserver.ThreadingTCPServer((settings.HOST, settings.PORT), Mytcpclass)  #多用户连接
        server.serve_forever()
