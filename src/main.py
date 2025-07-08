import sys
import json
import os
import signal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QStatusBar, QTabWidget, QTextEdit, 
    QHeaderView, QDialog, QLineEdit, QFormLayout, QDialogButtonBox, 
    QMessageBox, QCheckBox, QHBoxLayout, QGroupBox, QTimeEdit, QLabel
)
from PyQt5.QtCore import QProcess, QTime, Qt
from apscheduler.schedulers.background import BackgroundScheduler

SCRIPTS_FILE = "scripts.json"

class ScheduleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Schedule")
        layout = QVBoxLayout(self)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        layout.addWidget(self.time_edit)

        self.days_group = QGroupBox("Days of the Week")
        days_layout = QHBoxLayout()
        self.days_checkboxes = {
            'mon': QCheckBox("Mon"), 'tue': QCheckBox("Tue"), 'wed': QCheckBox("Wed"),
            'thu': QCheckBox("Thu"), 'fri': QCheckBox("Fri"), 'sat': QCheckBox("Sat"), 'sun': QCheckBox("Sun")
        }
        for day in self.days_checkboxes.values():
            days_layout.addWidget(day)
        self.days_group.setLayout(days_layout)
        layout.addWidget(self.days_group)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_schedule_data(self):
        days = [day for day, checkbox in self.days_checkboxes.items() if checkbox.isChecked()]
        return {
            "time": self.time_edit.time(),
            "days": days
        }

class RegistrationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New Script")
        layout = QFormLayout(self)
        self.script_name = QLineEdit()
        self.bash_commands = QTextEdit()
        layout.addRow("Script Name:", self.script_name)
        layout.addRow("Bash Commands:", self.bash_commands)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_data(self):
        return {"name": self.script_name.text(), "commands": self.bash_commands.toPlainText()}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Script Scheduler")
        self.setGeometry(100, 100, 1200, 800)
        self.scripts = {}
        self.processes = {}
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        script_management_layout = QVBoxLayout()
        main_layout.addLayout(script_management_layout)

        self.script_table = QTableWidget()
        self.script_table.setColumnCount(5)
        self.script_table.setHorizontalHeaderLabels(["Enabled", "Script Name", "Schedule", "Run", "Actions"])
        self.script_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        script_management_layout.addWidget(self.script_table)

        self.register_button = QPushButton("Register Script")
        self.register_button.clicked.connect(self.open_registration_dialog)
        script_management_layout.addWidget(self.register_button)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.log_tabs = QTabWidget()
        main_layout.addWidget(self.log_tabs)
        self.setup_global_log_tab()
        self.load_scripts()

    def setup_global_log_tab(self):
        global_log_widget = QWidget()
        global_log_layout = QVBoxLayout(global_log_widget)
        self.global_log_tab = QTextEdit()
        self.global_log_tab.setReadOnly(True)
        global_clear_button = QPushButton("Clear Log")
        global_clear_button.clicked.connect(self.global_log_tab.clear)
        global_log_layout.addWidget(self.global_log_tab)
        global_log_layout.addWidget(global_clear_button)
        self.log_tabs.addTab(global_log_widget, "Global Log")

    def open_registration_dialog(self):
        dialog = RegistrationDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Warning", "Script name cannot be empty.")
                return
            if data["name"] in self.scripts:
                QMessageBox.warning(self, "Warning", "A script with this name already exists.")
                return
            self.scripts[data["name"]] = {"commands": data["commands"], "schedule_info": None, "job_id": None, "enabled": True}
            self.add_script_to_table(data["name"])

    def add_script_to_table(self, name, schedule_str="Not Set", enabled=True):
        row_position = self.script_table.rowCount()
        self.script_table.insertRow(row_position)

        checkbox = QCheckBox()
        checkbox.setChecked(enabled)
        checkbox.stateChanged.connect(lambda state, sn=name: self.toggle_job_enabled(sn, state))
        self.script_table.setCellWidget(row_position, 0, checkbox)

        self.script_table.setItem(row_position, 1, QTableWidgetItem(name))
        
        schedule_widget = QWidget()
        schedule_layout = QHBoxLayout(schedule_widget)
        schedule_layout.setContentsMargins(0, 0, 0, 0)
        schedule_label = QLabel(schedule_str)
        schedule_layout.addWidget(schedule_label)
        set_schedule_button = QPushButton("Set Schedule")
        set_schedule_button.clicked.connect(lambda _, sn=name: self.open_schedule_dialog(sn))
        schedule_layout.addWidget(set_schedule_button)
        self.script_table.setCellWidget(row_position, 2, schedule_widget)

        run_widget = QWidget()
        run_layout = QHBoxLayout(run_widget)
        run_layout.setContentsMargins(0, 0, 0, 0)
        run_button = QPushButton("Run Now")
        run_button.setObjectName("run_button")
        run_button.clicked.connect(lambda: self.run_script_now(name))
        stop_button = QPushButton("Stop")
        stop_button.setObjectName("stop_button")
        stop_button.clicked.connect(lambda: self.stop_script(name))
        stop_button.hide()
        run_layout.addWidget(run_button)
        run_layout.addWidget(stop_button)
        self.script_table.setCellWidget(row_position, 3, run_widget)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.handle_delete_button)
        self.script_table.setCellWidget(row_position, 4, delete_button)

        self.add_log_tab(name)

    def add_log_tab(self, name):
        log_tab_widget = QWidget()
        log_tab_layout = QVBoxLayout(log_tab_widget)
        log_view = QTextEdit()
        log_view.setReadOnly(True)
        clear_button = QPushButton("Clear Log")
        clear_button.clicked.connect(log_view.clear)
        log_tab_layout.addWidget(log_view)
        log_tab_layout.addWidget(clear_button)
        self.log_tabs.addTab(log_tab_widget, name)

    def open_schedule_dialog(self, script_name):
        dialog = ScheduleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            schedule_data = dialog.get_schedule_data()
            self.update_schedule(script_name, schedule_data)

    def update_schedule(self, script_name, data):
        job_id = self.scripts[script_name].get("job_id")
        if job_id:
            self.scheduler.remove_job(job_id)

        if not data['days']:
            self.scripts[script_name]["schedule_info"] = None
            self.scripts[script_name]["job_id"] = None
            schedule_str = "Not Set"
        else:
            schedule_info = {
                'day_of_week': ','.join(data['days']),
                'hour': data['time'].hour(),
                'minute': data['time'].minute()
            }
            self.scripts[script_name]["schedule_info"] = schedule_info
            job = self.scheduler.add_job(self.execute_script, 'cron', **schedule_info, args=[script_name], id=script_name)
            self.scripts[script_name]["job_id"] = job.id
            schedule_str = f"{schedule_info['day_of_week']} at {data['time'].toString('HH:mm')}"
        
        for row in range(self.script_table.rowCount()):
            if self.script_table.item(row, 1).text() == script_name:
                schedule_widget = self.script_table.cellWidget(row, 2)
                if schedule_widget:
                    schedule_widget.findChild(QLabel).setText(schedule_str)
                break

    def toggle_job_enabled(self, script_name, state):
        self.scripts[script_name]['enabled'] = (state == Qt.Checked)
        job_id = self.scripts[script_name].get("job_id")
        if not job_id:
            return
        if self.scripts[script_name]['enabled']:
            self.scheduler.resume_job(job_id)
        else:
            self.scheduler.pause_job(job_id)

    def run_script_now(self, script_name):
        self.execute_script(script_name)

    def stop_script(self, script_name):
        if script_name in self.processes:
            self.status_bar.showMessage(f"Stopping script: {script_name}...")
            process = self.processes[script_name]
            pid = process.pid()
            if pid:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except ProcessLookupError:
                    # The process might have finished just before we tried to kill it.
                    pass

    def execute_script(self, script_name):
        if script_name in self.processes:
            QMessageBox.warning(self, "Warning", f"Script '{script_name}' is already running.")
            return

        self.status_bar.showMessage(f"Executing script: {script_name}...")
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.MergedChannels)
        process.readyReadStandardOutput.connect(lambda: self.handle_log_output(script_name))
        process.finished.connect(lambda: self.handle_process_finished(script_name))
        self.processes[script_name] = process
        commands = self.scripts[script_name]["commands"]
        process.start("setsid", ["bash", "-c", commands])

        for row in range(self.script_table.rowCount()):
            if self.script_table.item(row, 1).text() == script_name:
                run_widget = self.script_table.cellWidget(row, 3)
                if run_widget:
                    run_widget.findChild(QPushButton, "run_button").hide()
                    run_widget.findChild(QPushButton, "stop_button").show()
                break

    def handle_log_output(self, script_name):
        process = self.processes.get(script_name)
        if process:
            output = process.readAllStandardOutput().data().decode().strip()
            self.log_to_tab(script_name, output)
            self.global_log_tab.append(f"[{script_name}] {output}")

    def handle_process_finished(self, script_name):
        self.status_bar.showMessage(f"Script '{script_name}' finished.", 5000)
        if script_name in self.processes:
            del self.processes[script_name]

        for row in range(self.script_table.rowCount()):
            if self.script_table.item(row, 1) and self.script_table.item(row, 1).text() == script_name:
                run_widget = self.script_table.cellWidget(row, 3)
                if run_widget:
                    run_widget.findChild(QPushButton, "run_button").show()
                    run_widget.findChild(QPushButton, "stop_button").hide()
                break

    def log_to_tab(self, tab_name, message):
        for i in range(self.log_tabs.count()):
            if self.log_tabs.tabText(i) == tab_name:
                log_widget = self.log_tabs.widget(i).findChild(QTextEdit)
                if log_widget:
                    log_widget.append(message)
                break

    def handle_delete_button(self):
        button = self.sender()
        if button:
            row = self.script_table.indexAt(button.pos()).row()
            self.delete_script(row)

    def delete_script(self, row):
        if row < 0 or row >= self.script_table.rowCount(): return
        script_name = self.script_table.item(row, 1).text()
        reply = QMessageBox.question(self, 'Delete Script', f"Are you sure you want to delete the script '{script_name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if script_name in self.processes:
                self.processes[script_name].kill()

            job_id = self.scripts[script_name].get("job_id")
            if job_id:
                self.scheduler.remove_job(job_id)
            del self.scripts[script_name]

            for i in range(self.log_tabs.count()):
                if self.log_tabs.tabText(i) == script_name:
                    self.log_tabs.removeTab(i)
                    break
            self.script_table.removeRow(row)

    def load_scripts(self):
        if not os.path.exists(SCRIPTS_FILE):
            return
        with open(SCRIPTS_FILE, 'r') as f:
            loaded_scripts = json.load(f)
        
        for name, data in loaded_scripts.items():
            self.scripts[name] = {
                'commands': data['commands'],
                'schedule_info': data.get('schedule_info'),
                'job_id': None,
                'enabled': data.get('enabled', True)
            }
            schedule_str = "Not Set"
            if data.get('schedule_info'):
                info = data['schedule_info']
                schedule_str = f"{info['day_of_week']} at {info['hour']:02d}:{info['minute']:02d}"
                job = self.scheduler.add_job(self.execute_script, 'cron', **info, args=[name], id=name)
                self.scripts[name]['job_id'] = job.id
                if not self.scripts[name]['enabled']:
                    self.scheduler.pause_job(job.id)

            self.add_script_to_table(name, schedule_str, self.scripts[name]['enabled'])

    def save_scripts(self):
        scripts_to_save = {}
        for name, data in self.scripts.items():
            scripts_to_save[name] = {
                'commands': data['commands'],
                'schedule_info': data.get('schedule_info'),
                'enabled': data.get('enabled', True)
            }
        with open(SCRIPTS_FILE, 'w') as f:
            json.dump(scripts_to_save, f, indent=4)

    def closeEvent(self, event):
        self.save_scripts()
        self.scheduler.shutdown()
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec_())
