from bs4 import BeautifulSoup
import copy
import datetime
import email
from email import header
import imaplib
import json
import os
import platform
import pytz
import requests
import rtoml
import socket
import time
import threading
import traceback
import urllib.parse

version = '1.3.1-Beta'
mode = 2  # 0:Release;1:Alpha;2:Beta;3:Demo
authentication = ['name', 'MailDownloader', 'version', version]
available_bigfile_website_list = [
    'wx.mail.qq.com', 'mail.qq.com', 'dashi.163.com', 'mail.163.com', 'mail.sina.com.cn']  # 先后顺序不要动!
unavailable_bigfile_website_list = []
website_blacklist = ['fs.163.com', 'u.163.com']

lock_print_global = threading.Lock()
lock_var_global = threading.Lock()
lock_io_global = threading.Lock()


class Date():
    __month_dict = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May',
                    6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
    year = 1
    month = 1
    day = 1
    enabled = False

    def __init__(self, enabled=False, year=0, month=0, day=0):
        self.enabled = enabled
        if year > 0:
            self.year = year
        if month > 0:
            self.month = month
        if day > 0:
            self.day = day

    def time(self):
        return '{:0>2d}-{}-{:0>4d}'.format(self.day, self.__month_dict[self.month], self.year)


config_load_state = False
config_primary_data = {
    'mail': [],
    'allow_manual_input_search_date': True,
    'min_search_date': False,
    'max_search_date': False,
    'only_search_unseen_mails': True,
    'thread_count': 4,
    'rollback_when_download_failed': True,
    'sign_unseen_tag_after_downloading': True,
    'reconnect_max_times': 3,
    'download_path': ''
}


def operation_load_config():
    global host, address, password
    global settings_allow_manual_input_search_date, settings_mail_min_date, settings_mail_max_date
    global settings_only_search_unseen_mails
    global settings_thread_count
    global settings_rollback_when_download_failed
    global settings_sign_unseen_tag_after_downloading
    global settings_reconnect_max_times
    global settings_download_path
    print('正在读取配置文件...', flush=True)
    try:
        with open(os.path.join(get_path(), 'config.toml'), 'rb') as config_file:
            config_file_data = rtoml.load(
                bytes.decode(config_file.read(), 'utf-8'))
            host = []
            address = []
            password = []
            for eachdata_mail in config_file_data['mail']:
                if type(eachdata_mail['host']) != str:
                    raise ValueError
                host.append(eachdata_mail['host'])
                if type(eachdata_mail['address']) != str:
                    raise ValueError
                address.append(eachdata_mail['address'])
                if type(eachdata_mail['password']) != str:
                    raise ValueError
                password.append(eachdata_mail['password'])
            settings_allow_manual_input_search_date = config_file_data[
                'allow_manual_input_search_date']
            if type(settings_allow_manual_input_search_date) != bool:
                raise ValueError
            settings_mail_min_date = Date()
            if config_file_data['min_search_date'] == False:
                settings_mail_min_date.enabled = False
            else:
                settings_mail_min_date.enabled = True
                settings_mail_min_date.year = config_file_data['min_search_date'][0]
                if type(settings_mail_min_date.year) != int:
                    raise ValueError
                settings_mail_min_date.month = config_file_data['min_search_date'][1]
                if type(settings_mail_min_date.month) != int:
                    raise ValueError
                settings_mail_min_date.day = config_file_data['min_search_date'][2]
                if type(settings_mail_min_date.day) != int:
                    raise ValueError
            settings_mail_max_date = Date()
            if config_file_data['max_search_date'] == False:
                settings_mail_max_date.enabled = False
            else:
                settings_mail_max_date.enabled = True
                settings_mail_max_date.year = config_file_data['max_search_date'][0]
                if type(settings_mail_max_date.year) != int:
                    raise ValueError
                settings_mail_max_date.month = config_file_data['max_search_date'][1]
                if type(settings_mail_max_date.month) != int:
                    raise ValueError
                settings_mail_max_date.day = config_file_data['max_search_date'][2]
                if type(settings_mail_max_date.day) != int:
                    raise ValueError
            settings_only_search_unseen_mails = config_file_data['only_search_unseen_mails']
            if type(settings_only_search_unseen_mails) != bool:
                raise ValueError
            settings_thread_count = config_file_data['thread_count']
            if type(settings_thread_count) != int or settings_thread_count < 1:
                raise ValueError
            settings_rollback_when_download_failed = config_file_data[
                'rollback_when_download_failed']
            if type(settings_rollback_when_download_failed) != bool:
                raise ValueError
            settings_sign_unseen_tag_after_downloading = config_file_data[
                'sign_unseen_tag_after_downloading']
            if type(settings_allow_manual_input_search_date) != bool:
                raise ValueError
            settings_reconnect_max_times = config_file_data['reconnect_max_times']
            if type(settings_reconnect_max_times) != int and settings_reconnect_max_times < 0:
                raise ValueError
            settings_download_path = config_file_data['download_path']
    except:
        print('E: 配置文件错误.', flush=True)
        return False
    else:
        print('配置加载成功.', flush=True)
        return True


