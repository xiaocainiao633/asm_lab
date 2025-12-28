"""
主窗口界面 - 多标签页版本
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QGroupBox, QListWidget,
                             QMessageBox, QFileDialog, QProgressBar, QInputDialog,
                             QTabWidget, QApplication, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import time
from utils.user_info import get_current_user, get_user_info
from utils.usb_detector import get_usb_drives, format_size
from utils.file_operations import (write_text_file, copy_file_to_usb, delete_file_from_usb,
                                   copy_file_to_usb_with_progress, TransferMonitor, format_transfer_rate)
from gui.file_manager_tab import FileManagerTab
from gui.transfer_monitor_tab import TransferMonitorTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.usb_devices = []  # 存储当前 USB 设备列表
        self.init_ui()
        self.load_user_info()
        self.refresh_usb_devices()
        
        # 设置定时器，每 2 秒检测一次 USB 设备变化
        self.usb_monitor_timer = QTimer()
        self.usb_monitor_timer.timeout.connect(self.monitor_usb_changes)
        self.usb_monitor_timer.start(2000)  # 2000 毫秒 = 2 秒
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('USB 总线及挂载设备测试系统')
        self.setGeometry(100, 100, 1400, 900)  # 增大默认窗口尺寸
        self.setMinimumSize(1200, 800)  # 设置最小窗口尺寸
        
        # 设置超现代化样式
        self.setStyleSheet("""
            /* 主窗口 - 深色渐变背景 */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
            }
            
            /* 分组框 - 玻璃态卡片设计 */
            QGroupBox {
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                font-weight: 600;
                font-size: 17px;
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 16px;
                margin-top: 20px;
                padding: 25px 20px 20px 20px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 20px;
                top: 10px;
                padding: 0 10px;
                color: #4CAF50;
                font-size: 18px;
            }
            
            /* 按钮 - 发光效果 */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #56ab2f, stop:1 #a8e063);
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 10px;
                font-size: 15px;
                font-weight: 600;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                min-height: 45px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a8e063, stop:1 #56ab2f);
                box-shadow: 0 0 20px rgba(86, 171, 47, 0.6);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3d7c1f, stop:1 #7cb342);
                padding-top: 14px;
                padding-bottom: 10px;
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
            
            /* 标签 - 亮色文字 */
            QLabel {
                font-size: 15px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                color: #e0e0e0;
            }
            
            /* 标签页 - 霓虹效果 */
            QTabWidget::pane {
                border: none;
                background-color: transparent;
                border-radius: 16px;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.6);
                padding: 16px 32px;
                margin-right: 6px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: 15px;
                font-weight: 600;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                min-width: 150px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #56ab2f, stop:1 #a8e063);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                box-shadow: 0 0 15px rgba(86, 171, 47, 0.5);
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            /* 列表控件 - 玻璃态 */
            QListWidget {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                outline: none;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 16px;
                border-radius: 8px;
                margin: 4px 0;
                border-left: 4px solid transparent;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(86, 171, 47, 0.3), stop:1 rgba(168, 224, 99, 0.3));
                color: #a8e063;
                border-left: 4px solid #56ab2f;
                font-weight: 600;
            }
            QListWidget::item:hover:!selected {
                background: rgba(255, 255, 255, 0.1);
                border-left: 4px solid rgba(255, 255, 255, 0.3);
            }
            
            /* 文本编辑框 - 深色主题 */
            QTextEdit, QLineEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                padding: 14px;
                font-size: 14px;
                font-family: 'Consolas', 'Microsoft YaHei UI', monospace;
                selection-background-color: rgba(86, 171, 47, 0.5);
                color: #e0e0e0;
            }
            QTextEdit:focus, QLineEdit:focus {
                border: 2px solid #56ab2f;
                background: rgba(0, 0, 0, 0.4);
                box-shadow: 0 0 15px rgba(86, 171, 47, 0.3);
            }
            
            /* 树形控件 */
            QTreeWidget {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                outline: none;
                color: #e0e0e0;
            }
            QTreeWidget::item {
                padding: 12px;
                border-radius: 6px;
            }
            QTreeWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(86, 171, 47, 0.3), stop:1 rgba(168, 224, 99, 0.3));
                color: #a8e063;
            }
            QTreeWidget::item:hover:!selected {
                background: rgba(255, 255, 255, 0.1);
            }
            
            /* 下拉框 */
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                min-height: 40px;
                color: #e0e0e0;
            }
            QComboBox:hover {
                border: 1px solid #56ab2f;
                background: rgba(255, 255, 255, 0.15);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 7px solid #a8e063;
                margin-right: 10px;
            }
            
            /* 进度条 - 霓虹效果 */
            QProgressBar {
                border: none;
                border-radius: 16px;
                text-align: center;
                height: 32px;
                background: rgba(0, 0, 0, 0.3);
                font-size: 14px;
                font-weight: 700;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #56ab2f, stop:0.5 #a8e063, stop:1 #56ab2f);
                border-radius: 16px;
                box-shadow: 0 0 10px rgba(86, 171, 47, 0.8);
            }
            
            /* 滚动条 - 现代化 */
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 7px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* 状态栏 */
            QStatusBar {
                background: rgba(0, 0, 0, 0.3);
                color: #a8e063;
                font-size: 13px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding: 5px;
            }
            
            /* 对话框样式 */
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
                border: 2px solid rgba(168, 224, 99, 0.5);
                border-radius: 12px;
            }
            
            QMessageBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
                font-size: 14px;
                min-width: 400px;
            }
            
            QMessageBox QLabel {
                color: #e0e0e0;
                font-size: 14px;
                padding: 10px;
                min-width: 350px;
            }
            
            QMessageBox QPushButton {
                min-width: 100px;
                min-height: 40px;
                font-size: 14px;
                padding: 10px 20px;
            }
            
            QInputDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
                min-width: 450px;
            }
            
            QInputDialog QLabel {
                color: #e0e0e0;
                font-size: 14px;
                padding: 10px;
            }
            
            QInputDialog QLineEdit, QInputDialog QTextEdit {
                min-width: 400px;
                min-height: 35px;
                font-size: 14px;
            }
            
            QInputDialog QPushButton {
                min-width: 100px;
                min-height: 40px;
                font-size: 14px;
            }
            
            QFileDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
                color: #e0e0e0;
            }
            
            QFileDialog QLabel {
                color: #e0e0e0;
                font-size: 14px;
            }
            
            QFileDialog QPushButton {
                min-width: 100px;
                min-height: 40px;
                font-size: 14px;
            }
        """)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 标题栏 - 霓虹渐变设计（紧凑版）
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0f2027, stop:0.3 #203a43, stop:0.7 #2c5364, stop:1 #0f2027);
            border-radius: 16px;
            padding: 15px;
            margin-bottom: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_widget.setLayout(title_layout)
        
        title_label = QLabel('USB 总线及挂载设备测试系统')
        title_font = QFont()
        title_font.setFamily('Microsoft YaHei UI')
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #a8e063;
            padding: 5px;
            background: transparent;
            letter-spacing: 3px;
            text-shadow: 0 0 10px rgba(168, 224, 99, 0.5);
        """)
        title_layout.addWidget(title_label)
        
        main_layout.addWidget(title_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Tab 1: 设备监控
        self.device_monitor_tab = self.create_device_monitor_tab()
        self.tab_widget.addTab(self.device_monitor_tab, '🖥️ 设备监控')
        
        # Tab 2: 文件操作
        self.file_operation_tab = self.create_file_operation_tab()
        self.tab_widget.addTab(self.file_operation_tab, '📝 文件操作')
        
        # Tab 3: 文件管理
        self.file_manager_tab = FileManagerTab(self)
        self.tab_widget.addTab(self.file_manager_tab, '📁 文件管理')
        
        # Tab 4: 传输监控
        self.transfer_monitor_tab = TransferMonitorTab(self)
        self.tab_widget.addTab(self.transfer_monitor_tab, '📊 传输监控')
        
        # 系统状态汇总区域
        self.status_summary_widget = self.create_status_summary()
        main_layout.addWidget(self.status_summary_widget)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
        
        # 标签页切换事件
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def create_device_monitor_tab(self):
        """创建设备监控标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # 用户信息区域
        self.user_group = self.create_user_info_group()
        layout.addWidget(self.user_group)
        
        # USB 设备信息区域
        self.usb_group = self.create_usb_info_group()
        layout.addWidget(self.usb_group)
        
        return tab
    
    def create_file_operation_tab(self):
        """创建文件操作标签页"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # 文件操作区域
        self.file_group = self.create_file_operation_group()
        layout.addWidget(self.file_group)
        
        return tab
        
    def create_user_info_group(self):
        """创建用户信息组 - 紧凑设计"""
        group = QGroupBox('👤 当前登录用户信息')
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # 用户图标区域
        icon_label = QLabel('👤')
        icon_label.setStyleSheet("""
            font-size: 32px;
            padding: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(86, 171, 47, 0.3), stop:1 rgba(168, 224, 99, 0.3));
            border-radius: 28px;
            min-width: 56px;
            max-width: 56px;
            min-height: 56px;
            max-height: 56px;
            border: 2px solid rgba(168, 224, 99, 0.5);
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # 用户信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        self.user_label = QLabel('用户名: 加载中...')
        self.user_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 700;
            padding: 3px;
            color: #a8e063;
        """)
        info_layout.addWidget(self.user_label)
        
        self.home_label = QLabel('主目录: 加载中...')
        self.home_label.setStyleSheet("""
            font-size: 13px;
            padding: 3px;
            color: rgba(255, 255, 255, 0.7);
        """)
        info_layout.addWidget(self.home_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        group.setLayout(layout)
        group.setMaximumHeight(125)
        return group
        
    def create_usb_info_group(self):
        """创建 USB 设备信息组 - 现代化设计"""
        group = QGroupBox('💾 USB 设备信息')
        layout = QVBoxLayout()
        
        # 设备列表
        self.usb_list = QListWidget()
        self.usb_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                font-family: 'Microsoft YaHei UI', 'Segoe UI', Arial;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 6px;
                margin: 3px 0;
                border-left: 4px solid transparent;
                color: #e0e0e0;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(168, 224, 99, 0.3), stop:1 rgba(168, 224, 99, 0.2));
                color: #a8e063;
                border-left: 4px solid #a8e063;
                font-weight: 600;
            }
            QListWidget::item:hover:!selected {
                background-color: rgba(255, 255, 255, 0.1);
                border-left: 4px solid rgba(255, 255, 255, 0.3);
            }
        """)
        self.usb_list.itemClicked.connect(self.show_device_details)
        layout.addWidget(self.usb_list)
        
        # 设备详细信息显示区域
        details_label = QLabel('📋 设备详细信息')
        details_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 700;
            color: #a8e063;
            padding: 10px 0 6px 0;
        """)
        layout.addWidget(details_label)
        
        self.device_details = QTextEdit()
        self.device_details.setReadOnly(True)
        self.device_details.setMinimumHeight(200)  # 增加最小高度，移除最大高度限制
        self.device_details.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                padding: 14px;
                font-size: 12px;
                font-family: 'Consolas', 'Microsoft YaHei UI', monospace;
                line-height: 1.8;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(self.device_details)
        
        # 显示初始空状态引导
        self.show_empty_state_guide()
        
        # 刷新按钮 - 增强实验语义
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton('🔍 执行 USB 总线扫描')
        self.refresh_btn.setToolTip('执行 USB 总线枚举检测\n扫描系统可移动设备插槽\n识别已挂载的 USB 存储设备')
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                min-width: 180px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #764ba2, stop:1 #667eea);
                box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_usb_devices)
        btn_layout.addWidget(self.refresh_btn)
        
        # 扫描状态标签
        self.scan_status_label = QLabel('⚪ 就绪')
        self.scan_status_label.setStyleSheet("""
            font-size: 13px;
            color: #a8e063;
            padding: 8px 16px;
            background: rgba(168, 224, 99, 0.15);
            border-radius: 8px;
            border: 1px solid rgba(168, 224, 99, 0.3);
        """)
        btn_layout.addWidget(self.scan_status_label)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        group.setLayout(layout)
        return group
    
    def create_status_summary(self):
        """创建系统状态汇总区域"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 0, 0, 0.4), stop:1 rgba(0, 0, 0, 0.3));
                border-top: 1px solid rgba(168, 224, 99, 0.3);
                border-radius: 0px;
                padding: 8px 15px;
            }
        """)
        layout = QHBoxLayout()
        widget.setLayout(layout)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 用户信息
        self.status_user_label = QLabel('👤 用户: 加载中...')
        self.status_user_label.setStyleSheet("""
            font-size: 12px;
            color: #a8e063;
            background: transparent;
            padding: 4px 10px;
        """)
        layout.addWidget(self.status_user_label)
        
        # 分隔符
        sep1 = QLabel('|')
        sep1.setStyleSheet('color: rgba(255, 255, 255, 0.3); background: transparent;')
        layout.addWidget(sep1)
        
        # USB 监听状态
        self.status_monitor_label = QLabel('📡 USB 监听: 激活')
        self.status_monitor_label.setStyleSheet("""
            font-size: 12px;
            color: #4caf50;
            background: transparent;
            padding: 4px 10px;
        """)
        layout.addWidget(self.status_monitor_label)
        
        # 分隔符
        sep2 = QLabel('|')
        sep2.setStyleSheet('color: rgba(255, 255, 255, 0.3); background: transparent;')
        layout.addWidget(sep2)
        
        # 设备数量
        self.status_device_count_label = QLabel('💾 设备: 0 个')
        self.status_device_count_label.setStyleSheet("""
            font-size: 12px;
            color: #ff9800;
            background: transparent;
            padding: 4px 10px;
        """)
        layout.addWidget(self.status_device_count_label)
        
        # 分隔符
        sep3 = QLabel('|')
        sep3.setStyleSheet('color: rgba(255, 255, 255, 0.3); background: transparent;')
        layout.addWidget(sep3)
        
        # 当前模块
        self.status_module_label = QLabel('📍 模块: 设备监控')
        self.status_module_label.setStyleSheet("""
            font-size: 12px;
            color: #2196f3;
            background: transparent;
            padding: 4px 10px;
        """)
        layout.addWidget(self.status_module_label)
        
        layout.addStretch()
        
        return widget
    
    def show_empty_state_guide(self):
        """显示空状态引导信息"""
        self.usb_list.clear()
        
        # 创建引导卡片
        guide_item = QListWidgetItem()
        guide_item.setText('🔍 实验引导')
        guide_item.setForeground(Qt.darkBlue)
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        guide_item.setFont(font)
        self.usb_list.addItem(guide_item)
        
        # 步骤 1
        step1 = QListWidgetItem()
        step1.setText('① 插入 USB 存储设备（U 盘）')
        step1.setForeground(Qt.darkGreen)
        self.usb_list.addItem(step1)
        
        # 步骤 2
        step2 = QListWidgetItem()
        step2.setText('② 点击"执行 USB 总线扫描"按钮')
        step2.setForeground(Qt.darkGreen)
        self.usb_list.addItem(step2)
        
        # 步骤 3
        step3 = QListWidgetItem()
        step3.setText('③ 系统将自动检测并显示设备信息')
        step3.setForeground(Qt.darkGreen)
        self.usb_list.addItem(step3)
        
        # 分隔线
        sep = QListWidgetItem()
        sep.setText('─' * 50)
        sep.setForeground(Qt.lightGray)
        self.usb_list.addItem(sep)
        
        # 说明标题
        info_title = QListWidgetItem()
        info_title.setText('📋 设备插入后将展示以下信息：')
        info_title.setForeground(Qt.darkMagenta)
        font2 = QFont()
        font2.setBold(True)
        info_title.setFont(font2)
        self.usb_list.addItem(info_title)
        
        # 信息列表
        info_items = [
            '• 设备挂载点（盘符）',
            '• 设备制造商和型号',
            '• 设备序列号',
            '• USB 接口类型',
            '• 文件系统类型',
            '• 存储容量和使用情况',
            '• 传输速率测试结果'
        ]
        
        for info in info_items:
            item = QListWidgetItem()
            item.setText(info)
            item.setForeground(Qt.darkCyan)
            self.usb_list.addItem(item)
        
        # 设备详细信息区域的引导
        guide_text = """
╔══════════════════════════════════════════════════════════════╗
║  USB 设备测试系统 - 实验引导
╚══════════════════════════════════════════════════════════════╝

📌 实验目的：
   • 理解 USB 总线的工作原理
   • 掌握设备枚举和识别过程
   • 测试文件系统的读写操作
   • 分析 USB 设备的性能特征

🔧 实验准备：
   1. 准备一个 USB 存储设备（U 盘）
   2. 确保设备可正常读写
   3. 建议使用 USB 2.0 或 USB 3.0 设备

⚡ 开始实验：
   → 插入 USB 设备
   → 点击"执行 USB 总线扫描"按钮
   → 观察设备检测过程和结果

💡 提示：
   系统会自动监听设备插拔事件，插入设备后会立即检测。
   设备信息将在此区域详细展示，包括硬件参数和存储状态。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        self.device_details.setPlainText(guide_text)
    
    def on_tab_changed(self, index):
        """标签页切换事件"""
        tab_names = ['设备监控', '文件操作', '文件管理', '传输监控']
        if 0 <= index < len(tab_names):
            self.status_module_label.setText(f'📍 模块: {tab_names[index]}')
            self.statusBar().showMessage(f'当前模块: {tab_names[index]}')
        
    def create_file_operation_group(self):
        """创建文件操作组 - 现代化设计"""
        group = QGroupBox('📝 文件操作')
        layout = QVBoxLayout()
        
        # 按钮布局 - 使用网格布局
        btn_widget = QWidget()
        btn_widget.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout()
        btn_widget.setLayout(btn_layout)
        
        # 写入文件按钮 - 增强实验语义
        self.write_btn = QPushButton('✍️ 写入文件到 USB')
        self.write_btn.setToolTip('实验操作：向 USB 设备写入文本文件\n测试文件系统写入能力\n验证设备挂载状态')
        self.write_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                min-width: 140px;
                icon-size: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5cb85c, stop:1 #4CAF50);
            }
        """)
        self.write_btn.clicked.connect(self.write_file)
        btn_layout.addWidget(self.write_btn)
        
        # 拷贝文件按钮 - 增强实验语义
        self.copy_btn = QPushButton('📋 拷贝文件到 USB')
        self.copy_btn.setToolTip('实验操作：测试文件传输性能\n计算传输速率\n监控 I/O 操作')
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #764ba2, stop:1 #667eea);
                box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
            }
        """)
        self.copy_btn.clicked.connect(self.copy_file)
        btn_layout.addWidget(self.copy_btn)
        
        # 删除文件按钮 - 增强实验语义
        self.delete_btn = QPushButton('🗑️ 删除 USB 文件')
        self.delete_btn.setToolTip('实验操作：测试文件系统删除操作\n验证设备写入权限\n测试文件系统完整性')
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f093fb, stop:1 #f5576c);
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f5576c, stop:1 #f093fb);
                box-shadow: 0 0 20px rgba(245, 87, 108, 0.6);
            }
        """)
        self.delete_btn.clicked.connect(self.delete_file)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        layout.addWidget(btn_widget)
        
        # 操作日志标签
        log_label = QLabel('📜 操作日志')
        log_label.setStyleSheet("""
            font-size: 15px;
            font-weight: 700;
            color: #a8e063;
            padding: 10px 0 6px 0;
        """)
        layout.addWidget(log_label)
        
        # 操作日志
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(250)  # 增加最小高度，移除最大高度限制
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                padding: 14px;
                font-size: 12px;
                font-family: 'Consolas', 'Microsoft YaHei UI', monospace;
                line-height: 2.0;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(self.log_text)
        
        group.setLayout(layout)
        return group
        
    def load_user_info(self):
        """加载用户信息"""
        try:
            user_info = get_user_info()
            username = user_info['username']
            home_dir = user_info['home_dir']
            
            self.user_label.setText(f'👤 用户名: {username}')
            self.home_label.setText(f'🏠 主目录: {home_dir}')
            
            # 更新状态汇总区域
            self.status_user_label.setText(f'👤 用户: {username}')
            
            self.log(f'✓ 成功加载用户信息: {username}')
            self.statusBar().showMessage(f'当前用户: {username}')
        except Exception as e:
            self.user_label.setText(f'加载用户信息失败: {str(e)}')
            self.status_user_label.setText('👤 用户: 未知')
            self.log(f'✗ 加载用户信息失败: {str(e)}')
            
    def refresh_usb_devices(self):
        """刷新 USB 设备列表 - 增强实验反馈"""
        try:
            # 显示扫描中状态
            self.scan_status_label.setText('🔄 总线扫描中...')
            self.scan_status_label.setStyleSheet("""
                font-size: 13px;
                color: #ffa726;
                padding: 8px 16px;
                background: rgba(255, 167, 38, 0.15);
                border-radius: 8px;
                border: 1px solid rgba(255, 167, 38, 0.3);
            """)
            self.refresh_btn.setEnabled(False)
            self.statusBar().showMessage('正在执行 USB 总线枚举检测...')
            
            # 强制刷新界面
            QApplication.processEvents()
            
            self.usb_list.clear()
            self.device_details.clear()
            self.usb_devices = get_usb_drives()
            
            if not self.usb_devices:
                # 显示空状态引导
                self.show_empty_state_guide()
                self.log('⚠ USB 总线扫描完成 - 未检测到可移动设备')
                
                # 显示扫描完成状态（无设备）
                self.scan_status_label.setText('⚠️ 无设备')
                self.scan_status_label.setStyleSheet("""
                    font-size: 13px;
                    color: #ff9800;
                    padding: 8px 16px;
                    background: rgba(255, 152, 0, 0.15);
                    border-radius: 8px;
                    border: 1px solid rgba(255, 152, 0, 0.3);
                """)
                
                # 更新状态汇总
                self.status_device_count_label.setText('💾 设备: 0 个')
                self.status_device_count_label.setStyleSheet("""
                    font-size: 12px;
                    color: #ff9800;
                    background: transparent;
                    padding: 4px 10px;
                """)
            else:
                for device in self.usb_devices:
                    # 获取设备分类信息
                    from utils.usb_detector import classify_usb_device
                    classification = classify_usb_device(device)
                    
                    device_text = (
                        f"{classification['icon']} {device['mountpoint']} | "
                        f"{classification['category']} | "
                        f"{device['model']} | "
                        f"容量: {format_size(device['total'])} | "
                        f"可用: {format_size(device['free'])}"
                    )
                    self.usb_list.addItem(device_text)
                
                self.log(f'✓ USB 总线扫描完成 - 检测到 {len(self.usb_devices)} 个设备')
                self.statusBar().showMessage(f'总线扫描完成 - 检测到 {len(self.usb_devices)} 个 USB 设备')
                
                # 显示扫描完成状态（有设备）
                self.scan_status_label.setText(f'✅ 检测到 {len(self.usb_devices)} 个设备')
                self.scan_status_label.setStyleSheet("""
                    font-size: 13px;
                    color: #4caf50;
                    padding: 8px 16px;
                    background: rgba(76, 175, 80, 0.15);
                    border-radius: 8px;
                    border: 1px solid rgba(76, 175, 80, 0.3);
                """)
                
                # 更新状态汇总
                self.status_device_count_label.setText(f'💾 设备: {len(self.usb_devices)} 个')
                self.status_device_count_label.setStyleSheet("""
                    font-size: 12px;
                    color: #4caf50;
                    background: transparent;
                    padding: 4px 10px;
                """)
                
                # 自动显示第一个设备的详细信息
                if self.usb_devices:
                    self.show_device_details_by_index(0)
                
                # 刷新文件管理器的设备列表
                if hasattr(self, 'file_manager_tab'):
                    self.file_manager_tab.refresh_devices()
                
                # 刷新传输监控的设备状态
                if hasattr(self, 'transfer_monitor_tab'):
                    self.transfer_monitor_tab.refresh_device_status()
                    
        except Exception as e:
            self.log(f'✗ USB 总线扫描失败: {str(e)}')
            QMessageBox.warning(self, '错误', f'USB 总线扫描失败: {str(e)}')
            
            # 显示错误状态
            self.scan_status_label.setText('❌ 扫描失败')
            self.scan_status_label.setStyleSheet("""
                font-size: 13px;
                color: #f44336;
                padding: 8px 16px;
                background: rgba(244, 67, 54, 0.15);
                border-radius: 8px;
                border: 1px solid rgba(244, 67, 54, 0.3);
            """)
            
            # 更新状态汇总
            self.status_device_count_label.setText('💾 设备: 错误')
            self.status_device_count_label.setStyleSheet("""
                font-size: 12px;
                color: #f44336;
                background: transparent;
                padding: 4px 10px;
            """)
        finally:
            self.refresh_btn.setEnabled(True)
        
    def write_file(self):
        """写入文件到 U 盘 - 增强实验反馈"""
        if not self.usb_devices:
            QMessageBox.warning(self, '警告', '未检测到 USB 设备！\n请先执行 USB 总线扫描。')
            return
        
        # 选择目标 USB 设备
        device_list = [d['mountpoint'] for d in self.usb_devices]
        target_device, ok = QInputDialog.getItem(
            self, '选择目标设备', '请选择要写入的 USB 设备:', 
            device_list, 0, False
        )
        
        if not ok:
            return
        
        # 输入文件名
        filename, ok = QInputDialog.getText(
            self, '输入文件名', '请输入文件名（如 test.txt）:'
        )
        
        if not ok or not filename:
            return
        
        # 输入文件内容
        content, ok = QInputDialog.getMultiLineText(
            self, '输入文件内容', '请输入要写入的文本内容:'
        )
        
        if not ok:
            return
        
        # 显示操作开始状态
        self.log(f'⏳ [文件写入实验] 开始写入操作...')
        self.log(f'   目标设备: {target_device}')
        self.log(f'   文件名: {filename}')
        self.statusBar().showMessage(f'正在执行文件写入操作 - {filename}')
        
        # 写入文件
        success, message = write_text_file(target_device, filename, content)
        
        if success:
            self.log(f'✓ [文件写入实验] {message}')
            self.statusBar().showMessage(f'✓ 文件写入成功 - {filename}')
            self.show_message('实验成功', f'文件写入操作完成\n\n{message}', 'information')
        else:
            self.log(f'✗ [文件写入实验] {message}')
            self.statusBar().showMessage(f'✗ 文件写入失败')
            self.show_message('实验失败', f'文件写入操作失败\n\n{message}', 'warning')
        
    def copy_file(self):
        """拷贝文件到 U 盘 - 增强实验反馈（支持实时速率监测）"""
        if not self.usb_devices:
            QMessageBox.warning(self, '警告', '未检测到 USB 设备！\n请先执行 USB 总线扫描。')
            return
        
        # 选择源文件
        source_file, _ = QFileDialog.getOpenFileName(
            self, '选择要拷贝的文件', '', 'All Files (*.*)'
        )
        
        if not source_file:
            return
        
        # 选择目标 USB 设备
        device_list = [d['mountpoint'] for d in self.usb_devices]
        target_device, ok = QInputDialog.getItem(
            self, '选择目标设备', '请选择目标 USB 设备:', 
            device_list, 0, False
        )
        
        if not ok:
            return
        
        # 显示操作开始状态
        import os
        file_size = os.path.getsize(source_file)
        filename = os.path.basename(source_file)
        self.log(f'⏳ [文件传输实验] 开始传输操作...')
        self.log(f'   源文件: {source_file}')
        self.log(f'   文件大小: {format_size(file_size)}')
        self.log(f'   目标设备: {target_device}')
        self.statusBar().showMessage(f'正在执行文件传输实验 - 实时监测传输速率...')
        
        # 切换到传输监控标签页
        self.tab_widget.setCurrentWidget(self.transfer_monitor_tab)
        
        # 初始化传输监控
        self.transfer_monitor_tab.start_transfer(filename, target_device, file_size)
        
        # 创建传输监控器
        monitor = TransferMonitor()
        
        # 连接进度更新信号
        monitor.progress_updated.connect(self.transfer_monitor_tab.update_transfer_progress)
        
        # 强制刷新界面
        QApplication.processEvents()
        
        # 拷贝文件（带进度监控）
        success, message, rate = copy_file_to_usb_with_progress(source_file, target_device, monitor)
        
        if success:
            self.log(f'✓ [文件传输实验] {message}')
            self.log(f'   平均传输速率: {rate}')
            peak_rate = format_transfer_rate(monitor.peak_speed)
            self.log(f'   峰值传输速率: {peak_rate}')
            self.statusBar().showMessage(f'✓ 文件传输完成 - 平均速率: {rate}')
            self.show_message('实验成功', 
                            f'文件传输操作完成\n\n{message}\n\n'
                            f'平均速率: {rate}\n'
                            f'峰值速率: {peak_rate}', 
                            'information')
            
            # 更新传输监控
            if hasattr(self, 'transfer_monitor_tab'):
                self.transfer_monitor_tab.finish_transfer(True, message, rate)
        else:
            self.log(f'✗ [文件传输实验] {message}')
            self.statusBar().showMessage(f'✗ 文件传输失败')
            self.show_message('实验失败', f'文件传输操作失败\n\n{message}', 'warning')
            
            # 更新传输监控
            if hasattr(self, 'transfer_monitor_tab'):
                self.transfer_monitor_tab.finish_transfer(False, message, '0 B/s')
        
    def delete_file(self):
        """删除 U 盘中的文件 - 增强实验反馈"""
        if not self.usb_devices:
            QMessageBox.warning(self, '警告', '未检测到 USB 设备！\n请先执行 USB 总线扫描。')
            return
        
        # 选择要删除的文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择要删除的文件', '', 'All Files (*.*)'
        )
        
        if not file_path:
            return
        
        # 确认删除
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('确认删除实验操作')
        msg_box.setText(f'确定要执行文件删除操作吗？\n\n目标文件:\n{file_path}\n\n此操作将测试文件系统的删除功能。')
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setMinimumSize(550, 250)
        msg_box.setStyleSheet("""
            QMessageBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
                min-width: 550px;
            }
            QMessageBox QLabel {
                color: #e0e0e0;
                font-size: 15px;
                padding: 20px;
                min-width: 500px;
                min-height: 100px;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #56ab2f, stop:1 #a8e063);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
                min-height: 45px;
            }
            QMessageBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a8e063, stop:1 #56ab2f);
            }
        """)
        
        reply = msg_box.exec_()
        
        if reply == QMessageBox.No:
            return
        
        # 显示操作开始状态
        self.log(f'⏳ [文件删除实验] 开始删除操作...')
        self.log(f'   目标文件: {file_path}')
        self.statusBar().showMessage(f'正在执行文件删除实验...')
        
        # 删除文件
        success, message = delete_file_from_usb(file_path)
        
        if success:
            self.log(f'✓ [文件删除实验] {message}')
            self.statusBar().showMessage(f'✓ 文件删除成功')
            self.show_message('实验成功', f'文件删除操作完成\n\n{message}', 'information')
        else:
            self.log(f'✗ [文件删除实验] {message}')
            self.statusBar().showMessage(f'✗ 文件删除失败')
            self.show_message('实验失败', f'文件删除操作失败\n\n{message}', 'warning')
        
    def log(self, message):
        """添加日志信息"""
        self.log_text.append(message)
    
    def show_message(self, title, message, msg_type='information'):
        """显示优化后的消息框"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setMinimumSize(500, 200)  # 设置最小尺寸
        
        # 设置图标
        if msg_type == 'information':
            msg_box.setIcon(QMessageBox.Information)
        elif msg_type == 'warning':
            msg_box.setIcon(QMessageBox.Warning)
        elif msg_type == 'error':
            msg_box.setIcon(QMessageBox.Critical)
        elif msg_type == 'question':
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
        else:
            msg_box.setStandardButtons(QMessageBox.Ok)
        
        # 设置样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364);
                min-width: 500px;
            }
            QMessageBox QLabel {
                color: #e0e0e0;
                font-size: 15px;
                padding: 15px;
                min-width: 450px;
                min-height: 80px;
            }
            QMessageBox QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #56ab2f, stop:1 #a8e063);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: 600;
                min-width: 120px;
                min-height: 45px;
            }
            QMessageBox QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a8e063, stop:1 #56ab2f);
            }
        """)
        
        return msg_box.exec_()
    
    def monitor_usb_changes(self):
        """监控 USB 设备变化（插拔检测）- 增强实验反馈"""
        try:
            current_devices = get_usb_drives()
            current_mountpoints = set([d['mountpoint'] for d in current_devices])
            previous_mountpoints = set([d['mountpoint'] for d in self.usb_devices])
            
            # 检测新插入的设备
            new_devices = current_mountpoints - previous_mountpoints
            if new_devices:
                for mountpoint in new_devices:
                    self.log(f'🔌 [设备插入事件] 检测到新 USB 设备: {mountpoint}')
                    self.statusBar().showMessage(f'⚡ 设备插入事件 - {mountpoint}')
                    
                    # 更新扫描状态标签
                    self.scan_status_label.setText('🔌 检测到设备插入')
                    self.scan_status_label.setStyleSheet("""
                        font-size: 13px;
                        color: #2196f3;
                        padding: 8px 16px;
                        background: rgba(33, 150, 243, 0.15);
                        border-radius: 8px;
                        border: 1px solid rgba(33, 150, 243, 0.3);
                    """)
                    
                    # 更新生命周期状态
                    if hasattr(self, 'transfer_monitor_tab'):
                        self.transfer_monitor_tab.update_lifecycle_status('insert', 'completed', f'✓ 设备已插入: {mountpoint}')
                        self.transfer_monitor_tab.update_lifecycle_status('enumerate', 'active', '正在枚举设备...')
                        QApplication.processEvents()
                        time.sleep(0.3)
                        self.transfer_monitor_tab.update_lifecycle_status('enumerate', 'completed')
                        self.transfer_monitor_tab.update_lifecycle_status('mount', 'active', '正在挂载设备...')
                        QApplication.processEvents()
                        time.sleep(0.3)
                        self.transfer_monitor_tab.update_lifecycle_status('mount', 'completed')
                        self.transfer_monitor_tab.update_lifecycle_status('ready', 'completed', f'✓ 设备就绪: {mountpoint}')
                    
                self.refresh_usb_devices()
            
            # 检测拔出的设备
            removed_devices = previous_mountpoints - current_mountpoints
            if removed_devices:
                for mountpoint in removed_devices:
                    self.log(f'🔌 [设备拔出事件] USB 设备已移除: {mountpoint}')
                    self.statusBar().showMessage(f'⚡ 设备拔出事件 - {mountpoint}')
                    
                    # 更新扫描状态标签
                    self.scan_status_label.setText('🔌 检测到设备拔出')
                    self.scan_status_label.setStyleSheet("""
                        font-size: 13px;
                        color: #ff5722;
                        padding: 8px 16px;
                        background: rgba(255, 87, 34, 0.15);
                        border-radius: 8px;
                        border: 1px solid rgba(255, 87, 34, 0.3);
                    """)
                    
                    # 更新生命周期状态
                    if hasattr(self, 'transfer_monitor_tab'):
                        self.transfer_monitor_tab.update_lifecycle_status('remove', 'completed', f'✓ 设备已拔出: {mountpoint}')
                        QApplication.processEvents()
                        time.sleep(1)
                        self.transfer_monitor_tab.reset_lifecycle_status()
                    
                self.refresh_usb_devices()
        except Exception as e:
            pass  # 静默处理监控错误，避免频繁弹窗
    
    def show_device_details(self, item):
        """显示选中设备的详细信息"""
        try:
            # 获取选中项的索引
            index = self.usb_list.row(item)
            self.show_device_details_by_index(index)
        except Exception as e:
            self.log(f'✗ 显示设备详细信息失败: {str(e)}')
    
    def show_device_details_by_index(self, index):
        """根据索引显示设备详细信息"""
        try:
            if 0 <= index < len(self.usb_devices):
                device = self.usb_devices[index]
                
                # 获取设备分类信息
                from utils.usb_detector import classify_usb_device
                classification = classify_usb_device(device)
                
                details_text = f"""
╔══════════════════════════════════════════════════════════════╗
║  USB 设备详细信息
╚══════════════════════════════════════════════════════════════╝

{classification['icon']} 设备类型: {classification['category']}
📍 挂载点: {device['mountpoint']}
🏭 制造商: {device['manufacturer']}
📦 型号: {device['model']}
🔢 序列号: {device['serial_number']}
🔌 接口类型: {device['interface_type']}
💾 介质类型: {device['media_type']}
📊 文件系统: {device['fstype']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💿 存储信息:
   • 总容量: {format_size(device['total'])}
   • 已使用: {format_size(device['used'])} ({device['percent']:.1f}%)
   • 可用空间: {format_size(device['free'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 功能支持:
   • 文件读写: {'支持' if classification['supports_file_ops'] else '不支持'}
   • 文件管理: {'支持' if classification['supports_file_ops'] else '不支持'}
   • 传输监控: 支持

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                """
                
                self.device_details.setPlainText(details_text)
        except Exception as e:
            self.device_details.setPlainText(f'无法显示设备详细信息: {str(e)}')
