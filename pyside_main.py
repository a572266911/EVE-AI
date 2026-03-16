#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EVENTURI-AI PySide6 GUI
FPS 视觉辅助工具 - PySide6 现代化重构版本
"""

import sys
import os
import glob
import threading
from typing import Optional, List, Dict, Any

from PySide6.QtCore import (
    Qt, Signal, Slot, QTimer, QThread, QMutex, QMutexLocker,
    QSize, QMetaObject, Q_ARG,QObject, Signal
)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFormLayout, QStackedWidget, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QSlider, QCheckBox, QRadioButton, QComboBox,
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QGroupBox, QFrame,
    QSplitter, QStatusBar, QSizePolicy, QScrollArea, QMessageBox,
    QColorDialog, QButtonGroup, QInputDialog
)

from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QTextCursor

import main
from main import (
    start_aimbot, stop_aimbot, is_aimbot_running,
    reload_model, get_model_classes, get_model_size
)
from config import config
from mouse import connect_to_makcu, test_move, switch_to_4m, button_states, button_states_lock

try:
    from recoil_loader import get_available_games, get_available_weapons
except ImportError:
    def get_available_games():
        return []
    def get_available_weapons(game):
        return []

NEON = "#ff1744"
BG = "#0a0a0a"
BG_DARK = "#050505"
BG_CARD = "#121212"
BG_INPUT = "#1a1a1a"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#b0b0b0"
TEXT_ACCENT = "#00e676"
TEXT_HIGHLIGHT = "#ff1744"

DARK_STYLE = """
QMainWindow {
    background-color: #0a0a0a;
}
QWidget {
    background-color: #0a0a0a;
    color: #ffffff;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 12px;
}
QScrollArea {
    background-color: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 12px;
    border-radius: 6px;
}
QScrollBar::handle:vertical {
    background-color: #ff1744;
    border-radius: 6px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #d50000;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #1a1a1a;
    height: 12px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal {
    background-color: #ff1744;
    border-radius: 6px;
    min-width: 30px;
}
QListWidget {
    background-color: #0a0a0a;
    border: none;
    outline: none;
}
QListWidget::item {
    background-color: transparent;
    color: #b0b0b0;
    padding: 15px 20px;
    border-left: 3px solid transparent;
    font-size: 13px;
    font-weight: bold;
}
QListWidget::item:hover {
    background-color: #1a1a1a;
    color: #ffffff;
}
QListWidget::item:selected {
    background-color: #1a1a1a;
    color: #ff1744;
    border-left: 3px solid #ff1744;
}
QGroupBox {
    background-color: #121212;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    margin-top: 12px;
    padding: 15px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 10px;
    color: #00e676;
    font-size: 14px;
}
QPushButton {
    background-color: #2a2a2a;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #3a3a3a;
}
QPushButton:pressed {
    background-color: #1a1a1a;
}
QPushButton:disabled {
    background-color: #1a1a1a;
    color: #555555;
}
QPushButton[class="neon"] {
    background-color: #ff1744;
    color: #ffffff;
}
QPushButton[class="neon"]:hover {
    background-color: #d50000;
}
QPushButton[class="neon"]:pressed {
    background-color: #b71c1c;
}
QSlider::groove:horizontal {
    background-color: #2a2a2a;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background-color: #ff1744;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background-color: #ff4567;
}
QSlider::sub-page:horizontal {
    background-color: #ff1744;
    border-radius: 3px;
}
QCheckBox {
    spacing: 8px;
    color: #ffffff;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #3a3a3a;
    background-color: #1a1a1a;
}
QCheckBox::indicator:checked {
    background-color: #ff1744;
    border-color: #ff1744;
}
QCheckBox::indicator:hover {
    border-color: #ff1744;
}
QCheckBox::indicator:disabled {
    background-color: #0a0a0a;
    border-color: #2a2a2a;
}
QRadioButton {
    spacing: 8px;
    color: #ffffff;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 2px solid #3a3a3a;
    background-color: #1a1a1a;
}
QRadioButton::indicator:checked {
    background-color: #ff1744;
    border-color: #ff1744;
}
QRadioButton::indicator:hover {
    border-color: #ff1744;
}
QComboBox {
    background-color: #1a1a1a;
    color: #ffffff;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 100px;
}
QComboBox:hover {
    border-color: #ff1744;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #ff1744;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a1a;
    color: #ffffff;
    selection-background-color: #ff1744;
    selection-color: #ffffff;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
}
QLineEdit {
    background-color: #1a1a1a;
    color: #ff1744;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
}
QLineEdit:hover {
    border-color: #ff1744;
}
QLineEdit:focus {
    border-color: #ff1744;
    border-width: 2px;
}
QLineEdit:disabled {
    background-color: #0a0a0a;
    color: #555555;
}
QSpinBox, QDoubleSpinBox {
    background-color: #1a1a1a;
    color: #ff1744;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
}
QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #ff1744;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #2a2a2a;
    border: none;
    width: 20px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #ff1744;
}
QTextEdit {
    background-color: #0a0a0a;
    color: #00e676;
    border: 1px solid #2a2a2a;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
}
QTextEdit:focus {
    border-color: #ff1744;
}
QStatusBar {
    background-color: #050505;
    color: #ffffff;
    border-top: 1px solid #1a1a1a;
    font-size: 12px;
}
QStatusBar::item {
    border: none;
}
QSplitter::handle {
    background-color: #1a1a1a;
}
QFrame[class="card"] {
    background-color: #121212;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
}
QLabel[class="title"] {
    color: #00e676;
    font-size: 14px;
    font-weight: bold;
}
QLabel[class="value"] {
    color: #ff1744;
    font-weight: bold;
}
"""

class LogSignalEmitter(QObject):
    stdout_signal = Signal(str)
    stderr_signal = Signal(str)

log_emitter = LogSignalEmitter()

class StreamRedirector:
    def __init__(self, signal_emitter, stream_type='stdout'):
        self.signal_emitter = signal_emitter
        self.stream_type = stream_type
        self.original = sys.stdout if stream_type == 'stdout' else sys.stderr
    
    def write(self, text):
        if text and text.strip():
            if self.stream_type == 'stdout':
                self.signal_emitter.stdout_signal.emit(text)
            else:
                self.signal_emitter.stderr_signal.emit(text)
        self.original.write(text)
    
    def flush(self):
        self.original.flush()

class StatusUpdater(QObject):
    update_fps = Signal(float)
    update_connection = Signal(bool, str)
    update_aimbot_status = Signal(bool)
    update_button_states = Signal(dict)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LUCKY-AI")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        self._building = True
        self._updating_fov_x = False
        self._updating_fov_y = False
        self._updating_imgsz = False
        self._updating_target_height = False
        self._updating_deadzone_min = False
        self._updating_deadzone_max = False
        self._updating_deadzone_tolerance = False
        
        self.status_updater = StatusUpdater()
        self.status_updater.update_fps.connect(self._on_fps_update)
        self.status_updater.update_connection.connect(self._on_connection_update)
        self.status_updater.update_aimbot_status.connect(self._on_aimbot_status_update)
        
        self._setup_ui()
        self._setup_logging()
        self._start_polling()
        self._auto_connect()
        
        self._building = False
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_vbox = QVBoxLayout(central_widget)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)
        
        top_hbox = QHBoxLayout()
        top_hbox.setContentsMargins(0, 0, 0, 0)
        top_hbox.setSpacing(0)
        
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.addItem(QListWidgetItem("📷 画面与捕获"))
        self.nav_list.addItem(QListWidgetItem("🎯 视觉与识别"))
        self.nav_list.addItem(QListWidgetItem("🎮 瞄准与平滑"))
        self.nav_list.addItem(QListWidgetItem("🧨 扳机与压枪"))
        #self.nav_list.addItem(QListWidgetItem("⚙️ 硬件与配置"))
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self._create_capture_page())
        self.content_stack.addWidget(self._create_detection_page())
        self.content_stack.addWidget(self._create_aim_page())
        self.content_stack.addWidget(self._create_trigger_page())
        self.content_stack.addWidget(self._create_hardware_page())
        
        top_hbox.addWidget(self.nav_list)
        top_hbox.addWidget(self.content_stack, stretch=1)
        
        main_vbox.addLayout(top_hbox)
        
        log_group = QGroupBox("运行日志")
        log_group.setMaximumHeight(150)
        log_group.setStyleSheet("""
            QGroupBox {
                background-color: #050505;
                border: 1px solid #1a1a1a;
                border-radius: 6px;
                margin-top: 8px;
                padding: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #00e676;
                font-size: 13px;
            }
        """)
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(5, 5, 5, 5)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0a0a;
                color: #00e676;
                border: none;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        main_vbox.addWidget(log_group)
        
        self._setup_status_bar()
    
    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.conn_indicator = QLabel("●")
        self.conn_indicator.setStyleSheet("color: #b71c1c; font-size: 16px;")
        self.conn_label = QLabel("设备：未连接")
        self.conn_label.setStyleSheet("color: #b0b0b0;")
        
        self.aimbot_status_label = QLabel("状态：已停止")
        self.aimbot_status_label.setStyleSheet("color: #ff1744; font-weight: bold;")
        
        self.fps_label = QLabel("FPS: 0.0")
        self.fps_label.setStyleSheet("color: #00e676; font-weight: bold;")
        
        self.status_bar.addWidget(self.conn_indicator)
        self.status_bar.addWidget(self.conn_label)
        self.status_bar.addPermanentWidget(self.aimbot_status_label)
        self.status_bar.addPermanentWidget(self.fps_label)
    
    def _create_section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: 14px; font-weight: bold; padding: 10px 0;")
        return label
    
    def _create_card(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {BG_CARD};
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: {TEXT_ACCENT};
                font-size: 14px;
            }}
        """)
        return group
    
    def _create_slider_with_value(self, min_val: float, max_val: float, 
                                   default: float, decimals: int = 0,
                                   callback=None) -> tuple:
        layout = QHBoxLayout()
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val * (10 ** decimals)))
        slider.setMaximum(int(max_val * (10 ** decimals)))
        slider.setValue(int(default * (10 ** decimals)))
        
        if decimals > 0:
            value_label = QLabel(f"{default:.{decimals}f}")
        else:
            value_label = QLabel(str(int(default)))
        value_label.setStyleSheet(f"color: {NEON}; font-weight: bold; min-width: 50px;")
        value_label.setAlignment(Qt.AlignCenter)
        
        def on_slider_change(val):
            real_val = val / (10 ** decimals)
            if decimals > 0:
                value_label.setText(f"{real_val:.{decimals}f}")
            else:
                value_label.setText(str(int(real_val)))
            if callback:
                callback(real_val)
        
        slider.valueChanged.connect(on_slider_change)
        
        layout.addWidget(slider, stretch=1)
        layout.addWidget(value_label)
        
        return slider, value_label, layout
    
    def _create_labeled_slider(self, label_text: str, min_val: float, max_val: float,
                               default: float, decimals: int = 0, 
                               callback=None, parent_layout=None) -> tuple:
        row_layout = QHBoxLayout()
        
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 100px;")
        
        slider, value_label, slider_layout = self._create_slider_with_value(
            min_val, max_val, default, decimals, callback
        )
        
        row_layout.addWidget(label)
        row_layout.addLayout(slider_layout)
        
        if parent_layout:
            parent_layout.addLayout(row_layout)
        
        return slider, value_label, row_layout
    
    def _create_checkbox(self, text: str, default: bool, callback=None) -> QCheckBox:
        checkbox = QCheckBox(text)
        checkbox.setChecked(default)
        if callback:
            checkbox.stateChanged.connect(lambda state: callback(bool(state)))
        return checkbox
    
    def _create_radio_group(self, options: list, default_index: int = 0, 
                           callback=None) -> tuple:
        group = QButtonGroup()
        buttons = []
        
        for i, option in enumerate(options):
            radio = QRadioButton(option)
            if i == default_index:
                radio.setChecked(True)
            group.addButton(radio, i)
            buttons.append(radio)
        
        if callback:
            group.buttonClicked.connect(lambda btn: callback(group.id(btn)))
        
        return group, buttons
    
    def _create_combo(self, options: list, default: str, callback=None) -> QComboBox:
        combo = QComboBox()
        combo.addItems(options)
        combo.setCurrentText(default)
        if callback:
            combo.currentTextChanged.connect(callback)
        return combo
    
    def _create_entry(self, default: str, width: int = 80, 
                     callback=None) -> QLineEdit:
        entry = QLineEdit(default)
        entry.setFixedWidth(width)
        entry.setAlignment(Qt.AlignCenter)
        
        if callback:
            entry.editingFinished.connect(lambda: callback(entry.text()))
        
        return entry
    
    def _create_neon_button(self, text: str, callback=None, width: int = None) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NEON};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #d50000;
            }}
            QPushButton:pressed {{
                background-color: #b71c1c;
            }}
        """)
        if width:
            btn.setFixedWidth(width)
        if callback:
            btn.clicked.connect(callback)
        return btn
    
    def _create_capture_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        control_card = self._create_card("🚀 主控制")
        control_layout = QVBoxLayout(control_card)
        
        main_btn_row = QHBoxLayout()
        self.start_btn = self._create_neon_button("🎯 启动瞄准", self._on_start_aimbot, 150)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NEON};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #d50000;
            }}
        """)
        
        self.stop_btn = QPushButton("⏹ 停止")
        self.stop_btn.clicked.connect(self._on_stop_aimbot)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        
        main_btn_row.addWidget(self.start_btn)
        main_btn_row.addWidget(self.stop_btn)
        main_btn_row.addStretch()
        control_layout.addLayout(main_btn_row)
        
        scroll_layout.addWidget(control_card)
        
        profile_card = self._create_card("💾 配置管理")
        profile_layout = QVBoxLayout(profile_card)
        
        row1 = QHBoxLayout()
        profile_label = QLabel("当前配置:")
        profile_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(self._get_profile_list())
        self.profile_combo.setMaximumWidth(250)
        row1.addWidget(profile_label)
        row1.addWidget(self.profile_combo)
        row1.addStretch()
        
        row2 = QHBoxLayout()
        create_btn = self._create_neon_button("新建", self._on_create_profile, 80)
        rename_btn = QPushButton("重命名")
        rename_btn.clicked.connect(self._on_rename_profile)
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(self._on_delete_profile)
        delete_btn.setStyleSheet("background-color: #b71c1c;")
        save_btn = self._create_neon_button("保存", self._on_save_profile, 80)
        load_btn = QPushButton("加载选中")
        load_btn.clicked.connect(self._on_load_profile)
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._on_reset_defaults)
        row2.addWidget(create_btn)
        row2.addWidget(rename_btn)
        row2.addWidget(delete_btn)
        row2.addWidget(save_btn)
        row2.addWidget(load_btn)
        row2.addWidget(reset_btn)
        row2.addStretch()
        
        profile_layout.addLayout(row1)
        profile_layout.addLayout(row2)
        
        scroll_layout.addWidget(profile_card)
        
        device_card = self._create_card("🔌 设备控制")
        device_layout = QVBoxLayout(device_card)
        
        btn_row = QHBoxLayout()
        self.connect_btn = self._create_neon_button("连接 MAKCU", self._on_connect, 150)
        btn_row.addWidget(self.connect_btn)
        
        test_btn = QPushButton("测试移动")
        test_btn.clicked.connect(test_move)
        btn_row.addWidget(test_btn)
        
        switch_btn = QPushButton("切换到 4M")
        switch_btn.clicked.connect(self._on_switch_to_4m)
        btn_row.addWidget(switch_btn)
        
        btn_row.addStretch()
        device_layout.addLayout(btn_row)
        
        toggle_row = QHBoxLayout()
        self.input_monitor_cb = self._create_checkbox("输入监控", False, self._on_input_monitor_toggle)
        toggle_row.addWidget(self.input_monitor_cb)
        
        self.aim_button_mask_cb = self._create_checkbox("瞄准按键屏蔽", 
            bool(getattr(config, 'aim_button_mask', False)), self._on_aim_button_mask_toggle)
        toggle_row.addWidget(self.aim_button_mask_cb)
        
        self.trigger_button_mask_cb = self._create_checkbox("扳机按键屏蔽",
            bool(getattr(config, 'trigger_button_mask', False)), self._on_trigger_button_mask_toggle)
        toggle_row.addWidget(self.trigger_button_mask_cb)
        
        toggle_row.addStretch()
        device_layout.addLayout(toggle_row)
        
        scroll_layout.addWidget(device_card)
        
        capture_card = self._create_card("📷 画面捕获")
        capture_layout = QVBoxLayout(capture_card)
        
        method_row = QHBoxLayout()
        method_label = QLabel("捕获方式:")
        method_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.capture_mode_combo = self._create_combo(
            ["MSS", "NDI", "DXGI", "CaptureCard", "UDP"],
            config.capturer_mode.upper(),
            self._on_capture_mode_change
        )
        method_row.addWidget(method_label)
        method_row.addWidget(self.capture_mode_combo)
        method_row.addStretch()
        capture_layout.addLayout(method_row)
        
        self.ndi_frame = QFrame()
        ndi_layout = QVBoxLayout(self.ndi_frame)
        ndi_layout.setContentsMargins(0, 0, 0, 0)
        
        ndi_source_row = QHBoxLayout()
        ndi_source_label = QLabel("NDI 源:")
        ndi_source_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.ndi_source_combo = QComboBox()
        self.ndi_source_combo.setMinimumWidth(250)
        ndi_source_row.addWidget(ndi_source_label)
        ndi_source_row.addWidget(self.ndi_source_combo)
        ndi_source_row.addStretch()
        ndi_layout.addLayout(ndi_source_row)
        
        res_row = QHBoxLayout()
        res_label = QLabel("主 PC 分辨率:")
        res_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.main_res_w_entry = self._create_entry(str(getattr(config, 'main_pc_width', 1920)), 80)
        x_label = QLabel(" × ")
        self.main_res_h_entry = self._create_entry(str(getattr(config, 'main_pc_height', 1080)), 80)
        res_row.addWidget(res_label)
        res_row.addWidget(self.main_res_w_entry)
        res_row.addWidget(x_label)
        res_row.addWidget(self.main_res_h_entry)
        res_row.addStretch()
        ndi_layout.addLayout(res_row)
        
        capture_layout.addWidget(self.ndi_frame)
        
        self.capturecard_frame = QFrame()
        cc_layout = QVBoxLayout(self.capturecard_frame)
        cc_layout.setContentsMargins(0, 0, 0, 0)
        
        cc_row1 = QHBoxLayout()
        cc_device_label = QLabel("设备索引:")
        cc_device_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.cc_device_entry = self._create_entry(str(getattr(config, 'capture_device_index', 0)), 60)
        cc_fourcc_label = QLabel("FourCC 格式:")
        self.cc_fourcc_entry = self._create_entry(
            ",".join(getattr(config, 'capture_fourcc_preference', ["NV12", "YUY2", "MJPG"])), 150)
        cc_row1.addWidget(cc_device_label)
        cc_row1.addWidget(self.cc_device_entry)
        cc_row1.addWidget(cc_fourcc_label)
        cc_row1.addWidget(self.cc_fourcc_entry)
        cc_row1.addStretch()
        cc_layout.addLayout(cc_row1)
        
        cc_row2 = QHBoxLayout()
        cc_res_label = QLabel("分辨率:")
        cc_res_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.cc_res_w_entry = self._create_entry(str(getattr(config, 'capture_width', 1920)), 80)
        cc_x_label = QLabel(" × ")
        self.cc_res_h_entry = self._create_entry(str(getattr(config, 'capture_height', 1080)), 80)
        cc_fps_label = QLabel("目标 FPS:")
        self.cc_fps_entry = self._create_entry(str(getattr(config, 'capture_fps', 240)), 60)
        cc_row2.addWidget(cc_res_label)
        cc_row2.addWidget(self.cc_res_w_entry)
        cc_row2.addWidget(cc_x_label)
        cc_row2.addWidget(self.cc_res_h_entry)
        cc_row2.addWidget(cc_fps_label)
        cc_row2.addWidget(self.cc_fps_entry)
        cc_row2.addStretch()
        cc_layout.addLayout(cc_row2)
        
        cc_row3 = QHBoxLayout()
        cc_range_x_label = QLabel("X 范围:")
        cc_range_x_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.cc_range_x_entry = self._create_entry(str(getattr(config, 'capture_range_x', 0)), 60)
        cc_range_y_label = QLabel("Y 范围:")
        self.cc_range_y_entry = self._create_entry(str(getattr(config, 'capture_range_y', 0)), 60)
        cc_row3.addWidget(cc_range_x_label)
        cc_row3.addWidget(self.cc_range_x_entry)
        cc_row3.addWidget(cc_range_y_label)
        cc_row3.addWidget(self.cc_range_y_entry)
        cc_row3.addStretch()
        cc_layout.addLayout(cc_row3)
        
        cc_row4 = QHBoxLayout()
        cc_offset_x_label = QLabel("X 偏移:")
        cc_offset_x_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.cc_offset_x_entry = self._create_entry(str(getattr(config, 'capture_offset_x', 0)), 60)
        cc_offset_y_label = QLabel("Y 偏移:")
        self.cc_offset_y_entry = self._create_entry(str(getattr(config, 'capture_offset_y', 0)), 60)
        cc_row4.addWidget(cc_offset_x_label)
        cc_row4.addWidget(self.cc_offset_x_entry)
        cc_row4.addWidget(cc_offset_y_label)
        cc_row4.addWidget(self.cc_offset_y_entry)
        cc_row4.addStretch()
        cc_layout.addLayout(cc_row4)
        
        capture_layout.addWidget(self.capturecard_frame)
        
        self.udp_frame = QFrame()
        udp_layout = QVBoxLayout(self.udp_frame)
        udp_layout.setContentsMargins(0, 0, 0, 0)
        
        udp_row = QHBoxLayout()
        udp_ip_label = QLabel("UDP IP:")
        udp_ip_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.udp_ip_entry = self._create_entry(getattr(config, 'udp_ip', '192.168.0.01'), 120)
        udp_port_label = QLabel("端口:")
        self.udp_port_entry = self._create_entry(str(getattr(config, 'udp_port', 1234)), 60)
        udp_row.addWidget(udp_ip_label)
        udp_row.addWidget(self.udp_ip_entry)
        udp_row.addWidget(udp_port_label)
        udp_row.addWidget(self.udp_port_entry)
        udp_row.addStretch()
        udp_layout.addLayout(udp_row)
        
        capture_layout.addWidget(self.udp_frame)
        
        debug_row = QHBoxLayout()
        self.debug_window_cb = self._create_checkbox(
            "调试窗口", 
            bool(getattr(config, 'show_debug_window', False)),
            self._on_debug_toggle
        )
        debug_row.addWidget(self.debug_window_cb)
        
        self.debug_text_info_cb = self._create_checkbox(
            "显示文本信息",
            bool(getattr(config, 'show_debug_text_info', True)),
            self._on_debug_text_info_toggle
        )
        debug_row.addWidget(self.debug_text_info_cb)
        debug_row.addStretch()
        capture_layout.addLayout(debug_row)
        
        scroll_layout.addWidget(capture_card)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self._update_capture_mode_visibility()
        
        return page
    
    def _create_detection_page(self) -> QWidget:
        # 1. Create main container and main layout
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create scroll area for the page
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # 2. Create AI Model GroupBox
        ai_model_group = QGroupBox("🤖 AI 模型")
        ai_model_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {BG_CARD};
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: {TEXT_ACCENT};
                font-size: 14px;
            }}
        """)
        ai_model_layout = QVBoxLayout(ai_model_group)
        
        # Model selection row
        model_row = QHBoxLayout()
        model_label = QLabel("模型文件:")
        model_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(250)
        self.model_combo.addItems(self._get_model_list())
        self.model_combo.currentTextChanged.connect(self._on_model_select)
        
        reload_btn = self._create_neon_button("重新加载", self._on_reload_model, 100)
        
        model_row.addWidget(model_label)
        model_row.addWidget(self.model_combo)
        model_row.addWidget(reload_btn)
        model_row.addStretch()
        ai_model_layout.addLayout(model_row)
        
        # Target Classes Selection subsection
        target_section = QGroupBox("🎯 目标类别选择")
        target_section.setStyleSheet(f"""
            QGroupBox {{
                background-color: {BG_CARD};
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                color: {TEXT_ACCENT};
                font-size: 14px;
            }}
        """)
        target_section_layout = QVBoxLayout(target_section)
        
        # Instruction label
        instruction_label = QLabel("提示：按顺序勾选类别，勾选顺序即为优先级顺序")
        instruction_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        instruction_label.setWordWrap(True)
        target_section_layout.addWidget(instruction_label)
        
        # QListWidget for target classes with cyberpunk style
        self.target_class_list = QListWidget()
        self.target_class_list.setMaximumHeight(200)
        self.target_class_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
                font-size: 13px;
            }
            QListWidget::item {
                background-color: transparent;
                color: #b0b0b0;
                padding: 12px 15px;
                margin: 2px 0;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background-color: #1a1a1a;
            }
            QListWidget::item:selected {
                color: #ffffff;
                background-color: #1a1a1a;
            }
            QListWidget::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #444;
                background-color: #111;
            }
            QListWidget::indicator:checked {
                border-color: #ff1744;
                background-color: #ff1744;
            }
            QListWidget::indicator:hover {
                border-color: #ff1744;
            }
        """)
        self.target_class_list.itemChanged.connect(self._on_class_item_changed)
        target_section_layout.addWidget(self.target_class_list)
        
        # Priority display label
        self.priority_label = QLabel("当前优先级：无")
        self.priority_label.setStyleSheet(f"""
            color: {TEXT_ACCENT};
            font-size: 12px;
            font-weight: bold;
            padding: 10px 15px;
            background-color: #0f0f0f;
            border-radius: 6px;
            border-left: 3px solid {TEXT_ACCENT};
        """)
        self.priority_label.setWordWrap(True)
        target_section_layout.addWidget(self.priority_label)
        
        ai_model_layout.addWidget(target_section)
        
        # Add AI Model GroupBox to main layout
        scroll_layout.addWidget(ai_model_group)
        
        # 3. Create Detection Settings GroupBox
        detection_group = self._create_card("🔍 识别设置")
        detection_layout = QVBoxLayout(detection_group)
        
        self.imgsz_slider, self.imgsz_label, imgsz_row = self._create_labeled_slider(
            "识别分辨率", 128, 1280, config.imgsz, 0,
            self._on_imgsz_change, detection_layout
        )
        
        self.max_detect_slider, self.max_detect_label, max_detect_row = self._create_labeled_slider(
            "最大检测数", 1, 100, config.max_detect, 0,
            self._on_max_detect_change, detection_layout
        )
        
        # Add Detection Settings GroupBox to main layout
        scroll_layout.addWidget(detection_group)
        
        # 4. Add stretch at the bottom to push panels up
        scroll_layout.addStretch()
        
        # Set up scroll area
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # 5. Return the complete page object
        return page
    
    def _create_aim_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        aim_card = self._create_card("🎮 瞄准设置")
        aim_layout = QVBoxLayout(aim_card)
        
        self.always_on_cb = self._create_checkbox(
            "始终开启瞄准",
            bool(getattr(config, 'always_on_aim', False)),
            self._on_always_on_toggle
        )
        aim_layout.addWidget(self.always_on_cb)
        
        self.fov_x_slider, self.fov_x_label, fov_x_row = self._create_labeled_slider(
            "FOV X 尺寸", 20, 500, config.fov_x_size, 0,
            self._on_fov_x_change, aim_layout
        )
        
        self.fov_y_slider, self.fov_y_label, fov_y_row = self._create_labeled_slider(
            "FOV Y 尺寸", 20, 500, config.fov_y_size, 0,
            self._on_fov_y_change, aim_layout
        )
        
        self.y_offset_slider, self.y_offset_label, y_offset_row = self._create_labeled_slider(
            "Y 偏移", 0, 20, config.player_y_offset, 0,
            self._on_y_offset_change, aim_layout
        )
        
        self.x_offset_slider, self.x_offset_label, x_offset_row = self._create_labeled_slider(
            "X 偏移", -50, 50, getattr(config, 'x_center_offset_px', 0), 0,
            self._on_x_offset_change, aim_layout
        )
        
        self.smoothing_slider, self.smoothing_label, smoothing_row = self._create_labeled_slider(
            "平滑度", 0.1, 20, config.in_game_sens, 2,
            self._on_smoothing_change, aim_layout
        )
        
        aim_key_row = QHBoxLayout()
        aim_key_label = QLabel("瞄准按键:")
        aim_key_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 100px;")
        
        self.aim_key_group, self.aim_key_buttons = self._create_radio_group(
            ["左键", "右键", "中键", "侧键 4", "侧键 5"],
            config.selected_mouse_button,
            self._on_aim_key_change
        )
        
        aim_key_row.addWidget(aim_key_label)
        for btn in self.aim_key_buttons:
            aim_key_row.addWidget(btn)
        aim_key_row.addStretch()
        aim_layout.addLayout(aim_key_row)
        
        scroll_layout.addWidget(aim_card)
        
        height_card = self._create_card("📏 高度瞄准")
        height_layout = QVBoxLayout(height_card)
        
        self.height_targeting_cb = self._create_checkbox(
            "启用高度瞄准",
            bool(getattr(config, 'height_targeting_enabled', True)),
            self._on_height_targeting_toggle
        )
        height_layout.addWidget(self.height_targeting_cb)
        
        self.target_height_slider, self.target_height_label, target_height_row = self._create_labeled_slider(
            "目标高度", 0.1, 1.0, config.target_height, 3,
            self._on_target_height_change, height_layout
        )
        
        self.height_deadzone_cb = self._create_checkbox(
            "高度死区",
            bool(getattr(config, 'height_deadzone_enabled', True)),
            self._on_height_deadzone_toggle
        )
        height_layout.addWidget(self.height_deadzone_cb)
        
        self.deadzone_min_slider, self.deadzone_min_label, deadzone_min_row = self._create_labeled_slider(
            "死区最小值", 0.0, 0.235, config.height_deadzone_min, 3,
            self._on_deadzone_min_change, height_layout
        )
        
        self.deadzone_max_slider, self.deadzone_max_label, deadzone_max_row = self._create_labeled_slider(
            "死区最大值", 0.0, 0.235, config.height_deadzone_max, 3,
            self._on_deadzone_max_change, height_layout
        )
        
        self.deadzone_tolerance_slider, self.deadzone_tolerance_label, deadzone_tol_row = self._create_labeled_slider(
            "进入容差", 0.0, 15.0, config.height_deadzone_tolerance, 3,
            self._on_deadzone_tolerance_change, height_layout
        )
        
        scroll_layout.addWidget(height_card)
        
        mouse_card = self._create_card("🖱️ 鼠标移动")
        mouse_layout = QVBoxLayout(mouse_card)
        
        self.mouse_x_slider, self.mouse_x_label, mouse_x_row = self._create_labeled_slider(
            "X 轴速度", 0.0, 5.0, getattr(config, 'mouse_movement_multiplier_x', 1.0), 2,
            self._on_mouse_x_change, mouse_layout
        )
        
        self.mouse_y_slider, self.mouse_y_label, mouse_y_row = self._create_labeled_slider(
            "Y 轴速度", 0.0, 5.0, getattr(config, 'mouse_movement_multiplier_y', 1.0), 2,
            self._on_mouse_y_change, mouse_layout
        )
        
        self.mouse_x_enabled_cb = self._create_checkbox(
            "启用 X 轴移动",
            bool(getattr(config, 'mouse_movement_enabled_x', True)),
            self._on_mouse_x_enabled_toggle
        )
        mouse_layout.addWidget(self.mouse_x_enabled_cb)
        
        self.mouse_y_enabled_cb = self._create_checkbox(
            "启用 Y 轴移动",
            bool(getattr(config, 'mouse_movement_enabled_y', True)),
            self._on_mouse_y_enabled_toggle
        )
        mouse_layout.addWidget(self.mouse_y_enabled_cb)
        
        scroll_layout.addWidget(mouse_card)
        
        mode_card = self._create_card("⚡ 瞄准模式")
        mode_layout = QVBoxLayout(mode_card)
        
        mode_row = QHBoxLayout()
        mode_label = QLabel("模式:")
        mode_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 60px;")
        
        self.aim_mode_group, self.aim_mode_buttons = self._create_radio_group(
            ["普通", "贝塞尔", "静默", "平滑", "NCAF"],
            ["normal", "bezier", "silent", "smooth", "ncaf"].index(config.mode) if config.mode in ["normal", "bezier", "silent", "smooth", "ncaf"] else 0,
            self._on_aim_mode_change
        )
        
        mode_row.addWidget(mode_label)
        for btn in self.aim_mode_buttons:
            mode_row.addWidget(btn)
        mode_row.addStretch()
        mode_layout.addLayout(mode_row)
        
        self.mode_stack = QStackedWidget()
        
        normal_page = QWidget()
        normal_layout = QVBoxLayout(normal_page)
        self.normal_x_slider, _, _ = self._create_labeled_slider(
            "X 速度", 0.1, 1.0, config.normal_x_speed, 2,
            lambda v: setattr(config, 'normal_x_speed', v), normal_layout
        )
        self.normal_y_slider, _, _ = self._create_labeled_slider(
            "Y 速度", 0.1, 1.0, config.normal_y_speed, 2,
            lambda v: setattr(config, 'normal_y_speed', v), normal_layout
        )
        self.aim_humanize_cb = self._create_checkbox(
            "拟人化", bool(config.aim_humanization > 0), self._on_humanize_toggle
        )
        normal_layout.addWidget(self.aim_humanize_cb)
        self.humanize_slider, self.humanize_label, _ = self._create_labeled_slider(
            "拟人化强度", 10, 50, config.aim_humanization, 0,
            self._on_humanize_change, normal_layout
        )
        self.mode_stack.addWidget(normal_page)
        
        bezier_page = QWidget()
        bezier_layout = QVBoxLayout(bezier_page)
        self._create_labeled_slider(
            "贝塞尔段数", 0, 20, config.bezier_segments, 0,
            lambda v: setattr(config, 'bezier_segments', int(v)), bezier_layout
        )
        self._create_labeled_slider(
            "控制点 X", 0, 60, config.bezier_ctrl_x, 0,
            lambda v: setattr(config, 'bezier_ctrl_x', int(v)), bezier_layout
        )
        self._create_labeled_slider(
            "控制点 Y", 0, 60, config.bezier_ctrl_y, 0,
            lambda v: setattr(config, 'bezier_ctrl_y', int(v)), bezier_layout
        )
        self.mode_stack.addWidget(bezier_page)
        
        silent_page = QWidget()
        silent_layout = QVBoxLayout(silent_page)
        self._create_labeled_slider(
            "静默段数", 0, 20, config.silent_segments, 0,
            lambda v: setattr(config, 'silent_segments', int(v)), silent_layout
        )
        self._create_labeled_slider(
            "控制点 X", 0, 60, config.silent_ctrl_x, 0,
            lambda v: setattr(config, 'silent_ctrl_x', int(v)), silent_layout
        )
        self._create_labeled_slider(
            "控制点 Y", 0, 60, config.silent_ctrl_y, 0,
            lambda v: setattr(config, 'silent_ctrl_y', int(v)), silent_layout
        )
        self._create_labeled_slider(
            "静默速度", 1, 6, config.silent_speed, 0,
            lambda v: setattr(config, 'silent_speed', int(v)), silent_layout
        )
        self._create_labeled_slider(
            "冷却时间", 0.0, 0.5, config.silent_cooldown, 2,
            lambda v: setattr(config, 'silent_cooldown', v), silent_layout
        )
        self.mode_stack.addWidget(silent_page)
        
        smooth_page = QWidget()
        smooth_layout = QVBoxLayout(smooth_page)
        self._create_labeled_slider(
            "重力", 1, 20, config.smooth_gravity, 1,
            lambda v: setattr(config, 'smooth_gravity', v), smooth_layout
        )
        self._create_labeled_slider(
            "风力", 1, 20, config.smooth_wind, 1,
            lambda v: setattr(config, 'smooth_wind', v), smooth_layout
        )
        self._create_labeled_slider(
            "近距离速度", 0.1, 2.0, config.smooth_close_speed, 2,
            lambda v: setattr(config, 'smooth_close_speed', v), smooth_layout
        )
        self._create_labeled_slider(
            "远距离速度", 0.1, 2.0, config.smooth_far_speed, 2,
            lambda v: setattr(config, 'smooth_far_speed', v), smooth_layout
        )
        self._create_labeled_slider(
            "反应时间", 0.01, 0.3, config.smooth_reaction_max, 3,
            lambda v: setattr(config, 'smooth_reaction_max', v), smooth_layout
        )
        self._create_labeled_slider(
            "最大步长", 5, 50, config.smooth_max_step, 0,
            lambda v: setattr(config, 'smooth_max_step', v), smooth_layout
        )
        self.mode_stack.addWidget(smooth_page)
        
        ncaf_page = QWidget()
        ncaf_layout = QVBoxLayout(ncaf_page)
        self._create_labeled_slider(
            "近距半径", 10, 200, config.ncaf_near_radius, 0,
            lambda v: setattr(config, 'ncaf_near_radius', v), ncaf_layout
        )
        self._create_labeled_slider(
            "吸附半径", 5, 50, config.ncaf_snap_radius, 0,
            lambda v: setattr(config, 'ncaf_snap_radius', v), ncaf_layout
        )
        self._create_labeled_slider(
            "Alpha 指数", 0.5, 3.0, config.ncaf_alpha, 2,
            lambda v: setattr(config, 'ncaf_alpha', v), ncaf_layout
        )
        self._create_labeled_slider(
            "吸附加成", 0.5, 3.0, config.ncaf_snap_boost, 2,
            lambda v: setattr(config, 'ncaf_snap_boost', v), ncaf_layout
        )
        self._create_labeled_slider(
            "最大步长", 5, 100, config.ncaf_max_step, 0,
            lambda v: setattr(config, 'ncaf_max_step', v), ncaf_layout
        )
        self.mode_stack.addWidget(ncaf_page)
        
        mode_layout.addWidget(self.mode_stack)
        scroll_layout.addWidget(mode_card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self._update_mode_stack()
        
        return page
    
    def _create_trigger_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        trigger_card = self._create_card("🧨 扳机设置")
        trigger_layout = QVBoxLayout(trigger_card)
        
        toggle_row = QHBoxLayout()
        self.trigger_enabled_cb = self._create_checkbox(
            "启用扳机",
            bool(getattr(config, 'trigger_enabled', False)),
            self._on_trigger_enabled_toggle
        )
        toggle_row.addWidget(self.trigger_enabled_cb)
        
        self.trigger_always_on_cb = self._create_checkbox(
            "始终开启",
            bool(getattr(config, 'trigger_always_on', False)),
            self._on_trigger_always_on_toggle
        )
        toggle_row.addWidget(self.trigger_always_on_cb)
        
        self.trigger_head_only_cb = self._create_checkbox(
            "仅头部",
            bool(getattr(config, 'trigger_head_only', False)),
            self._on_trigger_head_only_toggle
        )
        toggle_row.addWidget(self.trigger_head_only_cb)
        toggle_row.addStretch()
        trigger_layout.addLayout(toggle_row)
        
        mode_row = QHBoxLayout()
        mode_label = QLabel("扳机模式:")
        mode_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.trigger_mode_combo = self._create_combo(
            ["模式 1 (距离检测)", "模式 2 (范围检测)", "模式 3 (颜色检测)"],
            ["模式 1 (距离检测)", "模式 2 (范围检测)", "模式 3 (颜色检测)"][getattr(config, 'trigger_mode', 1) - 1],
            self._on_trigger_mode_change
        )
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.trigger_mode_combo)
        mode_row.addStretch()
        trigger_layout.addLayout(mode_row)
        
        key_row = QHBoxLayout()
        key_label = QLabel("扳机按键:")
        key_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.trigger_key_group, self.trigger_key_buttons = self._create_radio_group(
            ["左键", "右键", "中键", "侧键 4", "侧键 5"],
            getattr(config, 'trigger_button', 1),
            self._on_trigger_key_change
        )
        key_row.addWidget(key_label)
        for btn in self.trigger_key_buttons:
            key_row.addWidget(btn)
        key_row.addStretch()
        trigger_layout.addLayout(key_row)
        
        params_frame = QFrame()
        params_frame.setStyleSheet(f"background-color: {BG_INPUT}; border-radius: 8px; padding: 10px;")
        params_layout = QVBoxLayout(params_frame)
        
        row1 = QHBoxLayout()
        
        self.trigger_radius_label = QLabel("半径 (px):")
        self.trigger_radius_entry = self._create_entry(str(getattr(config, 'trigger_radius_px', 8)), 60)
        row1.addWidget(self.trigger_radius_label)
        row1.addWidget(self.trigger_radius_entry)
        
        self.trigger_delay_label = QLabel("延迟 (ms):")
        self.trigger_delay_entry = self._create_entry(str(getattr(config, 'trigger_delay_ms', 30)), 60)
        row1.addWidget(self.trigger_delay_label)
        row1.addWidget(self.trigger_delay_entry)
        
        self.trigger_cooldown_label = QLabel("冷却 (ms):")
        self.trigger_cooldown_entry = self._create_entry(str(getattr(config, 'trigger_cooldown_ms', 120)), 60)
        row1.addWidget(self.trigger_cooldown_label)
        row1.addWidget(self.trigger_cooldown_entry)
        
        self.trigger_conf_label = QLabel("最小置信度:")
        self.trigger_conf_entry = self._create_entry(f"{getattr(config, 'trigger_min_conf', 0.35):.2f}", 60)
        row1.addWidget(self.trigger_conf_label)
        row1.addWidget(self.trigger_conf_entry)
        
        row1.addStretch()
        params_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        self.trigger_range_x_label = QLabel("范围 X:")
        self.trigger_range_x_entry = self._create_entry(f"{getattr(config, 'trigger_mode2_range_x', 50.0):.1f}", 60)
        row2.addWidget(self.trigger_range_x_label)
        row2.addWidget(self.trigger_range_x_entry)
        
        self.trigger_range_y_label = QLabel("范围 Y:")
        self.trigger_range_y_entry = self._create_entry(f"{getattr(config, 'trigger_mode2_range_y', 50.0):.1f}", 60)
        row2.addWidget(self.trigger_range_y_label)
        row2.addWidget(self.trigger_range_y_entry)
        
        row2.addStretch()
        params_layout.addLayout(row2)
        
        row3 = QHBoxLayout()
        self.trigger_color_label = QLabel("目标颜色:")
        self.color_preview_btn = QPushButton()
        self.color_preview_btn.setFixedSize(60, 25)
        self.color_preview_btn.setStyleSheet(
            f"background-color: {getattr(config, 'trigger_hsv_color_hex', '#a61fe0')}; border: none; border-radius: 4px;"
        )
        self.color_preview_btn.clicked.connect(self._on_pick_trigger_color)
        row3.addWidget(self.trigger_color_label)
        row3.addWidget(self.color_preview_btn)
        
        self.h_min_label = QLabel("H 最小:")
        self.h_min_entry = self._create_entry(str(getattr(config, 'trigger_hsv_h_min', 0)), 50)
        row3.addWidget(self.h_min_label)
        row3.addWidget(self.h_min_entry)
        
        self.h_max_label = QLabel("H 最大:")
        self.h_max_entry = self._create_entry(str(getattr(config, 'trigger_hsv_h_max', 179)), 50)
        row3.addWidget(self.h_max_label)
        row3.addWidget(self.h_max_entry)
        
        self.color_radius_label = QLabel("颜色半径:")
        self.color_radius_entry = self._create_entry(str(getattr(config, 'trigger_color_radius_px', 20)), 50)
        row3.addWidget(self.color_radius_label)
        row3.addWidget(self.color_radius_entry)
        
        row3.addStretch()
        params_layout.addLayout(row3)
        
        row4 = QHBoxLayout()
        self.s_min_label = QLabel("S 最小:")
        self.s_min_entry = self._create_entry(str(getattr(config, 'trigger_hsv_s_min', 0)), 50)
        row4.addWidget(self.s_min_label)
        row4.addWidget(self.s_min_entry)
        
        self.s_max_label = QLabel("S 最大:")
        self.s_max_entry = self._create_entry(str(getattr(config, 'trigger_hsv_s_max', 255)), 50)
        row4.addWidget(self.s_max_label)
        row4.addWidget(self.s_max_entry)
        
        self.v_min_label = QLabel("V 最小:")
        self.v_min_entry = self._create_entry(str(getattr(config, 'trigger_hsv_v_min', 0)), 50)
        row4.addWidget(self.v_min_label)
        row4.addWidget(self.v_min_entry)
        
        self.v_max_label = QLabel("V 最大:")
        self.v_max_entry = self._create_entry(str(getattr(config, 'trigger_hsv_v_max', 255)), 50)
        row4.addWidget(self.v_max_label)
        row4.addWidget(self.v_max_entry)
        
        row4.addStretch()
        params_layout.addLayout(row4)
        
        trigger_layout.addWidget(params_frame)
        scroll_layout.addWidget(trigger_card)
        
        rcs_card = self._create_card("🎯 压枪控制 (RCS)")
        rcs_layout = QVBoxLayout(rcs_card)
        
        rcs_toggle_row = QHBoxLayout()
        self.rcs_enabled_cb = self._create_checkbox(
            "启用压枪",
            bool(getattr(config, 'rcs_enabled', False)),
            self._on_rcs_enabled_toggle
        )
        rcs_toggle_row.addWidget(self.rcs_enabled_cb)
        
        self.rcs_ads_only_cb = self._create_checkbox(
            "仅开镜时",
            bool(getattr(config, 'rcs_ads_only', False)),
            self._on_rcs_ads_only_toggle
        )
        rcs_toggle_row.addWidget(self.rcs_ads_only_cb)
        
        self.rcs_disable_y_cb = self._create_checkbox(
            "禁用 Y 轴瞄准",
            bool(getattr(config, 'rcs_disable_y_axis', False)),
            self._on_rcs_disable_y_toggle
        )
        rcs_toggle_row.addWidget(self.rcs_disable_y_cb)
        rcs_toggle_row.addStretch()
        rcs_layout.addLayout(rcs_toggle_row)
        
        rcs_mode_row = QHBoxLayout()
        rcs_mode_label = QLabel("压枪模式:")
        rcs_mode_label.setStyleSheet(f"color: {TEXT_PRIMARY}; min-width: 80px;")
        self.rcs_mode_group, self.rcs_mode_buttons = self._create_radio_group(
            ["简单", "游戏"],
            0 if getattr(config, 'rcs_mode', 'simple') == 'simple' else 1,
            self._on_rcs_mode_change
        )
        rcs_mode_row.addWidget(rcs_mode_label)
        for btn in self.rcs_mode_buttons:
            rcs_mode_row.addWidget(btn)
        rcs_mode_row.addStretch()
        rcs_layout.addLayout(rcs_mode_row)
        
        self.rcs_game_frame = QFrame()
        rcs_game_layout = QVBoxLayout(self.rcs_game_frame)
        rcs_game_layout.setContentsMargins(0, 0, 0, 0)
        
        game_row = QHBoxLayout()
        game_label = QLabel("游戏:")
        self.rcs_game_combo = QComboBox()
        self.rcs_game_combo.addItems(get_available_games())
        self.rcs_game_combo.currentTextChanged.connect(self._on_rcs_game_change)
        game_row.addWidget(game_label)
        game_row.addWidget(self.rcs_game_combo)
        game_row.addStretch()
        rcs_game_layout.addLayout(game_row)
        
        weapon_row = QHBoxLayout()
        weapon_label = QLabel("武器:")
        self.rcs_weapon_combo = QComboBox()
        self.rcs_weapon_combo.currentTextChanged.connect(self._on_rcs_weapon_change)
        weapon_row.addWidget(weapon_label)
        weapon_row.addWidget(self.rcs_weapon_combo)
        weapon_row.addStretch()
        rcs_game_layout.addLayout(weapon_row)
        
        rcs_layout.addWidget(self.rcs_game_frame)
        
        self.rcs_simple_frame = QFrame()
        rcs_simple_layout = QVBoxLayout(self.rcs_simple_frame)
        rcs_simple_layout.setContentsMargins(0, 0, 0, 0)
        
        self.rcs_x_strength_slider, _, _ = self._create_labeled_slider(
            "X 轴强度", 0.1, 5.0, config.rcs_x_strength, 2,
            self._on_rcs_x_strength_change, rcs_simple_layout
        )
        
        self.rcs_x_delay_slider, _, _ = self._create_labeled_slider(
            "X 轴延迟 (ms)", 1, 100, int(config.rcs_x_delay * 1000), 0,
            self._on_rcs_x_delay_change, rcs_simple_layout
        )
        
        self.rcs_y_random_cb = self._create_checkbox(
            "启用 Y 轴随机抖动",
            bool(getattr(config, 'rcs_y_random_enabled', False)),
            self._on_rcs_y_random_toggle
        )
        rcs_simple_layout.addWidget(self.rcs_y_random_cb)
        
        self.rcs_y_strength_slider, _, _ = self._create_labeled_slider(
            "抖动强度", 0.1, 3.0, config.rcs_y_random_strength, 2,
            self._on_rcs_y_strength_change, rcs_simple_layout
        )
        
        self.rcs_y_delay_slider, _, _ = self._create_labeled_slider(
            "抖动延迟 (ms)", 1, 100, int(config.rcs_y_random_delay * 1000), 0,
            self._on_rcs_y_delay_change, rcs_simple_layout
        )
        
        rcs_key_row = QHBoxLayout()
        rcs_key_label = QLabel("压枪按键:")
        self.rcs_key_group, self.rcs_key_buttons = self._create_radio_group(
            ["左键", "右键", "中键", "侧键 4", "侧键 5"],
            getattr(config, 'rcs_button', 0),
            self._on_rcs_key_change
        )
        rcs_key_row.addWidget(rcs_key_label)
        for btn in self.rcs_key_buttons:
            rcs_key_row.addWidget(btn)
        rcs_key_row.addStretch()
        rcs_simple_layout.addLayout(rcs_key_row)
        
        rcs_layout.addWidget(self.rcs_simple_frame)
        
        scroll_layout.addWidget(rcs_card)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        self._update_trigger_mode_visibility()
        self._update_rcs_mode_visibility()
        
        return page
    
    def _create_hardware_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        info_label = QLabel("💡 提示：MAKCU 设备控制、主控制与配置管理已移至【画面与捕获】页面")
        info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; padding: 20px;")
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        
        scroll_layout.addWidget(info_label)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        return page
    
    def _setup_logging(self):
        sys.stdout = StreamRedirector(log_emitter, 'stdout')
        sys.stderr = StreamRedirector(log_emitter, 'stderr')
        log_emitter.stdout_signal.connect(self._append_log)
        log_emitter.stderr_signal.connect(self._append_log)
    
    def _append_log(self, text: str):
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
    
    def _start_polling(self):
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self._poll_status)
        self.fps_timer.start(200)
        
        self.ndi_timer = QTimer()
        self.ndi_timer.timeout.connect(self._poll_ndi_sources)
        self.ndi_timer.start(1000)
    
    def _poll_status(self):
        fps = getattr(main, 'fps', 0.0)
        self.status_updater.update_fps.emit(fps)
        
        connected = getattr(config, 'makcu_connected', False)
        status_msg = getattr(config, 'makcu_status_msg', '未连接')
        self.status_updater.update_connection.emit(connected, status_msg)
        
        running = is_aimbot_running()
        self.status_updater.update_aimbot_status.emit(running)
    
    def _poll_ndi_sources(self):
        sources = getattr(config, 'ndi_sources', [])
        if sources:
            self.ndi_source_combo.clear()
            self.ndi_source_combo.addItems(sources)
            selected = getattr(config, 'ndi_selected_source', None)
            if selected and selected in sources:
                self.ndi_source_combo.setCurrentText(selected)
    
    @Slot(float)
    def _on_fps_update(self, fps: float):
        self.fps_label.setText(f"FPS: {fps:.1f}")
    
    @Slot(bool, str)
    def _on_connection_update(self, connected: bool, msg: str):
        if connected:
            self.conn_indicator.setStyleSheet("color: #00FF00; font-size: 16px;")
            self.conn_label.setText(f"设备：{msg}")
            self.conn_label.setStyleSheet("color: #00FF00;")
        else:
            self.conn_indicator.setStyleSheet("color: #b71c1c; font-size: 16px;")
            self.conn_label.setText(f"设备：{msg}")
            self.conn_label.setStyleSheet("color: #b0b0b0;")
    
    @Slot(bool)
    def _on_aimbot_status_update(self, running: bool):
        if running:
            self.aimbot_status_label.setText("状态：运行中")
            self.aimbot_status_label.setStyleSheet("color: #00e676; font-weight: bold;")
        else:
            self.aimbot_status_label.setText("状态：已停止")
            self.aimbot_status_label.setStyleSheet("color: #ff1744; font-weight: bold;")
    
    def _auto_connect(self):
        QTimer.singleShot(500, self._on_connect)
    
    def _on_nav_changed(self, index: int):
        self.content_stack.setCurrentIndex(index)
    
    def _get_model_list(self) -> List[str]:
        models = []
        for ext in ("pt", "onnx", "engine"):
            models.extend(glob.glob(f"models/*.{ext}"))
        return [os.path.basename(m) for m in models]
    
    def _get_profile_list(self) -> List[str]:
        profiles = ["config_profile"]
        for f in glob.glob("config_*.json"):
            name = os.path.splitext(os.path.basename(f))[0]
            if name not in profiles:
                profiles.append(name)
        return profiles
    
    def _update_capture_mode_visibility(self):
        mode = self.capture_mode_combo.currentText()
        self.ndi_frame.setVisible(mode == "NDI")
        self.capturecard_frame.setVisible(mode == "CaptureCard")
        self.udp_frame.setVisible(mode == "UDP")
    
    def _update_mode_stack(self):
        mode = config.mode
        mode_map = {"normal": 0, "bezier": 1, "silent": 2, "smooth": 3, "ncaf": 4}
        self.mode_stack.setCurrentIndex(mode_map.get(mode, 0))
    
    def _update_trigger_mode_visibility(self):
        mode = getattr(config, 'trigger_mode', 1)
        enabled = self.trigger_enabled_cb.isChecked()
        
        # 模式 1 (距离检测): 显示半径、延迟、冷却、置信度
        # 模式 2 (范围检测): 显示范围 X、范围 Y
        # 模式 3 (颜色检测): 显示 HSV 相关控件
        
        # 模式 1 和模式 3 显示半径、延迟、冷却、置信度
        radius_visible = mode != 2
        self.trigger_radius_label.setVisible(radius_visible)
        self.trigger_radius_entry.setVisible(radius_visible)
        self.trigger_delay_label.setVisible(radius_visible)
        self.trigger_delay_entry.setVisible(radius_visible)
        self.trigger_cooldown_label.setVisible(radius_visible)
        self.trigger_cooldown_entry.setVisible(radius_visible)
        self.trigger_conf_label.setVisible(radius_visible)
        self.trigger_conf_entry.setVisible(radius_visible)
        
        # 仅模式 2 显示范围 X、范围 Y
        range_visible = mode == 2
        self.trigger_range_x_label.setVisible(range_visible)
        self.trigger_range_x_entry.setVisible(range_visible)
        self.trigger_range_y_label.setVisible(range_visible)
        self.trigger_range_y_entry.setVisible(range_visible)
        
        # 仅模式 3 显示 HSV 相关控件
        hsv_visible = mode == 3
        self.trigger_color_label.setVisible(hsv_visible)
        self.color_preview_btn.setVisible(hsv_visible)
        self.h_min_label.setVisible(hsv_visible)
        self.h_min_entry.setVisible(hsv_visible)
        self.h_max_label.setVisible(hsv_visible)
        self.h_max_entry.setVisible(hsv_visible)
        self.color_radius_label.setVisible(hsv_visible)
        self.color_radius_entry.setVisible(hsv_visible)
        self.s_min_label.setVisible(hsv_visible)
        self.s_min_entry.setVisible(hsv_visible)
        self.s_max_label.setVisible(hsv_visible)
        self.s_max_entry.setVisible(hsv_visible)
        self.v_min_label.setVisible(hsv_visible)
        self.v_min_entry.setVisible(hsv_visible)
        self.v_max_label.setVisible(hsv_visible)
        self.v_max_entry.setVisible(hsv_visible)
    
    def _update_rcs_mode_visibility(self):
        mode = "simple" if self.rcs_mode_group.checkedId() == 0 else "game"
        self.rcs_game_frame.setVisible(mode == "game")
        self.rcs_simple_frame.setVisible(mode == "simple")
    
    def _on_connect(self):
        if connect_to_makcu():
            config.makcu_connected = True
            config.makcu_status_msg = "已连接"
            self._append_log("[INFO] MAKCU 设备连接成功\n")
        else:
            config.makcu_connected = False
            config.makcu_status_msg = "连接失败"
            self._append_log("[ERROR] MAKCU 设备连接失败\n")
    
    def _on_switch_to_4m(self):
        if not config.makcu_connected:
            self._append_log("[WARN] 请先连接 MAKCU 设备\n")
            return
        if switch_to_4m():
            config.makcu_status_msg = "已连接 (4M)"
            self._append_log("[INFO] 成功切换到 4M 波特率\n")
        else:
            self._append_log("[WARN] 切换到 4M 失败\n")
    
    def _on_input_monitor_toggle(self, checked: bool):
        pass
    
    def _on_aim_button_mask_toggle(self, checked: bool):
        config.aim_button_mask = checked
        config.save()
    
    def _on_trigger_button_mask_toggle(self, checked: bool):
        config.trigger_button_mask = checked
        config.save()
    
    def _on_capture_mode_change(self, text: str):
        mode_map = {"MSS": "mss", "NDI": "ndi", "DXGI": "dxgi", "CAPTURECARD": "capturecard", "UDP": "udp"}
        config.capturer_mode = mode_map.get(text.upper(), "mss")
        self._update_capture_mode_visibility()
        config.save()
    
    def _on_debug_toggle(self, checked: bool):
        config.show_debug_window = checked
        config.save()
    
    def _on_debug_text_info_toggle(self, checked: bool):
        config.show_debug_text_info = checked
        config.save()
    
    def _on_model_select(self, name: str):
        path = os.path.join("models", name)
        if os.path.isfile(path):
            config.model_path = path
            try:
                reload_model(path)
                self._load_class_list()
            except Exception as e:
                self._append_log(f"[ERROR] 加载模型失败：{e}\n")
    
    def _on_reload_model(self):
        try:
            reload_model(config.model_path)
            self._load_class_list()
        except Exception as e:
            self._append_log(f"[ERROR] 重新加载模型失败：{e}\n")
    
    def _load_class_list(self):
        try:
            classes = get_model_classes(config.model_path)
            
            # Update target class checkboxes
            self._update_target_class_checkboxes(classes)
            
            # Update priority display
            self._update_priority_display()
            
            # Update detection resolution slider to match model's native imgsz
            self._update_imgsz_ui(config.imgsz)
        except Exception as e:
            self._append_log(f"[ERROR] 加载类别列表失败：{e}\n")
    
    def _update_target_class_checkboxes(self, classes):
        """Update target class QListWidget based on loaded model classes"""
        # 1. Block signals during population to prevent triggering _on_class_item_changed
        self.target_class_list.blockSignals(True)
        self.target_class_list.clear()
        
        # 2. Populate QListWidget with checkable items
        for i, class_name in enumerate(classes):
            item = QListWidgetItem(class_name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            
            # Set check state based on config
            if i in config.target_classes:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            
            self.target_class_list.addItem(item)
        
        # 3. Restore signals
        self.target_class_list.blockSignals(False)
        
        # 4. Update priority display
        priority_names = [config.model_classes[idx] for idx in config.target_classes if idx < len(config.model_classes)]
        if not priority_names:
            self.priority_label.setText("当前优先级：无")
        else:
            self.priority_label.setText(f"当前优先级：{' > '.join(priority_names)}")
    
    def _on_class_item_changed(self, item):
        """Handle QListWidgetItem check state change - maintains click order priority"""
        class_name = item.text()
        
        # Find the class index from config.model_classes
        try:
            class_index = config.model_classes.index(class_name)
        except ValueError:
            print(f"[ERROR] Class '{class_name}' not found in model_classes")
            return
        
        # Update config.target_classes based on check state
        if item.checkState() == Qt.Checked:
            # Append to end of list if not already present
            if class_index not in config.target_classes:
                config.target_classes.append(class_index)
        else:
            # Remove from list if present
            if class_index in config.target_classes:
                config.target_classes.remove(class_index)
        
        config.save()
        
        # Update priority display
        self._update_priority_display()
        
        # Debug output
        print(f"[DEBUG] 当前瞄准优先级 (ID): {config.target_classes}")
    
    def _update_priority_display(self):
        """Update the priority label to show current target class priority order"""
        if not config.target_classes:
            self.priority_label.setText("当前优先级：无")
            return
        
        # Get class names from model_classes based on indices
        priority_names = []
        for idx in config.target_classes:
            if 0 <= idx < len(config.model_classes):
                class_name = config.model_classes[idx]
                priority_names.append(class_name)
        
        # Join with " > " separator
        if priority_names:
            priority_text = " > ".join(priority_names)
            self.priority_label.setText(f"当前优先级：{priority_text}")
        else:
            self.priority_label.setText("当前优先级：无")
    
    def _update_imgsz_ui(self, imgsz: int):
        """Update the imgsz slider and label to match the model's native resolution"""
        if hasattr(self, 'imgsz_slider') and hasattr(self, 'imgsz_label'):
            self._updating_imgsz = True
            self.imgsz_slider.setValue(imgsz)
            self.imgsz_label.setText(str(imgsz))
            self._updating_imgsz = False
    
    def _on_imgsz_change(self, val: float):
        if self._updating_imgsz:
            return
        val = int(val)
        val = max(128, min(1280, val))
        val = (val // 32) * 32
        config.imgsz = val
        self._updating_imgsz = True
        self.imgsz_slider.setValue(val)
        self.imgsz_label.setText(str(val))
        self._updating_imgsz = False
    
    def _on_max_detect_change(self, val: float):
        config.max_detect = int(val)
    
    def _on_always_on_toggle(self, checked: bool):
        config.always_on_aim = checked
        config.save()
    
    def _on_fov_x_change(self, val: float):
        if self._updating_fov_x:
            return
        config.fov_x_size = int(val)
        config.region_size = max(config.fov_x_size, config.fov_y_size)
    
    def _on_fov_y_change(self, val: float):
        if self._updating_fov_y:
            return
        config.fov_y_size = int(val)
        config.region_size = max(config.fov_x_size, config.fov_y_size)
    
    def _on_y_offset_change(self, val: float):
        config.player_y_offset = int(val)
    
    def _on_x_offset_change(self, val: float):
        config.x_center_offset_px = int(val)
        config.save_async()
    
    def _on_smoothing_change(self, val: float):
        config.in_game_sens = round(val, 2)
    
    def _on_aim_key_change(self, idx: int):
        config.selected_mouse_button = idx
    
    def _on_height_targeting_toggle(self, checked: bool):
        config.height_targeting_enabled = checked
    
    def _on_target_height_change(self, val: float):
        config.target_height = round(val, 3)
    
    def _on_height_deadzone_toggle(self, checked: bool):
        config.height_deadzone_enabled = checked
    
    def _on_deadzone_min_change(self, val: float):
        config.height_deadzone_min = round(val, 3)
    
    def _on_deadzone_max_change(self, val: float):
        config.height_deadzone_max = round(val, 3)
    
    def _on_deadzone_tolerance_change(self, val: float):
        config.height_deadzone_tolerance = round(val, 3)
    
    def _on_mouse_x_change(self, val: float):
        config.mouse_movement_multiplier_x = round(val, 2)
    
    def _on_mouse_y_change(self, val: float):
        config.mouse_movement_multiplier_y = round(val, 2)
    
    def _on_mouse_x_enabled_toggle(self, checked: bool):
        config.mouse_movement_enabled_x = checked
    
    def _on_mouse_y_enabled_toggle(self, checked: bool):
        config.mouse_movement_enabled_y = checked
    
    def _on_aim_mode_change(self, idx: int):
        modes = ["normal", "bezier", "silent", "smooth", "ncaf"]
        config.mode = modes[idx]
        self._update_mode_stack()
    
    def _on_humanize_toggle(self, checked: bool):
        if checked:
            config.aim_humanization = int(self.humanize_slider.value() / 10)
        else:
            config.aim_humanization = 0
    
    def _on_humanize_change(self, val: float):
        config.aim_humanization = int(val)
    
    def _on_trigger_enabled_toggle(self, checked: bool):
        config.trigger_enabled = checked
        self._update_trigger_mode_visibility()
        config.save()
    
    def _on_trigger_always_on_toggle(self, checked: bool):
        config.trigger_always_on = checked
        config.save()
    
    def _on_trigger_head_only_toggle(self, checked: bool):
        config.trigger_head_only = checked
        config.save()
    
    def _on_trigger_mode_change(self, text: str):
        if "模式 1" in text:
            config.trigger_mode = 1
        elif "模式 2" in text:
            config.trigger_mode = 2
        else:
            config.trigger_mode = 3
        self._update_trigger_mode_visibility()
        config.save()
    
    def _on_trigger_key_change(self, idx: int):
        config.trigger_button = idx
        config.save()
    
    def _on_pick_trigger_color(self):
        current = getattr(config, 'trigger_hsv_color_hex', '#a61fe0')
        color = QColorDialog.getColor(QColor(current), self, "选择目标颜色")
        if color.isValid():
            hex_color = color.name()
            config.trigger_hsv_color_hex = hex_color
            self.color_preview_btn.setStyleSheet(
                f"background-color: {hex_color}; border: none; border-radius: 4px;"
            )
            config.save()
    
    def _on_rcs_enabled_toggle(self, checked: bool):
        config.rcs_enabled = checked
        config.save()
    
    def _on_rcs_ads_only_toggle(self, checked: bool):
        config.rcs_ads_only = checked
        config.save()
    
    def _on_rcs_disable_y_toggle(self, checked: bool):
        config.rcs_disable_y_axis = checked
        config.save()
    
    def _on_rcs_mode_change(self, idx: int):
        config.rcs_mode = "simple" if idx == 0 else "game"
        self._update_rcs_mode_visibility()
        config.save()
    
    def _on_rcs_game_change(self, game: str):
        config.rcs_game = game
        weapons = get_available_weapons(game)
        self.rcs_weapon_combo.clear()
        self.rcs_weapon_combo.addItems(weapons)
        config.save()
    
    def _on_rcs_weapon_change(self, weapon: str):
        config.rcs_weapon = weapon
        config.save()
    
    def _on_rcs_x_strength_change(self, val: float):
        config.rcs_x_strength = round(val, 2)
        config.save()
    
    def _on_rcs_x_delay_change(self, val: float):
        config.rcs_x_delay = val / 1000.0
        config.save()
    
    def _on_rcs_y_random_toggle(self, checked: bool):
        config.rcs_y_random_enabled = checked
        config.save()
    
    def _on_rcs_y_strength_change(self, val: float):
        config.rcs_y_random_strength = round(val, 2)
        config.save()
    
    def _on_rcs_y_delay_change(self, val: float):
        config.rcs_y_random_delay = val / 1000.0
        config.save()
    
    def _on_rcs_key_change(self, idx: int):
        config.rcs_button = idx
        config.save()
    
    def _on_create_profile(self):
        name, ok = QInputDialog.getText(self, "新建配置", "配置名称:")
        if ok and name:
            config.save(f"{name}.json")
            self.profile_combo.addItem(name)
            self.profile_combo.setCurrentText(name)
    
    def _on_rename_profile(self):
        current = self.profile_combo.currentText()
        name, ok = QInputDialog.getText(self, "重命名配置", "新名称:", text=current)
        if ok and name:
            old_path = f"{current}.json"
            new_path = f"{name}.json"
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                self.profile_combo.setItemText(self.profile_combo.currentIndex(), name)
    
    def _on_delete_profile(self):
        current = self.profile_combo.currentText()
        if current == "config_profile":
            QMessageBox.warning(self, "警告", "无法删除默认配置")
            return
        reply = QMessageBox.question(self, "确认删除", f"确定要删除配置 '{current}' 吗?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            path = f"{current}.json"
            if os.path.exists(path):
                os.remove(path)
            self.profile_combo.removeItem(self.profile_combo.currentIndex())
    
    def _on_save_profile(self):
        config.save()
        self._append_log("[INFO] 配置已保存\n")
    
    def _on_load_profile(self):
        name = self.profile_combo.currentText()
        config.load(f"{name}.json")
        self._append_log(f"[INFO] 已加载配置：{name}\n")
    
    def _on_reset_defaults(self):
        config.reset_to_defaults()
        self._append_log("[INFO] 已恢复默认配置\n")
    
    def _on_start_aimbot(self):
        start_aimbot()
        button_names = ["左键", "右键", "中键", "侧键 4", "侧键 5"]
        btn_name = button_names[config.selected_mouse_button]
        self._append_log(f"[INFO] 瞄准已启动。按住 {btn_name} 进行瞄准\n")
    
    def _on_stop_aimbot(self):
        stop_aimbot()
        self._append_log("[INFO] 瞄准已停止\n")
    
    def closeEvent(self, event):
        stop_aimbot()
        event.accept()


def main_entry():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main_entry()
