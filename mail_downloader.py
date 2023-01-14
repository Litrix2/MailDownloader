import urllib.parse
import time
from email import header
import email
import imaplib
import datetime
import os
import socket
import copy
import rtoml
from bs4 import BeautifulSoup
import requests
version = '1.0'
authentication = ['name', 'MailDownloader', 'version', version]
available_bigfile_website_list = ['wx.mail.qq.com', 'mail.qq.com']
unavailable_bigfile_website_list = ['dashi.163.com']


class Time():
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
    'allow_manual_input_search_time': True,
    'min_search_time': False,
    'max_search_time': False,
    'only_search_unseen_mails': True,
    'sign_unseen_tag_after_downloading': True,
    'reconnect_max_times': 3,
    'download_path': ''
}


def init(reset_imaps=False, reset_msgs=False):
    global imap_list, imap_succeed_index_list, imap_connect_failed_index_list, imap_wrong_index_list
    global download_state_last_global
    global msgs_processed_count_global, msgs_with_undownloadable_attachments_list_global, msgs_with_downloadable_attachments_list_global, msgs_failed_list
    global subject_list_global, subject_with_undownloadable_attachments_list_global
    global file_download_count_global, file_name_raw_list_global, file_name_list_global
    global bigfile_undownloadable_link_list_global
    if reset_imaps:
        imaplib.Commands['ID'] = ('AUTH')
        imap_list = []
        imap_succeed_index_list = []
        imap_connect_failed_index_list = [[], []]
        imap_wrong_index_list = []
    if reset_msgs:
        download_state_last_global = -1  # 0:正常;1:有无法下载的文件;2:下载失败
        msgs_processed_count_global = 0
        msgs_with_undownloadable_attachments_list_global = []
        msgs_with_downloadable_attachments_list_global = []
        msgs_failed_list = []
        subject_list_global = []
        subject_with_undownloadable_attachments_list_global = []
        file_download_count_global = 0
        file_name_raw_list_global = []
        file_name_list_global = []
        bigfile_undownloadable_link_list_global = []
        for i in range(len(host)):
            msgs_with_undownloadable_attachments_list_global.append([])
            msgs_with_downloadable_attachments_list_global.append([])
            msgs_failed_list.append([])
            subject_list_global.append([])
            subject_with_undownloadable_attachments_list_global.append([])
            file_name_raw_list_global.append([])
            file_name_list_global.append([])
            bigfile_undownloadable_link_list_global.append([])


def operation_load_config():
    global host, address, password
    global settings_allow_manual_input_search_time, settings_mail_min_time, settings_mail_max_time
    global settings_only_search_unseen_mails
    global settings_sign_unseen_tag_after_downloading
    global settings_reconnect_max_times
    global settings_download_path
    print('正在读取配置文件...', flush=True)
    try:
        with open(os.path.join(os.path.dirname(__file__), 'config.toml'), 'rb') as config_file:
            config_file_data = rtoml.load(
                bytes.decode(config_file.read(), 'utf-8'))

            host = []
            address = []
            password = []
            for eachdata_mail in config_file_data['mail']:
                host.append(eachdata_mail['host'])
                address.append(eachdata_mail['address'])
                password.append(eachdata_mail['password'])
            settings_allow_manual_input_search_time = config_file_data[
                'allow_manual_input_search_time']
            settings_mail_min_time = Time()
            if config_file_data['min_search_time'] == False:
                settings_mail_min_time.enabled = False
            else:
                settings_mail_min_time.enabled = True
                settings_mail_min_time.year = config_file_data['min_search_time'][0]
                settings_mail_min_time.month = config_file_data['min_search_time'][1]
                settings_mail_min_time.day = config_file_data['min_search_time'][1]
            settings_mail_max_time = Time()
            if config_file_data['max_search_time'] == False:
                settings_mail_max_time.enabled = False
            else:
                settings_mail_max_time.enabled = True
                settings_mail_max_time.year = config_file_data['max_search_time'][0]
                settings_mail_max_time.month = config_file_data['max_search_time'][1]
                settings_mail_max_time.day = config_file_data['max_search_time'][1]
            settings_only_search_unseen_mails = config_file_data['only_search_unseen_mails']
            settings_sign_unseen_tag_after_downloading = config_file_data[
                'sign_unseen_tag_after_downloading']
            settings_reconnect_max_times = config_file_data['reconnect_max_times']
            settings_download_path = config_file_data['download_path']
    except:
        print('E:配置文件错误.', flush=True)
        return False
    else:
        print('配置加载成功.', flush=True)
        return True


