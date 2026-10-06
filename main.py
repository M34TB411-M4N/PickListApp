from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt
import sys
import pandas as pd
import time

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

        clearButton = QPushButton("Remove All Checked Cards")
        clearButton.clicked.connect(self.ClearTable)
        main_layout.addWidget(clearButton)

        central_widget.setLayout(main_layout)

    def OpenFileWindow(self, fileType):
        fileSelect, _ = QFileDialog.getOpenFileName(self, "CSV Select", "", "CSV Files (*.csv)")

        if fileSelect:
            if fileType == "master":
                self.masterCSV = fileSelect
                self.masterCSVLabel.setText(f"{self.masterCSVLabel.text()} - {fileSelect}")
            elif fileType == "picklist":
                # self.picklistCSVs.append(fileSelect)
                self.picklistCSV = fileSelect
                self.picklistCSVLabel.setText(f"{self.picklistCSVLabel.text()} - {fileSelect}")
            print(f"{fileType} CSV: {fileSelect}")

    def ProcessCSVs(self):
        if self.masterCSV and self.picklistCSV:
            self.master_df = pd.read_csv(self.masterCSV)
            picklist_df = pd.read_csv(self.picklistCSV)

            #set types for each column in the dataframe - sometimes can be misinterpreted from a lack of data
            master_type_dict = {'Location':str, 'Name':str, 'Set code':str, 'Collector number':str, 'Finish':str, 'Quantity':int, 'Scryfall ID':str, 'Colors':str, 'CMC':int, 'Type':str, 'Price (USD)':float}
            picklist_type_dict = {'Set Code':str, 'Collector #':str, 'Finish':str}

            self.master_df = self.master_df.astype(master_type_dict)
            picklist_df = picklist_df.astype(picklist_type_dict)

            print("master types")
            print(self.master_df.dtypes)
            print("picklist types")
            print(picklist_df.dtypes)

            # clean strings in dfs to be consistent between dfs
            self.master_df["Set code"] = self.master_df["Set code"].str.lower()
            self.master_df["Finish"] = self.master_df["Finish"].str.lower()
            self.master_df["Collector number"] = self.master_df["Collector number"].str.lower()

            picklist_df["Set Code"] = picklist_df["Set Code"].str.lower()
            picklist_df["Finish"] = picklist_df["Finish"].replace(["Non-Foil", "Foil"], ["normal", "foil"])
            picklist_df["Collector #"] = picklist_df["Collector #"].str.lower()

            # expand each row to duplicate equal to the quantity of that card
            ex_master_df = self.master_df.loc[self.master_df.index.repeat(self.master_df["Quantity"])]
            picklist_df = picklist_df.loc[picklist_df.index.repeat(picklist_df["Quantity"])]

            # each card gets a count of how many times that exact card is seen before
            # this allows the merge to only grab the next card needed
            ex_master_df["CopyNum"] = ex_master_df.groupby(["Set code", "Collector number", "Finish"]).cumcount()
            picklist_df["CopyNum"] = picklist_df.groupby(["Set Code", "Collector #", "Finish"]).cumcount()

            joined_df = pd.merge(ex_master_df, 
                                 picklist_df, 
                                 how="inner", 
                                 left_on=["Set code", "Collector number", "Finish", "CopyNum"], 
                                 right_on=["Set Code", "Collector #", "Finish", "CopyNum"], 
                                 suffixes=["_master", "_picklist"]
                                )

            # joined_df = pd.concat([ex_master_df, 
            #                      picklist_df.rename(columns={'Set Code':'Set code','Collector #':'Collector number'})], 
            #                      join="inner", 
            #                      keys=['Set code','Collector number', 'Finish', 'CopyNum']
            #                      axis=1
            #                     )

            joined_df["letter"] = joined_df["Location"].str.extract(r"([A-Za-z]+)")
            joined_df["number"] = joined_df["Location"].str.extract(r"(\d+)").astype(float)
            
            joined_df = joined_df.sort_values(["letter", "number"]).drop(columns=["letter", "number"])

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

    def ClearTable(self):
        print("clearing table")
        for i in range(self.cardListTable.rowCount()):
            checkbox = self.cardListTable.item(i, 0)
            if checkbox.checkState() == Qt.CheckState.Checked:
                location = self.cardListTable.item(i, 1).text()
                setCode = self.cardListTable.item(i, 3).text()
                collectNum = self.cardListTable.item(i, 4).text()
                finish = self.cardListTable.item(i, 5).text()

                self.master_df.loc[((self.master_df["Location"] == location) & (self.master_df["Set code"] == setCode) & (self.master_df["Collector number"].astype(str) == collectNum) & (self.master_df["Finish"] == finish)), "Quantity"] -= 1

        self.master_df = self.master_df[self.master_df["Quantity"] > 0]

        with open('cannys_updated_masterlist_' + time.ctime().replace(' ', '_').replace(':', '-') + '.csv', 'w') as file:
            self.master_df.to_csv(file, index=False)



        # reset values to default
        self.cardListTable.setRowCount(0)
        self.masterCSV = None
        self.picklistCSV = None
        self.masterCSVLabel.setText("Add the master CSV")
        self.picklistCSVLabel.setText("Add the pick list CSV")



        
            



        

app = QApplication(sys.argv)
app.setStyle("Fusion")
window = Window()
window.show()
sys.exit(app.exec())