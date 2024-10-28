from abc import ABC, abstractmethod
from common.profileRepos.IScriptRepository import IScriptRepository

class IScriptStrategy(ABC):
    @abstractmethod
    def execute(self, repo: IScriptRepository):
        pass