def operation_login_imap_server(host, address, password):
    is_login_succeed = False
    try:
        print('\r正在连接 ', host,
              '        ', end='', sep='', flush=True)
        imap = imaplib.IMAP4_SSL(
            host)
        print('\r已连接 ', host,
              '            ', sep='', flush=True)
        print('\r正在登录 ', address,
              end='', sep='', flush=True)
        imap.login(address, password)
        print('\r', address,
              '登录成功            ', sep='', flush=True)
        imap._simple_command(
            'ID', '("' + '" "'.join(authentication) + '")')  # 发送ID
    except socket.gaierror as e:
        print('\n服务器连接错误.', flush=True)
    except imaplib.IMAP4.error as e:
        print('\n用户名或密码错误.', flush=True)
    except (socket.timeout, TimeoutError):
        print('\n服务器连接超时.', flush=True)
    else:
        is_login_succeed = True
    if is_login_succeed:
        imap.select()
        return imap
    else:
        return None


def operation_set_time():
    settings_mail_min_time.enabled = False
    settings_mail_max_time.enabled = False
    if input_option('是否设置检索开始日期?', 'y', 'n', default_option='y', end=':') == 'y':
        settings_mail_min_time.enabled = True
        while True:
            try:
                settings_mail_min_time.year = int(input_option(
                    '输入年份', allow_undefind_input=True, default_option=str(datetime.datetime.now().year), end=':'))
                if settings_mail_min_time.year < 0:
                    raise Exception
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
        while True:
            try:
                settings_mail_min_time.month = int(input_option(
                    '输入月份', allow_undefind_input=True, default_option=str(datetime.datetime.now().month), end=':'))
                if settings_mail_min_time.month < 1 or settings_mail_min_time.month > 12:
                    raise Exception
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
        while True:
            try:
                settings_mail_min_time.day = int(input_option(
                    '输入日期', allow_undefind_input=True, default_option=str(datetime.datetime.now().day), end=':'))
                if settings_mail_min_time.day < 1 or settings_mail_min_time.day > 31:
                    raise Exception
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)

    if input_option('是否设置检索截止日期?', 'y', 'n', default_option='n', end=':') == 'y':
        settings_mail_max_time.enabled = True
        while True:
            try:
                settings_mail_max_time.year = int(input_option(
                    '输入年份', allow_undefind_input=True, default_option=str(datetime.datetime.now().year), end=':'))
                if settings_mail_max_time.year < 0:
                    print('无效选项,请重新输入.', flush=True)
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
        while True:
            try:
                settings_mail_max_time.month = int(input_option(
                    '输入月份', allow_undefind_input=True, default_option=str(datetime.datetime.now().month), end=':'))
                if settings_mail_max_time.month < 1 or settings_mail_max_time.month > 12:
                    print('无效选项,请重新输入.', flush=True)
                else:
                    break
            except Exception:
                print('无效选项,请重新输入.', flush=True)
        while True:
            try:
                settings_mail_max_time.day = int(input_option(
                    '输入日期', allow_undefind_input=True, default_option=str(datetime.datetime.now().day), end=':'))
                if settings_mail_max_time.day < 1 or settings_mail_max_time.day > 31:
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
            file_name_raw)-file_name_raw[::-1].find('.')-1 if file_name_raw.find('.') != -1 else -1
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


def operation_close_all_connection():
    try:
        for imap_index_int in range(len(imap_list)):
            try:
                if not (imap_list[imap_index_int] == None):
                    imap_list[imap_index_int].close()
                    imap_list[imap_index_int].logout()
            except imaplib.IMAP4_SSL.abort:
                continue
    except NameError:
        return


def program_login_all_imapserver():
    init(True, True)
    for imap_index_int in range(len(host)):
        imap = operation_login_imap_server(
            host[imap_index_int], address[imap_index_int], password[imap_index_int])
        imap_list.append(imap)
        if imap != None:
            imap_succeed_index_list.append(imap_index_int)
            msgs_with_downloadable_attachments_list_global.append([])
            file_name_raw_list_global.append([])
        else:
            imap_connect_failed_index_list[0].append(imap_index_int)
    if len(imap_succeed_index_list):
        print('已成功连接的邮箱:', flush=True)
        for imap_succeed_index_int in imap_succeed_index_list:
            print('    ', address[imap_succeed_index_int], sep='')
        if len(imap_list) < len(host):
            print('E:', '以下邮箱未能连接:', flush=True)
            for imap_connect_failed_index_int in imap_connect_failed_index_list[0]:
                print('    ', address[imap_connect_failed_index_int],
                      sep='', flush=True)
            print('    请尝试重新连接.', flush=True)
    else:
        print('E:', '没有成功连接的邮箱,请尝试重新连接.', flush=True)