def init():
    global stop_state_global
    global has_thread_state_changed_global
    global imap_list_global, imap_succeed_index_int_list_global, imap_connect_failed_index_int_list_global, imap_with_undownloadable_attachments_index_int_list_global, imap_overdueanddeleted_index_int_list_global, imap_fetch_failed_index_int_list_global, imap_download_failed_index_int_list_global
    global msg_processed_count_global, msg_list_global, msg_with_undownloadable_attachments_list_global, msg_with_downloadable_attachments_list_global, msg_overdueanddeleted_list_global, msg_fetch_failed_list_global, msg_download_failed_list_global
    global send_time_with_undownloadable_attachments_list_global, send_time_overdueanddeleted_list_global, send_time_download_failed_list_global
    global subject_with_undownloadable_attachments_list_global, subject_overdueanddeleted_list_global, subject_download_failed_list_global
    global file_download_count_global, file_name_raw_list_global, file_name_list_global
    global bigfile_undownloadable_link_list_global
    global bigfile_undownloadable_code_list_global
    stop_state_global = 0
    has_thread_state_changed_global = True

    imaplib.Commands['ID'] = ('AUTH')
    imap_list_global = []
    imap_succeed_index_int_list_global = []
    imap_connect_failed_index_int_list_global = []
    imap_with_undownloadable_attachments_index_int_list_global = []
    imap_overdueanddeleted_index_int_list_global = []
    imap_fetch_failed_index_int_list_global = []
    imap_download_failed_index_int_list_global = []

    msg_processed_count_global = 0
    msg_list_global = []
    msg_with_undownloadable_attachments_list_global = []
    msg_with_downloadable_attachments_list_global = []
    msg_overdueanddeleted_list_global = []
    msg_fetch_failed_list_global = []
    msg_download_failed_list_global = []
    send_time_with_undownloadable_attachments_list_global = []
    send_time_overdueanddeleted_list_global = []
    send_time_download_failed_list_global = []
    subject_with_undownloadable_attachments_list_global = []
    subject_overdueanddeleted_list_global = []
    subject_download_failed_list_global = []
    file_download_count_global = 0
    file_name_raw_list_global = []
    file_name_list_global = []
    bigfile_undownloadable_link_list_global = []  # 2级下载链接
    bigfile_undownloadable_code_list_global = []
    for i in range(len(host)):
        msg_list_global.append([])
        msg_with_undownloadable_attachments_list_global.append([])
        msg_with_downloadable_attachments_list_global.append([])
        msg_overdueanddeleted_list_global.append([])
        msg_fetch_failed_list_global.append([])
        msg_download_failed_list_global.append([])
        send_time_with_undownloadable_attachments_list_global.append([])
        send_time_overdueanddeleted_list_global.append([])
        send_time_download_failed_list_global.append([])
        subject_with_undownloadable_attachments_list_global.append([])
        subject_overdueanddeleted_list_global.append([])
        subject_download_failed_list_global.append([])
        file_name_raw_list_global.append([])
        file_name_list_global.append([])
        bigfile_undownloadable_link_list_global.append([])
        bigfile_undownloadable_code_list_global.append([])


def operation_login_imap_server(host, address, password, display=True):
    is_login_succeed = False
    try:
        if display:
            print('\r正在连接 ', host,
                  indent(3), end='', sep='', flush=True)
        imap = imaplib.IMAP4_SSL(
            host)
        if display:
            print('\r已连接 ', host,
                  indent(3), sep='', end='', flush=True)
            print('\r正在登录 ', address, indent(3),
                  end='', sep='', flush=True)
        imap.login(address, password)
        if display:
            print('\r', address,
                  ' 登录成功', indent(3), sep='', flush=True)
        imap._simple_command(
            'ID', '("' + '" "'.join(authentication) + '")')  # 发送ID
    except imaplib.IMAP4.error:
        if display:
            print('\nE: 用户名或密码错误.', flush=True)
    except (socket.timeout, TimeoutError):
        if display:
            print('\nE: 服务器连接超时.', flush=True)
    except Exception:
        if display:
            print('\nE: 服务器连接错误.', flush=True)
    else:
        is_login_succeed = True
    if is_login_succeed:
        imap.select()
        return imap
    else:
        return None


def operation_login_all_imapserver():
    init()
    for imap_index_int in range(len(host)):
        imap = operation_login_imap_server(
            host[imap_index_int], address[imap_index_int], password[imap_index_int])
        imap_list_global.append(imap)
        if imap != None:
            imap_succeed_index_int_list_global.append(imap_index_int)
        else:
            imap_connect_failed_index_int_list_global.append(imap_index_int)
    if len(host):
        if len(imap_succeed_index_int_list_global):
            print('已成功连接的邮箱:', flush=True)
            for imap_succeed_index_int in imap_succeed_index_int_list_global:
                print(indent(1), address[imap_succeed_index_int], sep='')
            if len(imap_succeed_index_int_list_global) < len(host):
                print('E: 以下邮箱未能连接:', flush=True)
                for imap_connect_failed_index_int in imap_connect_failed_index_int_list_global:
                    print(indent(1), address[imap_connect_failed_index_int],
                          sep='', flush=True)
        else:
            print('E: 没有成功连接的邮箱.', flush=True)
    else:
        print('E: 没有邮箱.')


def operation_set_time():
    settings_mail_min_date.enabled = False
    settings_mail_max_date.enabled = False
    if input_option('是否设置检索开始日期?', 'y', 'n', default_option='y', end=':') == 'y':
        settings_mail_min_date.enabled = True
        while True:
            try:
                settings_mail_min_date.year = int(input_option(
                    '输入年份', allow_undefind_input=True, default_option=str(datetime.datetime.now().year), end=':'))
                if settings_mail_min_date.year < 0:
                    raise Exception
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
        while True:
            try:
                settings_mail_min_date.month = int(input_option(
                    '输入月份', allow_undefind_input=True, default_option=str(datetime.datetime.now().month), end=':'))
                if settings_mail_min_date.month < 1 or settings_mail_min_date.month > 12:
                    raise Exception
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
        while True:
            try:
                settings_mail_min_date.day = int(input_option(
                    '输入日期', allow_undefind_input=True, default_option=str(datetime.datetime.now().day), end=':'))
                if settings_mail_min_date.day < 1 or settings_mail_min_date.day > 31:
                    raise Exception
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)

    if input_option('是否设置检索截止日期?', 'y', 'n', default_option='n', end=':') == 'y':
        settings_mail_max_date.enabled = True
        while True:
            try:
                settings_mail_max_date.year = int(input_option(
                    '输入年份', allow_undefind_input=True, default_option=str(datetime.datetime.now().year), end=':'))
                if settings_mail_max_date.year < 0:
                    print('无效选项,请重新输入.', flush=True)
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
        while True:
            try:
                settings_mail_max_date.month = int(input_option(
                    '输入月份', allow_undefind_input=True, default_option=str(datetime.datetime.now().month), end=':'))
                if settings_mail_max_date.month < 1 or settings_mail_max_date.month > 12:
                    print('无效选项,请重新输入.', flush=True)
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
        while True:
            try:
                settings_mail_max_date.day = int(input_option(
                    '输入日期', allow_undefind_input=True, default_option=str(datetime.datetime.now().day), end=':'))
                if settings_mail_max_date.day < 1 or settings_mail_max_date.day > 31:
                    print('无效选项,请重新输入.', flush=True)
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)


