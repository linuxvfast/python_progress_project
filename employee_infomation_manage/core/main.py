__author__ = 'progress'
import os
from conf import settings

def sql_parse(sql):
    '''
    sql解析,分发到对应的语法解析服务
    :param sql: 用户输入的字符串
    :return: 返回字典格式sql解析结果
    '''
    parse_func = {
        'select':select_parse,
        'insert':insert_parse,
        'update':update_parse,
        'delete':delete_parse,
    }

    sql_l = sql.split(' ')
    func = sql_l[0]
    res = ''
    if func in parse_func:
        res = parse_func[func](sql_l)
    return res

def select_parse(sql_l):
    '''
    select 解析分支,定义select语法
    :param sql_l: sql按照空格分割的列表
    :return: 返回字典格式的sql解析结果
    '''
    sql_dic = {
        'select': [],  # 查询字段
        'from': [],  # 表
        'where': [],  # filter条件
        'limit': [],  # limit条件
    }
    return handle_parse(sql_l,sql_dic)

def handle_parse(sql_l,sql_dic):
    '''
    填充sql_dic字典
    :param sql_l:sql按照空格分割的列表
    :param sql_dic: 待填充的空字典
    :return: 返回字典格式的sql解析结果
    '''
    # print('sql_l is %s'%sql_l)
    #select * from db.info where id <=2 or name like 李
    tags = False
    for line in sql_l:
        if tags and line in sql_dic:
            tags = False
        if not tags and line in sql_dic:
            tags = True
            key = line
            continue
        if tags:
            sql_dic[key].append(line)
    # print('\033[41;1mhandler_parse in %s\033[0m'%sql_dic)
    if sql_dic.get('where'):
        sql_dic['where'] = where_parse(sql_dic.get('where'))
    return sql_dic

def where_parse(where_l):
    '''
    对用户输入的where子句后的条件格式化,每个子条件都改成列表形式
    :param where_l: 用户输入where后对应的过滤条件列表
    :return: where后子条件组成的列表
    '''
    # print('\033[41;1mhandler_parse in %s\033[0m' % where_l)
    res = []
    key = ['and', 'or', 'not']
    char = ''
    for line in where_l:
        if len(line) == 0:
            continue
        if line in key:
            if len(char) != 0:
                char = three_parse(char) #将每一个小的过滤条件如,id>=1转换成['id','>=','1']
                res.append(char)
            res.append(line)
            char = ''
        else:
            char += line
    else:
        char=three_parse(char)
        res.append(char)
    # print('res is %s'%res)
    return res

def three_parse(child_where):
    '''
    将每一个小的过滤条件如,id>=1转换成['id','>=','1']
    :param child_where: where条件中的子条件如['id' ,'>=1']
    :return: 子条件['id','>=1']转换为列表形式['id','>=','1']
    '''
    # print('\033[41;1mhandler_parse in %s\033[0m' %child_where)
    key=['>','=','<']
    res=[]
    char=''
    opt=''
    tags = False
    for line in child_where:
        if line in key:
            tags = True
            if len(char) != 0:
                res.append(char)
                char = ''
            opt += line
        if not tags:
            char += line
        if tags and line not in key:
            tags = False
            res.append(opt)
            opt = ''
            char += line
    else:
        res.append(char)
    # 新增like功能
    if len(res) == 1:  # ['namelike李']
        res = res[0].split('like')
        res.insert(1, 'like')
    # print('res is %s'%res)
    return res

def insert_parse(sql_l):
    '''
    定义insert语句的语法结构,执行sql解析操作,返回sql_dict
    :return:
    '''
    # print('from insert_parse in %s'%sql_l)
    sql_dic = {
        # 'func': select_action,
        'insert': [],  # 用户输入命令的查询字段
        'into': [],  # 需要查询的库,表
        'values': [],  # 查询条件
    }
    return handle_parse(sql_l,sql_dic)

def update_parse(sql_l):
    '''
    定义insert语句的语法结构,执行sql解析操作,返回sql_dict
    :param sql_l: 以空格分割的where条件列表
    :return: 格式化的条件字典
    '''
    # print('sql_l in the update_parse \033[41;1m%s\033[0m' % sql_l)
    sql_dic = {
        'update':[],
        'set':[],
        'where':[],
    }

    return handle_parse(sql_l, sql_dic)

