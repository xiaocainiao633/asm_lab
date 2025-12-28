"""
USB 设备检测模块
功能：检测系统中的 USB 设备及其信息
"""
import psutil
import os
import string
import subprocess
import re

def get_usb_device_details_wmi(drive_letter):
    """
    使用 WMI 获取 USB 设备详细信息
    参数: drive_letter - 驱动器盘符 (如 'E:')
    返回: 设备详细信息字典
    """
    try:
        import wmi
        c = wmi.WMI()
        
        # 获取逻辑磁盘信息
        for disk in c.Win32_LogicalDisk():
            if disk.DeviceID == drive_letter.rstrip('\\'):
                # 查找对应的物理磁盘
                for disk_drive in c.Win32_DiskDrive():
                    if disk_drive.InterfaceType == 'USB':
                        # 检查是否是对应的磁盘
                        for partition in disk_drive.associators("Win32_DiskDriveToDiskPartition"):
                            for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                                if logical_disk.DeviceID == disk.DeviceID:
                                    return {
                                        'manufacturer': disk_drive.Manufacturer or '未知',
                                        'model': disk_drive.Model or '未知',
                                        'serial_number': disk_drive.SerialNumber.strip() if disk_drive.SerialNumber else '未知',
                                        'interface_type': disk_drive.InterfaceType,
                                        'media_type': disk_drive.MediaType or '未知',
                                        'size': disk_drive.Size
                                    }
    except Exception as e:
        pass
    
    return None

def get_usb_device_details_powershell(drive_letter):
    """
    使用 PowerShell 获取 USB 设备详细信息
    """
    try:
        # 移除尾部的反斜杠
        drive = drive_letter.rstrip('\\')
        
        # 使用 PowerShell 获取详细的 USB 设备信息
        ps_script = f'''
$drive = "{drive}"
$partition = Get-Partition | Where-Object {{$_.DriveLetter -eq $drive.Replace(":", "")}}
if ($partition) {{
    $disk = Get-Disk -Number $partition.DiskNumber
    $physicalDisk = Get-PhysicalDisk | Where-Object {{$_.DeviceId -eq $disk.Number}}
    
    $result = @{{
        FriendlyName = $disk.FriendlyName
        SerialNumber = if ($physicalDisk.SerialNumber) {{$physicalDisk.SerialNumber}} else {{"未知"}}
        BusType = $disk.BusType
        MediaType = $physicalDisk.MediaType
        Manufacturer = if ($physicalDisk.Manufacturer) {{$physicalDisk.Manufacturer}} else {{"未知"}}
        Model = $disk.Model
        Size = $disk.Size
    }}
    
    $result | ConvertTo-Json
}}
'''
        
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            timeout=5,
            encoding='utf-8'
        )
        
        if result.returncode == 0 and result.stdout.strip():
            import json
            device_info = json.loads(result.stdout)
            
            return {
                'manufacturer': device_info.get('Manufacturer', '未知'),
                'model': device_info.get('Model', device_info.get('FriendlyName', '未知')),
                'serial_number': device_info.get('SerialNumber', '未知'),
                'interface_type': device_info.get('BusType', 'USB'),
                'media_type': device_info.get('MediaType', '可移动磁盘'),
                'size': device_info.get('Size', 0)
            }
    except Exception as e:
        pass
    
    return None

