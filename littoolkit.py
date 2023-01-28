"""小工具合集."""
import base64
import os
__version__ = '1.0.0'
__author__ = 'Litrix'

def indent(count: int, unit_count: int = 4, unit_char: str = ' ') -> str:
    """实现输出缩进功能."""
    indent_str = ''
    for _ in range(0, count*unit_count):
        indent_str += unit_char
    return indent_str


def safe_list_find(List: list, element):
    """
    安全查找列表中元素.
    如果列表中没有指定元素,返回-1,而不是报错.
    """
    try:
        index = List.index(element)
        return index
    except ValueError:
        return -1


def find_list_substr(List: str, Str: str):
    """遍历列表,判断列表中字符串是否为指定字符串的子字符串."""
    for j in List:
        if j in Str:
            return True
    return False


def extract_nested_list(List: list):
    """展开嵌套列表."""
    result_list = []
    for i in range(len(List)):
        if isinstance(List[i], list) or isinstance(List[i], tuple):
            result_list += extract_nested_list(List[i])
        else:
            result_list.append(List[i])
    return result_list


def _base64_encode(source: str):
    return b'&'+base64.b64encode(source.encode('UTF-16BE')).rstrip(b'==').replace(b'/', b',')+b'-' if source else b''


def imap_utf7_bytes_encode(source: str):
    """将字符串编码成IMAP协议专用的UTF-7格式字节串."""
    result = b''
    base64_str = ''
    for char in source:
        char_int = ord(char)
        if char_int <= 0x7f:
            result += _base64_encode(base64_str)
            base64_str = ''
            if char_int == ord('&'):
                result += b'&-'
            else:
                result += char.encode()
        else:
            base64_str += char
    result += _base64_encode(base64_str)
    base64_str = ''
    return bytes(result)


def imap_utf7_bytes_decode(source: bytes):
    """将成IMAP协议专用的UTF-7格式字节串解码成字符串."""
    result = ''
    base64_status = False
    ampersand_status = False
    base64_bytes = b''
    for byte_int, byte in enumerate(source):
        byte = byte.to_bytes()
        if byte == b'&':
            if source[byte_int+1].to_bytes() == b'-':
                ampersand_status = True
                result += '&'
            else:
                base64_status = True
        elif byte == b'-':
            if base64_status:
                base64_status = False
                base64_bytes = base64_bytes.replace(b',', b'/')
                result += base64.b64decode(base64_bytes +
                                           b'==').decode('UTF-16BE')
                base64_bytes = b''
            elif ampersand_status:
                ampersand_status = False
            else:
                result += '-'
        else:
            if base64_status:
                base64_bytes += byte
            else:
                result += byte.decode()
    return result

def input_option(prompt: str, *options: str, allow_undefind_input: bool = False, default_option: str = '', end: str = ''):
    """实现输入选项功能."""
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
        try:
            print(prompt, end='', flush=True)
            result = input()
            if not len(result) and len(default_option):
                return default_option
            else:
                if not allow_undefind_input:
                    if safe_list_find(options, result) == -1:
                        raise ValueError
                return result
        except Exception:
            print('无效选项,请重新输入.', flush=True)


def pause_exit(code: int = 0):
    """先暂停再退出."""
    input_option('按回车键退出 ', allow_undefind_input=True)
    exit(code)