def delete_parse(sql_l):
    '''
    从字典sql_dict中提取命令,分发给具体的命令执行函数去执行
    :param sql_dict:
    :return:
    '''
    # print('from delete_parse in %s'%sql_l)
    sql_dic = {
        # 'func': select_action,
        'delete': [],  # 用户输入命令的查询字段
        'from': [],  # 需要查询的库,表
        'where': [],  # 查询条件
    }
    # print('sql_dic in the delete_parse \033[41;1m%s\033[0m'%sql_dic)
    return handle_parse(sql_l, sql_dic)

def sql_action(sql_dic):
    '''
    从字典sql_dic中提取命令,分发给具体的命令执行函数去执行
    :param sql_dic:
    :return:
    '''
    # print('sql_dic is %s'%sql_dic)
    action_func = {
        'select':select_action,
        'insert':insert_action,
        'update':update_action,
        'delete':delete_action,
    }
    res = []
    for i in sql_dic:
        if i in action_func:
            res = action_func[i](sql_dic)
    # return sql_dic.get('func')(sql_dic)
    return res

def select_action(sql_dic):
    '''
    执行select命令查询
    :param sql_dict:自定义的字典形式命令
    :return:
    '''
    # first:from
    db,table = sql_dic.get('from')[0].split('.')
    fh = open('%s/%s/%s'%(settings.base_dir,db,table),'r',encoding='utf-8')

    # second:where
    filter_res = where_action(fh, sql_dic.get('where'))
    # for line in filter_res:
    #     print('filter_res is %s'%line)
    # third:limit
    limit_res = limit_action(filter_res, sql_dic.get('limit'))
    # for line in limit_res:
    #     print('limit_res is %s'%limit_res)
    # last:select
    search_res,row_num = search_action(limit_res, sql_dic.get('select'))
    # return search_res
    print('\033[32m---查询结果如下---\033[0m'.center(50,'-'))
    for line in row_num:
        print(' '.join(line).strip())
    print('\033[31m查询成功,查询结果为%s行满足条件\033[0m'%len(row_num))

def where_action(fh,where_l):
    '''
    判断where是否有条件，根据条件返回对应的结果
    :param fh:打开的文件
    :param where_l:where条件
    :return:
    '''
    res = []
    # print('from in where_action \033[41;1m %s \033[0m',where_l)
    logic_l = ['and','or','not']
    title = "id,name,age,phone,dept,enroll_data"
    if len(where_l) != 0:
        for line in fh:
            dic = dict(zip(title.split(','),line.split(',')))
            # print('dic is %s'%dic)
            #逻辑判断
            logic_res = logic_action(dic,where_l)
            if logic_res:
                res.append(line.split(','))
    else:
        res = fh.readlines()
    # print('from in where_action %s'%res)
    return res

def logic_action(dic,where_l):
    '''
    对where条件进行逻辑判断
    :param dic:文件中的标题和内容压缩成的字典
    :param where_l:where条件
    :return:返回bool值的结果
    '''
    res = []
    for exp in where_l:
        if type(exp) is list:
            exp_k, opt, exp_v = exp
            if exp[1] == '=':
                opt = '=='
            logical_char = "'%s'%s'%s'" % (dic[exp_k], opt, exp_v)
            if opt != 'like':
                exp = str(eval(logical_char))
            else:
                if exp_v in dic[exp_k]:
                    exp = 'True'
                else:
                    exp = 'False'
        res.append(exp)
    res = eval(' '.join(res))
    return res

def limit_action(filter_res,limit_l):
    res = []
    if len(limit_l) != 0:
        index = int(limit_l[0])
        res = filter_res[0:index]
    else:
        res = filter_res
    return res

def search_action(limit_res,select_l):
    res = []
    fields_l = []
    title = "id,name,age,phone,dept,enroll_data"
    if select_l[0] == '*':
        filed_l = title.split(',')
        res = limit_res
    else:
        for record in limit_res:
            dic = dict(zip(title.split(','),record))
            res_l = []
            filed_l = select_l[0].split(',')
            for i in filed_l:
                res_l.append(dic[i].strip())
            res.append(res_l)
    # print('filed_l %s',filed_l)
    # print('res %s'%res)
    return (filed_l,res)