def operation_parse_file_name(file_name_raw):
    file_name = file_name_raw
    if not os.path.exists(settings_download_path):
        os.mkdir(settings_download_path)
    if os.path.exists(os.path.join(settings_download_path, file_name_raw)):
        i = 2
        dot_index_int = len(
            file_name_raw)-file_name_raw[::-1].find('.')-1 if '.' in file_name_raw else -1
        while True:
            if dot_index_int == -1:
                file_name = file_name_raw + \
                    ' ('+str(i)+')'
            else:
                file_name = '.'.join(
                    [file_name_raw[0:dot_index_int]+'('+str(i)+')', file_name_raw[dot_index_int+1:]])
            if not os.path.exists(os.path.join(settings_download_path, file_name)):
                break
            i += 1
    return file_name


def operation_rollback(file_name_list_raw, file_name=None, bigfile_name=None, file_name_tmp=None, bigfile_name_tmp=None):
    global file_download_count_global
    if file_name:
        file_name_list_raw.append(file_name)
    if bigfile_name:
        file_name_list_raw.append(bigfile_name)
    if file_name_tmp:
        if os.path.isfile(os.path.join(settings_download_path, file_name_tmp)):
            os.remove(os.path.join(
                settings_download_path, file_name_tmp))
    if bigfile_name_tmp:
        if os.path.isfile(os.path.join(settings_download_path, bigfile_name_tmp)):
            os.remove(os.path.join(
                settings_download_path, bigfile_name_tmp))
    for file_mixed_name in file_name_list_raw:
        if os.path.isfile(os.path.join(settings_download_path, file_mixed_name)):
            os.remove(os.path.join(
                settings_download_path, file_mixed_name))
            file_download_count_global -= 1