def get_usb_drives():
    """
    获取所有可移动 USB 驱动器（增强版，包含详细信息）
    返回: USB 驱动器信息列表
    """
    usb_drives = []
    
    try:
        # 获取所有磁盘分区
        partitions = psutil.disk_partitions()
        
        for partition in partitions:
            # 在 Windows 上，可移动设备的 fstype 通常包含 'removable' 或检查 opts
            if 'removable' in partition.opts.lower() or partition.fstype == '':
                try:
                    # 获取磁盘使用情况
                    usage = psutil.disk_usage(partition.mountpoint)
                    
                    # 获取详细的设备信息（优先使用 PowerShell，然后尝试 WMI）
                    details = get_usb_device_details_powershell(partition.mountpoint)
                    if not details:
                        details = get_usb_device_details_wmi(partition.mountpoint)
                    
                    if not details:
                        details = {
                            'manufacturer': '未知',
                            'model': '未知',
                            'serial_number': '未知',
                            'interface_type': 'USB',
                            'media_type': '可移动磁盘',
                            'size': usage.total
                        }
                    
                    drive_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype if partition.fstype else 'FAT32',
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': usage.percent,
                        # 新增详细信息
                        'manufacturer': details['manufacturer'],
                        'model': details['model'],
                        'serial_number': details['serial_number'],
                        'interface_type': details['interface_type'],
                        'media_type': details['media_type']
                    }
                    usb_drives.append(drive_info)
                except Exception as e:
                    # 某些驱动器可能无法访问
                    continue
    except Exception as e:
        print(f"获取 USB 驱动器时出错: {e}")
    
    return usb_drives


def classify_usb_device(device_info):
    """
    分类 USB 设备
    参数: device_info - 设备信息字典
    返回: 设备类型和分类信息
    """
    device_type = 'storage'  # 默认为存储设备
    device_category = '存储设备'
    device_icon = '💾'
    supports_file_ops = True
    
    # 根据介质类型判断
    media_type = device_info.get('media_type', '').lower()
    model = device_info.get('model', '').lower()
    
    # 判断是否为固态硬盘
    if 'ssd' in media_type or 'ssd' in model:
        device_category = '固态硬盘 (SSD)'
        device_icon = '⚡'
    # 判断是否为机械硬盘
    elif 'hdd' in media_type or 'hard' in media_type:
        device_category = '机械硬盘 (HDD)'
        device_icon = '💿'
    # 判断是否为 U 盘
    elif 'removable' in media_type or device_info.get('total', 0) < 128 * 1024 * 1024 * 1024:  # 小于128GB
        device_category = 'U 盘'
        device_icon = '🔌'
    # 移动硬盘
    else:
        device_category = '移动硬盘'
        device_icon = '💾'
    
    return {
        'type': device_type,
        'category': device_category,
        'icon': device_icon,
        'supports_file_ops': supports_file_ops,
        'description': f'{device_icon} {device_category}'
    }


def get_all_usb_devices():
    """
    获取所有 USB 设备（包括非存储设备）
    返回: 所有 USB 设备信息列表
    """
    all_devices = []
    
    # 获取存储设备
    storage_devices = get_usb_drives()
    for device in storage_devices:
        classification = classify_usb_device(device)
        device.update(classification)
        all_devices.append(device)
    
    # TODO: 添加 HID 设备检测（键盘、鼠标等）
    # TODO: 添加其他 USB 设备检测（摄像头、打印机等）
    
    return all_devices


def format_size(bytes_size):
    """
    格式化字节大小为可读格式
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def get_usb_device_info(drive_letter):
    """
    获取指定驱动器的详细信息
    参数: drive_letter - 驱动器盘符 (如 'E:')
    返回: 设备详细信息字典
    """
    try:
        usage = psutil.disk_usage(drive_letter)
        
        info = {
            'drive': drive_letter,
            'total_size': format_size(usage.total),
            'used_size': format_size(usage.used),
            'free_size': format_size(usage.free),
            'usage_percent': f"{usage.percent}%"
        }
        
        return info
    except Exception as e:
        return None

def is_usb_drive(drive_letter):
    """
    检查指定驱动器是否为 USB 设备
    参数: drive_letter - 驱动器盘符 (如 'E:')
    返回: True/False
    """
    try:
        partitions = psutil.disk_partitions()
        for partition in partitions:
            if partition.device.startswith(drive_letter):
                return 'removable' in partition.opts.lower()
        return False
    except:
        return False
