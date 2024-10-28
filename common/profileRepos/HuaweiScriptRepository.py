from common.profileRepos.IScriptRepository import IScriptRepository
from aaaWizard.AAAWizardRepository import AAAWizardRepository
from configSender.ConfigSenderRepository import ConfigSenderRepository
from dot1xWizard.Dot1xWizardRepository import Dot1xWizardRepository
from enableCommandSender.EnableCommandSenderRepository import EnableCommandSenderRepository
from interfaceExplorer.InterfaceExplorerRepository import InterfaceExplorerRepository
from inventoryCreator.InventoryCreatorRepository import InventoryCreatorRepository
from takeNetworkSnapshotv1_1.NetworkSnapshotRepository import NetworkSnapshotRepository
from logAnalyzer.LogAnalyserRepository import LogAnalyserRepository

class HuaweiScriptRepository(IScriptRepository):
    def __init__(self):
        self.aaaWizardRepository = AAAWizardRepository()
        self.configSenderRepository = ConfigSenderRepository()
        self.dot1xWizardRepository = Dot1xWizardRepository()
        self.enableCommandSenderRepository = EnableCommandSenderRepository()
        self.interfaceExplorerRepository = InterfaceExplorerRepository()
        self.inventoryCreatorRepository = InventoryCreatorRepository()
        self.networkSnapshotRepository = NetworkSnapshotRepository()
        self.logAnalyserRepository = LogAnalyserRepository()

    def sendAAAConfigurations(self, args: dict):
        self.aaaWizardRepository.huawei_sendAAAConfigurations(args)

    def sendConfigurations(self, args: dict):
        self.configSenderRepository.huawei_sendConfigurations(args)

    def dot1xConfigurator(self, args: dict):
        self.dot1xWizardRepository.huawei_dot1xConfigurator(args)

    def sendEnableCommands(self, args: dict):
        self.enableCommandSenderRepository.huawei_sendEnableCommand(args)

    def interfaceExplorer(self, args: dict):
        self.interfaceExplorerRepository.huawei_interfaceExplorer(args)

    def prepareWorksheet(self, args: dict):
        self.interfaceExplorerRepository.huawei_prepareWorksheet(args)

    def inventoryCreator(self, args: dict):
        self.inventoryCreatorRepository.huawei_inventoryCreator(args)

    def sendConfigurationsMulti(self, args: dict):
        self.configSenderRepository.huawei_sendConfigurationsMulti(args)

    def takeNetworkSnapshot(self, args: dict):
        self.networkSnapshotRepository.huawei_takeNetworkSnapshot(args)

    def analyseLogs(self, args: dict):
        self.logAnalyserRepository.analyseFirewallLogs(args)