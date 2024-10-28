from netmiko import ConnectHandler
from common.Logger import Logger
from netmiko.exceptions import NetMikoTimeoutException
from netmiko.exceptions import AuthenticationException
from paramiko.ssh_exception import SSHException
import os
import textfsm
import traceback

class NetworkSnapshotRepository:
    def __init__(self):
        pass

    def __createConfigBackupFile(self, pageName, configString, switch):
        """configBackups klasorune switch konfigurasyonunu kaydeder."""
        try:
            fileName = "configBackup_" + switch.replace(".", "_") + ".txt"
            path = f"./{pageName}configBackups"
            configPath = os.path.join(path, fileName)
            with open(configPath, "w", encoding="utf-8") as configFile:
                configFile.write(configString)
            configFile.close()
        except:
            Logger.writeToLogfile(pageName, "HATA: Switch konfigurasyon dosyasi olusturulamadi.")

    def __getFullConfig(self, pageName, session):
        """Cihazda 'show run' ciktisini çalıştırıp, return eder."""
        try:
            deviceConfig = session.send_command("show running-config")
            Logger.writeToLogfile(pageName, "BILGI: Cihaz konfigurasyonu SSH ile basariyla alindi.")
            return deviceConfig
        except:
            Logger.writeToLogfile(pageName, "HATA: Cihaz konfigurasyonu SSH ile alinamadi.")
            return None
        
    def __getCdpItems_cisco(self, pageName, output):
        """CDP'de gorunen cihazları port:hostname şeklinde dictionary olarak return eder."""
        try:
            cdpDict = {}
            for row in output:
                swName = row['Device_ID']
                portName = row['Local_Intf']
                if not swName.startswith("SEP"):  # IP telefonlari CDP tablosundan cikar
                    # Isımlendirilmemis AP'leri tum ismi ile al (MAC adresi)
                    # Switch domain name'i sil
                    if "." in swName and not swName.startswith("AP"):
                        swName = swName[:(swName.find("."))]
                    cdpDict[portName] = swName
            Logger.writeToLogfile(pageName, "BILGI: LLDP dictionary basariyla olusturuldu.")
            return cdpDict
        except:
            Logger.writeToLogfile(pageName, "HATA: LLDP dictionary olusturulamadi.")
            return None
        
    def __getFullConfig_huawei(self, pageName, session):
        """Cihazda 'display current-configuration' ciktisini çalıştırıp, return eder."""
        try:
            deviceConfig = session.send_command("display current-configuration")
            Logger.writeToLogfile(pageName, "BILGI: Cihaz konfigurasyonu SSH ile basariyla alindi.")
            return deviceConfig
        except:
            Logger.writeToLogfile(pageName, "HATA: Cihaz konfigurasyonu SSH ile alinamadi.")
            return None
        
    def __getCdpItems_huawei(self, pageName, output):
        """CDP'de gorunen cihazları port:hostname şeklinde dictionary olarak return eder."""
        try:
            cdpDict = {}
            for row in output:
                swName = row['Neighbor_Dev']
                portName = row['Local_Intf']
                if not swName.startswith("SEP"):  # IP telefonlari CDP tablosundan cikar
                    # Isımlendirilmemis AP'leri tum ismi ile al (MAC adresi)
                    # Switch domain name'i sil
                    if "." in swName and not swName.startswith("AP"):
                        swName = swName[:(swName.find("."))]
                    cdpDict[portName] = swName
            Logger.writeToLogfile(pageName, "BILGI: CDP dictionary basariyla olusturuldu.")
            return cdpDict
        except:
            Logger.writeToLogfile(pageName, "HATA: CDP dictionary olusturulamadi.")
            return None

    def cisco_takeNetworkSnapshot(self, args: dict):
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'wantToSaveConfig' in args and \
                'createTopology' in args and \
                'switchTreeDict' in args and \
                'switchTreeDetailedDict' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'wantToSaveConfig' ve 'configurations' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']
        configBackupRequested = args['wantToSaveConfig']
        topologyRequested = args['createTopology']
        if not configBackupRequested and not topologyRequested:
            Logger.writeToLogfile(pageName, "BILGI: Ister yok. Iptal ediliyor...")
            return
        if configBackupRequested:
            if not os.path.isdir(f"./{pageName}configBackups"):
                os.mkdir(f"./{pageName}configBackups")
        templateBasePath = "./common/textfsmTemplates"

        try:
            ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                        'username': args['username'], 'password': args['password'],
                        'secret': args['password'], 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitch)
            ssh.enable()
            Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)
            swName = ssh.find_prompt()
            swName = swName[:-1]
            Logger.writeToLogfile(pageName, "BILGI: Switch hostname: %s " % swName)

            if configBackupRequested:  # Switch konfigurasyon yedegi al
                rawSwConfig = self.__getFullConfig(pageName, ssh)
                self.__createConfigBackupFile(pageName, rawSwConfig, switchIP)
                Logger.writeToLogfile(pageName, "BILGI: Switch konfigurasyonu 'configBackups' klasorune kaydedildi.")
            
            if topologyRequested:
                cdpOutput = ssh.send_command("show lldp neighbors")

                with open(f"{templateBasePath}/ciscoLldpTemplate.textfsm") as templateFile:
                    fsm = textfsm.TextFSM(templateFile)
                    parsedOutput = fsm.ParseText(cdpOutput)
                    headers = fsm.header

                cdpDict = self.__getCdpItems_cisco(pageName, [dict(zip(headers, row)) for row in parsedOutput])
                args['switchTreeDict'][swName] = list(cdpDict.values())
                args['switchTreeDetailedDict'][swName] = cdpDict
            # SSH baglantisini sonlandir
            ssh.disconnect()
        except (NetMikoTimeoutException):
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch'e baglanilamadi. Timeout." % switchIP)
            return
        except (AuthenticationException):
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch'e baglanilamadi. Parola hatali." % switchIP)
            return
        except (SSHException):
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch'e SSH ile baglanilamadi. Telnet ile deneyin." % switchIP)
            return
        except:
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch islenirken hata olustu. %s" % switchIP, traceback.extract_tb())
            return
        

    def huawei_takeNetworkSnapshot(self, args: dict):
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'wantToSaveConfig' in args and \
                'createTopology' in args and \
                'switchTreeDict' in args and \
                'switchTreeDetailedDict' in args
        except AssertionError:
            Logger.writeToLogfile("./takeNetworkSnapshotv1_1/", f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'wantToSaveConfig' ve 'configurations' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']
        configBackupRequested = args['wantToSaveConfig']
        topologyRequested = args['createTopology']
        if not configBackupRequested and not topologyRequested:
            Logger.writeToLogfile(pageName, "BILGI: Ister yok. Iptal ediliyor...")
            return
        if configBackupRequested:
            if not os.path.isdir(f"./{pageName}configBackups"):
                os.mkdir(f"./{pageName}configBackups")
        templateBasePath = "./common/textfsmTemplates"

        try:
            huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                        'username': args['username'], 'password': args['password'], 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitch)
            ssh.config_mode()
            Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)
            swName = ssh.find_prompt()
            swName = swName[1:-1]
            Logger.writeToLogfile(pageName, "BILGI: Switch hostname: %s " % swName)

            if configBackupRequested:  # Switch konfigurasyon yedegi al
                rawSwConfig = self.__getFullConfig_huawei(pageName, ssh)
                self.__createConfigBackupFile(pageName, rawSwConfig, switchIP)
                Logger.writeToLogfile(pageName, "BILGI: Switch konfigurasyonu 'configBackups' klasorune kaydedildi.")
            
            if topologyRequested:
                cdpOutput = ssh.send_command("display lldp neighbor brief")

                if "Neighbor Interface" in cdpOutput:
                    with open(f"{templateBasePath}/huaweiLldpTemplateNewer.textfsm") as templateFile:
                        fsm = textfsm.TextFSM(templateFile)
                        parsedOutput = fsm.ParseText(cdpOutput)
                        headers = fsm.header
                else:    
                    with open(f"{templateBasePath}/huaweiLldpTemplate.textfsm") as templateFile:
                        fsm = textfsm.TextFSM(templateFile)
                        parsedOutput = fsm.ParseText(cdpOutput)
                        headers = fsm.header

                cdpDict = self.__getCdpItems_huawei(pageName, [dict(zip(headers, row)) for row in parsedOutput])
                print(cdpDict)
                args['switchTreeDict'][swName] = list(cdpDict.values())
                args['switchTreeDetailedDict'][swName] = cdpDict
            # SSH baglantisini sonlandir
            ssh.disconnect()
        except (NetMikoTimeoutException):
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch'e baglanilamadi. Timeout." % switchIP)
            return
        except (AuthenticationException):
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch'e baglanilamadi. Parola hatali." % switchIP)
            return
        except (SSHException):
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch'e SSH ile baglanilamadi. Telnet ile deneyin." % switchIP)
            return
        except:
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch islenirken hata olustu. %s" % switchIP, traceback.extract_tb())
            return