def operation_download_all():
    global thread_state_list_global  # 0:其他;1:读取邮件数据/获取链接;2:下载文件
    global has_thread_state_changed_global
    global thread_list_global, thread_file_name_list_global
    global msg_list_global, msg_total_count_global, msg_processed_count_global
    operation_login_all_imapserver()
    if not len(imap_succeed_index_int_list_global):
        print('E: 无法执行该操作.原因: 没有可用邮箱.', flush=True)
        return
    if settings_allow_manual_input_search_date:
        operation_set_time()
    start_time = time.time()
    if not (settings_mail_min_date.enabled or settings_mail_max_date.enabled):
        if settings_only_search_unseen_mails:
            print('仅检索未读邮件', flush=True)
        else:
            print('检索全部邮件', flush=True)
    else:
        prompt = ''
        prompt += '仅检索日期'
        prompt += ('从 '+settings_mail_min_date.time()
                   ) if settings_mail_min_date.enabled else '在 ' if settings_mail_max_date else ''
        prompt += ' 开始' if settings_mail_min_date.enabled and not settings_mail_max_date.enabled else (str(
            settings_mail_max_date.time()+' 截止')) if not settings_mail_min_date.enabled and settings_mail_max_date.enabled else ' 到 '
        prompt += settings_mail_max_date.time() if settings_mail_min_date.enabled and settings_mail_max_date.enabled else ''
        prompt += '的未读邮件' if settings_only_search_unseen_mails else '的邮件'
        print(prompt, sep='', flush=True)
    for imap_index_int in imap_succeed_index_int_list_global:
        if not (settings_mail_min_date.enabled or settings_mail_max_date.enabled):
            search_command = ''
            if settings_only_search_unseen_mails:
                search_command = 'unseen'
            else:
                search_command = 'all'
        else:
            search_command = ''
            search_command += ('since '+settings_mail_min_date.time()
                               ) if settings_mail_min_date.enabled else ''
            search_command += ' ' if settings_mail_min_date.enabled and settings_mail_max_date.enabled else ''
            search_command += ('before ' + settings_mail_max_date.time()
                               ) if settings_mail_max_date.enabled else ''
            search_command += ' ' if (
                settings_mail_max_date.enabled or settings_mail_min_date.enabled) and settings_only_search_unseen_mails else ''
            search_command += 'unseen' if settings_only_search_unseen_mails else ''
        search_state_last = False
        for i in range(settings_reconnect_max_times+1):
            try:
                typ, data_msg_index_raw = imap_list_global[imap_index_int].search(
                    None, search_command)
                search_state_last = True
                break
            except Exception:
                for i in range(settings_reconnect_max_times):
                    imap_list_global[imap_index_int] = operation_login_imap_server(
                        host[imap_index_int], address[imap_index_int], password[imap_index_int], False)
                    if imap_list_global[imap_index_int] != None:
                        break
        if not search_state_last:
            print('E: 邮箱', address[imap_index_int], '搜索失败,已跳过.', flush=True)
            imap_connect_failed_index_int_list_global.append(
                imap_index_int)
            imap_index_int = None
            continue
        msg_list = list(reversed(data_msg_index_raw[0].split()))
        msg_list_global[imap_index_int] = msg_list
        print(
            '\r邮箱: ', address[imap_index_int], indent(3), sep='', flush=True)
        print(indent(1), '共 ', len(msg_list), ' 封邮件', sep='', flush=True)
    if len(extract_nested_list(msg_list_global)):
        print('共 ', len(extract_nested_list(msg_list_global)),
              ' 封邮件', sep='', flush=True)
    else:
        print('没有符合条件的邮件.\n', flush=True)
        return
    # print(msg_list_global)  # debug
    start_time = time.time()
    print('开始处理...\n', end='', flush=True)
    msg_total_count_global = len(extract_nested_list(msg_list_global))
    thread_list_global = []
    thread_state_list_global = []
    thread_file_name_list_global = []
    for thread_id in range(settings_thread_count):
        thread_state_list_global.append(0)
        thread_file_name_list_global.append([])
        thread = threading.Thread(
            target=download_thread_func, args=(thread_id,))
        thread_list_global.append(thread)
        thread.daemon = True
        thread.start()
    while True:
        if stop_state_global:
            return
        if thread_state_list_global.count(-1) == len(thread_state_list_global):
            break
        if has_thread_state_changed_global:
            has_thread_state_changed_global = False
            with lock_print_global:
                print('\r已处理 (', msg_processed_count_global, '/',
                      msg_total_count_global, '),', sep='', end='', flush=True)
                print('线程信息 (', len(thread_state_list_global)-thread_state_list_global.count(-1), '/', len(thread_list_global), ',',
                      thread_state_list_global.count(1), ',', thread_state_list_global.count(2), ')', indent(3), sep='', end='', flush=True)
        time.sleep(0)
    finish_time = time.time()
    with lock_print_global:
        if file_download_count_global > 0:
            print('\r共下载 ', file_download_count_global,
                  ' 个附件', indent(8), sep='', flush=True)
        else:
            print('\r没有可下载的附件', indent(8), flush=True)
        print('耗时: ', round(finish_time-start_time, 2),
              ' 秒', indent(8), sep='', flush=True)
        if len(imap_connect_failed_index_int_list_global):
            print('E: 以下邮箱断开连接,且未能成功连接:', flush=True)
            for imap_connect_failed_index_int in imap_connect_failed_index_int_list_global:
                print(
                    indent(1), address[imap_connect_failed_index_int], sep='', flush=True)
        for msg_list_index_int in range(len(msg_list_global)):
            if len(msg_list_global[msg_list_index_int]) > 0:
                if safe_list_find(imap_fetch_failed_index_int_list_global, msg_list_index_int) == -1:
                    imap_fetch_failed_index_int_list_global.append(
                        msg_list_index_int)
                    for msg in msg_list_global[msg_list_index_int]:
                        msg_fetch_failed_list_global[msg_list_index_int].append(
                            msg)
        if len(imap_fetch_failed_index_int_list_global):
            print('E: 以下邮箱有处理失败的邮件,请尝试重新下载:', flush=True)
            for imap_fetch_failed_index_int in imap_fetch_failed_index_int_list_global:
                print(indent(
                    1), '邮箱: ', address[imap_fetch_failed_index_int], sep='', flush=True)
                print(indent(2), len(
                    msg_fetch_failed_list_global[imap_fetch_failed_index_int]), ' 封邮件处理失败', sep='', flush=True)
        if len(extract_nested_list(msg_download_failed_list_global)):
            msg_download_failed_counted_count = 0
            print('E: 以下邮件有超大附件无法识别或下载失败,请尝试手动下载:', flush=True)
            for imap_download_failed_index_int in imap_download_failed_index_int_list_global:
                print(indent(
                    1), '邮箱: ', address[imap_download_failed_index_int], sep='', flush=True)
                for subject_index_int in range(len(subject_download_failed_list_global[imap_download_failed_index_int])):
                    print(indent(2), msg_download_failed_counted_count+1, ' ',
                          subject_download_failed_list_global[imap_download_failed_index_int][subject_index_int], ' - ', send_time_download_failed_list_global[imap_download_failed_index_int][subject_index_int], sep='', flush=True)
                    msg_download_failed_counted_count += 1
        if len(extract_nested_list(msg_with_undownloadable_attachments_list_global)):
            msg_with_undownloadable_attachments_counted_count = 0
            bigfile_undownloadable_link_counted_count = 0
            print('W: 以下邮件的超大附件无法直接下载,但仍可获取链接,请尝试手动下载:', flush=True)
            for imap_with_undownloadable_attachments_index_int in imap_with_undownloadable_attachments_index_int_list_global:
                print(indent(
                    1), '邮箱: ', address[imap_with_undownloadable_attachments_index_int], sep='', flush=True)
                for subject_index_int in range(len(subject_with_undownloadable_attachments_list_global[imap_with_undownloadable_attachments_index_int])):
                    print(indent(2), msg_with_undownloadable_attachments_counted_count+1, ' ',
                          subject_with_undownloadable_attachments_list_global[imap_with_undownloadable_attachments_index_int][subject_index_int], ' - ', send_time_with_undownloadable_attachments_list_global[imap_with_undownloadable_attachments_index_int][subject_index_int], sep='', flush=True)
                    for link_index_int in range(len(bigfile_undownloadable_link_list_global[imap_with_undownloadable_attachments_index_int][subject_index_int])):
                        print(indent(3), bigfile_undownloadable_link_counted_count+1, ' ',
                              bigfile_undownloadable_link_list_global[imap_with_undownloadable_attachments_index_int][subject_index_int][link_index_int], sep='', flush=True)
                        bigfile_download_code = bigfile_undownloadable_code_list_global[
                            imap_with_undownloadable_attachments_index_int][subject_index_int][link_index_int]
                        if bigfile_download_code != 0:
                            print(indent(4), '错误代码: ',
                                  bigfile_download_code, sep='', flush=True)
                            if bigfile_download_code == 602 or bigfile_download_code == -4:
                                print(indent(4), '原因: 文件下载次数达到最大限制.',
                                      sep='', flush=True)
                        bigfile_undownloadable_link_counted_count += 1
                    msg_with_undownloadable_attachments_counted_count += 1
            if settings_sign_unseen_tag_after_downloading:
                if input_option('要将以上邮件设为已读吗?', 'y', 'n', default_option='n', end=':') == 'y':
                    msg_with_downloadable_attachments_signed_count = 0
                    print('\r正在标记...', end='', flush=True)
                    for imap_index_int in range(len(imap_list_global)):
                        for msg_index in msg_with_undownloadable_attachments_list_global[imap_index_int]:
                            for i in range(settings_reconnect_max_times+1):
                                try:
                                    imap_list_global[imap_index_int].store(msg_index,
                                                                           'flags', '\\seen')
                                    break
                                except Exception:
                                    for i in range(settings_reconnect_max_times):
                                        imap_list_global[imap_index_int] = operation_login_imap_server(
                                            host[imap_succeed_index_int_list_global[imap_index_int]], address[imap_succeed_index_int_list_global[imap_index_int]], password[imap_succeed_index_int_list_global[imap_index_int]], False)
                                        if imap_list_global[imap_index_int] != None:
                                            break
                            msg_with_downloadable_attachments_signed_count += 1
                    print('\r', indent(6), sep='', end='', flush=True)
                    if not len(extract_nested_list(msg_overdueanddeleted_list_global)):
                        print(flush=True)
                else:
                    if not len(extract_nested_list(msg_overdueanddeleted_list_global)):
                        print(flush=True)
            else:
                if not len(extract_nested_list(msg_overdueanddeleted_list_global)):
                    print(flush=True)
        else:
            if not len(extract_nested_list(msg_overdueanddeleted_list_global)):
                print(flush=True)
        if len(extract_nested_list(msg_overdueanddeleted_list_global)):
            msg_overdueanddeleted_counted_count = 0
            print('\rN: 以下邮件的超大附件全部过期或被删除:', flush=True)
            for imap_overdueanddeleted_index_int in imap_overdueanddeleted_index_int_list_global:
                print(indent(
                    1), '邮箱: ', address[imap_overdueanddeleted_index_int], sep='', flush=True)
                for subject_index_int in range(len(subject_overdueanddeleted_list_global[imap_overdueanddeleted_index_int])):
                    print(indent(2), msg_overdueanddeleted_counted_count+1, ' ',
                          subject_overdueanddeleted_list_global[imap_overdueanddeleted_index_int][subject_index_int], ' - ', send_time_overdueanddeleted_list_global[imap_overdueanddeleted_index_int][subject_index_int], sep='', flush=True)
                    msg_overdueanddeleted_counted_count += 1
            if settings_sign_unseen_tag_after_downloading:
                if input_option('要将以上邮件设为已读吗?', 'y', 'n', default_option='y', end=':') == 'y':
                    msg_overdueanddeleted_signed_count = 0
                    print('\r正在标记...', end='', flush=True)
                    for imap_index_int in range(len(imap_list_global)):
                        for msg_index in msg_overdueanddeleted_list_global[imap_index_int]:
                            for i in range(settings_reconnect_max_times+1):
                                try:
                                    imap_list_global[imap_index_int].store(msg_index,
                                                                           'flags', '\\seen')
                                    break
                                except Exception:
                                    for i in range(settings_reconnect_max_times):
                                        imap_list_global[imap_index_int] = operation_login_imap_server(
                                            host[imap_succeed_index_int_list_global[imap_index_int]], address[imap_succeed_index_int_list_global[imap_index_int]], password[imap_succeed_index_int_list_global[imap_index_int]], False)
                                        if imap_list_global[imap_index_int] != None:
                                            break
                            msg_overdueanddeleted_signed_count += 1
                    print('\r', indent(6), sep='', flush=True)
                else:
                    print(flush=True)
            else:
                print(flush=True)


