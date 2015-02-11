"""
Created on Thu Jan 29 15:26:00 2015
@author: f.groestlinger
"""
from PyQt4 import QtCore, QtGui, uic
from log_table import LogTableModel
import os
import sys
import datetime
import re


class LogParser(QtGui.QMainWindow):
    
    _dateTimeDisplayFormat = "yyyy-MM-dd hh:mm:ss"
    
    def __init__(self, parent=None):
        super(LogParser, self).__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        uic.loadUi("log_parser.ui", self)
        self.actionOpen.triggered.connect(self._file_button_clicked)
        self.searchLineEdit.editingFinished.connect(self._regex_text_changed)
        self.searchCheckBox.stateChanged.connect(self._search_check_box_changed)
        self._log_table_model = LogTableModel([""])
        self._log_table_model.log_types_changed.connect(self._log_types_changed)
        self.logTableView.setModel(self._log_table_model)
        self.logTableView.verticalScrollBar().sliderReleased.connect(self._table_scrolled)
        self.logTypeComboBox.currentIndexChanged.connect(self._combo_box_selection_changed)
        self.logTypeCheckBox.stateChanged.connect(self._log_type_check_box_changed)        
        self.startDateTimeEdit.setDisplayFormat(LogParser._dateTimeDisplayFormat)
        self.endDateTimeEdit.setDisplayFormat(LogParser._dateTimeDisplayFormat)
        now = datetime.datetime.now()
        start = now + datetime.timedelta(0, -3600)
        end = now + datetime.timedelta(0, 3600)
        self._log_table_model.start_date_time = start
        self._log_table_model.end_date_time = end
        self.startDateTimeEdit.setDateTime(QtCore.QDateTime(start.year, start.month, start.day, start.hour, start.minute, start.second))
        self.endDateTimeEdit.setDateTime(QtCore.QDateTime(end.year, end.month, end.day, end.hour, end.minute, end.second))
        self.startDateTimeEdit.setCalendarPopup(True)
        self.startDateTimeEdit.setCalendarWidget(QtGui.QCalendarWidget())
        self.endDateTimeEdit.setCalendarPopup(True)
        self.endDateTimeEdit.setCalendarWidget(QtGui.QCalendarWidget())
        self.startDateTimeEdit.dateTimeChanged.connect(self._start_date_time_changed)
        self.endDateTimeEdit.dateTimeChanged.connect(self._end_date_time_changed)
        
    def _file_button_clicked(self):
        start_dir = "C:/"
        self.file_name = QtGui.QFileDialog.getOpenFileName(self, "Log file name", start_dir)
        self.fileLabel.setText(self.file_name)
        self._log_table_model.file_names = self._list_all_files(self.file_name)
        self._format_log_table()     
    
    def _list_all_files(self, full_file_name):
        directory, file_name = os.path.split(str(full_file_name))
        re_fn = re.compile("^(?P<file_name>{0}.\d+)$".format(file_name))
        file_names = []
        for path, _, files in os.walk(directory):
            for file_name in files:
                if re_fn.search(file_name):
                    file_names.append(os.path.join(path, file_name))
        file_names.sort(key=lambda s: s.split(".")[-1], reverse=True)
        file_names.append(full_file_name)
        return file_names
    
    def _log_types_changed(self):
        selected_log_type = self.logTypeComboBox.currentText()        
        self.logTypeComboBox.clear()
        self.logTypeComboBox.insertItems(0, self._log_table_model.log_types)  
        if selected_log_type in self._log_table_model.log_types:
            self.logTypeComboBox.setCurrentIndex(self._log_table_model.log_types.index(selected_log_type))
        
    def _format_log_table(self):
        self.logTableView.resizeColumnsToContents()
        self.logTableView.horizontalHeader().setStretchLastSection(True)
             
    def _regex_text_changed(self):
        try:
            self._log_table_model.regex_string = str(self.searchLineEdit.text())
            self._format_log_table()
        except Exception as e:
            print("Regex text error: {0}".format(e.message))
            
    def _search_check_box_changed(self):
        self._log_table_model.is_search_active = self.searchCheckBox.isChecked()
        self._format_log_table()
        
    def _table_scrolled(self):
        self._format_log_table()
        
    def _combo_box_selection_changed(self):
        self._log_table_model.log_type = self.logTypeComboBox.currentText()
        self._format_log_table()
            
    def _log_type_check_box_changed(self):
        self._log_table_model.is_log_type_active = self.logTypeCheckBox.isChecked()
        self._format_log_table()
        
    def _start_date_time_changed(self, dateTime):
        start = self.startDateTimeEdit.dateTime()
        start_date_time = self._qdateTime_to_datetime(start)     
        self._log_table_model.start_date_time = start_date_time
        self._format_log_table()
        
    def _end_date_time_changed(self, dateTime):
        end = self.endDateTimeEdit.dateTime()
        end_date_time = self._qdateTime_to_datetime(end)     
        self._log_table_model.end_date_time = end_date_time
        self._format_log_table() 
        
    def _qdateTime_to_datetime(self, date_time):
        date = date_time.date()
        time = date_time.time()
        dt = datetime.datetime(date.year(), date.month(), date.day(),
            time.hour(), time.minute(), time.second())
        return dt        
                
        
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mw = LogParser()
    mw.show()
    sys.exit(app.exec_())