def program_download():
    global imap_list, imap_succeed_index_list, imap_connect_failed_index_list, imap_wrong_index_list
    global download_state_last_global
    global msgs_processed_count_global, msgs_with_undownloadable_attachments_list_global, msgs_with_downloadable_attachments_list_global, msgs_failed_list
    global subject_list_global, subject_with_undownloadable_attachments_list_global
    global file_download_count_global, file_name_raw_list_global, file_name_list_global
    global bigfile_undownloadable_link_list_global
    if not (settings_mail_min_time.enabled or settings_mail_max_time.enabled):
        if settings_only_search_unseen_mails:
            print('仅检索未读邮件', flush=True)
        else:
            print('检索全部邮件', flush=True)
    else:
        prompt = ''
        prompt += '仅检索日期'
        prompt += ('从 '+settings_mail_min_time.time()
                   ) if settings_mail_min_time.enabled else '在 ' if settings_mail_max_time else ''
        prompt += ' 开始' if settings_mail_min_time.enabled and not settings_mail_max_time.enabled else (str(
            settings_mail_max_time.time()+' 截止')) if not settings_mail_min_time.enabled and settings_mail_max_time.enabled else ' 到 '
        prompt += settings_mail_max_time.time() if settings_mail_min_time.enabled and settings_mail_max_time.enabled else ''
        prompt += '的未读邮件' if settings_only_search_unseen_mails else '的邮件'
        print(prompt, sep='', flush=True)
    start_time = time.time()
    for imap_index_int in range(len(imap_list)):
        if imap_list[imap_index_int] == None:
            continue
        file_download_count = 0
        is_reconnect_succeed = False
        try:
            imap_list[imap_index_int].noop()
            is_reconnect_succeed = True
        except imaplib.IMAP4_SSL.abort:
            print('\rW: 连接已断开,正在尝试重连...', flush=True)
            for i in range(settings_reconnect_max_times):
                imap_list[imap_index_int] = operation_login_imap_server(
                    host[imap_index_int], address[imap_index_int], password[imap_index_int])
                if imap_list[imap_index_int] != None:
                    is_reconnect_succeed = True
                    break
            if not is_reconnect_succeed:
                imap_list[imap_index_int] = None
                print(
                    'E: 无法连接至', address[imap_index_int], ',已跳过.', flush=True)
                imap_connect_failed_index_list[0].append(
                    imap_index_int)
                imap_succeed_index_list.remove(imap_index_int)
                continue
        msgs_processed_count = 0
        has_downloadable_attachments_in_mail = False
        print(
            '\r邮箱: ', address[imap_index_int], indent(3), sep='', flush=True)
        if not (settings_mail_min_time.enabled or settings_mail_max_time.enabled):
            search_command = ''
            if settings_only_search_unseen_mails:
                search_command = 'unseen'
            else:
                search_command = 'all'
            typ, data_msg_index_raw = imap_list[imap_index_int].search(
                None, search_command)
        else:
            search_command = ''
            search_command += ('since '+settings_mail_min_time.time()
                               ) if settings_mail_min_time.enabled else ''
            search_command += ' ' if settings_mail_min_time.enabled and settings_mail_max_time.enabled else ''
            search_command += ('before ' + settings_mail_max_time.time()
                               ) if settings_mail_max_time.enabled else ''
            search_command += ' ' if (
                settings_mail_max_time.enabled or settings_mail_min_time.enabled) and settings_only_search_unseen_mails else ''
            search_command += 'unseen' if settings_only_search_unseen_mails else ''
            typ, data_msg_index_raw = imap_list[imap_index_int].search(
                None, search_command)
        msg_list = list(reversed(data_msg_index_raw[0].split()))
        print(indent(1), '共 ', len(msg_list), ' 封邮件', sep='', flush=True)
        for msg_index_int in range(len(msg_list)):
            try:
                imap_list[imap_index_int].noop()
                is_reconnect_succeed = True
            except imaplib.IMAP4_SSL.abort:
                print('\rW: 连接已断开,正在尝试重连...', flush=True)
                for i in range(settings_reconnect_max_times):
                    imap_list[imap_index_int] = operation_login_imap_server(
                        host[imap_index_int], address[imap_index_int], password[imap_index_int])
                    if imap_list[imap_index_int] != None:
                        is_reconnect_succeed = True
                        break
                if not is_reconnect_succeed:
                    imap_list[imap_index_int] = None
                    print(
                        'E: 无法连接至', address[imap_index_int], ',已跳过.', flush=True)
                    imap_connect_failed_index_list[1].append(
                        imap_index_int)
                    imap_succeed_index_list.remove(imap_index_int)
                    break
            download_state_last_global = -1
            has_downloadable_attachments = False
            file_name_list = []
            bigfile_downloadable_link_list = []
            bigfile_undownloadable_link_list = []
            file_name_raw_list_global[imap_index_int].append([])
            print('\r正在读取邮件数据... (', msgs_processed_count+1, ',', msgs_processed_count_global+1,
                  ')', indent(3), sep='', end='', flush=True)
            typ, data_msg_raw = imap_list[imap_index_int].fetch(
                msg_list[msg_index_int], 'BODY.PEEK[]')
            data_msg = email.message_from_bytes(
                data_msg_raw[0][1])
            subject = str(header.make_header(
                header.decode_header(data_msg.get('Subject'))))
            try:
                for eachdata_msg in data_msg.walk():
                    file_name = None
                    bigfile_name = None
                    if eachdata_msg.get_content_disposition():
                        if not has_downloadable_attachments:
                            print('\r', indent(1), len(extract_nested_list(msgs_with_downloadable_attachments_list_global))+1, ' ', subject,
                                  indent(8), sep='')
                        has_downloadable_attachments_in_mail = True
                        has_downloadable_attachments = True
                        file_name_raw = str(header.make_header(
                            header.decode_header(eachdata_msg.get_filename())))
                        file_data = eachdata_msg.get_payload(decode=True)
                        file_name = operation_parse_file_name(
                            file_name_raw)
                        file_name_tmp = operation_parse_file_name(
                            file_name+'.tmp')
                        print('\r正在下载普通附件... ', '(', file_download_count+1, ',', file_download_count_global +
                              1, ')        ', sep='', end='', flush=True)
                        with open(os.path.join(settings_download_path, file_name_tmp), 'wb') as file:
                            file.write(file_data)
                        os.renames(os.path.join(settings_download_path, file_name_tmp),
                                   os.path.join(settings_download_path, file_name))
                        print('\r', indent(2), file_download_count_global+1, ' 已下载 ', file_name, (
                            ' <- '+file_name_raw)if file_name != file_name_raw else '', indent(2), sep='', flush=True)
                        file_download_count_global += 1
                        file_download_count += 1
                        file_name_list.append(file_name)
                    if eachdata_msg.get_content_type() == 'text/html':
                        eachdata_msg_charset = eachdata_msg.get_content_charset()
                        eachdata_msg_data_raw = eachdata_msg.get_payload(
                            decode=True)
                        eachdata_msg_data = bytes.decode(
                            eachdata_msg_data_raw, eachdata_msg_charset)
                        html_fetcher = BeautifulSoup(eachdata_msg_data, 'lxml')
                        if eachdata_msg_data.find('附件') != -1:
                            # with open(os.path.join(os.path.dirname(__file__),'mail.html'),'wb') as a:
                            #     a.write(eachdata_msg_data_raw)
                            href_list = html_fetcher.find_all('a')
                            for href in href_list:
                                if href.get_text().find('下载') != -1:
                                    print('\r正在获取链接(1)...', indent(3),
                                          sep='', end='', flush=True)
                                    bigfile_downloadable_link = None
                                    bigfile_link = href.get('href')
                                    download_page_html = requests.get(
                                        bigfile_link)
                                    html_fetcher_2 = BeautifulSoup(
                                        download_page_html.text, 'lxml')
                                    if find_childstr_to_list(available_bigfile_website_list, bigfile_link):
                                        # wx.mail.qq.com
                                        if bigfile_link.find(available_bigfile_website_list[0]) != -1:
                                            script = html_fetcher_2.select_one(
                                                'body > script:nth-child(2)')
                                            if script.find('var url = ""') == -1:
                                                script = script.get_text()
                                                bigfile_downloadable_link = script[script.find(
                                                    'https://gzc-download.ftn.qq.com'):-1]
                                                bigfile_downloadable_link = bigfile_downloadable_link.replace(
                                                    '\\x26', '&')
                                                bigfile_downloadable_link_list.append(
                                                    bigfile_downloadable_link)
                                        # mail.qq.com
                                        elif bigfile_link.find(available_bigfile_website_list[1]) != -1:
                                            bigfile_downloadable_link = html_fetcher_2.select_one(
                                                '#main > div.ft_d_mainWrapper > div > div > div.ft_d_fileToggle.default > a.ft_d_btnDownload.btn_blue')
                                            if bigfile_downloadable_link:
                                                bigfile_downloadable_link = bigfile_downloadable_link.get(
                                                    'href')
                                            bigfile_downloadable_link_list.append(
                                                bigfile_downloadable_link)
                                    elif find_childstr_to_list(unavailable_bigfile_website_list, bigfile_link):
                                        bigfile_undownloadable_link_list.append(
                                            bigfile_link)
                                        download_state_last_global = 1
                                    if bigfile_downloadable_link:
                                        if not has_downloadable_attachments:
                                            print('\r', indent(1), file_download_count_global+1, ' ', subject,
                                                  indent(8), sep='')
                                        print('\r正在获取链接(2)...', indent(
                                            3), sep='', end='', flush=True)
                                        has_downloadable_attachments_in_mail = True
                                        has_downloadable_attachments = True
                                        bigfile_data = requests.get(
                                            bigfile_downloadable_link, stream=True)
                                        bigfile_name_raw = bigfile_data.headers.get(
                                            'Content-Disposition')
                                        bigfile_name_raw = urllib.parse.unquote(bigfile_name_raw[bigfile_name_raw.find(
                                            'filename*=utf-8\'\'')+len('filename*=utf-8\'\''):len(bigfile_name_raw)])
                                        bigfile_name = operation_parse_file_name(
                                            bigfile_name_raw)
                                        bigfile_name_tmp = operation_parse_file_name(
                                            bigfile_name+'.tmp')
                                        print('\r正在下载超大附件... ', '(', file_download_count+1, ',', file_download_count_global +
                                              1, ')', indent(2), sep='', end='', flush=True)
                                        with open(os.path.join(settings_download_path, bigfile_name_tmp), 'wb') as file:
                                            for bigfile_data_chunk in bigfile_data.iter_content(1024):
                                                file.write(bigfile_data_chunk)
                                        os.renames(
                                            os.path.join(settings_download_path, bigfile_name_tmp), os.path.join(settings_download_path, bigfile_name))
                                        print('\r', indent(2), file_download_count_global+1, ' 已下载 ', bigfile_name, (
                                            ' <- '+bigfile_name_raw)if bigfile_name != bigfile_name_raw else '', indent(2), sep='', flush=True)
                                        file_download_count_global += 1
                                        file_download_count += 1
                                        file_name_list.append(bigfile_name)
            except KeyboardInterrupt as e:
                print('\n回滚操作...', flush=True)
                if file_name:
                    file_name_list.append(file_name)
                if bigfile_name:
                    file_name_list.append(bigfile_name)
                for file_mixed_name in file_name_list:
                    file_mixed_name_tmp = file_mixed_name+'.tmp'
                    if os.path.isfile(os.path.join(settings_download_path, file_mixed_name)):
                        os.remove(os.path.join(
                            settings_download_path, file_mixed_name))
                    if os.path.isfile(os.path.join(settings_download_path, file_mixed_name_tmp)):
                        os.remove(os.path.join(
                            settings_download_path, file_mixed_name_tmp))
                raise KeyboardInterrupt
            else:
                download_state_last_global = 0
            if has_downloadable_attachments:
                msgs_with_downloadable_attachments_list_global[imap_index_int].append(
                    msg_list[msg_index_int])
                file_name_list_global[imap_index_int].append(file_name_list)
            if settings_sign_unseen_tag_after_downloading and download_state_last_global == 0:
                imap_list[imap_index_int].store(msg_list[msg_index_int],
                                                'flags', '\\seen')
            if download_state_last_global == 1:
                if safe_list_find(imap_wrong_index_list, imap_index_int) == -1:
                    imap_wrong_index_list.append(imap_index_int)
                msgs_with_undownloadable_attachments_list_global[imap_index_int].append(
                    msg_list[msg_index_int])
                subject_with_undownloadable_attachments_list_global[imap_index_int].append(
                    subject)
                bigfile_undownloadable_link_list_global[imap_index_int].append(
                    bigfile_undownloadable_link_list)
            msgs_processed_count += 1
            msgs_processed_count_global += 1
        if not is_reconnect_succeed:
            continue
        if not has_downloadable_attachments_in_mail:
            print('\r', indent(1), '无可下载的附件', indent(8), sep='', flush=True)
    stop_time = time.time()
    print('\r总计检索', msgs_processed_count_global, '封邮件,', end='', flush=True)
    if file_download_count_global:
        print('共下载', file_download_count_global, '个附件', flush=True)
    else:
        print('没有可下载的附件', flush=True)
    print('耗时', round(stop_time-start_time, 1), '秒', flush=True)
    if len(imap_connect_failed_index_list[0]):
        print('E: 以下邮箱断开连接,且未能成功连接:', flush=True)
        for imap_connect_failed_index_int in imap_connect_failed_index_list[0]:
            print(
                indent(1), address[imap_connect_failed_index_int], sep='', flush=True)
    if len(imap_connect_failed_index_list[1]):
        print('E: 以下邮箱在下载途中断开连接,且未能成功连接:', flush=True)
        for imap_connect_failed_2_index_int in imap_connect_failed_index_list[1]:
            print(
                indent(1), address[imap_connect_failed_2_index_int], sep='', flush=True)
        print(indent(1), '请尝试重新下载.', sep='', flush=True)
    if len(extract_nested_list(msgs_with_undownloadable_attachments_list_global)):
        bigfile_undownloadable_link_counted_count = 0
        print('W:以下邮件的超大附件无法直接下载,但仍可获取链接:', flush=True)
        for imap_wrong_index_int in imap_wrong_index_list:
            print(indent(
                1), '邮箱: ', address[imap_wrong_index_list[imap_wrong_index_int]], sep='', flush=True)
            for subject_index_int in range(len(subject_with_undownloadable_attachments_list_global[imap_wrong_index_int])):
                print(indent(2), subject_index_int+1, ' ',
                      subject_with_undownloadable_attachments_list_global[imap_wrong_index_int][subject_index_int], sep='', flush=True)
                for link_index_int in range(len(bigfile_undownloadable_link_list_global[imap_wrong_index_int][subject_index_int])):
                    print(indent(3), bigfile_undownloadable_link_counted_count+1, ' ',
                          bigfile_undownloadable_link_list_global[imap_wrong_index_int][subject_index_int][link_index_int], sep='', flush=True)
                    bigfile_undownloadable_link_counted_count += 1
        print(indent(1), '请尝试手动下载.', sep='', flush=True)


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
        if Str.find(j) != -1:
            return True
    return False