def operation_fresh_thread_state(thread_id, state):
    global has_thread_state_changed_global
    thread_state_list_global[thread_id] = state
    has_thread_state_changed_global = True


def download_thread_func(thread_id):
    global file_download_count_global, msg_processed_count_global, msg_list_global
    global thread_file_name_list_global
    imap_list = []
    imap_index_int_list = []
    for imap_index_int in range(len(imap_succeed_index_int_list_global)):
        if imap_succeed_index_int_list_global[imap_index_int] == None:
            continue
        req_state_last = False
        for i in range(settings_reconnect_max_times+1):
            imap = operation_login_imap_server(
                host[imap_succeed_index_int_list_global[imap_index_int]], address[imap_succeed_index_int_list_global[imap_index_int]], password[imap_succeed_index_int_list_global[imap_index_int]], False)
            if imap != None:
                break
        imap_list.append(imap)
        imap_index_int_list.append(imap_index_int)
        if imap != None:
            while True:
                lock_var_global.acquire()
                if len(msg_list_global[imap_succeed_index_int_list_global[imap_index_int]]):
                    msg_index = msg_list_global[imap_succeed_index_int_list_global[imap_index_int]].pop(
                        0)
                    lock_var_global.release()
                    file_download_count = 0
                    download_state_last = -1  # -2:下载失败;-1:无附件且处理正常;0:有附件且处理正常;1:有无法直接下载的附件;2:附件全部过期或不存在
                    thread_file_name_list_global[thread_id] = []
                    bigfile_undownloadable_code_list = []
                    has_downloadable_attachment = False
                    bigfile_downloadable_link_list = []
                    bigfile_download_code = 0
                    bigfile_undownloadable_link_list = []
                    with lock_var_global:
                        operation_fresh_thread_state(thread_id, 1)
                    fetch_state_last = False
                    for i in range(settings_reconnect_max_times+1):
                        try:
                            typ, data_msg_raw = imap.fetch(
                                msg_index, 'BODY.PEEK[]')
                            fetch_state_last = True
                            break
                        except Exception:
                            for i in range(settings_reconnect_max_times):
                                imap = operation_login_imap_server(
                                    host[imap_succeed_index_int_list_global[imap_index_int]], address[imap_succeed_index_int_list_global[imap_index_int]], password[imap_succeed_index_int_list_global[imap_index_int]], False)
                                if imap != None:
                                    break
                    if not fetch_state_last:
                        print('E: 有邮件获取失败,已跳过.')
                    else:
                        data_msg = email.message_from_bytes(
                            data_msg_raw[0][1])
                        subject = str(header.make_header(
                            header.decode_header(data_msg.get('Subject'))))
                        send_time_raw = str(header.make_header(
                            header.decode_header(data_msg.get('Date'))))[5:]
                        send_time = copy.copy(send_time_raw)
                        try:
                            if '(' in send_time_raw:
                                send_time = send_time_raw[:send_time_raw.find(
                                    ' (')]
                            if '+' in send_time or '-' in send_time:
                                send_time = str(datetime.datetime.strptime(
                                    send_time, '%d %b %Y %H:%M:%S %z').astimezone(pytz.timezone('Etc/GMT-8')))[:-6]
                            elif 'GMT' in send_time_raw:
                                send_time = str(datetime.datetime.strptime(
                                    send_time_raw, '%d %b %Y %H:%M:%S %Z').astimezone(pytz.timezone('Etc/GMT+8')))[:-6]
                            else:
                                raise ValueError
                        except ValueError:
                            send_time = send_time_raw
                        try:
                            for eachdata_msg in data_msg.walk():
                                file_name = None
                                bigfile_name = None
                                file_name_tmp = None
                                bigfile_name_tmp = None
                                # print(eachdata_msg)
                                if eachdata_msg.get_content_disposition() and 'attachment' in eachdata_msg.get_content_disposition():
                                    has_downloadable_attachment = True
                                    file_name_raw = str(header.make_header(
                                        header.decode_header(eachdata_msg.get_filename())))
                                    file_data = eachdata_msg.get_payload(
                                        decode=True)
                                    with lock_var_global:
                                        operation_fresh_thread_state(
                                            thread_id, 2)
                                    if stop_state_global:
                                        if settings_rollback_when_download_failed:
                                            with lock_io_global:
                                                operation_rollback(
                                                    thread_file_name_list_global[thread_id], file_name, bigfile_name, file_name_tmp, bigfile_name_tmp)
                                        return
                                    lock_io_global.acquire()
                                    file_name_tmp = operation_parse_file_name(
                                        file_name_raw+'.tmp')
                                    with open(os.path.join(settings_download_path, file_name_tmp), 'wb') as file:
                                        lock_io_global.release()
                                        file.write(file_data)
                                    with lock_io_global:
                                        file_name = operation_parse_file_name(
                                            file_name_raw)
                                        os.renames(os.path.join(settings_download_path, file_name_tmp),
                                                   os.path.join(settings_download_path, file_name))
                                    if stop_state_global:
                                        if settings_rollback_when_download_failed:
                                            with lock_io_global:
                                                operation_rollback(
                                                    thread_file_name_list_global[thread_id], file_name, bigfile_name, file_name_tmp, bigfile_name_tmp)
                                        return
                                    with lock_print_global, lock_var_global:
                                        print('\r', file_download_count_global+1, ' 已下载 ', file_name, (
                                            ' <- '+file_name_raw)if file_name != file_name_raw else '', indent(8), sep='', flush=True)
                                        print(indent(
                                            1), '邮箱: ', address[imap_succeed_index_int_list_global[imap_index_int]], sep='', flush=True)
                                        print(indent(1), '邮件标题: ', subject, ' - ',
                                              send_time, sep='', flush=True)
                                        file_download_count_global += 1
                                        file_download_count += 1
                                        thread_file_name_list_global[thread_id].append(
                                            file_name)
                                        operation_fresh_thread_state(
                                            thread_id, 0)
                                    if download_state_last == -1 or download_state_last == 2:  # 去除邮件无附件标记或全部过期标记
                                        download_state_last = 0
                                if eachdata_msg.get_content_type() == 'text/html':
                                    eachdata_msg_charset = eachdata_msg.get_content_charset()
                                    eachdata_msg_data_raw = eachdata_msg.get_payload(
                                        decode=True)
                                    eachdata_msg_data = bytes.decode(
                                        eachdata_msg_data_raw, eachdata_msg_charset)
                                    html_fetcher = BeautifulSoup(
                                        eachdata_msg_data, 'lxml')
                                    if '附件' in eachdata_msg_data:
                                        # with open(os.path.join(get_path(), 'test/mail2.html'), 'wb') as a:
                                        #     a.write(eachdata_msg_data_raw)
                                        with lock_var_global:
                                            operation_fresh_thread_state(
                                                thread_id, 1)
                                        href_list = html_fetcher.find_all('a')
                                        for href in href_list:
                                            if '下载' in href.get_text():
                                                bigfile_downloadable_link = None
                                                bigfile_link = href.get('href')
                                                if find_childstr_to_list(available_bigfile_website_list, bigfile_link):
                                                    req_state_last = False
                                                    for i in range(settings_reconnect_max_times+1):
                                                        try:
                                                            download_page = requests.get(
                                                                bigfile_link)
                                                            req_state_last = True
                                                            break
                                                        except Exception:
                                                            pass
                                                    if not req_state_last:
                                                        raise Exception
                                                    html_fetcher_2 = BeautifulSoup(
                                                        download_page.text, 'lxml')
                                                    if 'wx.mail.qq.com' in bigfile_link:
                                                        script = html_fetcher_2.select_one(
                                                            'body > script:nth-child(2)')
                                                        if not 'var url = ""' in script:
                                                            script = script.get_text()
                                                            bigfile_downloadable_link = script[script.find(
                                                                'https://gzc-download.ftn.qq.com'):-1]
                                                            bigfile_downloadable_link = bigfile_downloadable_link.replace(
                                                                '\\x26', '&')
                                                            bigfile_download_method = 0  # get
                                                        else:
                                                            if not has_downloadable_attachment and download_state_last != 1:
                                                                download_state_last = 2
                                                    elif 'mail.qq.com' in bigfile_link:
                                                        bigfile_downloadable_link = html_fetcher_2.select_one(
                                                            '#main > div.ft_d_mainWrapper > div > div > div.ft_d_fileToggle.default > a.ft_d_btnDownload.btn_blue')
                                                        if bigfile_downloadable_link:
                                                            bigfile_downloadable_link = bigfile_downloadable_link.get(
                                                                'href')
                                                            bigfile_download_method = 0  # get
                                                        else:
                                                            if not has_downloadable_attachment and download_state_last != 1:
                                                                download_state_last = 2
                                                    elif 'dashi.163.com' in bigfile_link:
                                                        link_key = urllib.parse.parse_qs(
                                                            urllib.parse.urlparse(bigfile_link).query)['key'][0]
                                                        req_state_last = False
                                                        for i in range(settings_reconnect_max_times+1):
                                                            try:
                                                                fetch_result = json.loads(requests.post(
                                                                    'https://dashi.163.com/filehub-master/file/dl/prepare2', json={'fid': '', 'linkKey': link_key}).text)
                                                                req_state_last = True
                                                                break
                                                            except Exception:
                                                                pass
                                                        if not req_state_last:
                                                            raise Exception
                                                        bigfile_download_code = fetch_result['code']
                                                        if bigfile_download_code == 200:
                                                            bigfile_downloadable_link = fetch_result[
                                                                'result']['downloadUrl']
                                                            bigfile_download_method = 0  # get
                                                        elif bigfile_download_code == 404 or bigfile_download_code == 601:
                                                            if not has_downloadable_attachment and download_state_last != 1:
                                                                download_state_last = 2
                                                        else:
                                                            bigfile_undownloadable_link_list.append(
                                                                bigfile_link)
                                                            bigfile_undownloadable_code_list.append(
                                                                bigfile_download_code)
                                                            download_state_last = 1
                                                    elif 'mail.163.com' in bigfile_link:
                                                        link_key = urllib.parse.parse_qs(
                                                            urllib.parse.urlparse(bigfile_link).query)['file'][0]
                                                        req_state_last = False
                                                        for i in range(settings_reconnect_max_times+1):
                                                            try:
                                                                fetch_result = json.loads(requests.get(
                                                                    'https://fs.mail.163.com/fs/service', params={'f': link_key, 'op': 'fs_dl_f_a'}).text)
                                                                req_state_last = True
                                                                break
                                                            except Exception:
                                                                pass
                                                        if not req_state_last:
                                                            raise Exception
                                                        bigfile_download_code = fetch_result['code']
                                                        if bigfile_download_code == 200:
                                                            bigfile_downloadable_link = fetch_result[
                                                                'result']['downloadUrl']
                                                            bigfile_download_method = 0  # get
                                                        elif bigfile_download_code == -17 or bigfile_download_code == -3:
                                                            if not has_downloadable_attachment and download_state_last != 1:
                                                                download_state_last = 2
                                                        else:
                                                            bigfile_undownloadable_link_list.append(
                                                                bigfile_link)
                                                            bigfile_undownloadable_code_list.append(
                                                                bigfile_download_code)
                                                            download_state_last = 1
                                                    elif 'mail.sina.com.cn' in bigfile_link:
                                                        req_state_last = False
                                                        for i in range(settings_reconnect_max_times+1):
                                                            try:
                                                                download_page = requests.get(
                                                                    bigfile_link)
                                                                req_state_last = True
                                                                break
                                                            except Exception:
                                                                pass
                                                        if not req_state_last:
                                                            raise Exception
                                                        html_fetcher_2 = BeautifulSoup(
                                                            download_page.text, 'lxml')
                                                        can_download = len(
                                                            html_fetcher_2.find_all('input'))
                                                        if can_download:
                                                            bigfile_downloadable_link = bigfile_link
                                                            bigfile_download_method = 1  # post
                                                        else:
                                                            if not has_downloadable_attachment and download_state_last != 1:
                                                                download_state_last = 2
                                                elif find_childstr_to_list(unavailable_bigfile_website_list, bigfile_link):
                                                    bigfile_undownloadable_link_list.append(
                                                        bigfile_link)
                                                    bigfile_undownloadable_code_list.append(
                                                        bigfile_download_code)
                                                    download_state_last = 1
                                                elif find_childstr_to_list(website_blacklist, bigfile_link):
                                                    continue
                                                else:
                                                    download_state_last = -2
                                                if bigfile_downloadable_link:
                                                    bigfile_downloadable_link_list.append(
                                                        bigfile_downloadable_link)
                                                    has_downloadable_attachment = True
                                                    req_state_last = False
                                                    for i in range(settings_reconnect_max_times+1):
                                                        try:
                                                            if bigfile_download_method == 0:
                                                                bigfile_data = requests.get(
                                                                    bigfile_downloadable_link, stream=True)
                                                            else:
                                                                bigfile_data = requests.post(
                                                                    bigfile_downloadable_link, stream=True)
                                                            req_state_last = True
                                                            break
                                                        except Exception:
                                                            pass
                                                    if not req_state_last:
                                                        raise Exception
                                                    bigfile_name_raw = bigfile_data.headers.get(
                                                        'Content-Disposition')
                                                    bigfile_name_raw = bigfile_name_raw.encode(
                                                        'ISO-8859-1').decode('utf8')  # 转码
                                                    bigfile_name_raw = bigfile_name_raw.split(';')[
                                                        1]
                                                    bigfile_name_raw = (bigfile_name_raw[bigfile_name_raw.find(
                                                        'filename="')+len(
                                                        'filename="'):])[:-1]
                                                    with lock_var_global:
                                                        operation_fresh_thread_state(
                                                            thread_id, 2)
                                                    if stop_state_global:
                                                        if settings_rollback_when_download_failed:
                                                            with lock_io_global:
                                                                operation_rollback(
                                                                    thread_file_name_list_global[thread_id], file_name, bigfile_name, file_name_tmp, bigfile_name_tmp)
                                                        return
                                                    lock_io_global.acquire()
                                                    bigfile_name_tmp = operation_parse_file_name(
                                                        bigfile_name_raw+'.tmp')
                                                    req_state_last = False
                                                    for i in range(settings_reconnect_max_times+1):
                                                        try:
                                                            with open(os.path.join(settings_download_path, bigfile_name_tmp), 'wb') as file:
                                                                lock_io_global.release()
                                                                for bigfile_data_chunk in bigfile_data.iter_content(1024):
                                                                    if stop_state_global:
                                                                        break
                                                                    file.write(
                                                                        bigfile_data_chunk)
                                                            req_state_last = True
                                                            break
                                                        except Exception:
                                                            pass
                                                    if not req_state_last:
                                                        raise Exception
                                                    with lock_io_global:
                                                        bigfile_name = operation_parse_file_name(
                                                            bigfile_name_raw)
                                                        os.renames(
                                                            os.path.join(settings_download_path, bigfile_name_tmp), os.path.join(settings_download_path, bigfile_name))
                                                    if stop_state_global:
                                                        if settings_rollback_when_download_failed:
                                                            with lock_io_global:
                                                                operation_rollback(
                                                                    thread_file_name_list_global[thread_id], file_name, bigfile_name, file_name_tmp, bigfile_name_tmp)
                                                        return
                                                    with lock_print_global, lock_var_global:
                                                        print('\r', file_download_count_global+1, ' 已下载 ', bigfile_name, (
                                                            ' <- '+bigfile_name_raw)if bigfile_name != bigfile_name_raw else '', indent(8), sep='', flush=True)
                                                        print(indent(
                                                            1), '邮箱: ', address[imap_succeed_index_int_list_global[imap_index_int]], sep='', flush=True)
                                                        print(indent(
                                                            1), '邮件标题: ', subject, ' - ', send_time, sep='', flush=True)
                                                        file_download_count_global += 1
                                                        file_download_count += 1
                                                        thread_file_name_list_global[thread_id].append(
                                                            bigfile_name)
                                                        operation_fresh_thread_state(
                                                            thread_id, 0)
                                                    if download_state_last == -1 or download_state_last == 2:  # 去除邮件无附件标记或全部过期标记
                                                        download_state_last = 0
                        except Exception as e:
                            if lock_io_global.locked():
                                lock_io_global.release()
                            with lock_print_global:
                                if not req_state_last:
                                    print('E: 有附件下载失败,该邮件已跳过.', flush=True)
                                    if settings_rollback_when_download_failed:
                                        operation_rollback(
                                            thread_file_name_list_global[thread_id], file_name, bigfile_name, file_name_tmp, bigfile_name_tmp)
                            download_state_last = -2
                    with lock_var_global:
                        if fetch_state_last:
                            if download_state_last == 0:
                                if has_downloadable_attachment:
                                    msg_with_downloadable_attachments_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                        msg_index)
                                    file_name_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                        thread_file_name_list_global[thread_id])
                                    # 防止回滚时把全部下载成功的邮件的附件删除
                                    thread_file_name_list_global[thread_id] = [
                                    ]
                                    if settings_sign_unseen_tag_after_downloading:
                                        for i in range(settings_reconnect_max_times+1):
                                            try:
                                                if settings_sign_unseen_tag_after_downloading and download_state_last == 0:
                                                    imap_list_global[imap_succeed_index_int_list_global[imap_index_int]].store(msg_index,
                                                                                                                               'flags', '\\seen')
                                                break
                                            except Exception:
                                                for i in range(settings_reconnect_max_times):
                                                    imap = operation_login_imap_server(
                                                        host[imap_succeed_index_int_list_global[imap_index_int]], address[imap_succeed_index_int_list_global[imap_index_int]], password[imap_succeed_index_int_list_global[imap_index_int]], False)
                                                    if imap != None:
                                                        break
                            elif download_state_last == 1:
                                if safe_list_find(imap_with_undownloadable_attachments_index_int_list_global, imap_succeed_index_int_list_global[imap_index_int]) == -1:
                                    imap_with_undownloadable_attachments_index_int_list_global.append(
                                        imap_succeed_index_int_list_global[imap_index_int])
                                msg_with_undownloadable_attachments_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    msg_index)
                                send_time_with_undownloadable_attachments_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    send_time)
                                subject_with_undownloadable_attachments_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    subject)
                                bigfile_undownloadable_link_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    bigfile_undownloadable_link_list)
                                bigfile_undownloadable_code_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    bigfile_undownloadable_code_list)
                            elif download_state_last == 2:
                                if safe_list_find(imap_overdueanddeleted_index_int_list_global, imap_succeed_index_int_list_global[imap_index_int]) == -1:
                                    imap_overdueanddeleted_index_int_list_global.append(
                                        imap_succeed_index_int_list_global[imap_index_int])
                                msg_overdueanddeleted_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    msg_index)
                                send_time_overdueanddeleted_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    send_time)
                                subject_overdueanddeleted_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    subject)
                            elif download_state_last == -2:
                                if safe_list_find(imap_download_failed_index_int_list_global, imap_succeed_index_int_list_global[imap_index_int]) == -1:
                                    imap_download_failed_index_int_list_global.append(
                                        imap_succeed_index_int_list_global[imap_index_int])
                                msg_download_failed_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    msg_index)
                                send_time_download_failed_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    send_time)
                                subject_download_failed_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                    subject)
                            msg_processed_count_global += 1
                            operation_fresh_thread_state(thread_id, 0)
                        else:
                            if safe_list_find(imap_fetch_failed_index_int_list_global, imap_succeed_index_int_list_global[imap_index_int]) == -1:
                                imap_fetch_failed_index_int_list_global.append(
                                    imap_succeed_index_int_list_global[imap_index_int])
                            msg_fetch_failed_list_global[imap_succeed_index_int_list_global[imap_index_int]].append(
                                msg_index)
                else:
                    lock_var_global.release()
                    break
    with lock_var_global:
        operation_fresh_thread_state(thread_id, -1)


