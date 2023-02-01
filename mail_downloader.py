import littoolkit as ltk
from bs4 import BeautifulSoup
import copy
import datetime
import email
from email import header, utils
import getopt
import imaplib
import json
import logging
import os
import platform
import pytz
import re
import requests
import rtoml
import socket
import sys
import time
import threading
import traceback
import urllib.parse

__version__ = '1.4.5'
_depend_toolkit_version = '1.0.1'
__status__ = 1
__author__ = 'Litrix'

_status_dict = {
    0: 'Release',
    1: 'Alpha',
    2: 'Beta',
    3: 'Demo'
}
_regex_flag_dict = {
    'a': re.ASCII,
    'i': re.IGNORECASE,
    'l': re.LOCALE,
    'm': re.MULTILINE,
    's': re.DOTALL,
    'x': re.VERBOSE,
    'u': re.UNICODE
}
_month_dict = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May',
               6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

config_custom_path_global = None

authentication_global = ['name', 'MailDownloader', 'version', __version__]
available_largefile_website_list_global = [
    'wx.mail.qq.com', 'mail.qq.com', 'dashi.163.com', 'mail.163.com', 'mail.sina.com.cn']  # 先后顺序不要动
unavailable_largefile_website_list_global = []
website_blacklist_global = ['fs.163.com', 'u.163.com']

thread_excepion_list_global = []

lock_print_global = threading.Lock()
lock_var_global = threading.Lock()
lock_io_global = threading.Lock()
debug_mode_global = __status__ == 1 or __status__ == 2
# 屏蔽调试信息
if not debug_mode_global:
    logging.disable(logging.DEBUG)
log_global = logging.getLogger('main_logger')
log_global.setLevel(logging.DEBUG)
log_file_handler_global = None
log_global.addHandler(logging.NullHandler())


class Date():
    year = 0
    month = 0
    day = 0
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
        return '{:0>2d}-{}-{:0>4d}'.format(self.day, _month_dict[self.month], self.year)


config_load_status_global = False
config_primary_data_global = {
    'program': {
        'silent_download_mode': False,
        'log': False
    },
    'mailbox': {
        'account': []
    },
    'search': {
        'folder': [],
        'search_mail_type': 1,
        'date': {
            'manual_input_search_date': True,
            'min_search_date': [],
            'max_search_date': []
        },
        'filter': {
            'sender_name': [],
            'sender_address': [],
            'subject': []
        }
    },
    'download': {
        'reconnect_max_times': 3,
        'rollback_when_download_failed': True,
        'sign_unseen_flag_after_downloading': True,
        'thread_count': 4,
        'display': {
            'mailbox': True,
            'subject_and_time': True,
            'mime_type': False
        },
        'path': {
            'default_path': '',
            'mime_type_classfication': [],
            'file_name_classfication': []
        }
    }
}


def init(func):
    def wrapper():
        global download_stop_flag_global
        global has_thread_status_changed_global
        global imap_list_global, imap_succeed_index_list_global, imap_connect_failed_index_list_global, imap_with_undownloadable_attachments_index_list_global, imap_overdueanddeleted_index_list_global, imap_fetch_failed_index_list_global, imap_download_failed_index_list_global
        global msg_processed_count_global, msg_list_global, msg_with_undownloadable_attachments_list_global, msg_overdueanddeleted_list_global, msg_fetch_failed_list_global, msg_download_failed_list_global
        global send_time_with_undownloadable_attachments_list_global, send_time_overdueanddeleted_list_global, send_time_download_failed_list_global
        global subject_with_undownloadable_attachments_list_global, subject_overdueanddeleted_list_global, subject_download_failed_list_global
        global file_download_count_global, file_download_path_global
        global largefile_undownloadable_link_list_global
        global largefile_undownloadable_code_list_global
        download_stop_flag_global = 0
        has_thread_status_changed_global = True

        imaplib.Commands['ID'] = ('AUTH')
        imap_list_global = []
        imap_succeed_index_list_global = []
        imap_connect_failed_index_list_global = []
        imap_with_undownloadable_attachments_index_list_global = []
        imap_overdueanddeleted_index_list_global = []
        imap_fetch_failed_index_list_global = []
        imap_download_failed_index_list_global = []

        msg_processed_count_global = 0
        msg_list_global = []
        msg_with_undownloadable_attachments_list_global = []
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
        file_download_path_global = []
        largefile_undownloadable_link_list_global = []  # 2级下载链接
        largefile_undownloadable_code_list_global = []
        for i in range(len(host_global)):
            msg_list_global.append([])
            msg_with_undownloadable_attachments_list_global.append([])
            msg_overdueanddeleted_list_global.append([])
            msg_fetch_failed_list_global.append([])
            msg_download_failed_list_global.append([])
            send_time_with_undownloadable_attachments_list_global.append([])
            send_time_overdueanddeleted_list_global.append([])
            send_time_download_failed_list_global.append([])
            subject_with_undownloadable_attachments_list_global.append([])
            subject_overdueanddeleted_list_global.append([])
            subject_download_failed_list_global.append([])
            file_download_path_global.append([])
            largefile_undownloadable_link_list_global.append([])
            largefile_undownloadable_code_list_global.append([])
            for _ in range(len(setting_search_folder_global[i])):
                msg_list_global[-1].append([])
                msg_with_undownloadable_attachments_list_global[-1].append([])
                msg_overdueanddeleted_list_global[-1].append([])
                msg_fetch_failed_list_global[-1].append([])
                msg_download_failed_list_global[-1].append([])
                send_time_with_undownloadable_attachments_list_global[-1].append([
                ])
                send_time_overdueanddeleted_list_global[-1].append([])
                send_time_download_failed_list_global[-1].append([])
                subject_with_undownloadable_attachments_list_global[-1].append([
                ])
                subject_overdueanddeleted_list_global[-1].append([])
                subject_download_failed_list_global[-1].append([])
                file_download_path_global[-1].append([])
                largefile_undownloadable_link_list_global[-1].append([])
                largefile_undownloadable_code_list_global[-1].append([])
        func()
    return wrapper


def check_config_load_status(func):
    def wrapper():
        if config_load_status_global:
            func()
        else:
            print('E: 未能成功加载配置,请在重新加载后执行该操作.', flush=True)
    return wrapper


