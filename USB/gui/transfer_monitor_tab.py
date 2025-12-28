"""
传输监控标签页
功能：实时传输进度、传输速率显示、设备状态监控
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QTextEdit, QGroupBox,
                             QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
import time

class TransferMonitorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.transfer_history = []
        self.init_ui()
    
    def init_ui(self):
        """初始化传输监控界面"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # USB 生命周期状态组
        lifecycle_group = QGroupBox('🔄 USB 设备生命周期状态')
        lifecycle_layout = QVBoxLayout()
        lifecycle_group.setLayout(lifecycle_layout)
        
        # 生命周期状态标签
        self.lifecycle_status = QLabel('等待设备插入...')
        self.lifecycle_status.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
            padding: 15px;
            color: #a8e063;
            background: rgba(168, 224, 99, 0.1);
            border-radius: 8px;
            border: 2px solid rgba(168, 224, 99, 0.3);
        """)
        lifecycle_layout.addWidget(self.lifecycle_status)
        
        # 生命周期步骤指示器
        steps_widget = QWidget()
        steps_layout = QHBoxLayout()
        steps_widget.setLayout(steps_layout)
        
        self.step_labels = {}
        steps = [
            ('插入', 'insert'),
            ('枚举', 'enumerate'),
            ('挂载', 'mount'),
            ('可读写', 'ready'),
            ('安全移除', 'eject'),
            ('拔出', 'remove')
        ]
        
        for step_name, step_key in steps:
            step_label = QLabel(step_name)
            step_label.setAlignment(Qt.AlignCenter)
            step_label.setStyleSheet("""
                padding: 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.5);
                font-size: 13px;
                min-width: 80px;
            """)
            self.step_labels[step_key] = step_label
            steps_layout.addWidget(step_label)
        
        lifecycle_layout.addWidget(steps_widget)
        layout.addWidget(lifecycle_group)
        
        # 当前传输状态组 - 现代化设计
        current_group = QGroupBox('📊 当前传输状态')
        current_group.setStyleSheet("""
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border: 2px solid #2196F3;
            }
        """)
        current_layout = QVBoxLayout()
        current_group.setLayout(current_layout)
        
        # 传输信息
        self.transfer_info_label = QLabel('暂无传输任务')
        self.transfer_info_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            padding: 10px;
            color: #1976d2;
            background: transparent;
        """)
        current_layout.addWidget(self.transfer_info_label)
        
        # 进度条 - 现代化设计
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 12px;
                text-align: center;
                height: 28px;
                background-color: #e0e0e0;
                font-size: 13px;
                font-weight: 700;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:0.5 #66BB6A, stop:1 #81C784);
                border-radius: 12px;
            }
        """)
        current_layout.addWidget(self.progress_bar)
        
        # 传输速率 - 三速率显示卡片式设计
        speed_widget = QWidget()
        speed_widget.setStyleSheet("""
            background: white;
            border-radius: 10px;
            padding: 15px;
        """)
        speed_layout = QHBoxLayout()
        speed_widget.setLayout(speed_layout)
        
        # 当前速率显示
        current_speed_card = QWidget()
        current_speed_card.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #e8f5e9, stop:1 #c8e6c9);
            border-radius: 8px;
            padding: 10px;
        """)
        current_speed_layout = QVBoxLayout()
        current_speed_card.setLayout(current_speed_layout)
        
        current_speed_title = QLabel('⚡ 当前速率')
        current_speed_title.setStyleSheet("""
            font-size: 12px;
            color: #2e7d32;
            background: transparent;
        """)
        current_speed_layout.addWidget(current_speed_title)
        
        self.current_speed_label = QLabel('0 B/s')
        self.current_speed_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #4CAF50;
            background: transparent;
        """)
        current_speed_layout.addWidget(self.current_speed_label)
        
        speed_layout.addWidget(current_speed_card)
        
        # 平均速率显示
        avg_speed_card = QWidget()
        avg_speed_card.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #e3f2fd, stop:1 #bbdefb);
            border-radius: 8px;
            padding: 10px;
        """)
        avg_speed_layout = QVBoxLayout()
        avg_speed_card.setLayout(avg_speed_layout)
        
        avg_speed_title = QLabel('📊 平均速率')
        avg_speed_title.setStyleSheet("""
            font-size: 12px;
            color: #1565c0;
            background: transparent;
        """)
        avg_speed_layout.addWidget(avg_speed_title)
        
        self.avg_speed_label = QLabel('0 B/s')
        self.avg_speed_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2196F3;
            background: transparent;
        """)
        avg_speed_layout.addWidget(self.avg_speed_label)
        
        speed_layout.addWidget(avg_speed_card)
        
        # 峰值速率显示
        peak_speed_card = QWidget()
        peak_speed_card.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #fff3e0, stop:1 #ffe0b2);
            border-radius: 8px;
            padding: 10px;
        """)
        peak_speed_layout = QVBoxLayout()
        peak_speed_card.setLayout(peak_speed_layout)
        
        peak_speed_title = QLabel('🚀 峰值速率')
        peak_speed_title.setStyleSheet("""
            font-size: 12px;
            color: #e65100;
            background: transparent;
        """)
        peak_speed_layout.addWidget(peak_speed_title)
        
        self.peak_speed_label = QLabel('0 B/s')
        self.peak_speed_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #ff9800;
            background: transparent;
        """)
        peak_speed_layout.addWidget(self.peak_speed_label)
        
        speed_layout.addWidget(peak_speed_card)
        
        current_layout.addWidget(speed_widget)
        
        layout.addWidget(current_group)
        
        # USB 设备状态监控组
        device_group = QGroupBox('🔌 USB 设备状态监控')
        device_layout = QVBoxLayout()
        device_group.setLayout(device_layout)
        
        self.device_status_list = QListWidget()
        self.device_status_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 8px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                margin: 3px 0;
            }
            QListWidget::item:selected {
                background: rgba(168, 224, 99, 0.3);
                color: #a8e063;
            }
            QListWidget::item:hover:!selected {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        device_layout.addWidget(self.device_status_list)
        
        # 刷新按钮
        refresh_btn = QPushButton('🔄 刷新设备状态')
        refresh_btn.clicked.connect(self.refresh_device_status)
        device_layout.addWidget(refresh_btn)
        
        layout.addWidget(device_group)
        
        # 传输历史组
        history_group = QGroupBox('📜 传输历史')
        history_layout = QVBoxLayout()
        history_group.setLayout(history_layout)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setMinimumHeight(200)  # 增加最小高度，移除最大高度限制
        self.history_text.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 10px;
            color: #e0e0e0;
            font-size: 13px;
        """)
        history_layout.addWidget(self.history_text)
        
        # 清除历史按钮
        clear_btn = QPushButton('🗑️ 清除历史')
        clear_btn.clicked.connect(self.clear_history)
        history_layout.addWidget(clear_btn)
        
        layout.addWidget(history_group)
        
        # 定时刷新设备状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_device_status)
        self.status_timer.start(3000)  # 每 3 秒刷新一次
    
    def refresh_device_status(self):
        """刷新设备状态"""
        self.device_status_list.clear()
        
        if hasattr(self.parent_window, 'usb_devices') and len(self.parent_window.usb_devices) > 0:
            for device in self.parent_window.usb_devices:
                status_text = (
                    f"🟢 {device['mountpoint']} - {device['model']}\n"
                    f"   状态: 已连接 | "
                    f"可用: {self.format_size(device['free'])} / {self.format_size(device['total'])} | "
                    f"使用率: {device['percent']:.1f}%"
                )
                
                item = QListWidgetItem(status_text)
                
                # 根据使用率设置颜色
                if device['percent'] > 90:
                    item.setForeground(Qt.red)
                elif device['percent'] > 70:
                    item.setForeground(Qt.darkYellow)
                else:
                    item.setForeground(Qt.darkGreen)
                
                self.device_status_list.addItem(item)
        else:
            # 空状态：显示系统诊断信息
            self.show_empty_state_info()
    
    def start_transfer(self, source, target, size):
        """开始传输"""
        self.transfer_info_label.setText(f'正在传输: {source} → {target}')
        self.progress_bar.setValue(0)
        self.current_speed_label.setText('0 B/s')
        self.avg_speed_label.setText('0 B/s')
        self.peak_speed_label.setText('0 B/s')
    
    def update_transfer_progress(self, progress, current_speed, avg_speed, peak_speed):
        """更新传输进度
        
        Args:
            progress: 进度百分比 (0-100)
            current_speed: 当前速率字符串
            avg_speed: 平均速率字符串
            peak_speed: 峰值速率字符串
        """
        self.progress_bar.setValue(int(progress))
        self.current_speed_label.setText(current_speed)
        self.avg_speed_label.setText(avg_speed)
        self.peak_speed_label.setText(peak_speed)
    
    def finish_transfer(self, success, message, speed):
        """完成传输"""
        if success:
            self.transfer_info_label.setText('✓ 传输完成')
            self.progress_bar.setValue(100)
        else:
            self.transfer_info_label.setText('✗ 传输失败')
        
        # 添加到历史
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        status = '✓ 成功' if success else '✗ 失败'
        history_entry = f"[{timestamp}] {status} - {message} | 速率: {speed}"
        
        self.transfer_history.append(history_entry)
        self.history_text.append(history_entry)
    
    def clear_history(self):
        """清除传输历史"""
        self.transfer_history.clear()
        self.history_text.clear()
    
    def show_empty_state_info(self):
        """显示空状态信息（无 USB 设备时）"""
        import psutil
        
        # 标题
        title_item = QListWidgetItem('⚠️ 未检测到 USB 设备')
        title_item.setForeground(Qt.darkGray)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        title_item.setFont(font)
        self.device_status_list.addItem(title_item)
        
        # 分隔线
        separator = QListWidgetItem('─' * 50)
        separator.setForeground(Qt.lightGray)
        self.device_status_list.addItem(separator)
        
        # 扫描时间
        scan_time = time.strftime('%Y-%m-%d %H:%M:%S')
        time_item = QListWidgetItem(f'🕐 最近扫描时间: {scan_time}')
        time_item.setForeground(Qt.darkBlue)
        self.device_status_list.addItem(time_item)
        
        # USB 监听状态
        monitoring_status = '✓ 激活' if self.status_timer.isActive() else '✗ 未激活'
        monitor_item = QListWidgetItem(f'📡 USB 监听状态: {monitoring_status}')
        monitor_item.setForeground(Qt.darkGreen if self.status_timer.isActive() else Qt.red)
        self.device_status_list.addItem(monitor_item)
        
        # 扫描间隔
        interval = self.status_timer.interval() / 1000
        interval_item = QListWidgetItem(f'⏱️ 扫描间隔: {interval:.0f} 秒')
        interval_item.setForeground(Qt.darkBlue)
        self.device_status_list.addItem(interval_item)
        
        # 系统磁盘信息
        try:
            partitions = psutil.disk_partitions()
            disk_count = len(partitions)
            removable_count = sum(1 for p in partitions if 'removable' in p.opts.lower())
            
            disk_item = QListWidgetItem(f'💾 系统可识别磁盘: {disk_count} 个')
            disk_item.setForeground(Qt.darkMagenta)
            self.device_status_list.addItem(disk_item)
            
            removable_item = QListWidgetItem(f'🔌 可移动设备插槽: {removable_count} 个')
            removable_item.setForeground(Qt.darkMagenta)
            self.device_status_list.addItem(removable_item)
            
            # 显示所有盘符
            drive_letters = [p.device for p in partitions]
            drives_text = ', '.join(drive_letters) if drive_letters else '无'
            drives_item = QListWidgetItem(f'📂 当前盘符: {drives_text}')
            drives_item.setForeground(Qt.darkCyan)
            self.device_status_list.addItem(drives_item)
            
        except Exception as e:
            error_item = QListWidgetItem(f'⚠️ 无法获取磁盘信息: {str(e)}')
            error_item.setForeground(Qt.red)
            self.device_status_list.addItem(error_item)
        
        # 分隔线
        separator2 = QListWidgetItem('─' * 50)
        separator2.setForeground(Qt.lightGray)
        self.device_status_list.addItem(separator2)
        
        # 提示信息
        tip_item = QListWidgetItem('💡 提示: 插入 USB 设备后将自动检测')
        tip_item.setForeground(Qt.darkGray)
        self.device_status_list.addItem(tip_item)
    
    def update_lifecycle_status(self, step, status='active', message=''):
        """更新 USB 生命周期状态
        
        Args:
            step: 步骤名称 ('insert', 'enumerate', 'mount', 'ready', 'eject', 'remove')
            status: 状态 ('active', 'completed', 'error', 'inactive')
            message: 状态消息
        """
        step_names = {
            'insert': '插入',
            'enumerate': '枚举',
            'mount': '挂载',
            'ready': '可读写',
            'eject': '安全移除',
            'remove': '拔出'
        }
        
        # 更新主状态标签
        if message:
            self.lifecycle_status.setText(message)
        else:
            self.lifecycle_status.setText(f'当前状态: {step_names.get(step, step)}')
        
        # 更新步骤指示器颜色
        if step in self.step_labels:
            label = self.step_labels[step]
            
            if status == 'active':
                # 当前活动步骤 - 蓝色
                label.setStyleSheet("""
                    padding: 10px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #2196F3, stop:1 #1976D2);
                    border-radius: 6px;
                    color: white;
                    font-size: 13px;
                    font-weight: 700;
                    min-width: 80px;
                """)
                self.lifecycle_status.setStyleSheet("""
                    font-size: 16px;
                    font-weight: 700;
                    padding: 15px;
                    color: #2196F3;
                    background: rgba(33, 150, 243, 0.1);
                    border-radius: 8px;
                    border: 2px solid rgba(33, 150, 243, 0.3);
                """)
            elif status == 'completed':
                # 已完成步骤 - 绿色
                label.setStyleSheet("""
                    padding: 10px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #4CAF50, stop:1 #45a049);
                    border-radius: 6px;
                    color: white;
                    font-size: 13px;
                    font-weight: 700;
                    min-width: 80px;
                """)
            elif status == 'error':
                # 错误状态 - 红色
                label.setStyleSheet("""
                    padding: 10px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #f44336, stop:1 #d32f2f);
                    border-radius: 6px;
                    color: white;
                    font-size: 13px;
                    font-weight: 700;
                    min-width: 80px;
                """)
                self.lifecycle_status.setStyleSheet("""
                    font-size: 16px;
                    font-weight: 700;
                    padding: 15px;
                    color: #f44336;
                    background: rgba(244, 67, 54, 0.1);
                    border-radius: 8px;
                    border: 2px solid rgba(244, 67, 54, 0.3);
                """)
            else:  # inactive
                # 未激活步骤 - 灰色
                label.setStyleSheet("""
                    padding: 10px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 6px;
                    color: rgba(255, 255, 255, 0.5);
                    font-size: 13px;
                    min-width: 80px;
                """)
    
    def reset_lifecycle_status(self):
        """重置生命周期状态"""
        self.lifecycle_status.setText('等待设备插入...')
        self.lifecycle_status.setStyleSheet("""
            font-size: 16px;
            font-weight: 700;
            padding: 15px;
            color: #a8e063;
            background: rgba(168, 224, 99, 0.1);
            border-radius: 8px;
            border: 2px solid rgba(168, 224, 99, 0.3);
        """)
        
        for label in self.step_labels.values():
            label.setStyleSheet("""
                padding: 10px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                color: rgba(255, 255, 255, 0.5);
                font-size: 13px;
                min-width: 80px;
            """)
    
    def format_size(self, bytes_size):
        """格式化字节大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
