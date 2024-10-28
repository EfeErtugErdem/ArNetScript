from common.profileRepos.IScriptRepository import IScriptRepository
from aaaWizard.AAAWizardRepository import AAAWizardRepository
from configSender.ConfigSenderRepository import ConfigSenderRepository
from dot1xWizard.Dot1xWizardRepository import Dot1xWizardRepository
from enableCommandSender.EnableCommandSenderRepository import EnableCommandSenderRepository
from interfaceExplorer.InterfaceExplorerRepository import InterfaceExplorerRepository
from inventoryCreator.InventoryCreatorRepository import InventoryCreatorRepository
from takeNetworkSnapshotv1_1.NetworkSnapshotRepository import NetworkSnapshotRepository
from logAnalyzer.LogAnalyserRepository import LogAnalyserRepository


class CiscoScriptRepository(IScriptRepository):
    def __init__(self):
        self.AAAWizardRepository = AAAWizardRepository()
        self.configSenderRepository = ConfigSenderRepository()
        self.dot1xWizardRepository = Dot1xWizardRepository()
        self.enableCommandSenderRepository = EnableCommandSenderRepository()
        self.interfaceExplorerRepository = InterfaceExplorerRepository()
        self.inventoryCreatorRepository = InventoryCreatorRepository()
        self.networkSnapshotRepository = NetworkSnapshotRepository()
        self.logAnalyserRepository = LogAnalyserRepository()

    def sendAAAConfigurations(self, args: dict):
        self.AAAWizardRepository.cisco_sendAAAConfigurations(args)

    def sendConfigurations(self, args: dict):
        self.configSenderRepository.cisco_sendConfigurations(args)

    def dot1xConfigurator(self, args: dict):
        self.dot1xWizardRepository.cisco_dot1xConfigurator(args)

    def sendEnableCommands(self, args: dict):
        self.enableCommandSenderRepository.cisco_sendEnableCommands(args)

    def interfaceExplorer(self, args: dict):
        self.interfaceExplorerRepository.cisco_interfaceExplorer(args)

    def prepareWorksheet(self, args: dict):
        self.interfaceExplorerRepository.cisco_prepareWorksheet(args)

    def inventoryCreator(self, args: dict):
        self.inventoryCreatorRepository.cisco_inventoryCreator(args)

    def sendConfigurationsMulti(self, args: dict):
        self.configSenderRepository.cisco_sendConfigurationsMulti(args)

    def takeNetworkSnapshot(self, args: dict):
        self.networkSnapshotRepository.cisco_takeNetworkSnapshot(args)

    def analyseLogs(self, args: dict):
        self.logAnalyserRepository.analyseFirewallLogs(args)