def get_path():
    return os.path.dirname(__file__)


def indent(count, unit=4, char=' '):
    placeholder_str = ''
    for i in range(0, count*unit):
        placeholder_str += char
    return placeholder_str


def safe_list_find(List, element):
    try:
        index = List.index(element)
        return index
    except ValueError:
        return -1


def find_childstr_to_list(List, Str):  # 遍历列表,判断列表中字符串是否为指定字符串的子字符串
    for j in List:
        if j in Str:
            return True
    return False


def extract_nested_list(List):
    List2 = copy.deepcopy(List)
    result_list = []
    for i in range(len(List2)):
        if isinstance(List2[i], list) or isinstance(List2[i], tuple):
            result_list += extract_nested_list(List2[i])
        else:
            result_list.append(List2[i])
    return result_list


def input_option(prompt, *options, allow_undefind_input=False, default_option='', end=''):
    if len(options) or len(default_option):
        prompt += ' ('
        for option in options:
            prompt += option
            prompt += '/'
        if len(options):
            prompt = prompt[0:-1]
        if len(default_option):
            if len(options):
                prompt += ','
            prompt += '默认选项:'
            prompt += default_option
        prompt += ')'
    prompt += end
    while True:
        print(prompt, end='', flush=True)
        result = input()
        if not len(result) and len(default_option):
            return default_option
        else:
            if not allow_undefind_input:
                if safe_list_find(options, result) == -1:
                    print('无效选项,请重新输入.', flush=True)
                    continue
            return result


