"""
Created on Thu Jan 29 15:26:00 2015
@author: f.groestlinger
"""
from PyQt4 import QtGui, uic
from log_table import LogTableModel
import sys


class LogParser(QtGui.QMainWindow):
    
    def __init__(self, parent=None):
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
        selected_log_type = self.logTypeComboBox.currentText()        
        self.logTypeComboBox.clear()
        self.logTypeComboBox.insertItems(0, self._log_table_model.log_types)  
        if selected_log_type in self._log_table_model.log_types:
            self.logTypeComboBox.setCurrentIndex(self._log_table_model.log_types.index(selected_log_type))
        
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