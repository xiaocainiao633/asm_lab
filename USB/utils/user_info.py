"""
用户信息获取模块
功能：获取当前系统登录用户信息
"""
import os
import getpass

def get_current_user():
    """
    获取当前登录用户名
    返回: 用户名字符串
    """
    try:
        # 方法1: 使用 getpass
        username = getpass.getuser()
        return username
    except Exception as e:
        # 方法2: 使用环境变量
        try:
            return os.environ.get('USERNAME', 'Unknown')
        except:
            return 'Unknown'

def get_user_info():
    """
    获取详细的用户信息
    返回: 包含用户信息的字典
    """
    info = {
        'username': get_current_user(),
        'home_dir': os.path.expanduser('~'),
        'current_dir': os.getcwd()
    }
    return info
