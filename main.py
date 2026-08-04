from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt
import sys
import pandas as pd

#Window dimensions
WIN_WID = 800
WIN_HEI = 600

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        #set start up params
        self.resize(WIN_WID, WIN_HEI)
        self.setWindowTitle("Canny's Little Helper")
        self.statusBar().showMessage("[Initializing]")

        #self.setWindowIcon(QIcon('findimagelater'))

        # declare picklistCSVs as list - feature WIP
        # self.picklistCSVs = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()

        self.masterCSVLabel = QLabel("Add the master CSV")
        # save master csv every time loaded - feature WIP
        # if self.masterCSVLabel:
        #     self.masterCSVLabel += QLabel(": found")
        main_layout.addWidget(self.masterCSVLabel)

        masterCSVButton = QPushButton("Add Master CSV")
        masterCSVButton.clicked.connect(lambda: self.OpenFileWindow("master"))
        main_layout.addWidget(masterCSVButton)

        self.picklistCSVLabel = QLabel("Add the pick list CSV")
        main_layout.addWidget(self.picklistCSVLabel)

        picklistCSVButton = QPushButton("Add Pick List CSV")
        picklistCSVButton.clicked.connect(lambda: self.OpenFileWindow("picklist"))
        main_layout.addWidget(picklistCSVButton)

        self.processLabel = QLabel("Find the cards")
        main_layout.addWidget(self.processLabel)

        processButton = QPushButton("Find Cards")
        processButton.clicked.connect(self.ProcessCSVs)
        main_layout.addWidget(processButton)

        self.cardListTable = QTableWidget()
        main_layout.addWidget(self.cardListTable)

        central_widget.setLayout(main_layout)

    def OpenFileWindow(self, fileType):
        fileSelect, _ = QFileDialog.getOpenFileName(self, "CSV Select", "", "CSV Files (*.csv)")

        if fileSelect:
            if fileType == "master":
                self.masterCSV = fileSelect
                self.masterCSVLabel.setText(f"{self.masterCSVLabel.text()} - found")
            elif fileType == "picklist":
                # self.picklistCSVs.append(fileSelect)
                self.picklistCSVs = fileSelect
                self.picklistCSVLabel.setText(f"{self.picklistCSVLabel.text()} - found")
            print(f"{fileType} CSV: {fileSelect}")

    def ProcessCSVs(self):
        if self.masterCSV and self.picklistCSVs:
            master_df = pd.read_csv(self.masterCSV)
            picklist_df = pd.read_csv(self.picklistCSVs)

            # clean stirngs in dfs to be consistent between dfs
            master_df["Set code"] = master_df["Set code"].str.lower()
            master_df["Finish"] = master_df["Finish"].str.lower()

            picklist_df["Set Code"] = picklist_df["Set Code"].str.lower()
            picklist_df["Finish"] = picklist_df["Finish"].replace(["Non-Foil", "Foil"], ["normal", "foil"])

            # expand each row to duplicate equal to the quantity of that card
            master_df = master_df.loc[master_df.index.repeat(master_df["Quantity"])]
            picklist_df = picklist_df.loc[picklist_df.index.repeat(picklist_df["Quantity"])]

            # each card gets a count of how many times that exact card is seen before
            # this allows the merge to only grab the next card needed
            master_df["CopyNum"] = master_df.groupby(["Set code", "Collector number", "Finish"]).cumcount()
            picklist_df["CopyNum"] = picklist_df.groupby(["Set Code", "Collector #", "Finish"]).cumcount()

            joined_df = pd.merge(master_df, 
                                 picklist_df, 
                                 how="inner", 
                                 left_on=["Set code", "Collector number", "Finish", "CopyNum"], 
                                 right_on=["Set Code", "Collector #", "Finish", "CopyNum"], 
                                 suffixes=["_master", "_picklist"]
                                )
            joined_df = joined_df.sort_values(by="Location")

            # find any cards that might be missing with an anti-join
            antijoin_df = pd.merge(picklist_df, 
                                   joined_df, 
                                   how="left",
                                   left_on=["Set Code", "Collector #", "Finish", "CopyNum"], 
                                   right_on=["Set code", "Collector number", "Finish", "CopyNum"], 
                                   indicator=True
                                   )

            missing = antijoin_df[antijoin_df["_merge"] == "left_only"]
            print(missing.to_string())


            headers = ["Location", "Name", "Set code", "Collector #", "Finish"]
            self.PopulateTable(joined_df[headers])

            with open("joined.txt", "w") as f:
                f.write(joined_df.to_string())

    def PopulateTable(self, df):

        self.cardListTable.setRowCount(len(df))
        self.cardListTable.setColumnCount(len(df.columns) + 1) # found?, Location, Name, Set code, Collector #, Finish

        self.cardListTable.setHorizontalHeaderLabels(["Found?"] + list(df.columns))

        for rInd, row in enumerate(df.values):
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox.setCheckState(Qt.CheckState.Unchecked)
            self.cardListTable.setItem(rInd, 0, checkbox)

            for cInd, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                self.cardListTable.setItem(rInd, cInd + 1, item)
        
            



        

app = QApplication(sys.argv)
app.setStyle("Fusion")
window = Window()
window.show()
sys.exit(app.exec())