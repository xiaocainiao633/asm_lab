"""
文件操作模块
功能：实现向 USB 设备写入、拷贝和删除文件
"""
import os
import shutil
import time
from PyQt5.QtCore import QObject, pyqtSignal


class TransferMonitor(QObject):
    """文件传输监控类"""
    progress_updated = pyqtSignal(int, str, str, str)  # 进度, 当前速率, 平均速率, 峰值速率
    
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.transferred_bytes = 0
        self.current_speed = 0
        self.average_speed = 0
        self.peak_speed = 0
        self.speed_history = []
        self.last_update_time = None
        self.last_transferred_bytes = 0
    
    def start(self, total_size):
        """开始传输监控"""
        self.start_time = time.time()
        self.transferred_bytes = 0
        self.current_speed = 0
        self.average_speed = 0
        self.peak_speed = 0
        self.speed_history = []
        self.last_update_time = self.start_time
        self.last_transferred_bytes = 0
        self.total_size = total_size
    
    def update(self, bytes_transferred):
        """更新传输统计"""
        current_time = time.time()
        self.transferred_bytes = bytes_transferred
        
        # 计算当前速率（基于上次更新）
        time_delta = current_time - self.last_update_time
        if time_delta > 0:
            bytes_delta = bytes_transferred - self.last_transferred_bytes
            self.current_speed = bytes_delta / time_delta
            
            # 更新峰值速率
            if self.current_speed > self.peak_speed:
                self.peak_speed = self.current_speed
            
            # 记录历史
            self.speed_history.append(self.current_speed)
            if len(self.speed_history) > 100:  # 只保留最近100个数据点
                self.speed_history.pop(0)
        
        # 计算平均速率
        elapsed = current_time - self.start_time
        if elapsed > 0:
            self.average_speed = self.transferred_bytes / elapsed
        
        # 计算进度
        progress = int((self.transferred_bytes / self.total_size) * 100) if self.total_size > 0 else 0
        
        # 发送更新信号
        self.progress_updated.emit(
            progress,
            format_transfer_rate(self.current_speed),
            format_transfer_rate(self.average_speed),
            format_transfer_rate(self.peak_speed)
        )
        
        self.last_update_time = current_time
        self.last_transferred_bytes = bytes_transferred
    
    def finish(self):
        """完成传输"""
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            self.average_speed = self.transferred_bytes / elapsed
        return format_transfer_rate(self.average_speed)


def write_text_file(target_path, filename, content):
    """
    向指定路径写入文本文件
    参数:
        target_path: 目标路径（如 'E:\\'）
        filename: 文件名
        content: 文件内容
    返回: (成功标志, 消息)
    """
    try:
        full_path = os.path.join(target_path, filename)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True, f"成功写入文件: {full_path}"
    except PermissionError:
        return False, "权限不足，无法写入文件"
    except Exception as e:
        return False, f"写入文件失败: {str(e)}"

def copy_file_to_usb_with_progress(source_file, target_path, monitor=None):
    """
    拷贝文件到 USB 设备（支持进度监控）
    参数:
        source_file: 源文件路径
        target_path: 目标路径（如 'E:\\'）
        monitor: TransferMonitor 实例 (可选)
    返回: (成功标志, 消息, 传输速率)
    """
    try:
        if not os.path.exists(source_file):
            return False, "源文件不存在", "0 B/s"
        
        filename = os.path.basename(source_file)
        target_file = os.path.join(target_path, filename)
        
        # 获取文件大小
        file_size = os.path.getsize(source_file)
        
        # 初始化监控
        if monitor:
            monitor.start(file_size)
        
        # 记录开始时间
        start_time = time.time()
        
        # 分块拷贝文件以支持进度更新
        chunk_size = 1024 * 1024  # 1MB
        transferred = 0
        
        with open(source_file, 'rb') as src:
            with open(target_file, 'wb') as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    transferred += len(chunk)
                    
                    # 更新监控
                    if monitor:
                        monitor.update(transferred)
        
        # 计算传输时间和速率
        elapsed_time = time.time() - start_time
        transfer_rate = file_size / elapsed_time if elapsed_time > 0 else 0
        
        # 格式化传输速率
        if monitor:
            rate_str = monitor.finish()
        else:
            rate_str = format_transfer_rate(transfer_rate)
        
        return True, f"成功拷贝文件: {filename} 到 {target_path}", rate_str
    except PermissionError:
        return False, "权限不足，无法拷贝文件", "0 B/s"
    except Exception as e:
        return False, f"拷贝文件失败: {str(e)}", "0 B/s"