def extract_nested_list(List):
    List2 = copy.copy(List)
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
        result = input(prompt)
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
    print('MailDownloader', 'Desingned by Litrix',
          '版本:'+version, '', sep='\n')
    config_load_state = operation_load_config()
    while True:
        command = input_option(
            '请选择操作 [d:下载;r:重载配置文件;n:新建配置文件;q:退出]', 'd', 'r', 'n', 'q', default_option='d', end=':')
        if command == 'd':
            if not config_load_state:
                print('E:配置文件错误,请在重新加载后执行该操作.', flush=True)
            else:
                if command == 'd':
                    program_login_all_imapserver()
                    if not len(imap_list):
                        print('E: 无可用邮箱,请在重新连接后执行该操作.', flush=True)
                        continue
                    if settings_allow_manual_input_search_time:
                        operation_set_time()
                    program_download()
        elif command == 'r':
            config_load_state = operation_load_config()
        elif command == 'n':
            if input_option('此操作将生成 config_new.toml,是否继续?', 'y', 'n', default_option='n', end=':') == 'y':
                with open(os.path.join(os.path.dirname(__file__), 'config_new.toml'), 'w') as config_new_file:
                    rtoml.dump(config_primary_data, config_new_file)
                print('操作成功完成.', flush=True)
        elif command == 'q':
            break
    print('正在关闭连接...', flush=True)
    operation_close_all_connection()
    nexit(0)
except KeyboardInterrupt:
    print('\n强制退出', flush=True)
    operation_close_all_connection()
    nexit(1)
