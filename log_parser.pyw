"""
Created on Thu Jan 29 15:26:00 2015
@author: f.groestlinger
"""

from PyQt4 import QtCore, QtGui, uic
import matplotlib.pyplot as plt
import os
import sys
import datetime
import re
from log_table import LogTableModel
import itertools
import logging


class ConfigFile(object):

    default_file_name = "config.txt"

    def __init__(self, default_log_dir=None):
        self.default_log_dir = default_log_dir

    def load(self, file_name=default_file_name):
        self.default_log_dir = None
        try:
            with open(file_name, "r") as fid:
                for line in fid:
                    line_split = line.split("=")
                    if line_split[0].strip() == "default log directory":
                        self.default_log_dir = line_split[1].strip()
        except:
            pass

    def save(self, file_name=default_file_name):
        with open(file_name, "w") as fid:
            fid.write("default log directory = {0}\n".format(self.default_log_dir))


class LogParser(QtGui.QMainWindow):
    
    _dateTimeDisplayFormat = "yyyy-MM-dd hh:mm:ss"
    
    def __init__(self, parent=None):       
        self._log = logging.getLogger(name="main")
        super(LogParser, self).__init__(parent)
        self._init_ui()
        self._config_file = ConfigFile()
        self._config_file.load()
        
    def _init_ui(self):
        uic.loadUi("log_parser.ui", self)
        self.actionOpen.triggered.connect(self._file_button_clicked)
        self.actionPlotRegexGroups.triggered.connect(self._plot_regex_groups)
        self.searchLineEdit.editingFinished.connect(self._regex_text_changed)
        self.searchCheckBox.stateChanged.connect(self._search_check_box_changed)
        self._log_table_model = LogTableModel([""])
        self._log_table_model.log_types_changed.connect(self._log_types_changed)        
        self.logTableView.setModel(self._log_table_model)
        self.logTableView.verticalScrollBar().sliderReleased.connect(self._table_scrolled)
        self._log_table_model.table_format_changed.connect(self._format_log_table)
        self.logTypeComboBox.currentIndexChanged.connect(self._combo_box_selection_changed)
        self.logTypeCheckBox.stateChanged.connect(self._log_type_check_box_changed)        
        self.startDateTimeEdit.setDisplayFormat(LogParser._dateTimeDisplayFormat)
        self.endDateTimeEdit.setDisplayFormat(LogParser._dateTimeDisplayFormat)
        now = datetime.datetime.now()
        start = now + datetime.timedelta(0, -3600)
        end = now + datetime.timedelta(0, 3600)
        self._log_table_model.start_date_time = start
        self._log_table_model.end_date_time = end
        self.fileProgressBar.setRange(0, 100)
        self._log_table_model.file_progress_changed.connect(self.fileProgressBar.setValue)
        self.startDateTimeEdit.setDateTime(QtCore.QDateTime(start.year, start.month, start.day, start.hour, start.minute, start.second))
        self.endDateTimeEdit.setDateTime(QtCore.QDateTime(end.year, end.month, end.day, end.hour, end.minute, end.second))
        cal1 = QtGui.QCalendarWidget()
        cal1.setFirstDayOfWeek(QtCore.Qt.Monday)
        self.startDateTimeEdit.setCalendarWidget(cal1)
        cal2 = QtGui.QCalendarWidget()
        cal2.setFirstDayOfWeek(QtCore.Qt.Monday)
        self.endDateTimeEdit.setCalendarWidget(cal2)
        self.startDateTimeEdit.dateTimeChanged.connect(self._start_date_time_changed)
        self.endDateTimeEdit.dateTimeChanged.connect(self._end_date_time_changed)
        
    def _file_button_clicked(self):
        try:
            if not self._config_file.default_log_dir: raise Exception("no valid default directory in config file")
            start_dir = self._config_file.default_log_dir
            self.file_name = QtGui.QFileDialog.getOpenFileName(self, "Log file name", start_dir)
        except:
            self.file_name = QtGui.QFileDialog.getOpenFileName(self, "Log file name", "C:\\")
        finally:
            self.fileLabel.setText(self.file_name)
            self._log_table_model.file_names = self._list_all_files(self.file_name)
            self._format_log_table()
            dir_name = os.path.dirname(str(self.file_name))
            self._config_file.default_log_dir = dir_name
    
    def _list_all_files(self, full_file_name):
        directory, file_name = os.path.split(str(full_file_name))
        re_fn = re.compile("^(?P<file_name>{0}.\d+)$".format(file_name))
        file_names = []
        for path, _, files in os.walk(directory):
            for file_name in files:
                if re_fn.search(file_name):
                    file_names.append(os.path.join(path, file_name))
        file_names.sort(key=lambda s: int(s.split(".")[-1]), reverse=True)
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
            logging.error("Regex text error: {0}".format(e.message))
            
    def _search_check_box_changed(self):
        self._log_table_model.is_search_active = self.searchCheckBox.isChecked()
        
    def _table_scrolled(self):
        self._format_log_table()
        
    def _combo_box_selection_changed(self):
        self._log_table_model.log_type = self.logTypeComboBox.currentText()
            
    def _log_type_check_box_changed(self):
        self._log_table_model.is_log_type_active = self.logTypeCheckBox.isChecked()
        
    def _start_date_time_changed(self, dateTime):
        start = self.startDateTimeEdit.dateTime()
        start_date_time = self._qdateTime_to_datetime(start)     
        self._log_table_model.start_date_time = start_date_time
        
    def _end_date_time_changed(self, dateTime):
        end = self.endDateTimeEdit.dateTime()
        end_date_time = self._qdateTime_to_datetime(end)     
        self._log_table_model.end_date_time = end_date_time
        
    def _qdateTime_to_datetime(self, date_time):
        date = date_time.date()
        time = date_time.time()
        dt = datetime.datetime(date.year(), date.month(), date.day(),
            time.hour(), time.minute(), time.second())
        return dt        
        
    def _plot_regex_groups(self):
        regex_plot = str(self.searchLineEdit.text())
        ts, ys = self._log_table_model.plot_regex_groups(regex_plot)
        marker = itertools.cycle(('o', 's', 'v', '^', 'd', '>', '<')) 
        if ts and ys:
            try:
                fig = plt.figure()
                ax = fig.add_subplot(1, 1, 1)
                for i, (t, y) in enumerate(zip(ts, ys)):
                    ax.plot(t, y, ls="-", marker=marker.next(), label="{0}".format(i + 1))
                ax.legend()
                fig.autofmt_xdate()
                fig.show()
            except Exception as e:
                logging.error("Error: {0}".format(e))

    def closeEvent(self, *args, **kwargs):
        self._config_file.save()
                
        
if __name__ == "__main__":
    fh = logging.FileHandler("trace.log")
    fmt = logging.Formatter("%(levelname)s %(asctime)s: %(message)s")
    fh.setFormatter(fmt)
    logger = logging.getLogger(name="main")
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)
    app = QtGui.QApplication(sys.argv)
    mw = LogParser()
    mw.show()
    sys.exit(app.exec_())