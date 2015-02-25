"""
Created on Fri Jan 30 16:08:20 2015
@author: f.groestlinger
"""
from PyQt4 import QtCore, QtGui
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
        
        
class LogEntries(object):

    def __init__(self):
        self.all_log_entries = []
        self.log_types = []        
        
        
class LoadDataThread(QtCore.QThread):
    
    data_loaded = QtCore.pyqtSignal(type(LogEntries))
    
    def __init__(self, file_names, start_date_time, end_date_time):
        super(LoadDataThread, self).__init__()
        self._file_names = file_names
        self._start_date_time = start_date_time
        self._end_date_time = end_date_time
        self._log_entries = LogEntries()      
        
    def run(self):
        for file_name in self._file_names:
            print("Reading file: {0}".format(file_name))
            if file_name == "":
                continue
            with open(file_name, "r") as fid:
                for i, line in enumerate(fid):
                    line_num = str(i + 1)
                    log_entry = LogEntry.from_log_line(line_num, line)
                    if log_entry:
                        if self._start_date_time and self._start_date_time > log_entry.date_time: continue 
                        if self._end_date_time and self._end_date_time < log_entry.date_time: continue
                        self._log_entries.all_log_entries.append(log_entry)
                        if log_entry.log_type not in self._log_entries.log_types:
                            self._log_entries.log_types.append(log_entry.log_type)
        self.data_loaded.emit(self._log_entries)
            
            
class LogTableModel(QtCore.QAbstractTableModel):
    
    _column_count = 4
    _header_labels = ["Line", "Log type", "Timestamp", "Message"]
    _log_type_colors = {
        "ERROR": (255, 0, 0, 200),
        "WARN": (255, 125, 0, 130),
        "INFO": (75, 255, 0, 80)}
    log_types_changed = QtCore.pyqtSignal()
    
    def __init__(self, file_names, parent=None, *args):        
        super(LogTableModel, self).__init__(parent, *args)
        self._file_names = file_names        
        self._current_log_type = ""
        self._is_log_type_active = False
        self._update_log_types = False
        self._regex_string = ""
        self._is_search_active = False
        self._log_types = []       
        self._log_entries = []
        self._all_log_entries = []
        self.update()
        self._start_date_time = None
        self._end_date_time = None
        self._load_data_threads = []
        
    def _get_start_date_time(self, date_time):
        return self._start_date_time
        
    def _set_start_date_time(self, date_time):
        if type(date_time) is datetime.datetime:
            self._start_date_time = date_time
            self._load_data()
        else:
            self._start_date_time = None
    
    start_date_time = property(_get_start_date_time, _set_start_date_time)
            
    def _get_end_date_time(self, date_time):
        return self._end_date_time
        
    def _set_end_date_time(self, date_time):
        if type(date_time) is datetime.datetime:
            self._end_date_time = date_time
            self._load_data()
        else:
            self._end_date_time = None
    
    end_date_time = property(_get_end_date_time, _set_end_date_time)           

    def _get_file_names(self):
        return self._file_names
        
    def _set_file_names(self, file_names):
        self._file_names = file_names
        self._load_data()
        
    file_names = property(_get_file_names, _set_file_names)
       
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
    
    def _get_is_search_active(self):
        return self._is_search_active
        
    def _set_is_search_active(self, is_search_active):
        self._is_search_active = is_search_active
        self.update()
        
    is_search_active = property(_get_is_search_active, _set_is_search_active)
    
    def rowCount(self, parent):
        return len(self._log_entries)
    
    def columnCount(self, parent):
        return LogTableModel._column_count
        
    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._header_labels[section]
        return super(LogTableModel, self).headerData(section, orientation, role)
    
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
                if log_type in self._log_type_colors:
                    rgb_color = self._log_type_colors[log_type]
                    result = QtGui.QBrush(QtGui.QColor(*rgb_color))
        return result
        
    def _load_data(self):
        load_data_thread = LoadDataThread(self._file_names, self._start_date_time, self._end_date_time)
        load_data_thread.data_loaded.connect(self._on_data_loaded)
        self._load_data_threads.append(load_data_thread)
        load_data_thread.start()       
   
    def _on_data_loaded(self, log_entries):
        print("on data loaded")
        self._all_log_entries = log_entries.all_log_entries
        self._log_types = log_entries.log_types
        self.update()
        
    def _update_data(self, update_log_types):
        self._log_entries = []
        regex = re.compile(self._regex_string)           
        try:
            for log_entry in self._all_log_entries:
                if self._is_log_type_active \
                    and self._current_log_type != log_entry.log_type and self._current_log_type != "":
                    continue
                if not self._is_search_active or self._regex_string == "":
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
        self._update_data(update_log_types)
        idx_start = QtCore.QModelIndex()
        idx_start.row = 0
        idx_start.column = 0
        idx_end = QtCore.QModelIndex()
        idx_end.row = len(self._log_entries)
        idx_end.column = LogTableModel._column_count
#        self.dataChanged.emit(idx_start, idx_end)
        self.layoutChanged.emit()     
        
    def plot_regex_groups(self, regex_plot):
        re_plot = re.compile(regex_plot)
        ts = []
        ys = []
        try:
            for log_entry in self._all_log_entries:
                match = re_plot.search(log_entry.message)
                if match:
                    gs = match.groups()
                    for j, g in enumerate(gs):
                        if g:
                            while j >= len(ys):
                                ys.append([])
                            while j >= len(ts):
                                ts.append([])         
                            ys[j].append(float(g))        
                            ts[j].append(log_entry.date_time)
            return ts, ys
        except Exception as e:
            print(e)
            return None