def nexit(code=0):
    input_option('按回车键退出 ', allow_undefind_input=True)
    exit(code)


try:
    print('Mail Downloader\nDesingned by Litrix', flush=True)
    print('版本:', version, flush=True)
    print('获取更多信息,请访问 https://github.com/Litrix2/MailDownloader', flush=True)
    if mode == 1:
        print('W: 此版本正在开发中,可能包含严重错误,请及时跟进仓库以获取最新信息.')
    elif mode == 2:
        print('W: 此版本正在测试中,可能不稳定,请及时跟进仓库以获取最新信息.')
    elif mode == 3:
        print('W: 此版本为演示版本,部分功能与信息显示与正式版本存在差异.')
    print(flush=True)
    config_load_state = operation_load_config()
    while True:
        command = input_option(
            '\r请选择操作 [d:下载;t:测试连接;r:重载配置;n:新建配置;c:清屏;q:退出]', 'd', 't', 'r', 'n', 'c', 'q', default_option='d', end=':')
        if command == 'd' or command == 't':
            if not config_load_state:
                print('E: 配置文件错误,请在重新加载后执行该操作.', flush=True)
            else:
                if command == 'd':
                    operation_download_all()
                elif command == 't':
                    operation_login_all_imapserver()
        elif command == 'r':
            config_load_state = operation_load_config()
        elif command == 'n':
            if input_option('此操作将生成 config_new.toml,是否继续?', 'y', 'n', default_option='n', end=':') == 'y':
                with open(os.path.join(get_path(), 'config_new.toml'), 'w') as config_new_file:
                    rtoml.dump(config_primary_data, config_new_file)
                print('操作成功完成.', flush=True)
        elif command == 'c':
            Platform = platform.platform().lower()
            if 'windows' in Platform:
                os.system('cls')
            elif 'linux' in Platform or 'macos' in Platform:
                os.system('clear')
            else:
                print('E: 操作系统类型未知,无法执行该操作.', flush=True)
        elif command == 'q':
            break
    nexit(0)
except KeyboardInterrupt:
    stop_state_global = 1
    if 'thread_state_list_global' in vars() and settings_rollback_when_download_failed and thread_state_list_global.count(-1) < len(thread_state_list_global):
        for thread_file_name_list in thread_file_name_list_global:
            with lock_io_global:
                operation_rollback(thread_file_name_list)
    with lock_print_global:
        print('\n强制退出', flush=True)
        time.sleep(1)
        nexit(1)
except Exception as e:
    stop_state_global = 1
    with lock_print_global:
        print('\nF: 遇到无法解决的错误.信息如下:', flush=True)
        traceback.print_exc()
        nexit(1)
