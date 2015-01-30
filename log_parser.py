"""
Created on Thu Jan 29 15:26:00 2015
@author: f.groestlinger
"""
from PyQt4 import QtCore, QtGui, uic
import sys
import re
import datetime


re_line = re.compile(r"^(?P<log_type>[\w ]{8}):\ (?P<date>\d{4}-\d{2}-\d{2}\ \d{2}:\d{2}:\d{2}(.\d*)?): (?P<message>.*)$")
re_date = re.compile(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\ (?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>[\d.]+)$")


def stringToDateTime(date_time_string):
    match = re_date.search(date_time_string)
    if match:
        gd = match.groupdict()
        year = int(gd["year"])
        month = int(gd["month"])
        day = int(gd["day"])
        hour = int(gd["hour"])
        minute = int(gd["minute"])
        second = int(float(gd["second"]))
        microsecond = int(1000 * (float(gd["second"]) - second))
        date_time = datetime.datetime(year, month, day, hour, minute, second, microsecond)
        return date_time
    else:
        return None


class LogEntry(object):
    
    def __init__(self, line_num, log_type, date_time, message):
        self.line_num = line_num
        self.log_type = log_type
        self.date_time = date_time
        self.message = message
        
    @staticmethod
    def from_log_line(line_num, log_line):
        match = re_line.search(log_line)
        if match:
            gd = match.groupdict()
            log_type = gd["log_type"].strip()
            date = gd["date"]
            message = gd["message"]
            date_time = stringToDateTime(date)
            log_entry = LogEntry(line_num, log_type, date_time, message)
            return log_entry
        else:
            return None
            
            
class LogTableModel(QtCore.QAbstractTableModel):
    
    _column_count = 4
    
    def __init__(self, file_name, parent=None, *args):        
        super(LogTableModel, self).__init__(self, parent, *args)
        self.file_name = file_name        
        self._current_log_type = ""
        self._is_log_type_active = False
        self._regex_string = ""
        self._load_data()
       
    def _get_log_type(self):
        return self._current_log_type
       
    def _set_log_type(self, log_type):
        self._current_log_type = log_type
        self.update()
        
    log_type = property(_get_log_type, _set_log_type)
    
    def _get_is_log_type_active(self):
        return self._is_log_type_active
        
    def _set_is_log_type_active(self, is_log_type_active):
        self._is_log_type_active = is_log_type_active
        self.update()
    
    def rowCount(self, parent):
        return len(self.log_entries)
    
    def columnCount(self, parent):
        return LogTableModel._column_count
    
    def data(self, index, role):
        result = QtCore.QVariant()
        if index.isValid() and role == QtCore.Qt.DisplayRole:           
            row = index.row()
            col = index.column()
            if col == 0:
                result = str(self.log_entries[row].line_num)
            elif col == 1:
                result = self.log_entries[row].log_type
            elif col == 2:
                result = self.log_entries[row].date_time.__str__()
            elif col == 3:
                result = self.log_entries[row].message
        return result
        
    def _load_data(self):
        log_entries = []
        regex = re.compile(self.regex_string)           
        log_types = []
        with open(self.file_name, "r") as fid:
            for i, line in enumerate(fid):
                line_num = str(i + 1)
                log_entry = LogEntry.from_log_line(line_num, line)
                if log_entry:            
                    if log_entry.log_type not in log_types:
                        log_types.append(log_entry.log_type)
                    if self._is_log_type_active \
                        and self.current_log_type != log_entry.log_type and self.current_log_type != "":
                        continue
                    if regex == "":                      
                        log_entries.append(log_entry)
                    else:
                        match = regex.search(log_entry.message)
                        if (match):
                            log_entries.append(log_entry)
                            
    def update(self):
        self._load_data()
        self.dataChanged()
        
        

class LogParser(QtGui.QMainWindow):
    
    def __init__(self, parent=None):
        self.re_line = re_line
        super(LogParser, self).__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        uic.loadUi("log_parser.ui", self)
        self.actionOpen.triggered.connect(self._file_button_clicked)
        self.searchLineEdit.textChanged.connect(self._regex_text_changed)
        self.logTable.verticalScrollBar().sliderReleased.connect(self._table_scrolled)
        self.logTypeComboBox.currentIndexChanged.connect(self._combo_box_selection_changed)
        self.logTypeCheckBox.stateChanged.connect(self._check_box_changed)
        
    def _file_button_clicked(self):
        start_dir = r"D:\Projekte\EOS\Online\EOSTATEMeltpoolTest\TestData\201501231400TestOneJobSuccess\Log"
        self.file_name = QtGui.QFileDialog.getOpenFileName(self, "Log file name", start_dir)
        self.fileLabel.setText(self.file_name)
        self._update_log(self._get_regex_string())
        
    def _get_regex_string(self):
        return str(self.searchLineEdit.text())
        
    @staticmethod
    def _get_log_brush(log_type):
        if log_type == "ERROR": background = QtGui.QBrush(QtGui.QColor(255, 0, 0, 200))
        elif log_type == "WARN": background = QtGui.QBrush(QtGui.QColor(255, 125, 0, 130))
        elif log_type == "INFO": background = QtGui.QBrush(QtGui.QColor(75, 255, 0, 80))
        else: background = None
        return background
    
    @staticmethod
    def _get_table_item(log_type, log_entry):
        log_entry_item = QtGui.QTableWidgetItem(log_entry)
        log_entry_brush = LogParser._get_log_brush(log_type)
        if log_entry_brush:
            log_entry_item.setBackground(log_entry_brush)
        return log_entry_item      
        
    def _update_log(self, regex_string, update_combo_box=True):
#        try:
            self.logTable.clearContents()
            self.logTable.setColumnCount(4)
            log_entries = []
            regex = re.compile(regex_string)
            current_log_type = self.logTypeComboBox.currentText()           
            log_types = []
            with open(self.file_name, "r") as fid:
                for i, line in enumerate(fid):
                    line_num = str(i + 1)
                    log_entry = LogEntry.from_log_line(line_num, line)
                    if log_entry:            
                        if log_entry.log_type not in log_types:
                            log_types.append(log_entry.log_type)
                        if self.logTypeCheckBox.isChecked() \
                            and current_log_type != log_entry.log_type and current_log_type != "":
                            continue
                        if regex == "":                      
                            log_entries.append(log_entry)
                        else:
                            match = regex.search(log_entry.message)
                            if (match):
                                log_entries.append(log_entry)
            self.logTable.setRowCount(len(log_entries))
            for i, log_entry in enumerate(log_entries):
                self.logTable.setItem(i, 0, LogParser._get_table_item(log_entry.log_type, str(log_entry.line_num)))
                self.logTable.setItem(i, 1, LogParser._get_table_item(log_entry.log_type, log_entry.log_type))
                self.logTable.setItem(i, 2, LogParser._get_table_item(log_entry.log_type, log_entry.date_time.__str__()))
                self.logTable.setItem(i, 3, LogParser._get_table_item(log_entry.log_type, log_entry.message))       
#        except:
#            pass
            self.logTable.resizeColumnsToContents()
            self.logTable.horizontalHeader().setStretchLastSection(True)
            if update_combo_box:
                self.logTypeComboBox.clear()
                self.logTypeComboBox.insertItems(0, log_types)
             
    def _regex_text_changed(self):
        self._update_log(self._get_regex_string())
        
    def _table_scrolled(self):
        self.logTable.resizeColumnsToContents()
        self.logTable.horizontalHeader().setStretchLastSection(True)
        
    def _combo_box_selection_changed(self):
        if self.logTypeCheckBox.isChecked():
            self._update_log(self._get_regex_string(), False)
            
    def _check_box_changed(self):
        self._update_log(self._get_regex_string(), False)
        
        
        
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mw = LogParser()
    mw.show()
    sys.exit(app.exec_())