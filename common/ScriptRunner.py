from common.DeviceDetector import DeviceDetector
from common.profileRepos.HuaweiScriptRepository import HuaweiScriptRepository
from common.profileRepos.CiscoScriptRepository import CiscoScriptRepository
from common.Logger import Logger
from common.scriptStrategies.IScriptStrategy import IScriptStrategy
import re
import threading
import traceback

class ScriptRunner:
    ## TODO: telnet bağlanıtısı seçenekleri eklenecek
    ## TODO: Daha iyi bir dizayn için Device detector repo döndürmeli
    repositoryDict = {
        "huawei": HuaweiScriptRepository(),
        "cisco_ios": CiscoScriptRepository(),
        "cisco_xe": CiscoScriptRepository() 
    }

    def __init__(self, pageName: str, scriptStrategy: IScriptStrategy, scriptArguments: dict):
        self.pageName = pageName
        self.scriptStrategy = scriptStrategy
        self.scrArgs = scriptArguments

    def __readSwitchList(self):
        switchList = []
        try:
            with open(f"./{self.pageName}/switchList.txt") as file:
                for line in file:
                    if len(line) > 1:
                        switchList.append(line.strip())
            Logger.writeToLogfile(self.pageName, "BILGI: Switch IP listesi olusturuldu. %d switch bulundu." % len(switchList))
        except Exception as e:
            Logger.writeToLogfile(self.pageName, f"HATA: Switch IP bilgileri alinamadi. Iptal ediliyor... {e}")
            return
        
        if len(switchList) == 0:
            Logger.writeToLogfile(self.pageName, "HATA: IP ya da konfigurasyon dosyalarinda eksik bilgi. Iptal ediliyor...")
            return
        
        return switchList

    def __readSwitchListMulti(self):
        configDict = {}
        try:
            with open(f"./{self.pageName}/switchList.txt") as file:
                for line in file:
                    if len(line) > 1:
                        # Satir basindaki ve sonundaki bosluklari sil
                        line = line.strip()
                        # IP belirteci (#) olan satiri dict'e key olarak ekle ve karsiligina bos liste ata
                        # Dict yapisi IP-adresi : [config] seklinde olacak
                        if line.startswith("#"):
                            currentKey = line.replace("#", "").strip()
                            configDict[currentKey] = []
                        else:  # Dict value'a konfigurasyonlari ekle
                            configDict[currentKey].append(line)
            Logger.writeToLogfile(self.pageName,"BILGI: Konfigurasyon veritabani olusturuldu. %d switch bulundu." % len(configDict))
        except:
            Logger.writeToLogfile(self.pageName,"HATA: Konfigurasyon bilgileri alinamadi. Iptal ediliyor...")
            return
        # Listelerin bos olmadigina emin ol
        if len(configDict) == 0:
            Logger.writeToLogfile(self.pageName,"HATA: Switch IP adresi bulunamadi. Iptal ediliyor...")
            return
        
        return configDict

    def runNetworkingScripts(self, args: dict, stop_event: threading.Event):
        isMultiConfig = False
        ipAddressPattern = re.compile(r'^#\b(?:(?:2(?:[0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9])\.){3}(?:(?:2([0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9]))\b$', re.IGNORECASE)
        switchList = []
        
        try:
            with open(f"./{self.pageName}/switchList.txt") as file:
                firstLine = file.readline()
                if ipAddressPattern.match(firstLine):
                    isMultiConfig = True
                    switchConfigDict = self.__readSwitchListMulti()
                    switchList = switchConfigDict.keys
                else:
                    switchList = self.__readSwitchList()
            Logger.writeToLogfile(self.pageName, "BILGI: Switch IP listesi olusturuldu. %d switch bulundu." % len(switchList))
        except Exception as e:
            Logger.writeToLogfile(self.pageName, f"HATA: Switch IP bilgileri alinamadi. Iptal ediliyor...{e}")
            return
        
        if len(switchList) == 0:
            Logger.writeToLogfile(self.pageName, "HATA: IP ya da konfigurasyon dosyalarinda eksik bilgi. Iptal ediliyor...")
            return
        
        try:
            for switchIP in switchList:
                if stop_event.is_set():
                    Logger.writeToLogfile(self.pageName, "Script durduruldu.")
                    return

                switchProfile = DeviceDetector.detectDevice(switchIP, self.pageName, self.scrArgs)
                activeRepo = self.repositoryDict[switchProfile]

                args['switchIP'] = switchIP
                args['repository'] = activeRepo
                if isMultiConfig:
                    args['configurations'] = switchConfigDict[switchIP]

                self.scriptStrategy.execute(args)

            # Daha iyi bir çözüm bulamadığım için bu şekilde.
            ## TODO: Workbook kapatıldıktan sonra stratejinin workbook we worksheet alanları None olmalı.
            if 'workbook' in args:
                args['workbook'].close()
                args['row'] = 1
                #self.scriptStrategy.resetWorkbook()
                #self.scriptStrategy.resetWorksheet()

        except Exception as e:
            Logger.writeToLogfile(self.pageName, f"HATA: switch IP'leri konfigüre edilirken hata {traceback.extract_tb()}.")

    def runAnalyserScripts(self, args: dict, stop_event: threading.Event):
        try:
            activeRepo = self.repositoryDict['cisco_ios']

            args['repository'] = activeRepo
            if stop_event.is_set():
                return
            
            self.scriptStrategy.execute(args)
        except Exception as e:
            Logger.writeToLogfile(self.pageName, f"Log dosyasi hazirlanirken hata: {e}")
