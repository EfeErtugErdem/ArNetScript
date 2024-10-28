from common.scriptStrategies.IScriptStrategy import IScriptStrategy
from common.Logger import Logger
from datetime import datetime
import xlsxwriter, xlsxwriter.worksheet
from pyvis import network as net
import traceback
import random, string

class AAAScriptStrategy(IScriptStrategy):
    def __init__(self):
        pass

    def execute(self, args):
        args['repository'].sendAAAConfigurations(args)

class ConfigSenderScriptStrategy(IScriptStrategy):
    def __init__(self):
        pass

    def execute(self, args):
        args['repository'].sendConfigurations(args)

class Dot1xWizardStrategy(IScriptStrategy):
    def __init__(self):
        pass

    def execute(self, args):
        args['repository'].dot1xConfigurator(args)

class SendEnableCommandsStrategy(IScriptStrategy):
    def __init__(self):
        pass

    def execute(self, args):
        args['repository'].sendEnableCommands(args)

class InterfaceExplorerStrategy(IScriptStrategy):
    excelWorksheet: xlsxwriter.worksheet
    excelWorkbook: xlsxwriter.Workbook

    def __init__(self):
        self.excelWorksheet = None
        self.excelWorkbook = None

    def resetWorkbook(self):
        self.excelWorkbook = None
    
    def resetWorksheet(self):
        self.excelWorksheet = None

    def __createExcelworksheet(self, args: dict):
        pageName = args['pageName']

        Logger.writeToLogfile(pageName, "BILGI: Excel dosyasi olusturuluyor.")
        fileName = f"./{pageName.strip()}Reports/interfaceExplorerReport_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        excelWorkbook = xlsxwriter.Workbook(fileName)
        excelWorksheet = excelWorkbook.add_worksheet(name="INTERFACE-INFO")
        excelWorksheet.write(0, 0, "Switch Info")

        return excelWorkbook, excelWorksheet

    def execute(self, args: dict):
        if self.excelWorkbook is None or self.excelWorksheet is None:
            self.excelWorkbook, self.excelWorksheet = self.__createExcelworksheet(args)
            args['worksheet'] = self.excelWorksheet
            args['workbook'] = self.excelWorkbook
            args['vlanLocations'] = {}
            args['repository'].prepareWorksheet(args)
            args['row'] = 1
        args['repository'].interfaceExplorer(args)

class InventoryCreatorStrategy():
    excelWorkbook: xlsxwriter.Workbook
    excelWorksheet: xlsxwriter.worksheet

    def __init__(self):
        self.excelWorksheet = None
        self.excelWorkbook = None

    def resetWorkbook(self):
        self.excelWorkbook = None
    
    def resetWorksheet(self):
        self.excelWorksheet = None

    def __createExcelWorksheet(self, args: dict):
        fileName = f"./{args['pageName']}Reports/inventoryReport_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        excelWorkbook = xlsxwriter.Workbook(fileName)
        excelWorksheet = excelWorkbook.add_worksheet(name="INVENTORY")
        excelWorksheet.write(0, 0, "Seri No")
        excelWorksheet.write(0, 1, "Cihaz Detay")
        excelWorksheet.write(0, 2, "Switch Hostname")
        excelWorksheet.write(0, 3, "Switch IP")

        return excelWorkbook, excelWorksheet
    
    def execute(self, args: dict):
        if self.excelWorksheet is None or self.excelWorksheet is None:
            self.excelWorkbook, self.excelWorksheet = self.__createExcelWorksheet(args=args)
            args['worksheet'] = self.excelWorksheet
            args['workbook'] = self.excelWorkbook
            args['row'] = 1
        args['repository'].inventoryCreator(args)

class MultiConfigSenderStrategy(IScriptStrategy):
    def __init__(self):
        pass

    def execute(self, args: dict):
        args['repository'].sendConfigurationsMulti(args)

class TakeNetworkSnapshotStrategy(IScriptStrategy):
    switchTreeDict: dict
    switchTreeDetailedDict: dict

    def __init__(self):
        self.switchTreeDict = {}
        self.switchTreeDetailedDict = {}

    def __drawTopology(self, args: dict):
        pageName = args['pageName']

        try:
            graphOptions = {
                "edges": {
                    "color": {
                        "inherit": True
                    },
                    "smooth": False
                },
                "manipulation": {
                    "enabled": True
                },
                "interaction": {
                    "hover": True
                },
                "physics": {
                    "barnesHut": {
                        "damping": 0.6,
                        "avoidOverlap": 0.05,
                        "springLength": 115
                    },
                    "minVelocity": 0.75
                }
            }
            # CDP verisi alinan switchlerin hostname'lerini nodeList'e ekle
            nodeList = list(self.switchTreeDict.keys())
            # CDP verisi alinan switchlere bagli alt switchleri edgeList'e ekle
            edgeList = list(self.switchTreeDict.values())
            # Grafik ortamini olustur
            networkGraph = net.Network(height='800px', width='100%', heading='')
            # Node ve edge listesi icindeki tum benzersiz switchleri nodesToAdd listesine ekle
            nodesToAdd = []
            for node in nodeList:
                if node not in nodesToAdd:
                    nodesToAdd.append(node)
            for subList in edgeList:
                for edge in subList:
                    if edge not in nodesToAdd:
                        nodesToAdd.append(edge)
            # Benzersiz switch'leri ve AP'leri node olarak ekle
            for node in nodesToAdd:
                nodeDetail = node
                if node in nodeList:
                    nodeDetail = str(self.switchTreeDetailedDict[node])
                if "sw" in node.lower():  # Node switch ise varsayılan gorunumu kullan
                    networkGraph.add_node(node, title=nodeDetail)
                elif "ap" in node.lower():  # Node AP ise yesile boya
                    networkGraph.add_node(node, title=nodeDetail, color="lightgreen")
                else:  # Diger node'lari griye boya
                    networkGraph.add_node(node, title=nodeDetail, color="lightgray")
            # nodeList ve edgeList listeleri ile grafigi olustur
            for i in range(len(nodeList)):
                node = nodeList[i]
                for edge in edgeList[i]:
                    if node != edge:
                        networkGraph.add_edge(node, edge, color="black")
            networkGraph.toggle_physics(True)
            #networkGraph.show_buttons() # Tum ayar menusunu goster
            networkGraph.options = graphOptions
            networkGraph.show(f"./{pageName}networkTopology_{datetime.now().strftime('%Y_%m_%d')}_{''.join(random.choice(string.ascii_letters) for _ in range(4))}.html", notebook=False)
            #display(HTML(f"./{userArgs}networkTopology.html"))
            Logger.writeToLogfile(pageName, "Bilgi: Topolojiye 'networkTopology.html' dosyasindan ulasilabilir.")
        except Exception as e:
            Logger.writeToLogfile(pageName, f"HATA: Topoloji olusturulurken hata olustu. {traceback.extract_tb()}")

    def execute(self, args: dict):
        args['switchTreeDict'] = self.switchTreeDict
        args['switchTreeDetailedDict'] = self.switchTreeDetailedDict

        args['repository'].takeNetworkSnapshot(args)

        self.switchTreeDict = args['switchTreeDict']
        self.switchTreeDetailedDict = args['switchTreeDetailedDict']

        if args['createTopology']:
            self.__drawTopology(args=args)

class LogAnalyserStrategy(IScriptStrategy):
    def __init__(self):
        pass

    def execute(self, args: dict):
        args['repository'].analyseLogs(args)
    

