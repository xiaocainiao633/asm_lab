"""
文件管理标签页
功能：显示 U 盘文件列表、文件预览、文件夹操作
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTreeWidget, QTreeWidgetItem, QTextEdit,
                             QComboBox, QMessageBox, QInputDialog, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
import os
from utils.file_operations import list_files_in_directory
from utils.usb_detector import format_size

class FileManagerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_path = None
        self.init_ui()
    
    def init_ui(self):
        """初始化文件管理界面"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 设备选择区域 - 深色主题设计
        device_widget = QWidget()
        device_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.1), stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                padding: 12px;
            }
        """)
        device_layout = QHBoxLayout()
        device_widget.setLayout(device_layout)
        
        device_label = QLabel('💾 选择设备:')
        device_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #a8e063;
            background: transparent;
        """)
        device_layout.addWidget(device_label)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(300)
        self.device_combo.setStyleSheet("""
            QComboBox {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #a8e063;
                background: rgba(0, 0, 0, 0.4);
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #a8e063;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(168, 224, 99, 0.3);
                selection-background-color: rgba(168, 224, 99, 0.3);
                selection-color: #a8e063;
                color: #e0e0e0;
                padding: 5px;
            }
        """)
        self.device_combo.currentTextChanged.connect(self.on_device_changed)
        device_layout.addWidget(self.device_combo)
        
        self.refresh_device_btn = QPushButton('🔍 重新枚举设备')
        self.refresh_device_btn.setToolTip('重新扫描 USB 总线\n枚举可移动存储设备\n更新设备挂载列表')
        self.refresh_device_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #42a5f5, stop:1 #2196F3);
            }
        """)
        self.refresh_device_btn.clicked.connect(self.refresh_devices)
        device_layout.addWidget(self.refresh_device_btn)
        
        self.show_hidden_checkbox = QPushButton('👁️ 显示隐藏文件')
        self.show_hidden_checkbox.setCheckable(True)
        self.show_hidden_checkbox.setChecked(True)
        self.show_hidden_checkbox.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9C27B0, stop:1 #7B1FA2);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                min-width: 140px;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ab47bc, stop:1 #9C27B0);
            }
            QPushButton:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #66bb6a, stop:1 #4CAF50);
            }
        """)
        self.show_hidden_checkbox.clicked.connect(self.refresh_file_list)
        device_layout.addWidget(self.show_hidden_checkbox)
        
        device_layout.addStretch()
        layout.addWidget(device_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：文件树
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        left_layout.addWidget(QLabel('📁 文件列表:'))
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(['名称', '大小', '类型'])
        self.file_tree.setColumnWidth(0, 250)
        self.file_tree.itemClicked.connect(self.on_file_selected)
        self.file_tree.itemDoubleClicked.connect(self.on_file_double_clicked)
        left_layout.addWidget(self.file_tree)
        
        # 文件操作按钮 - 现代化设计
        file_ops_layout = QHBoxLayout()
        
        self.create_folder_btn = QPushButton('📁 新建文件夹')
        self.create_folder_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                min-width: 120px;
            }
        """)
        self.create_folder_btn.clicked.connect(self.create_folder)
        file_ops_layout.addWidget(self.create_folder_btn)
        
        self.rename_btn = QPushButton('✏️ 重命名')
        self.rename_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF9800, stop:1 #F57C00);
                min-width: 100px;
            }
        """)
        self.rename_btn.clicked.connect(self.rename_item)
        file_ops_layout.addWidget(self.rename_btn)
        
        self.delete_btn = QPushButton('🗑️ 删除')
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f44336, stop:1 #d32f2f);
                min-width: 100px;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_item)
        file_ops_layout.addWidget(self.delete_btn)
        
        file_ops_layout.addStretch()
        left_layout.addLayout(file_ops_layout)
        
        splitter.addWidget(left_widget)
        
        # 右侧：文件预览
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        right_layout.addWidget(QLabel('👁️ 文件预览:'))
        
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 8px;
            padding: 10px;
            color: #e0e0e0;
            font-size: 13px;
            font-family: 'Consolas', 'Microsoft YaHei UI', monospace;
        """)
        right_layout.addWidget(self.preview_area)
        
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # 状态信息
        self.status_label = QLabel('请选择 USB 设备')
        self.status_label.setStyleSheet('color: #666; padding: 5px;')
        layout.addWidget(self.status_label)
    
    def refresh_devices(self):
        """刷新设备列表"""
        self.device_combo.clear()
        if hasattr(self.parent_window, 'usb_devices') and len(self.parent_window.usb_devices) > 0:
            for device in self.parent_window.usb_devices:
                self.device_combo.addItem(
                    f"{device['mountpoint']} - {device['model']} ({format_size(device['free'])} 可用)"
                )
        else:
            # 空状态：显示提示信息
            self.device_combo.addItem('⚠️ 未检测到 USB 设备')
            self.show_empty_state_info()
    
    def on_device_changed(self, text):
        """设备选择改变"""
        if text:
            # 提取挂载点
            mountpoint = text.split(' - ')[0]
            self.current_path = mountpoint
            self.refresh_file_list()
    
    def show_empty_state_info(self):
        """显示空状态信息（无 USB 设备时）"""
        import psutil
        import time
        
        self.file_tree.clear()
        self.preview_area.clear()
        
        # 在预览区域显示系统诊断信息
        info = "═" * 60 + "\n"
        info += "  🔍 USB 设备检测诊断信息\n"
        info += "═" * 60 + "\n\n"
        
        # 扫描时间
        scan_time = time.strftime('%Y-%m-%d %H:%M:%S')
        info += f"🕐 扫描时间: {scan_time}\n\n"
        
        # 系统磁盘信息
        try:
            partitions = psutil.disk_partitions()
            disk_count = len(partitions)
            removable_count = sum(1 for p in partitions if 'removable' in p.opts.lower())
            
            info += f"💾 系统可识别磁盘总数: {disk_count} 个\n"
            info += f"🔌 可移动设备插槽数: {removable_count} 个\n"
            info += f"📊 当前 USB 设备数: 0 个\n\n"
            
            info += "─" * 60 + "\n"
            info += "📂 当前系统盘符列表:\n"
            info += "─" * 60 + "\n\n"
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    is_removable = 'removable' in partition.opts.lower()
                    device_type = '🔌 可移动' if is_removable else '💿 固定'
                    
                    info += f"{device_type} {partition.device}\n"
                    info += f"  挂载点: {partition.mountpoint}\n"
                    info += f"  文件系统: {partition.fstype}\n"
                    info += f"  总容量: {format_size(usage.total)}\n"
                    info += f"  已使用: {format_size(usage.used)} ({usage.percent}%)\n"
                    info += f"  可用空间: {format_size(usage.free)}\n\n"
                except:
                    info += f"⚠️ {partition.device} - 无法访问\n\n"
            
        except Exception as e:
            info += f"⚠️ 无法获取磁盘信息: {str(e)}\n\n"
        
        info += "─" * 60 + "\n"
        info += "💡 提示:\n"
        info += "─" * 60 + "\n"
        info += "• 请插入 USB 设备后点击 '🔄 刷新' 按钮\n"
        info += "• 系统会自动检测新插入的 USB 设备\n"
        info += "• 确保 USB 设备已正确连接并被系统识别\n"
        info += "• 如果设备无法识别，请检查设备驱动程序\n"
        
        self.preview_area.setPlainText(info)
        self.status_label.setText('⚠️ 未检测到 USB 设备 - 请插入设备后刷新')
    
    def refresh_file_list(self):
        """刷新文件列表"""
        if not self.current_path:
            return
        
        try:
            self.file_tree.clear()
            show_hidden = self.show_hidden_checkbox.isChecked()
            files = list_files_in_directory(self.current_path, show_hidden)
            
            for file_info in files:
                item = QTreeWidgetItem()
                
                # 文件名
                name = file_info['name']
                if file_info['is_hidden']:
                    name = f"🔒 {name}"
                elif file_info['is_dir']:
                    name = f"📁 {name}"
                else:
                    name = f"📄 {name}"
                
                item.setText(0, name)
                
                # 大小
                if file_info['is_dir']:
                    item.setText(1, '<文件夹>')
                else:
                    item.setText(1, format_size(file_info['size']))
                
                # 类型
                if file_info['is_dir']:
                    item.setText(2, '文件夹')
                else:
                    ext = os.path.splitext(file_info['name'])[1]
                    item.setText(2, ext if ext else '文件')
                
                # 存储完整路径
                item.setData(0, Qt.UserRole, file_info['path'])
                item.setData(1, Qt.UserRole, file_info['is_dir'])
                
                self.file_tree.addTopLevelItem(item)
            
            self.status_label.setText(f'📊 共 {len(files)} 项')
        except Exception as e:
            QMessageBox.warning(self, '错误', f'读取文件列表失败: {str(e)}')
    
    def on_file_selected(self, item, column):
        """文件被选中"""
        file_path = item.data(0, Qt.UserRole)
        is_dir = item.data(1, Qt.UserRole)
        
        if not is_dir:
            self.preview_file(file_path)
    
    def on_file_double_clicked(self, item, column):
        """文件被双击"""
        file_path = item.data(0, Qt.UserRole)
        is_dir = item.data(1, Qt.UserRole)
        
        if is_dir:
            # 进入文件夹
            self.current_path = file_path
            self.refresh_file_list()
    
    def preview_file(self, file_path):
        """预览文件"""
        try:
            file_size = os.path.getsize(file_path)
            
            # 文件信息
            info = f"文件路径: {file_path}\n"
            info += f"文件大小: {format_size(file_size)}\n"
            info += f"{'='*60}\n\n"
            
            # 根据文件类型预览
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.log']:
                # 文本文件预览
                if file_size > 1024 * 1024:  # 大于 1MB
                    info += "文件过大，仅显示前 1000 行\n\n"
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = [f.readline() for _ in range(1000)]
                        info += ''.join(lines)
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        info += f.read()
            
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                info += "图片文件\n"
                info += f"格式: {ext}\n"
                info += "（图片预览功能待实现）"
            
            else:
                info += "不支持预览此文件类型"
            
            self.preview_area.setPlainText(info)
        
        except Exception as e:
            self.preview_area.setPlainText(f"预览失败: {str(e)}")
    
    def create_folder(self):
        """创建文件夹"""
        if not self.current_path:
            QMessageBox.warning(self, '警告', '请先选择设备')
            return
        
        folder_name, ok = QInputDialog.getText(self, '新建文件夹', '请输入文件夹名称:')
        
        if ok and folder_name:
            try:
                new_folder_path = os.path.join(self.current_path, folder_name)
                os.makedirs(new_folder_path)
                QMessageBox.information(self, '成功', f'文件夹创建成功: {folder_name}')
                self.refresh_file_list()
            except Exception as e:
                QMessageBox.warning(self, '错误', f'创建文件夹失败: {str(e)}')
    
    def rename_item(self):
        """重命名文件或文件夹"""
        item = self.file_tree.currentItem()
        if not item:
            QMessageBox.warning(self, '警告', '请先选择要重命名的项')
            return
        
        old_path = item.data(0, Qt.UserRole)
        old_name = os.path.basename(old_path)
        
        new_name, ok = QInputDialog.getText(self, '重命名', '请输入新名称:', text=old_name)
        
        if ok and new_name and new_name != old_name:
            try:
                new_path = os.path.join(os.path.dirname(old_path), new_name)
                os.rename(old_path, new_path)
                QMessageBox.information(self, '成功', '重命名成功')
                self.refresh_file_list()
            except Exception as e:
                QMessageBox.warning(self, '错误', f'重命名失败: {str(e)}')
    
    def delete_item(self):
        """删除文件或文件夹"""
        item = self.file_tree.currentItem()
        if not item:
            QMessageBox.warning(self, '警告', '请先选择要删除的项')
            return
        
        file_path = item.data(0, Qt.UserRole)
        is_dir = item.data(1, Qt.UserRole)
        
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除吗？\n{file_path}',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if is_dir:
                    import shutil
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                
                QMessageBox.information(self, '成功', '删除成功')
                self.refresh_file_list()
            except Exception as e:
                QMessageBox.warning(self, '错误', f'删除失败: {str(e)}')
