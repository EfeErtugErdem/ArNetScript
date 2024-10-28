import abc

class IScriptRepository(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def sendAAAConfigurations(self, args: dict):
        pass

    @abc.abstractmethod
    def sendConfigurations(self, args: dict):
        pass

    @abc.abstractmethod
    def dot1xConfigurator(self, args: dict):
        pass

    @abc.abstractmethod
    def sendEnableCommands(self, args: dict):
        pass

    @abc.abstractmethod
    def interfaceExplorer(self, args: dict):
        pass

    @abc.abstractmethod
    def inventoryCreator(self, args: dict):
        pass

    @abc.abstractmethod
    def sendConfigurationsMulti(self, args: dict):
        pass

    @abc.abstractmethod
    def takeNetworkSnapshot(self, args: dict):
        pass

    @abc.abstractmethod
    def analyseLogs(self, args: dict):
        pass