def insert_action(sql_dic):
    title = "id,name,age,phone,dept,enroll_data"
    tel = []
    db, table = sql_dic.get('into')[0].split('.')
    with open('%s/%s/%s'%(settings.base_dir,db,table),'r',encoding='utf-8') as f:
        for line in f:
            file_dict = dict(zip(title.split(','),line.strip().split(',')))
            tel.append(file_dict['phone'])
    db,table = sql_dic.get('into')[0].split('.')
    with open('%s/%s/%s'%(settings.base_dir,db,table),'ab+') as fh:
        offs = -100
        while True:
            fh.seek(offs,2)
            lines = fh.readlines()
            if len(lines) > 1:
                last = lines[-1]
                break
            offs *= 2
        last = last.decode(encoding='utf-8')
        last_id = int(last.split(',')[0])
        new_id = last_id + 1
        record = sql_dic.get('values')[0].split(',')
        if record[2] in tel:
            print('phone [%s] 已经存在了,不能重复' % record[2])
        else:
            record.insert(0, str(new_id))
            record_str = ','.join(record) + '\n'
            fh.write(bytes(record_str,encoding='utf-8'))
            fh.flush()
            print('insert successful')

def update_action(sql_dic):
    '''
    更新指定条件的数据
    :param sql_dic: 格式化的update语句
    :return:
    '''
    # print('sql_dic is update_action \033[44;1m%s\033[0m' % sql_dic)
    db,table = sql_dic.get('update')[0].split('.')
    set = sql_dic.get('set')
    # print(set)
    set_l = []
    if len(set) == 1:
        tags = False
        char = ''
        key = ['=']
        set = str(set).strip('[]').strip("'")
        for i in set:
            if i in key:
                tags = True
                if len(char) != 0:
                    set_l.append(char)
                    char = ''
            if not tags:
                char += i
            if tags and i not in key:
                tags = False
                char += i
        else:
            set_l.append(char)
    else:
        for i in set:
            if '=' in i:
                i = i.strip('=')
                set_l.append(i)
            if i not in set_l:
                set_l.append(i)
    # print(set_l)

    bak_file = table + '_bak'
    with open('%s/%s/%s' % (settings.base_dir,db, table), 'r', encoding='utf-8') as fh, \
            open('%s/%s/%s' % (settings.base_dir,db, bak_file), 'w', encoding='utf-8') as wh:
        update_count = 0
        for line in fh:
            title = "id,name,age,phone,dept,enroll_data"
            dic = dict(zip(title.split(','), line.split(',')))
            filter_res = logic_action(dic, sql_dic.get('where'))
            if not filter_res:
                wh.write(line)
            else:
                k = set_l[0]
                v = set_l[-1].strip("'")
                # print('k v %s %s'%(k,v))
                dic[k] = v
                print('change idc is %s'%dic)
                line = []
                for i in title.split(','):
                    line.append(dic[i])
                update_count += 1
                line = ','.join(line)
                wh.write(line)
        wh.flush()
    # os.remove('%s/%s' % (db, table))
    # os.rename('%s/%s' % (db, bak_file), '%s/%s' % (db, table))
    os.remove('%s/%s/%s' % (settings.base_dir, db, table))
    os.rename('%s/%s/%s' % (settings.base_dir, db, bak_file), '%s/%s/%s' % (settings.base_dir, db, table))
    print('[%s]行更新成功' % update_count)

def delete_action(sql_dic):
    '''
    删除指定条件的数据
    :param sql_dic: 格式化的delete命令
    :return:
    '''
    db,table = sql_dic.get('from')[0].split('.')
    bak_file = table + '_bak'
    with open('%s/%s/%s' % (settings.base_dir,db,table), 'r', encoding='utf-8') as fh, \
            open('%s/%s/%s' % (settings.base_dir,db,bak_file), 'w', encoding='utf-8') as wh:
        del_count = 0
        for line in fh:
            title = "id,name,age,phone,dept,enroll_data"
            dic = dict(zip(title.split(','), line.split(',')))
            filter_res = logic_action(dic, sql_dic.get('where'))
            if not filter_res:
                wh.write(line)
            else:
                del_count += 1
        wh.flush()
    os.remove('%s/%s/%s' % (settings.base_dir,db,table))
    os.rename('%s/%s/%s' % (settings.base_dir,db,bak_file), '%s/%s/%s' % (settings.base_dir,db,table))
    print('[%s]行删除成功' % del_count)

def main():
    while True:
        sql = input('sql>').strip()
        if len(sql) == 0:
            continue
        if sql == 'exit':
            break
        sql_dic = sql_parse(sql)
        if len(sql_dic) == 0:
            continue #输入命令非法
        sql_action(sql_dic)




