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
            
    def __str__(self):
        return "{0}) {1}: {2} {3}".format(self.line_num, self.date_time, self.log_type, self.message)
            
            
class LogTableModel(QtCore.QAbstractTableModel):
    
    _column_count = 4
    log_types_changed = QtCore.pyqtSignal()
    
    def __init__(self, file_name, parent=None, *args):        
        super(LogTableModel, self).__init__(parent, *args)
        self._file_name = file_name        
        self._current_log_type = ""
        self._is_log_type_active = False
        self._update_log_types = False
        self._regex_string = ""
        self._log_types = []       
        self._log_entries = []
        self.update()

    def _get_file_name(self):
        return self._file_name
        
    def _set_file_name(self, file_name):
        self._file_name = file_name
        self.update()
        
    file_name = property(_get_file_name, _set_file_name)
       
    def _get_log_type(self):
        return self._current_log_type
       
    def _set_log_type(self, log_type):
        self._current_log_type = log_type
        self.update(False)
        
    log_type = property(_get_log_type, _set_log_type)
    
    def _get_log_types(self):
        return self._log_types
        
    log_types = property(_get_log_types)
    
    def _get_is_log_type_active(self):
        return self._is_log_type_active
        
    def _set_is_log_type_active(self, is_log_type_active):
        self._is_log_type_active = is_log_type_active
        self.update(False)
     
    is_log_type_active = property(_get_is_log_type_active, _set_is_log_type_active)
    
    def _get_regex_string(self):
        return self._regex_string
        
    def _set_regex_string(self, regex_string):
        self._regex_string = str(regex_string)
        self.update()
        
    regex_string = property(_get_regex_string, _set_regex_string)
    
    def rowCount(self, parent):
        return len(self._log_entries)
    
    def columnCount(self, parent):
        return LogTableModel._column_count
    
    def data(self, index, role):
        result = QtCore.QVariant()
        if index.isValid():
            row = index.row()
            col = index.column()
            if role == QtCore.Qt.DisplayRole:           
                if col == 0:
                    result = str(self._log_entries[row].line_num)
                elif col == 1:
                    result = self._log_entries[row].log_type
                elif col == 2:
                    result = self._log_entries[row].date_time.__str__()
                elif col == 3:
                    result = self._log_entries[row].message
            elif role == QtCore.Qt.BackgroundColorRole:
                log_type = self._log_entries[row].log_type
                if log_type == "ERROR": result = QtGui.QBrush(QtGui.QColor(255, 0, 0, 200))
                elif log_type == "WARN": result = QtGui.QBrush(QtGui.QColor(255, 125, 0, 130))
                elif log_type == "INFO": result = QtGui.QBrush(QtGui.QColor(75, 255, 0, 80))
        return result
        
    def _load_data(self, update_log_types):
        self._log_entries = []
        regex = re.compile(self._regex_string)           
        self._log_types = []
        try:
            with open(self.file_name, "r") as fid:
                for i, line in enumerate(fid):
                    line_num = str(i + 1)
                    log_entry = LogEntry.from_log_line(line_num, line)
                    if log_entry:            
                        if log_entry.log_type not in self._log_types:
                            self._log_types.append(log_entry.log_type)
                        if self._is_log_type_active \
                            and self._current_log_type != log_entry.log_type and self._current_log_type != "":
                            continue
                        if self._regex_string == "":
                            self._log_entries.append(log_entry)
                        else:
                            match = regex.search(log_entry.message)
                            if (match):
                                self._log_entries.append(log_entry)
            if update_log_types:
                self.log_types_changed.emit()
        except Exception as e:
            print(e)
                            
    def update(self, update_log_types=True):
        self._load_data(update_log_types)
        idx_start = QtCore.QModelIndex()
        idx_start.row = 0
        idx_start.column = 0
        idx_end = QtCore.QModelIndex()
        idx_end.row = len(self._log_entries)
        idx_end.column = LogTableModel._column_count
#        self.dataChanged.emit(idx_start, idx_end)
        self.layoutChanged.emit()     
        

class LogParser(QtGui.QMainWindow):
    
    def __init__(self, parent=None):
        self.re_line = re_line
        super(LogParser, self).__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        uic.loadUi("log_parser.ui", self)
        self.actionOpen.triggered.connect(self._file_button_clicked)
        self.searchLineEdit.textChanged.connect(self._regex_text_changed)
        self._log_table_model = LogTableModel("")
        self._log_table_model.log_types_changed.connect(self._log_types_changed)
        self.logTableView.setModel(self._log_table_model)
        self.logTableView.verticalScrollBar().sliderReleased.connect(self._table_scrolled)
        self.logTypeComboBox.currentIndexChanged.connect(self._combo_box_selection_changed)
        self.logTypeCheckBox.stateChanged.connect(self._check_box_changed)
        
    def _file_button_clicked(self):
        start_dir = r"D:\Projekte\EOS\Online\EOSTATEMeltpoolTest\TestData\201501231400TestOneJobSuccess\Log"
        self.file_name = QtGui.QFileDialog.getOpenFileName(self, "Log file name", start_dir)
        self.fileLabel.setText(self.file_name)
        self._log_table_model.file_name = self.file_name
        self._format_log_table()     
    
    def _log_types_changed(self):
        self.logTypeComboBox.clear()
        self.logTypeComboBox.insertItems(0, self._log_table_model.log_types)      
        
    def _format_log_table(self):
        self.logTableView.resizeColumnsToContents()
        self.logTableView.horizontalHeader().setStretchLastSection(True)
             
    def _regex_text_changed(self):
        self._log_table_model.regex_string = str(self.searchLineEdit.text())
        self._format_log_table()
        
    def _table_scrolled(self):
        self._format_log_table()
        
    def _combo_box_selection_changed(self):
        self._log_table_model.log_type = self.logTypeComboBox.currentText()
        self._format_log_table()
            
    def _check_box_changed(self):
        self._log_table_model.is_log_type_active = self.logTypeCheckBox.isChecked()
        self._format_log_table()
        
        
        
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mw = LogParser()
    mw.show()
    sys.exit(app.exec_())