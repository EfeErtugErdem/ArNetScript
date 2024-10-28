from netmiko import ConnectHandler
import re
import os
from common.Logger import Logger

class AAAWizardRepository:
    '''
    Verilen cihaza AAA konfigürasyonlarini uygulamaya yarayan sinif.

    Attributes
    ----------
    Yok
    
    Methods
    -------
    cisco_sendAAAConfigurations(args: dict) -> None:\n
        Cisco marka cihazlara AAA konfigürasyonlarini uygular.\n
    huawei_sendAAAConfigurations(args: dict) -> None:\n
        Huawei marka cihazlara AAA konfigürasyonlarini uygular.
    '''

    def __init__(self):
        pass

    def __readConfig(self, pageName: str, fileName: str) -> list:
        """ Konfigürasyon dosyasinda yazilan komutlari liste halinde döndürür.
        Parameters
        ----------
        pageName: str
            Sinifin bulunduğu klasörün adi. Özel bir ad olmali.
        fileName: str
            Konfigürasyon komutlarinin bulunduğu dosyanin adi

        Returns
        -------
        configList: list
            Konfigürasyon komutlarini iceren array.
        """
        configList = []
        try:
            with open(f"./{pageName}{fileName}") as file:
                for line in file:
                    if len(line) > 1:
                        configList.append(line.strip())
            Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon listesi olusturuldu.")
        except:
            Logger.writeToLogfile(pageName, "HATA: Konfigurasyon bilgileri alinamadi. Iptal ediliyor...")
            return
        # Listelerin bos olmadigina emin ol
        if len(configList) == 0:
            Logger.writeToLogfile(pageName, "HATA: IP ya da konfigurasyon dosyalarinda eksik bilgi. Iptal ediliyor...")
            return

        return configList
    
    def cisco_sendAAAConfigurations(self, args: dict) -> None:
        """ Cisco IOS kullanan cihazlara AAA konfigürasyonlarini uygular.
        Parameters
        ----------
        args: dict
            Metoda verilen paramerelerin bulunduğu dictionary.\n
            "args" ASAGIDAKI ALANLARI ICERMELI:
        - pageName: str
            Sinifin bulunduğu klasörün adi. Özel bir ad olmali.
        - switchIP: str
            Konfigurasyonlarin uygulandigi cihazin IP adresi.
        - username: str
            Cihaza konfigurasyon uygulamak için gereken kullanici adi.
        - password: str
            Cihaza konfigurasyon uygulamak için gereken parola.
        - wantToSaveConfig: bool
            Konfigürasyonlar uygulandiktan sonra cihaza kaydedilecek mi?
        """
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'wantToSaveConfig' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"HATA: Eksik girdi: {list(args.keys())}; girdi 'pageName', 'switchIP', 'username', 'password' ve 'wantToSaveConfig' alanlarini icermeli.")
            
        switchIP = args['switchIP']
        pageName = args['pageName']

        configListNew = self.__readConfig(pageName, "configFileNew.txt")
        configListOld = self.__readConfig(pageName, "configFileOld.txt")
        
        if not os.path.isdir(f"./{pageName}commandOutputs"):
            os.mkdir(f"./{pageName}commandOutputs")

        isNewSyntax = False
        try:
            try:
                # SSH ile baglanmayi dene
                ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                            'username': args['username'], 'password': args['password'],
                            'secret': args['password'], 'port': 22, }
                ssh = ConnectHandler(**ciscoSwitch)
                ssh.enable()
                swName = ssh.find_prompt()
                swName = swName[:-1]
                if "Invalid input" in ssh.send_command("show run aaa"):
                    isNewSyntax = False
                else:
                    isNewSyntax = True
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi. Hostname: %s" %(switchIP,swName))

                # Yeni veya eski syntax kullanımı
                if isNewSyntax:
                    Logger.logCommandOutputs(pageName, ssh.send_config_set(configListNew), switchIP)
                    Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon listesi uygulandi (Yeni syntax).")
                else:
                    Logger.logCommandOutputs(pageName, ssh.send_config_set(configListOld), switchIP)
                    Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon listesi uygulandi (Eski syntax).")

                # Konfigürasyonlar uygulandıktan sonra cihaza kaydedilsin mi
                if args['wantToSaveConfig']:
                    Logger.logCommandOutputs(pageName, ssh.send_command("write"), switchIP)
                    Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)

                ssh.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
            except:
                # SSH basarisiz olursa telnet ile baglanmayi dene
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) SSH ile baglanilamadi. Telnet deneniyor." % switchIP)
                ciscoSwitch = {'device_type': 'cisco_ios_telnet', 'host': switchIP,
                            'username': args['username'], 'password': args['password'],
                            'secret': args['password'], 'port': 23, }
                telnet = ConnectHandler(**ciscoSwitch)
                telnet.enable()
                swName = telnet.find_prompt()
                swName = swName[:-1]
                if "Invalid input" in telnet.send_command("show run aaa"):
                    isNewSyntax = False
                else:
                    isNewSyntax = True
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi. Hostname: %s" %(switchIP,swName))
                
                # Yeni veya eski syntax kullanımı
                if isNewSyntax:
                    Logger.logCommandOutputs(pageName, telnet.send_config_set(configListNew), switchIP)
                    Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon listesi uygulandi (Yeni syntax).")
                else:
                    Logger.logCommandOutputs(pageName, telnet.send_config_set(configListOld), switchIP)
                    Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon listesi uygulandi (Eski syntax).")
                
                # Konfigürasyonlar uygulandıktan sonra cihaza kaydedilsin mi
                if args['wantToSaveConfig']:
                    Logger.logCommandOutputs(pageName, telnet.send_command("write"), switchIP)
                    Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
                
                telnet.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
        except:
            Logger.writeToLogfile(pageName, "HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)
        Logger.writeToLogfile(pageName, "BILGI: Islem tamamlandi.")

    def huawei_sendAAAConfigurations(self, args: dict):
        """ Huawei marka cihazlara AAA konfigürasyonlarini uygular.
        Parameters
        ----------
        args: dict
            Metoda verilen paramerelerin bulunduğu dictionary.\n
            "args" ASAGIDAKI ALANLARI ICERMELI:
        - pageName: str
            Sinifin bulunduğu klasörün adi. Özel bir ad olmali.
        - switchIP: str
            Konfigurasyonlarin uygulandigi cihazin IP adresi.
        - username: str
            Cihaza konfigurasyon uygulamak için gereken kullanici adi.
        - password: str
            Cihaza konfigurasyon uygulamak için gereken parola.
        - wantToSaveConfig: bool
            Konfigürasyonlar uygulandiktan sonra cihaza kaydedilecek mi?
        """
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'wantToSaveConfig' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"HATA: Eksik girdi: {list(args.keys())}; girdi 'pageName', 'switchIP', 'username', 'password' ve 'wantToSaveConfig' alanlarini icermeli.")

        switchIP = args['switchIP']
        pageName = args['pageName']

        configList = self.__readConfig(pageName, "configFile.txt")
        
        if not os.path.isdir(f"./{pageName}commandOutputs"):
            os.mkdir(f"./{pageName}commandOutputs")

        try:
            try:
                # SSH ile baglanmayi dene
                huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                            'username': args['username'], 'password': args['password'], 'port': 22, }
                ssh = ConnectHandler(**huaweiSwitch)
                ssh.config_mode()
                swName = ssh.find_prompt()
                swName = swName[1:-1]
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi. Hostname: %s" %(switchIP,swName))

                # Konfigürasyonları uygula
                for configCommand in configList:
                    configCommandOutput = ssh.send_command_timing(configCommand)
                    # Komut ayrı bir prompt (sonu [Y/N] ile biten) gönderiyorsa cevap gönder
                    if re.search(r'\[Y/N\]', configCommandOutput):
                        configCommandOutput += ssh.send_command_timing("Y")
                    Logger.logCommandOutputs(pageName, configCommandOutput, switchIP)

                # "current-configuration'u" startup'a kaydet
                if args['wantToSaveConfig']:
                    saveConfigOutput = ssh.send_command_timing("save current-configuration")
                    if re.search(r'\[Y/N\]', saveConfigOutput):
                        saveConfigOutput += ssh.send_command_timing("Y")
                    Logger.logCommandOutputs(pageName, saveConfigOutput, switchIP)
                    Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
                
                ssh.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
            except:
                # SSH basarisiz olursa telnet ile baglanmayi dene
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) SSH ile baglanilamadi. Telnet deneniyor." % switchIP)
                huaweiSwitch = {'device_type': 'huawei_telnet', 'host': switchIP,
                            'username': args['username'], 'password': args['password'], 'port': 23, }
                telnet = ConnectHandler(**huaweiSwitch)
                telnet.config_mode()
                swName = telnet.find_prompt()
                swName = swName[1:-1]
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi. Hostname: %s" %(switchIP,swName))
                
                # Konfigürasyonları uygula
                for configCommand in configList:
                    configCommandOutput = telnet.send_command_timing(configCommand)
                    # Komut ayrı bir prompt (sonu [Y/N] ile biten) gönderiyorsa cevap gönder
                    if re.search(r'\[Y/N\]', configCommandOutput):
                        configCommandOutput += telnet.send_command_timing("Y")
                    Logger.logCommandOutputs(pageName, configCommandOutput, switchIP)
                
                # "current-configuration'u" startup'a kaydet
                if args['wantToSaveConfig']:
                    saveConfigOutput = telnet.send_command_timing("save current-configuration")
                    if re.search(r'\[Y/N\]', saveConfigOutput):
                        saveConfigOutput += telnet.send_command_timing("Y")
                    Logger.logCommandOutputs(pageName, saveConfigOutput, switchIP)
                    Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
                
                telnet.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
        except:
            Logger.writeToLogfile(pageName, "HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)
        Logger.writeToLogfile(pageName, "BILGI: Islem tamamlandi.")