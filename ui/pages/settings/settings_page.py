from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTabWidget, QFormLayout, 
                               QLineEdit, QTableWidget, QHeaderView, QComboBox, 
                               QMessageBox, QDialog, QAbstractItemView, QTableWidgetItem, QFileDialog, QInputDialog, QAbstractItemView)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
import os
import datetime
from viewmodels.settings_viewmodel import SettingsViewModel

class AddUserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add User")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_username = QLineEdit()
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.cmb_role = QComboBox()
        self.cmb_role.addItems(["Employee", "Owner", "Admin"])
        
        form.addRow("Username:", self.txt_username)
        form.addRow("Password:", self.txt_password)
        form.addRow("Role:", self.cmb_role)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_save.setObjectName("btn_success")
        btn_cancel = QPushButton("Cancel")
        
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "username": self.txt_username.text(),
            "password": self.txt_password.text(),
            "role": self.cmb_role.currentText()
        }


class SettingsPage(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.viewmodel = SettingsViewModel()
        self.config_data = {}
        self._setup_ui()
        self._connect_signals()
        
        self.viewmodel.load_config()
        self.viewmodel.load_users()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #FFFFFF;")
        layout.addWidget(title)
        
        self.tabs = QTabWidget()
        
        # Company Info
        tab_company = QWidget()
        l_company = QFormLayout(tab_company)
        
        self.lbl_logo_preview = QLabel("No Logo")
        self.lbl_logo_preview.setFixedSize(150, 150)
        self.lbl_logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo_preview.setStyleSheet("border: 1px dashed #8B8B9E;")
        
        self.btn_upload_logo = QPushButton("Upload Logo")
        self.btn_upload_logo.setObjectName("btn_secondary")
        self.btn_upload_logo.clicked.connect(self._upload_logo)
        
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.lbl_logo_preview)
        logo_layout.addWidget(self.btn_upload_logo)
        logo_layout.addStretch()
        
        l_company.addRow("Company Logo:", logo_layout)
        
        self.comp_name = QLineEdit()
        self.comp_address = QLineEdit()
        self.comp_phone = QLineEdit()
        self.comp_email = QLineEdit()
        self.comp_web = QLineEdit()
        self.comp_ntn = QLineEdit()
        self.comp_strn = QLineEdit()
        
        l_company.addRow("Company Name:", self.comp_name)
        l_company.addRow("Address:", self.comp_address)
        l_company.addRow("Phone:", self.comp_phone)
        l_company.addRow("Email:", self.comp_email)
        l_company.addRow("Website:", self.comp_web)
        l_company.addRow("NTN:", self.comp_ntn)
        l_company.addRow("STRN:", self.comp_strn)
        
        self.btn_save_company = QPushButton("Save Company Info")
        self.btn_save_company.setObjectName("btn_primary")
        self.btn_save_company.setShortcut("Return")
        l_company.addRow("", self.btn_save_company)
        self.tabs.addTab(tab_company, "Company Info")
        
        # Database Manager
        tab_backup = QWidget()
        l_backup = QVBoxLayout(tab_backup)
        
        backup_top = QHBoxLayout()
        self.btn_backup = QPushButton("Run Incremental Backup")
        self.btn_backup.setObjectName("btn_success")
        
        self.btn_full_backup = QPushButton("Run Full SQLite Backup")
        self.btn_full_backup.setObjectName("btn_primary")
        self.btn_full_backup.setShortcut("Return")
        
        self.btn_restore = QPushButton("Restore Data")
        self.btn_restore.setObjectName("btn_danger")
        
        backup_top.addWidget(self.btn_backup)
        backup_top.addWidget(self.btn_full_backup)
        backup_top.addWidget(self.btn_restore)
        backup_top.addStretch()
        l_backup.addLayout(backup_top)
        
        self.tbl_backup = QTableWidget(0, 4)
        self.tbl_backup.setHorizontalHeaderLabels(["Type", "Timestamp", "File Path", "Status"])
        self.tbl_backup.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_backup.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_backup.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        l_backup.addWidget(self.tbl_backup)
        self.tabs.addTab(tab_backup, "Database Manager")
        
        # Users (Admin only)
        tab_users = QWidget()
        l_users = QVBoxLayout(tab_users)
        
        users_top = QHBoxLayout()
        self.btn_add_user = QPushButton("Add User")
        self.btn_add_user.setObjectName("btn_primary")
        self.btn_add_user.setShortcut("Return")
        
        self.btn_change_pwd = QPushButton("Change Password")
        self.btn_change_pwd.setObjectName("btn_secondary")
        
        users_top.addWidget(self.btn_add_user)
        users_top.addWidget(self.btn_change_pwd)
        users_top.addStretch()
        l_users.addLayout(users_top)
        
        self.tbl_users = QTableWidget(0, 5)
        self.tbl_users.setHorizontalHeaderLabels(["Username", "Role", "Department", "Status", "Last Login"])
        self.tbl_users.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_users.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_users.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        l_users.addWidget(self.tbl_users)
        self.tabs.addTab(tab_users, "Users")
        
        # About
        tab_about = QWidget()
        l_about = QVBoxLayout(tab_about)
        l_about.addWidget(QLabel("Hamza Irfan Travel & Tours Management System"))
        l_about.addWidget(QLabel("Version: 1.0.0"))
        l_about.addWidget(QLabel("Developed by Sabihul Islam Qureshi"))
        l_about.addStretch()
        self.tabs.addTab(tab_about, "About")
        
        layout.addWidget(self.tabs)
        
        # Apply permissions
        user_role = getattr(self.current_user, 'role', 'employee').lower()
        if user_role not in ('admin', 'owner'):
            self.tabs.setTabEnabled(2, False)  # Disable Users tab for Employees
        if user_role == 'owner':
            # Owner cannot edit company configuration
            self.btn_save_company.setEnabled(False)
            self.btn_save_company.setToolTip("Only Admin can update company configuration.")
            self.btn_upload_logo.setEnabled(False)
            self.btn_upload_logo.setToolTip("Only Admin can update company configuration.")

    def _connect_signals(self):
        self.viewmodel.config_loaded.connect(self._on_config_loaded)
        self.viewmodel.config_saved.connect(self._on_config_saved)
        self.viewmodel.backup_completed.connect(self._on_backup_success)
        self.viewmodel.backup_failed.connect(lambda e: QMessageBox.critical(self, "Error", f"Backup failed: {e}"))
        self.viewmodel.backup_history_loaded.connect(self._on_backup_history_loaded)
        self.viewmodel.restore_completed.connect(self._on_restore_success)
        self.viewmodel.users_loaded.connect(self._on_users_loaded)
        self.viewmodel.user_saved.connect(self.viewmodel.load_users)
        
        self.btn_save_company.clicked.connect(self._save_company_info)
        self.btn_backup.clicked.connect(self.viewmodel.create_backup)
        self.btn_full_backup.clicked.connect(self.viewmodel.create_full_backup)
        self.btn_restore.clicked.connect(self._restore_backup)
        self.btn_add_user.clicked.connect(self._add_user)
        self.btn_change_pwd.clicked.connect(self._change_password)
        
        self.viewmodel.load_backup_history()
        self.viewmodel.load_users()


    def _on_config_saved(self):
        # Reload from DB so the page stays in sync with what was saved
        self.viewmodel.load_config()
        win = self.window()
        if hasattr(win, 'statusBar'):
            sb = win.statusBar
            if callable(sb):
                sb().showMessage("Configuration saved successfully!", 3000)
            else:
                sb.showMessage("Configuration saved successfully!", 3000)

    def _on_config_loaded(self, profile):
        if not profile: return
        self.comp_name.setText(profile.company_name or "")
        self.comp_address.setText(profile.address or "")
        self.comp_phone.setText(profile.phone or "")
        self.comp_email.setText(profile.email or "")
        self.comp_web.setText(profile.website or "")
        self.comp_ntn.setText(profile.ntn or "")
        self.comp_strn.setText(profile.strn or "")
        
        self.logo_bytes = profile.logo_data
        if self.logo_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(self.logo_bytes)
            self.lbl_logo_preview.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            with open(file_path, "rb") as f:
                self.logo_bytes = f.read()
            pixmap = QPixmap(file_path)
            self.lbl_logo_preview.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def _save_company_info(self):
        from core.permissions import can_edit_company_config
        if not can_edit_company_config(self.current_user):
            QMessageBox.warning(self, "Access Denied", "Only the Admin can update company configuration.")
            return
        data = {
            "company_name": self.comp_name.text(),
            "address": self.comp_address.text(),
            "phone": self.comp_phone.text(),
            "email": self.comp_email.text(),
            "website": self.comp_web.text(),
            "ntn": self.comp_ntn.text(),
            "strn": self.comp_strn.text()
        }
        if hasattr(self, 'logo_bytes') and self.logo_bytes:
            data['logo_data'] = self.logo_bytes  # type: ignore
            
        self.viewmodel.save_config(data)

    def _on_backup_success(self, path):
        if hasattr(self.window(), 'statusBar'):
            self.window().statusBar().showMessage(f"Backup created successfully at:\\n{path}", 3000)  # type: ignore[attr-defined]
        self.viewmodel.load_backup_history()

    def _on_restore_success(self):
        QMessageBox.information(self, "Success", "Database successfully restored from backup! Please restart the application.")

    def _restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Backup File", "backups", "Backup Files (*.db *.json.gz)")
        if file_path:
            reply = QMessageBox.warning(self, "Restore Backup", 
                "Are you sure you want to restore from this backup? This will UPSERT data and overwrite newer identical UUID records.", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                if hasattr(self.window(), 'statusBar'):
                    self.window().statusBar().showMessage("Restoring database... Please wait.", 5000)  # type: ignore[attr-defined]
                self.viewmodel.restore_backup(file_path)

    def _on_backup_history_loaded(self, history):
        self.tbl_backup.setRowCount(0)
        for row, record in enumerate(history):
            self.tbl_backup.insertRow(row)
            self.tbl_backup.setItem(row, 0, QTableWidgetItem(record.backup_type.value))
            
            # Format timestamp safely
            ts = record.timestamp.strftime("%Y-%m-%d %H:%M:%S") if record.timestamp else "N/A"
            self.tbl_backup.setItem(row, 1, QTableWidgetItem(ts))
            self.tbl_backup.setItem(row, 2, QTableWidgetItem(os.path.basename(record.file_path)))
            self.tbl_backup.setItem(row, 3, QTableWidgetItem(record.status))

    def _on_users_loaded(self, users):
        self.tbl_users.setRowCount(0)
        for row, user in enumerate(users):
            self.tbl_users.insertRow(row)
            self.tbl_users.setItem(row, 0, QTableWidgetItem(user.username))
            self.tbl_users.setItem(row, 1, QTableWidgetItem(user.role))
            
            department = user.department if user.department else "N/A"
            self.tbl_users.setItem(row, 2, QTableWidgetItem(department))
            
            status = "Active" if user.is_active else "Inactive"
            self.tbl_users.setItem(row, 3, QTableWidgetItem(status))
            
            last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
            self.tbl_users.setItem(row, 4, QTableWidgetItem(last_login))

    def _add_user(self):
        dialog = AddUserDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if data["username"] and data["password"]:
                self.viewmodel.create_user(data)
            else:
                QMessageBox.warning(self, "Validation Error", "Username and password required.")
                
    def _change_password(self):
        selected_items = self.tbl_users.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a user to change their password.")
            return
            
        row = selected_items[0].row()
        user_item = self.tbl_users.item(row, 0)
        if not user_item:
            return
        username = user_item.text()
        
        new_password, ok = QInputDialog.getText(self, "Change Password", f"New password for {username}:", QLineEdit.EchoMode.Password)
        if ok and new_password:
            self.viewmodel.reset_password(username, new_password)
            QMessageBox.information(self, "Success", "Password updated successfully.")