def copy_file_to_usb(source_file, target_path, callback=None):
    """
    拷贝文件到 USB 设备
    参数:
        source_file: 源文件路径
        target_path: 目标路径（如 'E:\\'）
        callback: 进度回调函数 (可选)
    返回: (成功标志, 消息, 传输速率)
    """
    try:
        if not os.path.exists(source_file):
            return False, "源文件不存在", 0
        
        filename = os.path.basename(source_file)
        target_file = os.path.join(target_path, filename)
        
        # 获取文件大小
        file_size = os.path.getsize(source_file)
        
        # 记录开始时间
        start_time = time.time()
        
        # 拷贝文件
        shutil.copy2(source_file, target_file)
        
        # 计算传输时间和速率
        elapsed_time = time.time() - start_time
        transfer_rate = file_size / elapsed_time if elapsed_time > 0 else 0
        
        # 格式化传输速率
        rate_str = format_transfer_rate(transfer_rate)
        
        return True, f"成功拷贝文件: {filename} 到 {target_path}", rate_str
    except PermissionError:
        return False, "权限不足，无法拷贝文件", "0 B/s"
    except Exception as e:
        return False, f"拷贝文件失败: {str(e)}", "0 B/s"


def delete_file_from_usb(file_path):
    """
    从 USB 设备删除文件
    参数:
        file_path: 要删除的文件完整路径
    返回: (成功标志, 消息)
    """
    try:
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        if os.path.isfile(file_path):
            os.remove(file_path)
            return True, f"成功删除文件: {file_path}"
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
            return True, f"成功删除文件夹: {file_path}"
        else:
            return False, "未知的文件类型"
    except PermissionError:
        return False, "权限不足，无法删除文件"
    except Exception as e:
        return False, f"删除文件失败: {str(e)}"

def list_files_in_directory(directory_path, show_hidden=True):
    """
    列出目录中的所有文件（包括隐藏文件）
    参数:
        directory_path: 目录路径
        show_hidden: 是否显示隐藏文件
    返回: 文件列表
    """
    try:
        files = []
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            is_hidden = is_hidden_file(item_path)
            
            if not show_hidden and is_hidden:
                continue
            
            file_info = {
                'name': item,
                'path': item_path,
                'is_dir': os.path.isdir(item_path),
                'is_hidden': is_hidden,
                'size': os.path.getsize(item_path) if os.path.isfile(item_path) else 0
            }
            files.append(file_info)
        
        return files
    except Exception as e:
        return []

def is_hidden_file(file_path):
    """
    检查文件是否为隐藏文件（Windows）
    """
    try:
        import ctypes
        attrs = ctypes.windll.kernel32.GetFileAttributesW(file_path)
        return attrs != -1 and bool(attrs & 2)  # FILE_ATTRIBUTE_HIDDEN = 2
    except:
        # 如果无法使用 Windows API，则根据文件名判断
        return os.path.basename(file_path).startswith('.')

def format_transfer_rate(bytes_per_second):
    """
    格式化传输速率
    """
    for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
        if bytes_per_second < 1024.0:
            return f"{bytes_per_second:.2f} {unit}"
        bytes_per_second /= 1024.0
    return f"{bytes_per_second:.2f} TB/s"