def operation_load_config():
    global log_file_handler_global
    global host_global, address_global, password_global
    global setting_silent_download_mode_global
    global setting_search_folder_global
    global setting_search_mails_type_global
    global setting_manual_input_search_date_global
    global setting_min_search_date_global, setting_max_search_date_global
    global setting_filter_sender_global, setting_filter_sender_flag_global, setting_filter_subject_global, setting_filter_subject_flag_global
    global setting_download_thread_count_global
    global setting_rollback_when_download_failed_global
    global setting_sign_unseen_flag_after_downloading_global
    global setting_reconnect_max_times_global
    global setting_display_mailbox, setting_display_subject_and_time, setting_display_mime_type
    global setting_deafult_download_path_global, setting_mime_type_classfication_path_global, setting_file_name_classfication_path_global

    print('正在读取配置文件...', flush=True)
    try:
        if config_custom_path_global:
            config_path = os.path.join(os.getcwd(), config_custom_path_global)
        else:
            config_path = os.path.join(os.getcwd(), 'config.toml')
        with open(config_path, 'rb') as config_file:
            config_file_data = rtoml.load(
                bytes.decode(config_file.read(), 'UTF-8'))

            setting_silent_download_mode_global = config_file_data['program']['silent_download_mode']
            assert isinstance(setting_silent_download_mode_global, bool)

            log = config_file_data['program']['log']
            if log_file_handler_global != None:
                log_global.removeHandler(log_file_handler_global)
            if log != False:
                assert isinstance(log, dict) and isinstance(
                    log['path'], str) and isinstance(log['overwrite'], bool)
                log_write_type = 'w' if log['overwrite'] else 'a'
                log_path = os.path.join(os.getcwd(), log['path'])
                log_name = datetime.datetime.strftime(
                    datetime.datetime.now(), '%Y-%m-%d')+'.log'
                try:
                    if not os.path.exists(log_path):
                        os.makedirs(log_path)
                    log_file_handler_global = logging.FileHandler(
                        os.path.join(log_path, log_name), log_write_type, 'UTF-8')
                    log_file_handler_global.setLevel(logging.DEBUG)
                    log_file_handler_global.setFormatter(logging.Formatter(
                        '[%(asctime)s %(levelname)8s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
                    log_global.addHandler(log_file_handler_global)
                except OSError as e:
                    print('E: 日志文件创建错误.', flush=True)
                    raise e

            host_global = []
            address_global = []
            password_global = []
            account = config_file_data['mailbox']['account']
            assert isinstance(account, list)
            for account_splited in account:
                assert isinstance(account_splited, dict) and isinstance(account_splited['host'], str) and isinstance(
                    account_splited['address'], str) and isinstance(account_splited['password'], str)
                host_global.append(account_splited['host'])
                address_global.append(account_splited['address'])
                password_global.append(account_splited['password'])

            folder = config_file_data['search']['folder']
            assert isinstance(folder, list)
            for j in folder:
                assert isinstance(j, list)
            search_folder = operation_fetch_config_data1(
                folder, True, 'INBOX')[1]
            setting_search_folder_global = search_folder

            setting_search_mails_type_global = config_file_data['search']['search_mail_type']
            assert isinstance(setting_search_mails_type_global,
                              int) and 0 <= setting_search_mails_type_global <= 2

            setting_manual_input_search_date_global = config_file_data[
                'search']['date']['manual_input_search_date']
            assert isinstance(setting_manual_input_search_date_global, bool)

            setting_min_search_date_global = Date()
            min_search_date = config_file_data['search']['date']['min_search_date']
            assert isinstance(min_search_date, list)
            if len(min_search_date) > 0:
                assert isinstance(
                    min_search_date[0], int) and min_search_date[0] >= 1
                setting_min_search_date_global.enabled = True
                setting_min_search_date_global.year = min_search_date[0]
            if len(min_search_date) > 1:
                assert isinstance(
                    min_search_date[1], int) and 1 <= min_search_date[1] <= 12
                setting_min_search_date_global.enabled = True
                setting_min_search_date_global.month = min_search_date[1]
            if len(min_search_date) > 2:
                assert isinstance(
                    min_search_date[2], int) and 1 <= min_search_date[2] <= 31
                setting_min_search_date_global.enabled = True
                setting_min_search_date_global.day = min_search_date[2]

            setting_max_search_date_global = Date()
            max_search_date = config_file_data['search']['date']['max_search_date']
            assert isinstance(max_search_date, list)
            if len(max_search_date) > 0:
                assert isinstance(
                    max_search_date[0], int) and max_search_date[0] >= 1
                setting_max_search_date_global.enabled = True
                setting_max_search_date_global.year = max_search_date[0]
            if len(max_search_date) > 1:
                assert isinstance(
                    max_search_date[1], int) and 1 <= max_search_date[1] <= 12
                setting_max_search_date_global.enabled = True
                setting_max_search_date_global.month = max_search_date[1]
            if len(max_search_date) > 2:
                assert isinstance(
                    max_search_date[2], int) and 1 <= max_search_date[2] <= 31
                setting_max_search_date_global.enabled = True
                setting_max_search_date_global.day = max_search_date[2]

            setting_filter_sender_global = []
            setting_filter_sender_flag_global = []
            sender_name_raw = config_file_data['search']['filter']['sender_name']
            assert isinstance(sender_name_raw, list)
            setting_filter_sender_global.append([])
            setting_filter_sender_flag_global.append([])
            for sender_name_splited in sender_name_raw:
                assert isinstance(sender_name_splited, dict)
                sender_name_expression = sender_name_splited['exp']
                assert isinstance(sender_name_expression, list)
                sender_name_flag = sender_name_splited['flag']
                assert isinstance(sender_name_flag, list)
                filter_sender_name = operation_fetch_config_data1(
                    sender_name_expression)[1]
                filter_sender_name_flag = operation_fetch_config_data1(
                    sender_name_flag, False, '')[1]
                filter_sender_name_flag = operation_parse_regex_flag(
                    filter_sender_name_flag, filter_sender_name)
                assert operation_validate_regex(
                    filter_sender_name, filter_sender_name_flag)
                setting_filter_sender_global[-1].append(filter_sender_name)
                setting_filter_sender_flag_global[-1].append(
                    filter_sender_name_flag)

            sender_address_raw = config_file_data['search']['filter']['sender_address']
            assert isinstance(sender_address_raw, list)
            setting_filter_sender_global.append([])
            setting_filter_sender_flag_global.append([])
            for sender_address_splited in sender_address_raw:
                assert isinstance(sender_address_splited, dict)
                sender_address_expression = sender_address_splited['exp']
                assert isinstance(sender_address_expression, list)
                sender_address_flag = sender_address_splited['flag']
                assert isinstance(sender_address_flag, list)
                filter_sender_address = operation_fetch_config_data1(
                    sender_address_expression)[1]
                filter_sender_address_flag = operation_fetch_config_data1(
                    sender_address_flag, False, '')[1]
                filter_sender_address_flag = operation_parse_regex_flag(
                    filter_sender_address_flag, filter_sender_address)
                assert operation_validate_regex(
                    filter_sender_address, filter_sender_address_flag)
                setting_filter_sender_global[-1].append(filter_sender_address)
                setting_filter_sender_flag_global[-1].append(
                    filter_sender_address_flag)

            setting_filter_subject_global = []
            setting_filter_subject_flag_global = []
            subject_raw = config_file_data['search']['filter']['subject']
            assert isinstance(subject_raw, list)
            for subject_splited in subject_raw:
                assert isinstance(subject_splited, dict)
                subject_expression = subject_splited['exp']
                assert isinstance(subject_expression, list)
                subject_flag = subject_splited['flag']
                assert isinstance(subject_flag, list)
                filter_subject = operation_fetch_config_data1(subject_expression)[
                    1]
                filter_subject_flag = operation_fetch_config_data1(
                    subject_flag, False, '')[1]
                filter_subject_flag = operation_parse_regex_flag(
                    filter_subject_flag, filter_subject)
                assert operation_validate_regex(
                    filter_subject, filter_subject_flag)
                setting_filter_subject_global.append(filter_subject)
                setting_filter_subject_flag_global.append(filter_subject_flag)

            setting_download_thread_count_global = config_file_data['download']['thread_count']
            assert isinstance(setting_download_thread_count_global,
                              int) and setting_download_thread_count_global > 0

            setting_rollback_when_download_failed_global = config_file_data[
                'download']['rollback_when_download_failed']
            assert isinstance(
                setting_rollback_when_download_failed_global, bool)

            setting_sign_unseen_flag_after_downloading_global = config_file_data[
                'download']['sign_unseen_flag_after_downloading']
            assert isinstance(
                setting_sign_unseen_flag_after_downloading_global, bool)

            setting_reconnect_max_times_global = config_file_data['download']['reconnect_max_times']
            assert isinstance(setting_reconnect_max_times_global, int)

            assert isinstance(config_file_data['download']['display'], dict)
            setting_display_mailbox = config_file_data['download']['display']['mailbox']
            assert isinstance(setting_display_mailbox, bool)

            setting_display_subject_and_time = config_file_data[
                'download']['display']['subject_and_time']
            assert isinstance(setting_display_subject_and_time, bool)

            setting_display_mime_type = config_file_data['download']['display']['mime_type']
            assert isinstance(setting_display_mime_type, bool)

            default_download_path = os.path.join(
                os.getcwd(), config_file_data['download']['path']['default_path'])
            assert isinstance(default_download_path, str)
            try:
                if not os.path.exists(default_download_path):
                    os.makedirs(default_download_path)
            except OSError as e:
                print('E: 路径创建错误.', flush=True)
                raise e
            setting_deafult_download_path_global = default_download_path

            setting_mime_type_classfication_path_global = []
            mime_type_classfication_raw = config_file_data['download']['path']['mime_type_classfication']
            assert isinstance(mime_type_classfication_raw, list)
            if len(host_global):
                for mime_type_classfication_splited in mime_type_classfication_raw:
                    assert isinstance(mime_type_classfication_splited, dict) and isinstance(mime_type_classfication_splited['type'], dict) and isinstance(
                        mime_type_classfication_splited['path'], str) and isinstance(mime_type_classfication_splited['relative_to_download_path'], bool)
                    setting_mime_type_classfication_path_global.append([])
                    mime_type_classfication_splited_expression = mime_type_classfication_splited[
                        'type']['exp']
                    assert isinstance(
                        mime_type_classfication_splited_expression, list)
                    for j in mime_type_classfication_splited_expression:
                        assert isinstance(j, str)
                    mime_type_classfication_splited_expression = operation_fetch_config_data1(
                        mime_type_classfication_splited_expression)[1]
                    mime_type_classfication_splited_flag = mime_type_classfication_splited[
                        'type']['flag']
                    for j in mime_type_classfication_splited_flag:
                        assert isinstance(j, str)
                    mime_type_classfication_splited_flag = operation_fetch_config_data1(
                        mime_type_classfication_splited_flag, False, '')[1]
                    mime_type_classfication_splited_flag = operation_parse_regex_flag(
                        mime_type_classfication_splited_flag, mime_type_classfication_splited_expression)
                    assert operation_validate_regex(
                        mime_type_classfication_splited_expression, mime_type_classfication_splited_flag)
                    mime_type_classfication_splited_expression = mime_type_classfication_splited_expression[
                        0]
                    mime_type_classfication_splited_flag = mime_type_classfication_splited_flag[
                        0]
                    mime_type_classfication_splited_download_path = os.path.join(
                        default_download_path, mime_type_classfication_splited['path']) if mime_type_classfication_splited['relative_to_download_path'] else os.path.join(os.getcwd(), mime_type_classfication_splited['path'])
                    try:
                        if not os.path.exists(mime_type_classfication_splited_download_path):
                            os.makedirs(
                                mime_type_classfication_splited_download_path)
                    except OSError as e:
                        print('E: 路径创建错误.', flush=True)
                        raise e
                    setting_mime_type_classfication_path_global[-1].append(
                        mime_type_classfication_splited_expression)
                    setting_mime_type_classfication_path_global[-1].append(
                        mime_type_classfication_splited_flag)
                    setting_mime_type_classfication_path_global[-1].append(
                        mime_type_classfication_splited_download_path)

            setting_file_name_classfication_path_global = []
            file_name_classfication_raw = config_file_data['download']['path']['file_name_classfication']
            assert isinstance(file_name_classfication_raw, list)
            if len(host_global):
                for file_name_classfication_splited in file_name_classfication_raw:
                    assert isinstance(file_name_classfication_splited, dict) and isinstance(file_name_classfication_splited['name'], dict) and isinstance(file_name_classfication_splited['path'], str) and isinstance(
                        file_name_classfication_splited['extension'], bool) and isinstance(file_name_classfication_splited['relative_to_download_path'], bool)
                    setting_file_name_classfication_path_global.append([])
                    file_name_classfication_splited_expression = file_name_classfication_splited[
                        'name']['exp']
                    assert isinstance(
                        file_name_classfication_splited_expression, list)
                    for j in file_name_classfication_splited_expression:
                        assert isinstance(j, str)
                    file_name_classfication_splited_expression = operation_fetch_config_data1(
                        file_name_classfication_splited_expression)[1]
                    file_name_classfication_splited_flag = file_name_classfication_splited[
                        'name']['flag']
                    for j in file_name_classfication_splited_flag:
                        assert isinstance(j, str)
                    file_name_classfication_splited_flag = operation_fetch_config_data1(
                        file_name_classfication_splited_flag, False, '')[1]
                    file_name_classfication_splited_flag = operation_parse_regex_flag(
                        file_name_classfication_splited_flag, file_name_classfication_splited_expression)
                    assert operation_validate_regex(
                        file_name_classfication_splited_expression, file_name_classfication_splited_flag)
                    file_name_classfication_splited_expression = file_name_classfication_splited_expression[
                        0]
                    file_name_classfication_splited_flag = file_name_classfication_splited_flag[
                        0]
                    file_name_classfication_splited_download_path = os.path.join(
                        default_download_path, file_name_classfication_splited['path']) if file_name_classfication_splited['relative_to_download_path'] else os.path.join(os.getcwd(), file_name_classfication_splited['path'])
                    try:
                        if not os.path.exists(file_name_classfication_splited_download_path):
                            os.makedirs(
                                file_name_classfication_splited_download_path)
                    except OSError as e:
                        print('E: 路径创建错误.', flush=True)
                        raise e
                    setting_file_name_classfication_path_global[-1].append(
                        file_name_classfication_splited_expression)
                    setting_file_name_classfication_path_global[-1].append(
                        file_name_classfication_splited_flag)
                    setting_file_name_classfication_path_global[-1].append(
                        file_name_classfication_splited['extension'])
                    setting_file_name_classfication_path_global[-1].append(
                        file_name_classfication_splited_download_path)
    except Exception as e:
        if str(e):
            print('E: 读取配置文件时错误,信息如下:', flush=True)
            if debug_mode_global:
                traceback.print_exc()
            else:
                print(repr(e), flush=True)
        else:
            print('E: 读取配置文件时错误.', flush=True)
        return False
    else:
        print('配置加载成功.', flush=True)
        log_global.info('='*10+'开始记录'+'='*10)
        return True


def operation_fetch_config_data1(source, ignore_empty_str=True, *default):
    """整理配置中与邮箱一一对应的选项的数据,并添加默认选项."""
    target = [[], []]
    processed_count = 0
    for _, j in enumerate(source):
        if isinstance(j, list):
            if processed_count == len(host_global):
                continue
            target[1].append([])
            for j2 in j:
                assert isinstance(j2, str)
                if j2 or not ignore_empty_str:
                    target[1][-1].append(j2)
            if not len(target[1][-1]):
                target[1][-1] = target[0]
            processed_count += 1
        elif isinstance(j, str):
            if j or not ignore_empty_str:
                target[0].append(j)
        else:
            raise ValueError
    for _ in range(len(host_global)-processed_count):
        target[1].append(target[0])

    if not len(target[0]) and len(default):
        for j in default:
            target[0].append(j)
    return target


def operation_parse_regex_flag(source, compare):
    """将正则表达式标志项与表达式项对齐并转成数字形式."""
    target = []
    for i, j in enumerate(compare):
        target.append([])
        for i2 in range(min(len(source[i]), len(j))):
            target[-1].append(source[i][i2])
        for _ in range(len(j)-len(source[i])):
            target[-1].append('')
    for i, j in enumerate(target):
        for i2, j2 in enumerate(j):
            regex_flag = 0
            for j3 in j2:
                regex_flag |= int(_regex_flag_dict[j3])
            target[i][i2] = regex_flag
    return target


def operation_validate_regex(expression, flag):
    """验证正则表达式是否正确."""
    for i, j in enumerate(expression):
        for i2, j2 in enumerate(j):
            try:
                re.compile(j2, flag[i][i2])
            except re.error:
                return False
    return True


def operation_login_imap_server(host, address, password, display=True):
    is_login_succeed = False
    try:
        if display:
            print('\r正在连接 ', host,
                  ltk.indent(3), end='', sep='', flush=True)
        imap = imaplib.IMAP4_SSL(
            host)
        if display:
            print('\r已连接 ', host,
                  ltk.indent(3), sep='', end='', flush=True)
            print('\r正在登录 ', address, ltk.indent(3),
                  end='', sep='', flush=True)
        imap.login(address, password)
        if display:
            print('\r', address,
                  ' 登录成功', ltk.indent(3), sep='', flush=True)
            log_global.info('"'+address+'" 登录成功.')
        imap._simple_command(
            'ID', '("' + '" "'.join(authentication_global) + '")')  # 发送ID
    except imaplib.IMAP4.error:
        if display:
            print('\nE: 用户名或密码错误.', flush=True)
            log_global.error('"'+address+'" 登录失败.')
    except (socket.timeout, TimeoutError):
        if display:
            print('\nE: 服务器连接超时.', flush=True)
            log_global.error('"'+address+'" 登录失败.')
    except Exception:
        if display:
            print('\nE: 服务器连接错误.', flush=True)
            log_global.error('"'+address+'" 登录失败.')
    else:
        is_login_succeed = True
    if is_login_succeed:
        return imap
    else:
        return None


def operation_login_all_imapserver():
    for imap_index_int in range(len(host_global)):
        imap = operation_login_imap_server(
            host_global[imap_index_int], address_global[imap_index_int], password_global[imap_index_int])
        imap_list_global.append(imap)
        if imap != None:
            imap_succeed_index_list_global.append(imap_index_int)
        else:
            imap_connect_failed_index_list_global.append(imap_index_int)
    if len(host_global):
        if len(imap_succeed_index_list_global):
            print('已成功连接的邮箱:', flush=True)
            for imap_succeed_index_int in imap_succeed_index_list_global:
                print(
                    ltk.indent(1), address_global[imap_succeed_index_int], sep='')
            if len(imap_succeed_index_list_global) < len(host_global):
                print('E: 以下邮箱未能连接:', flush=True)
                for imap_connect_failed_index_int in imap_connect_failed_index_list_global:
                    print(ltk.indent(1), address_global[imap_connect_failed_index_int],
                          sep='', flush=True)
        else:
            print('E: 没有成功连接的邮箱.', flush=True)
    else:
        print('E: 没有邮箱.')


def operation_set_time():
    setting_min_search_date_global.enabled = False
    setting_max_search_date_global.enabled = False
    if ltk.input_option('是否设置检索开始日期?', 'y', 'n', default_option='y', end=':') == 'y':
        setting_min_search_date_global.enabled = True
        status = 0
        while True:
            try:
                if status == 0:
                    setting_min_search_date_global.year = int(ltk.input_option(
                        '输入年份', allow_undefind_input=True, default_option=str(datetime.datetime.now().year) if setting_min_search_date_global.year == 0 else str(setting_min_search_date_global.year), end=':'))
                    assert setting_min_search_date_global.year >= 1
                    status = 1
                elif status == 1:
                    setting_min_search_date_global.month = int(ltk.input_option(
                        '输入月份', allow_undefind_input=True, default_option=str(datetime.datetime.now().month) if setting_min_search_date_global.month == 0 else str(setting_min_search_date_global.month), end=':'))
                    assert 1 <= setting_min_search_date_global.month <= 12
                    status = 2
                elif status == 2:
                    setting_min_search_date_global.day = int(ltk.input_option(
                        '输入日期', allow_undefind_input=True, default_option=str(datetime.datetime.now().day) if setting_min_search_date_global.day == 0 else str(setting_min_search_date_global.day), end=':'))
                    assert 1 <= setting_min_search_date_global.day <= 31
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
    if ltk.input_option('是否设置检索截止日期?', 'y', 'n', default_option='n', end=':') == 'y':
        setting_max_search_date_global.enabled = True
        status = 0
        while True:
            try:
                if status == 0:
                    setting_max_search_date_global.year = int(ltk.input_option(
                        '输入年份', allow_undefind_input=True, default_option=str(datetime.datetime.now().year) if setting_max_search_date_global.year == 0 else str(setting_max_search_date_global.year), end=':'))
                    assert setting_max_search_date_global.year >= 1
                    status = 1
                elif status == 1:
                    setting_max_search_date_global.month = int(ltk.input_option(
                        '输入月份', allow_undefind_input=True, default_option=str(datetime.datetime.now().month) if setting_max_search_date_global.month == 0 else str(setting_max_search_date_global.month), end=':'))
                    assert 1 <= setting_max_search_date_global.month <= 12
                    status = 2
                elif status == 2:
                    setting_max_search_date_global.day = int(ltk.input_option(
                        '输入日期', allow_undefind_input=True, default_option=str(datetime.datetime.now().day) if setting_max_search_date_global.day == 0 else str(setting_max_search_date_global.day), end=':'))
                    assert 1 <= setting_max_search_date_global.day <= 31
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)


def operation_get_download_path(file_name_raw, mime_type):
    download_path = None
    for j in setting_mime_type_classfication_path_global:
        for i in range(len(j[0])):
            if len(re.compile(j[0][i], j[1][i]).findall(mime_type)):
                download_path = j[2]
    file_name_main, file_name_extension = operation_parse_file_name(
        file_name_raw)
    for j in setting_file_name_classfication_path_global:
        for i in range(len(j[0])):
            if len(re.compile(j[0][i], j[1][i]).findall(file_name_extension if j[2] else file_name_main)):
                download_path = j[3]
    if download_path == None:
        download_path = setting_deafult_download_path_global
    return download_path


def operation_parse_file_name(file_name_raw):
    file_name_main = ''
    file_name_extension = ''
    if '.' in file_name_raw:
        file_name_main = re.compile('.*(?=\.)').findall(file_name_raw)[0]
        file_name_extension = file_name_raw.replace(file_name_main+'.', '')
    else:
        file_name_main = file_name_raw
    return file_name_main, file_name_extension


def operation_fetch_file_name(file_name_raw, download_path):
    file_name = file_name_raw
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    if os.path.exists(os.path.join(download_path, file_name_raw)):
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
            if not os.path.exists(os.path.join(download_path, file_name)):
                break
            i += 1
    return file_name


def operation_rollback(file_name_list, file_download_path_list, file_name=None, largefile_name=None, file_download_path=None, largefile_download_path=None, file_name_tmp=None, largefile_name_tmp=None):
    global file_download_count_global
    if file_name:
        file_name_list.append(file_name)
        file_download_path_list.append(file_download_path)
    if largefile_name:
        file_name_list.append(largefile_name)
        file_download_path_list.append(largefile_download_path)
    if file_name_tmp:
        if os.path.isfile(os.path.join(file_download_path, file_name_tmp)):
            os.remove(os.path.join(
                file_download_path, file_name_tmp))
    if largefile_name_tmp:
        if os.path.isfile(os.path.join(largefile_download_path, largefile_name_tmp)):
            os.remove(os.path.join(
                largefile_download_path, largefile_name_tmp))
            log_global.error('已回滚 "'+os.path.join(
                largefile_download_path, largefile_name_tmp)+'"')
    for file_mixed_name_index_int in range(len(file_name_list)):
        if os.path.isfile(os.path.join(file_download_path_list[file_mixed_name_index_int], file_name_list[file_mixed_name_index_int])):
            os.remove(os.path.join(
                file_download_path_list[file_mixed_name_index_int], file_name_list[file_mixed_name_index_int]))
            with lock_var_global:
                file_download_count_global -= 1


@check_config_load_status
@init
def program_download_main():
    log_global.info('-'*8+'下载操作开始'+'-'*8)
    global thread_status_list_global  # 0:其他;1:读取邮件数据/获取链接;2:下载文件
    global has_thread_status_changed_global
    global thread_list_global, thread_file_name_list_global, thread_file_download_path_list_global
    global msg_list_global, msg_total_count_global, msg_processed_count_global
    operation_login_all_imapserver()
    if len(imap_succeed_index_list_global):
        if setting_manual_input_search_date_global:
            operation_set_time()
        setting_min_search_date_global.year = max(
            1, setting_min_search_date_global.year)
        setting_min_search_date_global.month = max(
            1, setting_min_search_date_global.month)
        setting_min_search_date_global.day = max(
            1, setting_min_search_date_global.day)
        setting_max_search_date_global.year = max(
            1, setting_max_search_date_global.year)
        setting_max_search_date_global.month = max(
            1, setting_max_search_date_global.month)
        setting_max_search_date_global.day = max(
            1, setting_max_search_date_global.day)
        prompt = ''
        if not (setting_min_search_date_global.enabled or setting_max_search_date_global.enabled):
            if setting_search_mails_type_global == 0:
                prompt = '检索全部邮件'
            elif setting_search_mails_type_global == 1:
                prompt = '仅检索未读邮件'
            else:
                prompt = '仅检索已读邮件'
        else:
            prompt += '仅检索日期'
            prompt += ('从 '+setting_min_search_date_global.time()
                       ) if setting_min_search_date_global.enabled else '在 ' if setting_max_search_date_global else ''
            prompt += ' 开始' if setting_min_search_date_global.enabled and not setting_max_search_date_global.enabled else (str(
                setting_max_search_date_global.time()+' 截止')) if not setting_min_search_date_global.enabled and setting_max_search_date_global.enabled else ' 到 '
            prompt += setting_max_search_date_global.time(
            ) if setting_min_search_date_global.enabled and setting_max_search_date_global.enabled else ''
            prompt += '的邮件' if setting_search_mails_type_global == 0 else '的未读邮件' if setting_search_mails_type_global == 1 else '的已读邮件'
        print(prompt, sep='', flush=True)
        log_global.info(prompt)
        for imap_index_int, imap_index in enumerate(imap_succeed_index_list_global):
            print('正在搜索... (', imap_index_int+1, '/',
                  len(imap_succeed_index_list_global), ')', sep='', end='', flush=True)
            search_command = ''
            search_command += ('since '+setting_min_search_date_global.time()
                               ) if setting_min_search_date_global.enabled else ''
            search_command += ' ' if setting_min_search_date_global.enabled and setting_max_search_date_global.enabled else ''
            search_command += ('before ' + setting_max_search_date_global.time()
                               ) if setting_max_search_date_global.enabled else ''
            search_command += ' ' if setting_max_search_date_global.enabled or setting_min_search_date_global.enabled else ''
            search_command += 'ALL' if setting_search_mails_type_global == 0 else 'UNSEEN' if setting_search_mails_type_global == 1 else 'SEEN'
            for folder_index_int in range(len(setting_search_folder_global[imap_index])):
                folder_raw = setting_search_folder_global[
                    imap_index][folder_index_int]
                folder = b'"'+ltk.imap_utf7_bytes_encode(folder_raw)+b'"'
                search_status_last = False
                for _ in range(setting_reconnect_max_times_global+1):
                    try:
                        select_status, _ = imap_list_global[imap_index].select(
                            folder)
                        search_status_last = True
                        break
                    except Exception:
                        for _ in range(setting_reconnect_max_times_global):
                            imap_list_global[imap_index] = operation_login_imap_server(
                                host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                            if imap_list_global[imap_index] != None:
                                imap_list_global[imap_index].select(
                                    folder)
                                break
                if not search_status_last or select_status == 'NO':
                    print('\rE: 邮箱', address_global[imap_index],
                          '的收件箱', folder_raw, '选择失败,已跳过.', ltk.indent(3), flush=True)
                    log_global.error(
                        '邮箱 "'+address_global[imap_index]+'" 的收件箱 "' + folder_raw + '" 选择失败.')
                    continue
                search_status_last = False
                for _ in range(setting_reconnect_max_times_global+1):
                    try:
                        _, msg_data_index_raw = imap_list_global[imap_index].search(
                            None, search_command)
                        search_status_last = True
                        break
                    except Exception:
                        for _ in range(setting_reconnect_max_times_global):
                            imap_list_global[imap_index] = operation_login_imap_server(
                                host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                            if imap_list_global[imap_index] != None:
                                imap_list_global[imap_index].select(
                                    folder)
                                break
                if not search_status_last:
                    print('\rE: 邮箱', address_global[imap_index],
                          '的收件箱', folder_raw, '搜索失败,已跳过.', ltk.indent(3), flush=True)
                    log_global.error(
                        '邮箱 "'+address_global[imap_index]+'" 的收件箱 "' + folder_raw + '" 搜索失败.')
                    if not ltk.safe_list_find(imap_connect_failed_index_list_global, imap_index):
                        imap_connect_failed_index_list_global.append(
                            imap_index)
                    continue
                msg_list = list(reversed(msg_data_index_raw[0].split()))
                msg_list_global[imap_index][folder_index_int] = msg_list
            print(
                '\r邮箱: ', address_global[imap_index], ltk.indent(3), sep='', flush=True)
            print(ltk.indent(1), '搜索到 ', len(ltk.extract_nested_list(
                msg_list_global[imap_index])), ' 封邮件', sep='', flush=True)
            log_global.info(
                '邮箱: "' + address_global[imap_index]+'"')
            log_global.info(ltk.indent(1)+'搜索到 ' + str(len(ltk.extract_nested_list(
                msg_list_global[imap_index]))) + ' 封邮件')
        if len(ltk.extract_nested_list(msg_list_global)):
            print('共 ', len(ltk.extract_nested_list(msg_list_global)),
                  ' 封邮件', sep='', flush=True)
            log_global.info(
                '共 '+str(len(ltk.extract_nested_list(msg_list_global)))+' 封邮件')
            start_time = time.time()
            print('开始处理...', flush=True)
            log_global.info('开始处理...')
            if len(ltk.extract_nested_list(setting_filter_sender_global)) or len(ltk.extract_nested_list(setting_filter_subject_global)):
                print('N: 过滤器已开启.', flush=True)
                log_global.info('过滤器已开启.')
            msg_total_count_global = len(
                ltk.extract_nested_list(msg_list_global))
            thread_list_global = []
            thread_status_list_global = []  # -1: 关闭;0: 空闲;1: 处理数据;2: 下载附件
            thread_file_name_list_global = []
            thread_file_download_path_list_global = []
            for thread_id in range(setting_download_thread_count_global):
                thread_status_list_global.append(0)
                thread_file_name_list_global.append([])
                thread_file_download_path_list_global.append([])
                thread = threading.Thread(
                    target=download_thread_func, args=(thread_id,), daemon=True)
                thread_list_global.append(thread)
                thread.start()
            while True:
                if download_stop_flag_global:
                    return
                if thread_status_list_global.count(-1) == len(thread_status_list_global):
                    break
                if len(thread_excepion_list_global):
                    with lock_var_global:
                        raise thread_excepion_list_global.pop(0)
                if has_thread_status_changed_global:
                    has_thread_status_changed_global = False
                    with lock_print_global:
                        print('\r已处理 (', msg_processed_count_global, '/',
                              msg_total_count_global, '),', sep='', end='', flush=True)
                        print('线程信息 (', len(thread_status_list_global)-thread_status_list_global.count(-1), '/', len(thread_list_global), ',',
                              thread_status_list_global.count(1), ',', thread_status_list_global.count(2), ')', ltk.indent(3), sep='', end='', flush=True)
                time.sleep(0)
            finish_time = time.time()
            with lock_print_global:
                if file_download_count_global > 0:
                    print('\r共下载 ', file_download_count_global,
                          ' 个附件', ltk.indent(8), sep='', flush=True)
                    log_global.info(
                        '共下载 '+str(file_download_count_global)+' 个附件')
                else:
                    print('\r没有可下载的附件.', ltk.indent(8), flush=True)
                    log_global.info('没有可下载的附件.')
                print('耗时: ', round(finish_time-start_time, 2),
                      ' 秒', ltk.indent(8), sep='', flush=True)
                log_global.info(
                    '耗时: '+str(round(finish_time-start_time, 2)) + ' 秒')

                if len(imap_connect_failed_index_list_global):
                    print('E: 以下邮箱连接失败:', flush=True)
                    log_global.error('以下邮箱连接失败:')
                    for imap_connect_failed_index in imap_connect_failed_index_list_global:
                        print(
                            ltk.indent(1), address_global[imap_connect_failed_index], sep='', flush=True)
                        log_global.error(ltk.indent(1)+'"' +
                                         address_global[imap_connect_failed_index]+'"')
                for imap_index, msg_list_global_splited in enumerate(msg_list_global):
                    for folder_index_int, msg_list_global_splited2 in enumerate(msg_list_global_splited):
                        if len(msg_list_global_splited2) > 0:
                            if ltk.safe_list_find(imap_fetch_failed_index_list_global, imap_index) == -1:
                                imap_fetch_failed_index_list_global.append(
                                    imap_index)
                            msg_fetch_failed_list_global[imap_index][
                                folder_index_int] += msg_list_global_splited2
                if len(imap_fetch_failed_index_list_global):
                    print('E: 以下邮件处理失败,请尝试重新下载:', flush=True)
                    log_global.error('以下邮件处理失败,请尝试重新下载:')
                    for imap_fetch_failed_index in imap_fetch_failed_index_list_global:
                        print(ltk.indent(
                            1), '邮箱: ', address_global[imap_fetch_failed_index], sep='', flush=True)
                        print(ltk.indent(2), len(ltk.extract_nested_list(
                            msg_fetch_failed_list_global[imap_fetch_failed_index])), ' 封邮件处理失败', sep='', flush=True)
                        log_global.error(ltk.indent(1)+'邮箱: "' +
                                         address_global[imap_fetch_failed_index]+'"')
                        log_global.error(ltk.indent(2)+str(len(ltk.extract_nested_list(
                            msg_fetch_failed_list_global[imap_fetch_failed_index])))+' 封邮件处理失败')
                if len(ltk.extract_nested_list(msg_download_failed_list_global)):
                    msg_download_failed_counted_count = 0
                    print('E: 以下邮件有附件下载失败,请尝试手动下载:', flush=True)
                    log_global.error('以下邮件有附件下载失败,请尝试手动下载:')
                    for imap_download_failed_index in imap_download_failed_index_list_global:
                        print(ltk.indent(
                            1), '邮箱: ', address_global[imap_download_failed_index], sep='', flush=True)
                        log_global.error(ltk.indent(
                            1) + '邮箱: "' + address_global[imap_download_failed_index]+'"')
                        for folder_index_int, msg_download_failed_list_global_splited in enumerate(msg_download_failed_list_global[imap_download_failed_index]):
                            if not len(msg_download_failed_list_global_splited):
                                continue
                            print(ltk.indent(
                                2), '文件夹: ', setting_search_folder_global[imap_download_failed_index][folder_index_int], sep='', flush=True)
                            log_global.error(ltk.indent(
                                2) + '文件夹: "' + setting_search_folder_global[imap_download_failed_index][folder_index_int]+'"')
                            for subject_index_int, subject in enumerate(subject_download_failed_list_global[imap_download_failed_index][folder_index_int]):
                                print(ltk.indent(3), msg_download_failed_counted_count+1, ' 标题-时间: ',
                                      subject, ' - ', send_time_download_failed_list_global[imap_download_failed_index][folder_index_int][subject_index_int], sep='', flush=True)
                                log_global.error(ltk.indent(3) + str(msg_download_failed_counted_count+1) + ' 标题: "' +
                                                 subject_download_failed_list_global[imap_download_failed_index][folder_index_int][subject_index_int]+'"')
                                log_global.error(ltk.indent(
                                    4)+'时间: '+send_time_download_failed_list_global[imap_download_failed_index][folder_index_int][subject_index_int])
                                msg_download_failed_counted_count += 1
                if len(ltk.extract_nested_list(msg_with_undownloadable_attachments_list_global)):
                    msg_with_undownloadable_attachments_counted_count = 0
                    largefile_undownloadable_link_counted_count = 0
                    print('W: 以下邮件的超大附件无法直接下载,但仍可获取链接,请尝试手动下载:', flush=True)
                    log_global.warning('以下邮件的超大附件无法直接下载,但仍可获取链接,请尝试手动下载:')
                    for imap_with_undownloadable_attachments_index in imap_with_undownloadable_attachments_index_list_global:
                        print(ltk.indent(
                            1), '邮箱: ', address_global[imap_with_undownloadable_attachments_index], sep='', flush=True)
                        log_global.warning(ltk.indent(
                            1) + '邮箱: "' + address_global[imap_with_undownloadable_attachments_index]+'"')
                        for folder_index_int, msg_with_undownloadable_attachments_list_global_splited in enumerate(msg_with_undownloadable_attachments_list_global[imap_with_undownloadable_attachments_index]):
                            if not len(msg_with_undownloadable_attachments_list_global_splited):
                                continue
                            print(ltk.indent(
                                2), '文件夹: ', setting_search_folder_global[imap_with_undownloadable_attachments_index][folder_index_int], sep='', flush=True)
                            log_global.warning(ltk.indent(
                                2) + '文件夹: "' + setting_search_folder_global[imap_with_undownloadable_attachments_index][folder_index_int]+'"')
                            for subject_index_int, subject in enumerate(subject_with_undownloadable_attachments_list_global[imap_with_undownloadable_attachments_index][folder_index_int]):
                                print(ltk.indent(3), msg_with_undownloadable_attachments_counted_count+1, ' 标题-时间: ',
                                      subject, ' - ', send_time_with_undownloadable_attachments_list_global[imap_with_undownloadable_attachments_index][folder_index_int][subject_index_int], sep='', flush=True)
                                log_global.warning(ltk.indent(3) + str(msg_with_undownloadable_attachments_counted_count+1) + ' 标题: "' +
                                                   subject+'"')
                                log_global.warning(ltk.indent(
                                    4)+'时间: '+send_time_with_undownloadable_attachments_list_global[imap_with_undownloadable_attachments_index][folder_index_int][subject_index_int])
                                for link_index_int, link in enumerate(largefile_undownloadable_link_list_global[imap_with_undownloadable_attachments_index][folder_index_int][subject_index_int]):
                                    print(ltk.indent(
                                        4), largefile_undownloadable_link_counted_count+1, ' 链接: ', link, sep='', flush=True)
                                    log_global.warning(ltk.indent(
                                        4) + str(largefile_undownloadable_link_counted_count+1) + ' 链接: "' + link+'"')
                                    largefile_download_code = largefile_undownloadable_code_list_global[
                                        imap_with_undownloadable_attachments_index][folder_index_int][subject_index_int][link_index_int]
                                    if largefile_download_code != 0:
                                        print(ltk.indent(5), '错误代码: ',
                                              largefile_download_code, sep='', flush=True)
                                        log_global.warning(ltk.indent(5) + '错误代码: ' +
                                                           str(largefile_download_code))
                                        if largefile_download_code == 602 or largefile_download_code == -4:
                                            print(ltk.indent(5), '原因: 文件下载次数达到最大限制.',
                                                  sep='', flush=True)
                                            log_global.warning(
                                                ltk.indent(5) + '原因: 文件下载次数达到最大限制.')
                                    largefile_undownloadable_link_counted_count += 1
                                msg_with_undownloadable_attachments_counted_count += 1
                    if setting_sign_unseen_flag_after_downloading_global and setting_search_mails_type_global != 2:
                        if setting_silent_download_mode_global or ltk.input_option('要将以上邮件设为已读吗?', 'y', 'n', default_option='n', end=':') == 'y':
                            msg_with_downloadable_attachments_signed_count = 0
                            print('\r正在标记...', end='', flush=True)
                            for imap_index in imap_with_undownloadable_attachments_index_list_global:
                                for folder_index_int, msg_with_undownloadable_attachments_list_global_splited in enumerate(msg_with_undownloadable_attachments_list_global[imap_index]):
                                    if not len(msg_with_undownloadable_attachments_list_global_splited):
                                        continue
                                    folder = b'"'+ltk.imap_utf7_bytes_encode(
                                        setting_search_folder_global[imap_index][folder_index_int])+b'"'
                                    for _ in range(setting_reconnect_max_times_global+1):
                                        try:
                                            imap_list_global[imap_index].select(
                                                folder)
                                            break
                                        except Exception:
                                            for _ in range(setting_reconnect_max_times_global):
                                                imap_list_global[imap_index] = operation_login_imap_server(
                                                    host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                                                if imap_list_global[imap_index] != None:
                                                    break
                                    for msg_index in msg_with_undownloadable_attachments_list_global_splited:
                                        for _ in range(setting_reconnect_max_times_global+1):
                                            try:
                                                imap_list_global[imap_index].store(msg_index,
                                                                                   'flags', '\\SEEN')
                                                break
                                            except Exception:
                                                pass
                                        msg_with_downloadable_attachments_signed_count += 1
                            print('\r', ltk.indent(6),
                                  sep='', end='', flush=True)
                            if not len(ltk.extract_nested_list(msg_overdueanddeleted_list_global)):
                                print(flush=True)
                        else:
                            if not len(ltk.extract_nested_list(msg_overdueanddeleted_list_global)):
                                print(flush=True)
                    else:
                        if not len(ltk.extract_nested_list(msg_overdueanddeleted_list_global)):
                            print(flush=True)
                else:
                    if not len(ltk.extract_nested_list(msg_overdueanddeleted_list_global)):
                        print(flush=True)
                if len(ltk.extract_nested_list(msg_overdueanddeleted_list_global)):
                    msg_overdueanddeleted_counted_count = 0
                    print('\rN: 以下邮件的超大附件全部过期或被删除:', flush=True)
                    log_global.info('以下邮件的超大附件全部过期或被删除:')
                    for imap_overdueanddeleted_index in imap_overdueanddeleted_index_list_global:
                        print(ltk.indent(
                            1), '邮箱: ', address_global[imap_overdueanddeleted_index], sep='', flush=True)
                        log_global.info(ltk.indent(
                            1) + '邮箱: "' + address_global[imap_overdueanddeleted_index]+'"')
                        for folder_index_int, msg_overdueanddeleted_list_global_splited in enumerate(msg_overdueanddeleted_list_global[imap_overdueanddeleted_index]):
                            if not len(msg_overdueanddeleted_list_global_splited):
                                continue
                            print(ltk.indent(
                                2), '文件夹: ', setting_search_folder_global[imap_overdueanddeleted_index][folder_index_int], sep='', flush=True)
                            log_global.info(ltk.indent(
                                2) + '文件夹: "' + setting_search_folder_global[imap_overdueanddeleted_index][folder_index_int]+'"')
                            for subject_index_int, subject in enumerate(subject_overdueanddeleted_list_global[imap_overdueanddeleted_index][folder_index_int]):
                                print(ltk.indent(3), msg_overdueanddeleted_counted_count+1, ' 标题-时间: ',
                                      subject, ' - ', send_time_overdueanddeleted_list_global[imap_overdueanddeleted_index][folder_index_int][subject_index_int], sep='', flush=True)
                                log_global.info(ltk.indent(3) + str(msg_overdueanddeleted_counted_count+1) + ' 标题: "' +
                                                subject+'"')
                                log_global.warning(ltk.indent(
                                    4)+'时间: '+send_time_overdueanddeleted_list_global[imap_overdueanddeleted_index][folder_index_int][subject_index_int])
                                msg_overdueanddeleted_counted_count += 1
                    if setting_sign_unseen_flag_after_downloading_global and setting_search_mails_type_global != 2:
                        if setting_silent_download_mode_global or ltk.input_option('要将以上邮件设为已读吗?', 'y', 'n', default_option='y', end=':') == 'y':
                            print('\r正在标记...', end='', flush=True)
                            for imap_index in imap_overdueanddeleted_index_list_global:
                                for folder_index_int, msg_overdueanddeleted_list_global_splited in enumerate(msg_overdueanddeleted_list_global[imap_index]):
                                    if not len(msg_overdueanddeleted_list_global_splited):
                                        continue
                                    folder = b'"'+ltk.imap_utf7_bytes_encode(
                                        setting_search_folder_global[imap_index][folder_index_int])+b'"'
                                    for _ in range(setting_reconnect_max_times_global+1):
                                        try:
                                            imap_list_global[imap_index].select(
                                                folder)
                                            break
                                        except Exception:
                                            for _ in range(setting_reconnect_max_times_global):
                                                imap_list_global[imap_index] = operation_login_imap_server(
                                                    host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                                                if imap_list_global[imap_index] != None:
                                                    break
                                    for msg_index in msg_overdueanddeleted_list_global_splited:
                                        for _ in range(setting_reconnect_max_times_global+1):
                                            try:
                                                imap_list_global[imap_index].store(msg_index,
                                                                                   'flags', '\\SEEN')
                                                break
                                            except Exception:
                                                pass
                            print('\r', ltk.indent(6), sep='', flush=True)
                        else:
                            print(flush=True)
                    else:
                        print(flush=True)
        else:
            print('没有符合条件的邮件.\n', flush=True)
            log_global.info('没有符合条件的邮件.')
    else:
        print('E: 无法执行该操作.原因: 没有可用邮箱.', flush=True)
        log_global.error('下载 操作无法执行. 原因: 没有可用邮箱.')
    log_global.info('-'*8+'下载操作完成'+'-'*8)


def operation_fresh_thread_status(thread_id, status):
    global has_thread_status_changed_global
    thread_status_list_global[thread_id] = status
    has_thread_status_changed_global = True


def download_thread_func(thread_id):
    global file_download_count_global, msg_processed_count_global, msg_list_global
    global thread_file_name_list_global, thread_file_download_path_list_global
    try:
        for imap_index in imap_succeed_index_list_global:
            if not len(msg_list_global[imap_index]):
                continue
            req_status_last = False
            for _ in range(setting_reconnect_max_times_global+1):
                imap = operation_login_imap_server(
                    host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                if imap != None:
                    break
            if imap == None:
                continue
            for folder_index_int in range(len(setting_search_folder_global[imap_index])):
                if not len(msg_list_global[imap_index][folder_index_int]):
                    continue
                folder_raw = setting_search_folder_global[
                    imap_index][folder_index_int]
                folder = b'"'+ltk.imap_utf7_bytes_encode(folder_raw)+b'"'
                select_status = False
                for _ in range(setting_reconnect_max_times_global+1):
                    try:
                        imap.select(folder)
                        select_status = True
                        break
                    except Exception:
                        for _ in range(setting_reconnect_max_times_global):
                            imap = operation_login_imap_server(
                                host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                            if imap != None:
                                break
                if not select_status:
                    with lock_print_global:
                        print('\rE: 邮箱', address_global[imap_index],
                              '的文件夹', folder_raw, '选择失败,已跳过.', ltk.indent(4), flush=True)
                        log_global.error(
                            '邮箱 "'+address_global[imap_index]+'" 的文件夹 "'+folder_raw+'" 选择失败.')
                    continue
                while True:
                    lock_var_global.acquire()
                    if len(msg_list_global[imap_index][folder_index_int]):
                        msg_index = msg_list_global[imap_index][folder_index_int].pop(
                            0)
                        lock_var_global.release()
                        file_download_count = 0
                        # -2:下载失败;-1:无附件且处理正常;0:有附件且处理正常;1:有无法直接下载的附件;2:附件全部过期或不存在;3:过滤器不通过
                        download_status_last = -1
                        thread_file_name_list_global[thread_id] = []
                        thread_file_download_path_list_global[thread_id] = []
                        largefile_undownloadable_code_list = []
                        has_downloadable_attachment = False
                        largefile_downloadable_link_list = []
                        largefile_download_code = 0
                        largefile_undownloadable_link_list = []
                        with lock_var_global:
                            operation_fresh_thread_status(thread_id, 1)
                        filter_status_last = [True, True, True]
                        fetch_status_last = True
                        if len(ltk.extract_nested_list(setting_filter_sender_global)) or len(ltk.extract_nested_list(setting_filter_subject_global)):
                            fetch_status_last = False
                            for _ in range(setting_reconnect_max_times_global+1):
                                try:
                                    header_data = email.message_from_bytes(
                                        imap.fetch(msg_index, 'BODY.PEEK[HEADER]')[1][0][1])
                                    sender_name, sender_address = utils.parseaddr(str(header.make_header(
                                        header.decode_header(header_data.get('From')))))
                                    subject = str(header.make_header(
                                        header.decode_header(header_data.get('Subject'))))
                                    for i in range(max(len(setting_filter_sender_global[0]), len(setting_filter_sender_global[1]), len(setting_filter_subject_global))):
                                        filter_status_last = [
                                            True, True, True]
                                        if i < len(setting_filter_sender_global[0]) and len(ltk.extract_nested_list(setting_filter_sender_global[0][i][imap_index])):
                                            filter_status_last[0] = False
                                            for filter_sender_name_index_int, filter_sender_name in enumerate(setting_filter_sender_global[0][i][imap_index]):
                                                if len(re.compile(filter_sender_name, setting_filter_sender_flag_global[0][i][imap_index][filter_sender_name_index_int]).findall(sender_name)):
                                                    filter_status_last[0] = True
                                                    break
                                        if i < len(setting_filter_sender_global[1]) and len(ltk.extract_nested_list(setting_filter_sender_global[1][i][imap_index])):
                                            filter_status_last[1] = False
                                            for filter_sender_address_index_int, filter_sender_address in enumerate(setting_filter_sender_global[1][i][imap_index]):
                                                if len(re.compile(filter_sender_address, setting_filter_sender_flag_global[1][i][imap_index][filter_sender_address_index_int]).findall(sender_address)):
                                                    filter_status_last[1] = True
                                                    break
                                        if i < len(setting_filter_subject_global) and len(ltk.extract_nested_list(setting_filter_subject_global[i][imap_index])):
                                            filter_status_last[2] = False
                                            for filter_subject_index_int, filter_subject in enumerate(setting_filter_subject_global[i][imap_index]):
                                                if len(re.compile(filter_subject, setting_filter_subject_flag_global[i][imap_index][filter_subject_index_int]).findall(subject)):
                                                    filter_status_last[2] = True
                                                    break
                                        if not False in filter_status_last:
                                            break
                                    fetch_status_last = True
                                    break
                                except Exception:
                                    pass
                        if not fetch_status_last:
                            with lock_print_global:
                                print(
                                    '\rE: 邮箱', address_global[imap_index], '有邮件数据获取失败,已跳过.', ltk.indent(4), flush=True)
                                log_global.error(
                                    '邮箱 "'+address_global[imap_index]+'" 有邮件数据获取失败.')
                        else:
                            if False in filter_status_last:
                                download_status_last = 3
                            else:
                                with lock_var_global:
                                    operation_fresh_thread_status(thread_id, 1)
                                fetch_status_last = False
                                for _ in range(setting_reconnect_max_times_global+1):
                                    try:
                                        _, msg_data_raw = imap.fetch(
                                            msg_index, 'BODY.PEEK[]')
                                        fetch_status_last = True
                                        break
                                    except Exception:
                                        for _ in range(setting_reconnect_max_times_global):
                                            try:
                                                imap = operation_login_imap_server(
                                                    host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                                                if imap != None:
                                                    imap.select(folder)
                                                    break
                                            except Exception:
                                                pass
                                if not fetch_status_last:
                                    with lock_print_global:
                                        print(
                                            '\rE: 邮箱', address_global[imap_index], '有邮件数据获取失败,已跳过.', ltk.indent(4), flush=True)
                                        log_global.error(
                                            '邮箱 "'+address_global[imap_index]+'" 有邮件数据获取失败.')
                                else:
                                    msg_data = email.message_from_bytes(
                                        msg_data_raw[0][1])
                                    subject = str(header.make_header(
                                        header.decode_header(msg_data.get('Subject')))).replace('\n', '')
                                    send_time_raw = msg_data.get('Date')
                                    if send_time_raw != None:
                                        send_time_raw = str(header.make_header(
                                            header.decode_header(send_time_raw)))[5:]
                                        send_time = copy.copy(send_time_raw)
                                        try:
                                            send_time = str(utils.parsedate_to_datetime(
                                                send_time_raw).astimezone(pytz.timezone('Etc/GMT-8')))[:-6]
                                        except ValueError:
                                            send_time = send_time_raw
                                    else:
                                        send_time = '(无法获取时间)'
                                    try:
                                        for msg_data_splited in msg_data.walk():
                                            file_name = None
                                            largefile_name = None
                                            file_download_path = None
                                            largefile_download_path = None
                                            file_name_tmp = None
                                            largefile_name_tmp = None
                                            if msg_data_splited.get_content_disposition() and 'attachment' in msg_data_splited.get_content_disposition():
                                                mime_type = msg_data_splited.get_content_type()
                                                has_downloadable_attachment = True
                                                file_name_raw = str(header.make_header(
                                                    header.decode_header(msg_data_splited.get_filename())))
                                                file_data = msg_data_splited.get_payload(
                                                    decode=True)
                                                if file_data != None:
                                                    with lock_var_global:
                                                        operation_fresh_thread_status(
                                                            thread_id, 2)
                                                    if download_stop_flag_global:
                                                        if setting_rollback_when_download_failed_global:
                                                            with lock_io_global:
                                                                operation_rollback(
                                                                    thread_file_name_list_global[thread_id], thread_file_download_path_list_global[thread_id], file_name, largefile_name, file_download_path, largefile_download_path, file_name_tmp, largefile_name_tmp)
                                                        return
                                                    lock_io_global.acquire()
                                                    file_download_path = operation_get_download_path(
                                                        file_name_raw, mime_type)
                                                    file_name_tmp = operation_fetch_file_name(
                                                        file_name_raw+'.tmp', file_download_path)
                                                    with open(os.path.join(file_download_path, file_name_tmp), 'wb') as file:
                                                        lock_io_global.release()
                                                        file.write(file_data)
                                                    with lock_io_global:
                                                        file_name = operation_fetch_file_name(
                                                            file_name_raw, file_download_path)
                                                        os.renames(os.path.join(file_download_path, file_name_tmp),
                                                                   os.path.join(file_download_path, file_name))
                                                    if download_stop_flag_global:
                                                        if setting_rollback_when_download_failed_global:
                                                            with lock_io_global:
                                                                operation_rollback(
                                                                    thread_file_name_list_global[thread_id], thread_file_download_path_list_global[thread_id], file_name, largefile_name, file_download_path, largefile_download_path, file_name_tmp, largefile_name_tmp)
                                                        return
                                                    with lock_print_global, lock_var_global:
                                                        print('\r', file_download_count_global+1, ' 已下载 ', file_name, (
                                                            ' <- '+file_name_raw)if file_name != file_name_raw else '', ltk.indent(8), sep='', flush=True)
                                                        log_global.info(str(file_download_count_global+1)+' 已下载 "' + file_name + ((
                                                            '" <- "'+file_name_raw+'"')if file_name != file_name_raw else '"'))
                                                        if setting_display_mailbox:
                                                            print(ltk.indent(
                                                                1), '邮箱: ', address_global[imap_index], sep='', flush=True)
                                                            log_global.info(ltk.indent(
                                                                1)+'邮箱: "'+address_global[imap_index]+'"')
                                                        if setting_display_subject_and_time:
                                                            print(ltk.indent(1), '标题-时间: ', subject, ' - ',
                                                                  send_time, sep='', flush=True)
                                                            log_global.info(
                                                                ltk.indent(1)+'标题: "'+subject+'"')
                                                            log_global.info(
                                                                ltk.indent(1)+'时间: '+send_time)
                                                        if setting_display_mime_type:
                                                            print(ltk.indent(1), 'MIME-TYPE: ',
                                                                  mime_type, sep='', flush=True)
                                                            log_global.info(
                                                                ltk.indent(1)+'MIME-TYPE: "'+mime_type+'"')
                                                        file_download_count_global += 1
                                                        file_download_count += 1
                                                        thread_file_name_list_global[thread_id].append(
                                                            file_name)
                                                        thread_file_download_path_list_global[thread_id].append(
                                                            file_download_path)
                                                        operation_fresh_thread_status(
                                                            thread_id, 0)
                                                    # 去除邮件无附件标记或全部过期标记
                                                    if download_status_last == -1 or download_status_last == 2:
                                                        download_status_last = 0
                                            if msg_data_splited.get_content_type() == 'text/html':
                                                msg_data_splited_charset = msg_data_splited.get_content_charset()
                                                msg_data_splited_data_raw = msg_data_splited.get_payload(
                                                    decode=True)
                                                msg_data_splited_data = bytes.decode(
                                                    msg_data_splited_data_raw, msg_data_splited_charset)
                                                html_fetcher = BeautifulSoup(
                                                    msg_data_splited_data, 'lxml')
                                                if '附件' in msg_data_splited_data:
                                                    with lock_var_global:
                                                        operation_fresh_thread_status(
                                                            thread_id, 1)
                                                    href_list = html_fetcher.find_all(
                                                        'a')
                                                    for href in href_list:
                                                        if '下载' in href.get_text():
                                                            largefile_downloadable_link = None
                                                            largefile_link = href.get(
                                                                'href')
                                                            if ltk.find_list_substr(available_largefile_website_list_global, largefile_link):
                                                                req_status_last = False
                                                                for _ in range(setting_reconnect_max_times_global+1):
                                                                    try:
                                                                        download_page = requests.get(
                                                                            largefile_link)
                                                                        req_status_last = True
                                                                        break
                                                                    except Exception:
                                                                        pass
                                                                assert req_status_last
                                                                html_fetcher_2 = BeautifulSoup(
                                                                    download_page.text, 'lxml')
                                                                if 'wx.mail.qq.com' in largefile_link:
                                                                    script = html_fetcher_2.select_one(
                                                                        'body > script:nth-child(2)').get_text()
                                                                    largefile_downloadable_link = re.compile(
                                                                        r'(?<=var url = ").+(?=")').findall(script)
                                                                    if len(largefile_downloadable_link):
                                                                        largefile_downloadable_link = largefile_downloadable_link[0].replace(
                                                                            '\\x26', '&')
                                                                        largefile_download_method = 0  # get
                                                                    else:
                                                                        if not has_downloadable_attachment and download_status_last != 1:
                                                                            download_status_last = 2
                                                                elif 'mail.qq.com' in largefile_link:
                                                                    largefile_downloadable_link = html_fetcher_2.select_one(
                                                                        '#main > div.ft_d_mainWrapper > div > div > div.ft_d_fileToggle.default > a.ft_d_btnDownload.btn_blue')
                                                                    if largefile_downloadable_link:
                                                                        largefile_downloadable_link = largefile_downloadable_link.get(
                                                                            'href')
                                                                        largefile_download_method = 0  # get
                                                                    else:
                                                                        if not has_downloadable_attachment and download_status_last != 1:
                                                                            download_status_last = 2
                                                                elif 'dashi.163.com' in largefile_link:
                                                                    link_key = urllib.parse.parse_qs(
                                                                        urllib.parse.urlparse(largefile_link).query)['key'][0]
                                                                    req_status_last = False
                                                                    for _ in range(setting_reconnect_max_times_global+1):
                                                                        try:
                                                                            fetch_result = json.loads(requests.post(
                                                                                'https://dashi.163.com/filehub-master/file/dl/prepare2', json={'fid': '', 'linkKey': link_key}).text)
                                                                            req_status_last = True
                                                                            break
                                                                        except Exception:
                                                                            pass
                                                                    assert req_status_last
                                                                    largefile_download_code = fetch_result['code']
                                                                    if largefile_download_code == 200:
                                                                        largefile_downloadable_link = fetch_result[
                                                                            'result']['downloadUrl']
                                                                        largefile_download_method = 0  # get
                                                                    elif largefile_download_code == 404 or largefile_download_code == 601:
                                                                        if not has_downloadable_attachment and download_status_last != 1:
                                                                            download_status_last = 2
                                                                    else:
                                                                        largefile_undownloadable_link_list.append(
                                                                            largefile_link)
                                                                        largefile_undownloadable_code_list.append(
                                                                            largefile_download_code)
                                                                        download_status_last = 1
                                                                elif 'mail.163.com' in largefile_link:
                                                                    link_key = urllib.parse.parse_qs(
                                                                        urllib.parse.urlparse(largefile_link).query)['file'][0]
                                                                    req_status_last = False
                                                                    for _ in range(setting_reconnect_max_times_global+1):
                                                                        try:
                                                                            fetch_result = json.loads(requests.get(
                                                                                'https://fs.mail.163.com/fs/service', params={'f': link_key, 'op': 'fs_dl_f_a'}).text)
                                                                            req_status_last = True
                                                                            break
                                                                        except Exception:
                                                                            pass
                                                                    assert req_status_last
                                                                    largefile_download_code = fetch_result['code']
                                                                    if largefile_download_code == 200:
                                                                        largefile_downloadable_link = fetch_result[
                                                                            'result']['downloadUrl']
                                                                        largefile_download_method = 0  # get
                                                                    elif largefile_download_code == -17 or largefile_download_code == -3:
                                                                        if not has_downloadable_attachment and download_status_last != 1:
                                                                            download_status_last = 2
                                                                    else:
                                                                        largefile_undownloadable_link_list.append(
                                                                            largefile_link)
                                                                        largefile_undownloadable_code_list.append(
                                                                            largefile_download_code)
                                                                        download_status_last = 1
                                                                elif 'mail.sina.com.cn' in largefile_link:
                                                                    req_status_last = False
                                                                    for _ in range(setting_reconnect_max_times_global+1):
                                                                        try:
                                                                            download_page = requests.get(
                                                                                largefile_link)
                                                                            req_status_last = True
                                                                            break
                                                                        except Exception:
                                                                            pass
                                                                    assert req_status_last
                                                                    html_fetcher_2 = BeautifulSoup(
                                                                        download_page.text, 'lxml')
                                                                    can_download = len(
                                                                        html_fetcher_2.find_all('input'))
                                                                    if can_download:
                                                                        largefile_downloadable_link = largefile_link
                                                                        largefile_download_method = 1  # post
                                                                    else:
                                                                        if not has_downloadable_attachment and download_status_last != 1:
                                                                            download_status_last = 2
                                                            elif ltk.find_list_substr(unavailable_largefile_website_list_global, largefile_link):
                                                                largefile_undownloadable_link_list.append(
                                                                    largefile_link)
                                                                largefile_undownloadable_code_list.append(
                                                                    largefile_download_code)
                                                                download_status_last = 1
                                                            elif ltk.find_list_substr(website_blacklist_global, largefile_link):
                                                                continue
                                                            else:
                                                                download_status_last = -2
                                                            if largefile_downloadable_link:
                                                                largefile_downloadable_link_list.append(
                                                                    largefile_downloadable_link)
                                                                has_downloadable_attachment = True
                                                                req_status_last = False
                                                                for _ in range(setting_reconnect_max_times_global+1):
                                                                    try:
                                                                        if largefile_download_method == 0:
                                                                            largefile_data = requests.get(
                                                                                largefile_downloadable_link, stream=True)
                                                                        else:
                                                                            largefile_data = requests.post(
                                                                                largefile_downloadable_link, stream=True)
                                                                        req_status_last = True
                                                                        break
                                                                    except Exception:
                                                                        pass
                                                                assert req_status_last
                                                                mime_type = largefile_data.headers.get(
                                                                    'Content-Type')
                                                                largefile_name_raw = largefile_data.headers.get(
                                                                    'Content-Disposition')
                                                                largefile_name_raw = largefile_name_raw.encode(
                                                                    'ISO-8859-1').decode('UTF-8')  # 转码
                                                                largefile_name_raw = largefile_name_raw.split(';')[
                                                                    1]
                                                                largefile_name_raw = re.compile(
                                                                    r'(?<=").+(?=")').findall(largefile_name_raw)[0]
                                                                with lock_var_global:
                                                                    operation_fresh_thread_status(
                                                                        thread_id, 2)
                                                                if download_stop_flag_global:
                                                                    if setting_rollback_when_download_failed_global:
                                                                        with lock_io_global:
                                                                            operation_rollback(
                                                                                thread_file_name_list_global[thread_id], thread_file_download_path_list_global[thread_id], file_name, largefile_name, file_download_path, largefile_download_path, file_name_tmp, largefile_name_tmp)
                                                                    return
                                                                lock_io_global.acquire()
                                                                largefile_download_path = operation_get_download_path(
                                                                    largefile_name_raw, mime_type)
                                                                largefile_name_tmp = operation_fetch_file_name(
                                                                    largefile_name_raw+'.tmp', largefile_download_path)
                                                                req_status_last = False
                                                                for _ in range(setting_reconnect_max_times_global+1):
                                                                    try:
                                                                        with open(os.path.join(largefile_download_path, largefile_name_tmp), 'wb') as file:
                                                                            lock_io_global.release()
                                                                            for largefile_data_chunk in largefile_data.iter_content(1024):
                                                                                if download_stop_flag_global:
                                                                                    break
                                                                                file.write(
                                                                                    largefile_data_chunk)
                                                                        req_status_last = True
                                                                        break
                                                                    except OSError as e:
                                                                        raise e
                                                                    except Exception:
                                                                        pass
                                                                assert req_status_last
                                                                with lock_io_global:
                                                                    largefile_name = operation_fetch_file_name(
                                                                        largefile_name_raw, largefile_download_path)
                                                                    os.renames(
                                                                        os.path.join(largefile_download_path, largefile_name_tmp), os.path.join(largefile_download_path, largefile_name))
                                                                if download_stop_flag_global:
                                                                    if setting_rollback_when_download_failed_global:
                                                                        with lock_io_global:
                                                                            operation_rollback(
                                                                                thread_file_name_list_global[thread_id], thread_file_download_path_list_global[thread_id], file_name, largefile_name, file_download_path, largefile_download_path, file_name_tmp, largefile_name_tmp)
                                                                    return
                                                                with lock_print_global, lock_var_global:
                                                                    print('\r', file_download_count_global+1, ' 已下载 ', largefile_name, (
                                                                        ' <- '+largefile_name_raw)if largefile_name != largefile_name_raw else '', ltk.indent(8), sep='', flush=True)
                                                                    log_global.info(str(file_download_count_global+1)+' 已下载 "' + largefile_name + ((
                                                                        '" <- "'+largefile_name_raw+'"')if largefile_name != largefile_name_raw else '"'))
                                                                    if setting_display_mailbox:
                                                                        print(ltk.indent(
                                                                            1), '邮箱: ', address_global[imap_index], sep='', flush=True)
                                                                        log_global.info(ltk.indent(
                                                                            1)+'邮箱: "'+address_global[imap_index]+'"')
                                                                    if setting_display_subject_and_time:
                                                                        print(ltk.indent(
                                                                            1), '标题-时间: ', subject, ' - ', send_time, sep='', flush=True)
                                                                        log_global.info(
                                                                            ltk.indent(1)+'标题: "'+subject+'"')
                                                                        log_global.info(
                                                                            ltk.indent(1)+'时间: '+send_time)
                                                                    if setting_display_mime_type:
                                                                        print(
                                                                            ltk.indent(1), 'MIME-TYPE: ', mime_type, sep='', flush=True)
                                                                        log_global.info(
                                                                            ltk.indent(1)+'MIME-TYPE: "'+mime_type+'"')
                                                                    file_download_count_global += 1
                                                                    file_download_count += 1
                                                                    thread_file_name_list_global[thread_id].append(
                                                                        largefile_name)
                                                                    thread_file_download_path_list_global[thread_id].append(
                                                                        largefile_download_path)
                                                                    operation_fresh_thread_status(
                                                                        thread_id, 0)
                                                                # 去除邮件无附件标记或全部过期标记
                                                                if download_status_last == -1 or download_status_last == 2:
                                                                    download_status_last = 0
                                    except Exception as e:
                                        if lock_io_global.locked():
                                            lock_io_global.release()
                                        with lock_print_global:
                                            if not req_status_last:
                                                print(
                                                    '\rE: 邮箱', address_global[imap_index], '有附件下载失败,该邮件已跳过.', ltk.indent(4), flush=True)
                                                log_global.error(
                                                    '邮箱 "'+address_global[imap_index]+'" 有附件下载失败.')
                                                if setting_rollback_when_download_failed_global:
                                                    operation_rollback(
                                                        thread_file_name_list_global[thread_id], thread_file_download_path_list_global[thread_id], file_name, largefile_name, file_download_path, largefile_download_path, file_name_tmp, largefile_name_tmp)
                                        download_status_last = -2
                        with lock_var_global:
                            if fetch_status_last:
                                if download_status_last == 0:
                                    if has_downloadable_attachment:
                                        # 防止回滚时把全部下载成功的邮件的附件删除
                                        thread_file_name_list_global[thread_id] = [
                                        ]
                                        if setting_sign_unseen_flag_after_downloading_global:
                                            for _ in range(setting_reconnect_max_times_global+1):
                                                try:
                                                    if setting_sign_unseen_flag_after_downloading_global and setting_search_mails_type_global != 2:
                                                        imap.store(msg_index,
                                                                   'flags', '\\SEEN')
                                                    break
                                                except Exception:
                                                    for _ in range(setting_reconnect_max_times_global):
                                                        try:
                                                            imap = operation_login_imap_server(
                                                                host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                                                            if imap != None:
                                                                imap.select(
                                                                    folder)
                                                                break
                                                        except Exception:
                                                            pass
                                elif download_status_last == 1:
                                    if ltk.safe_list_find(imap_with_undownloadable_attachments_index_list_global, imap_index) == -1:
                                        imap_with_undownloadable_attachments_index_list_global.append(
                                            imap_index)
                                    msg_with_undownloadable_attachments_list_global[imap_index][folder_index_int].append(
                                        msg_index)
                                    send_time_with_undownloadable_attachments_list_global[imap_index][folder_index_int].append(
                                        send_time)
                                    subject_with_undownloadable_attachments_list_global[imap_index][folder_index_int].append(
                                        subject)
                                    largefile_undownloadable_link_list_global[imap_index][folder_index_int].append(
                                        largefile_undownloadable_link_list)
                                    largefile_undownloadable_code_list_global[imap_index][folder_index_int].append(
                                        largefile_undownloadable_code_list)
                                elif download_status_last == 2:
                                    if ltk.safe_list_find(imap_overdueanddeleted_index_list_global, imap_index) == -1:
                                        imap_overdueanddeleted_index_list_global.append(
                                            imap_index)
                                    msg_overdueanddeleted_list_global[imap_index][folder_index_int].append(
                                        msg_index)
                                    send_time_overdueanddeleted_list_global[imap_index][folder_index_int].append(
                                        send_time)
                                    subject_overdueanddeleted_list_global[imap_index][folder_index_int].append(
                                        subject)
                                elif download_status_last == -2:
                                    if ltk.safe_list_find(imap_download_failed_index_list_global, imap_index) == -1:
                                        imap_download_failed_index_list_global.append(
                                            imap_index)
                                    msg_download_failed_list_global[imap_index][folder_index_int].append(
                                        msg_index)
                                    send_time_download_failed_list_global[imap_index][folder_index_int].append(
                                        send_time)
                                    subject_download_failed_list_global[imap_index][folder_index_int].append(
                                        subject)
                                msg_processed_count_global += 1
                            else:
                                if ltk.safe_list_find(imap_fetch_failed_index_list_global, imap_index) == -1:
                                    imap_fetch_failed_index_list_global.append(
                                        imap_index)
                                msg_fetch_failed_list_global[imap_index][folder_index_int].append(
                                    msg_index)
                            operation_fresh_thread_status(thread_id, 0)
                    else:
                        lock_var_global.release()
                        break
    except Exception as exception:
        with lock_var_global:
            thread_excepion_list_global.append(exception)
    with lock_var_global:
        operation_fresh_thread_status(thread_id, -1)


def program_tool_main():
    while True:
        command = ltk.input_option('选择操作 [l:列出邮箱文件夹;t:测试连接;q:返回主菜单]', 'l', 't', 'q',
                                   allow_undefind_input=False, default_option='l', end=':')
        if command == 'l':
            program_tool_list_mail_folders_main()
        elif command == 't':
            program_tool_test_connection_main()
        elif command == 'q':
            break


@check_config_load_status
@init
def program_tool_list_mail_folders_main():
    log_global.info('-'*3+'列出邮箱文件夹操作开始'+'-'*3)
    operation_login_all_imapserver()
    if not len(imap_succeed_index_list_global):
        print('E: 无法执行该操作.原因: 没有可用邮箱.', flush=True)
        log_global.error('列出邮箱文件夹 操作无法执行. 原因: 没有可用邮箱.')
    else:
        for imap_index_int, imap_index in enumerate(imap_succeed_index_list_global):
            list_status = False
            print('正在读取... (', imap_index_int+1, '/',
                  len(imap_succeed_index_list_global), ')', sep='', end='')
            for _ in range(setting_reconnect_max_times_global+1):
                try:
                    _, list_data_raw = imap_list_global[imap_index].list(
                    )
                    list_status = True
                    break
                except Exception:
                    for _ in range(setting_reconnect_max_times_global):
                        imap_list_global[imap_index] = operation_login_imap_server(
                            host_global[imap_index], address_global[imap_index], password_global[imap_index], False)
                        if imap_list_global[imap_index] != None:
                            break
            if not list_status:
                print('\rE: 邮箱 ', address_global[imap_index],
                      ' 获取文件夹列表失败,已跳过.', ltk.indent(2), sep='', flush=True)
                log_global.error(
                    '邮箱 "'+address_global[imap_index]+'" 获取文件夹列表失败.')
            else:
                print('\r邮箱: ', address_global[imap_index],
                      ltk.indent(3), sep='', flush=True)
                log_global.info('邮箱: "' + address_global[imap_index]+'"')
                for folder in list_data_raw:
                    try:
                        folder_name = ltk.imap_utf7_bytes_decode(
                            re.compile(rb'(?<=/" ").+(?=")').findall(folder)[0])
                        folder_flag = re.compile(
                            rb'(?<=\().+(?=\))').findall(folder)
                        print(ltk.indent(1), '文件夹: ',
                              folder_name, sep='', flush=True)
                        log_global.info(ltk.indent(1)+'文件夹: "'+folder_name+'"')
                        if len(folder_flag):
                            folder_flag = ltk.imap_utf7_bytes_decode(
                                folder_flag[0])
                            print(ltk.indent(2), '标签: ',
                                  folder_flag, sep='', flush=True)
                            log_global.info(ltk.indent(
                                2)+'标签: "'+folder_flag+'"')
                        else:
                            print(ltk.indent(2), '没有标签', sep='', flush=True)
                            log_global.info(ltk.indent(2)+'没有标签')
                    except UnicodeError:
                        print('\rE: 邮箱 ', address_global[imap_index], ' 有文件夹信息解码失败,已跳过.', ltk.indent(
                            2), sep='', flush=True)
                        log_global.error(
                            '邮箱 "'+address_global[imap_index]+'" 有文件夹信息解码失败.')
        print(flush=True)
    log_global.info('-'*3+'列出邮箱文件夹操作完成'+'-'*3)


@check_config_load_status
@init
def program_tool_test_connection_main():
    log_global.info('-'*6+'测试连接操作开始'+'-'*6)
    operation_login_all_imapserver()
    log_global.info('-'*6+'测试连接操作完成'+'-'*6)


if ltk.__version__ != _depend_toolkit_version:
    print('F: littoolkit 版本不符合要求.\n    依赖版本: '+_depend_toolkit_version +
          '\n    当前版本: '+ltk.__version__, flush=True)
    time.sleep(5)
    sys.exit(1)

# 读取参数
# -c: 配置文件路径
try:
    for opt, val in getopt.getopt(sys.argv[1:], 'c:')[0]:
        if opt == '-c':
            config_custom_path_global = val
except getopt.GetoptError:
    print('F: 程序参数错误.', flush=True)
    ltk.pause_exit(1)
try:
    print('Mail Downloader', flush=True)
    print('Desingned by Litrix', flush=True)
    print('版本:', __version__ +
          ('-'+_status_dict[__status__] if __status__ != 0 else ''), flush=True)
    print('获取更多信息,请访问 https://github.com/Litrix2/MailDownloader', flush=True)
    if __status__ == 1:
        print('W: 此版本正在开发中,可能包含严重错误,请及时跟进仓库以获取最新信息.')
    elif __status__ == 2:
        print('W: 此版本正在测试中,可能不稳定,请及时跟进仓库以获取最新信息.')
    elif __status__ == 3:
        print('W: 此版本为演示版本,部分功能与信息显示与正式版本存在差异.')
    print(flush=True)
    config_load_status_global = operation_load_config()
    if config_load_status_global and setting_silent_download_mode_global:
        print('W: 静默下载模式已开启.', flush=True)
        log_global.warning('静默下载模式已开启.')
        program_download_main()
        print('程序将在 5 秒后退出.')
        time.sleep(5)
        log_global.info('='*10+'程序退出'+'='*10)
        sys.exit(0)
    else:
        while True:
            command = ltk.input_option(
                '\r选择操作 [d:下载;t:工具;r:重载配置;n:新建配置;c:清屏;q:退出]', 'd', 't', 'r', 'n', 'c', 'q', default_option='d', end=':')
            if command == 'd':
                program_download_main()
            elif command == 't':
                program_tool_main()
            elif command == 'r':
                log_global.warning('='*10+'重载配置'+'='*10)
                config_load_status_global = operation_load_config()
            elif command == 'n':
                if ltk.input_option('此操作将在工作目录下生成 config_new.toml,是否继续?', 'y', 'n', default_option='n', end=':') == 'y':
                    log_global.info('-'*4+'新建配置文件操作开始'+'-'*4)
                    try:
                        with open(os.path.join(os.getcwd(), 'config_new.toml'), 'w') as config_new_file:
                            rtoml.dump(config_primary_data_global,
                                       config_new_file, pretty=True)
                        print('操作成功完成.', flush=True)
                        print(
                            'N: 有关配置文件的详细说明,请查看仓库中的示例配置文件;新配置文件的部分内容可能与示例配置文件不完全相同.', flush=True)
                        log_global.info('已生成新配置文件 "' +
                                        os.path.join(os.getcwd(), 'config_new.toml')+'"')
                    except OSError as e:
                        print('E: 操作失败,信息如下:', flush=True)
                        print(repr(e))
                        log_global.error('操作失败,信息如下:')
                        log_global.error(repr(e))
                    log_global.info('-'*4+'新建配置文件操作完成'+'-'*4)
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
        log_global.info('='*10+'程序退出'+'='*10)
        ltk.pause_exit(0)
except KeyboardInterrupt:
    download_stop_flag_global = 1
    if 'thread_status_list_global' in vars() and setting_rollback_when_download_failed_global and thread_status_list_global.count(-1) < setting_download_thread_count_global:
        for thread_id in range(setting_download_thread_count_global):
            with lock_io_global:
                operation_rollback(
                    thread_file_name_list_global[thread_id], thread_file_download_path_list_global[thread_id])
    with lock_print_global:
        print('\n强制退出', flush=True)
        log_global.critical('='*10+'强制退出'+'='*10)
        time.sleep(0.5)
        ltk.pause_exit(1)
except Exception:
    download_stop_flag_global = 1
    with lock_print_global:
        print('\nF: 遇到无法解决的错误.信息如下:', flush=True)
        log_global.critical('遇到无法解决的错误. 信息如下:')
        traceback_msg = traceback.format_exc()
        print(traceback_msg)
        for traceback_msg_splited in traceback_msg.splitlines():
            log_global.critical(traceback_msg_splited)
        log_global.critical('='*10+'异常退出'+'='*10)
        ltk.pause_exit(1)
