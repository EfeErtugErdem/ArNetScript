from netmiko import ConnectHandler
from paramiko import SSHClient, AutoAddPolicy
import re
import os
from common.Logger import Logger

class ConfigSenderRepository:
    """Verilen cihaza konfigürasyon göndermeye yarayan sinif.

    Cihazlara kullanicilarin istediği konfgürasyonlar girilebilir, 
    ayrica cihazlara banner yüklemek için de kullanilabilir. 

    Attributes
    ----------
    Yok
    
    Methods
    -------
    cisco_sendConfigurations(args: dict) -> None:\n
        Cisco marka cihazlara konfigurasyonlarini uygular.\n
    huawei_sendConfigurations(args: dict) -> None:\n
        Huawei marka cihazlara konfigurasyonlarini uygular.
    cisco_sendConfigurationsMulti(args: dict) -> None:\n
        Cisco marka cihazlara konfigurasyonlari uygular. 
        Farkli cihazlara farkli konfigurasyonlar uygulanabilir.
    huawei_sendConfigurationsMulti(args: dict) -> None:\n
        Huawei marka cihazlara konfigurasyonlari uygular. 
        Farkli cihazlara farkli konfigurasyonlar uygulanabilir.
    """

    arcelikBanner = ["""
    banner login ^CC
    ############################################################################
    #                      .++          _    ____   ____ _____ _     ___ _  __ #
    #                    -*%%%-        / \  |  _ \ / ___| ____| |   |_ _| |/ / #
    #                .-+#%%%%%#.      / _ \ | |_) | |   |  _| | |    | || ' /  #
    #            .:=*%%%%%%%%%%*     / ___ \|  _ <| |___| |___| |___ | || . \  #
    #      .:-=*#%%%%%%%%%%%%%%%=   /_/   \_\_| \_\\\____|_____|_____|___|_|\_\ #
    # =##%%%%%%%%%%%%%%%%%%%%%%%%:                                             #
    # .#%%%%%%%%%%%%%%%%%%%%%%%%%#   Yetkisiz erisim yasaktir. Yapilan tum     #
    #  -%%%%%%%%%%%%%%%%%%%%%%%%%%*  islemler veya denemeler kayitlanmaktadir. #
    #   *%%%%%%%%%%%%%%%%%%%%%%%%%%-                                           #
    #   .%%%%%%%%%%%%%%%%%%%%%%%%#-  Unauthorized access is forbidden.         #
    #    -%%%%%%%%%%%%%%%%%%%%%#+:   All actions taken or trials done on this  #
    #     *%%%%%%%%%%%%%%%%%#+:      device are logged.                        #
    #     .#%%%%%%%%%%%%#+=.                                                   #
    #      -%%%%%%%%%%+-:.           Email: SYND_ORG_00101026@arcelik.com      #
    #        \%%%**                                                            #
    ############################################################################
    ^C
    !
    """]

    bekoBanner = ["""
    banner login ^CC
    ##################################################################
    #                                                                #
    #  *****                          *****                          #
    #  *****                          *****                          #
    #  **********::       .:*****:.   *****   :****:   .:*****:.     #
    #  **************   .***********  *****  ******  ************:   #
    #  *****:    *****  ****    .**** ***** *****.  *****    :****:  #
    #  *****     .****:**************.*********:   .****.     *****  #
    #  *****     .****:************** **********   :****.     *****  #
    #  :****:    ***** .****.         ***** :****:  *****    .****:  #
    #   :************   .***********  *****  .*****. ************.   #
    #     .:*****::       .:*******:  :***:    :****:  :******:.     #
    #                                                          ..    #
    #                                            ...::::*********    #
    #                              ...:::************************    #
    #                ...:::****************************:::....       #
    #  ...:::****************************:::...                      #
    #  ********************:::...                                    #
    #  ******:::...                                                  #
    #                                                                #
    # Yetkisiz erisim yasaktir. Yapilan tum islemler veya denemeler  #
    # kayit altina alinmaktadir.                                     #
    #                                                                #
    # Unauthorized access is forbidden. All actions taken or trials  #
    # done on this device are logged.                                #
    #                                                                #
    # Email: SYND_ORG_00101026@arcelik.com                           #
    #                                                                #
    ##################################################################
    ^C
    !
    """]

    defyBanner = ["""
    banner login ^CC
    ##########################################################################
    #                                                                        #
    #          .##################################################.          #
    #        ########################################################        #
    #      #####                                                  #####      #
    #     ####    ########.    #########  #########  ###     ###    ####     #
    #    ####     ##########   ###        ###         ###   ###      ####    #
    #   ####      ###     ###  ###        ###          ###-###        ####   #
    #  :####      ###      ##: #########  #########      ###          ####:  #
    #   ####      ###     ###  ###        ###            ###          ####   #
    #    ####     ##########   ###        ###            ###         ####    #
    #     ####    ########'    #########  ###            ###        ####     #
    #      #####                                                  #####      #
    #        ########################################################        #
    #          '##################################################'          #
    #                                                                        #
    #  Yetkisiz erisim yasaktir. Yapilan tum islemler veya denemeler kayit   #
    #  altina alinmaktadir.                                                  #
    #                                                                        #
    #  Unauthorized access is forbidden. All actions taken or trials done    #
    #  on this device are logged.                                            #
    #                                                                        #
    #  Email: SYND_ORG_00101026@arcelik.com                                  #
    #                                                                        #
    ##########################################################################
    ^C
    !
    """]


    ihpaBanner = ["""
    banner login ^CC
    ###################################################################
    #                                                                 #
    #         ######  ######         ######  ############.            #
    #         ######  ######         ######  ##############   .       #
    #         ######  ######         ######  #####       ###  #.      #
    #         ######  ######         ######  #####       .#.  ##.     #
    #         ######  ######         ######  #####       .   .##.     #
    #         ######  #####################  #####          .###      #
    #         ######  #####################  #####        .####       #
    #         ######  ######         ######  #################        #
    #         ######  ######         ######  #############*'          #
    #         ######  ######         ######  #####                    #
    #         ######  ######         ######  #####                    #
    #         ######  ######         ######  #####                    #
    #                                                                 #
    #     _    ____  ____  _     ___    _    _   _  ____ _____ ____   #
    #    / \  |  _ \|  _ \| |   |_ _|  / \  | \ | |/ ___| ____/ ___|  #
    #   / _ \ | |_) | |_) | |    | |  / _ \ |  \| | |   |  _| \___ \  #
    #  / ___ \|  __/|  __/| |___ | | / ___ \| |\  | |___| |___ ___) | #
    # /_/   \_\_|   |_|   |_____|___/_/   \_\_| \_|\____|_____|____/  #
    #                                                                 #
    #   Yetkisiz erisim yasaktir. Yapilan tum islemler veya denemeler #
    # kayit altina alinmaktadir.                                      #
    #                                                                 #
    #   Unauthorized access is forbidden. All actions taken or trials #
    # done on this device are logged.                                 #
    #                                                                 #
    #   Email: SYND_ORG_00101026@arcelik.com                          #
    #                                                                 #
    ###################################################################
    ^C
    """]

    arcticBanner = ["""
    banner login ^CC
    ############################################################################
    #                                                                          #
    #                                           %%%%                           #
    #                                           %%%%                           #
    #      .:%%%%%%%:.  .%%%%%%%%   .%%%%%%%%%  %%%%%%%%. %%%%   .%%%%%%%%%    #
    #    .%%%%%%%%%%%%  %%%%       %%%%'        %%%%      %%%%  %%%%'          #
    #   :%%%'     %%%%  %%%%       %%%%         %%%%      %%%%  %%%%           #
    #   :%%%      %%%%  %%%%       %%%%         %%%%      %%%%  %%%%           #
    #   .%%%.     %%%%  %%%%       %%%%.        .%%%.     %%%%  %%%%.          #
    #    .%%%%%%  %%%%  %%%%        .%%%%%%%%%   '%%%%%%  %%%%   .%%%%%%%%%    #
    #                                                                          #
    # Yetkisiz erisim yasaktir. Yapilan tum islemler veya denemeler kayit      #
    # altina alinmaktadir.                                                     #
    #                                                                          #
    # Unauthorized access is forbidden. All actions taken or trials done on    #
    # this device are logged.                                                  #
    #                                                                          #
    # Email: SYND_ORG_00101026@arcelik.com                                     #
    #                                                                          #
    ############################################################################
    ^C
    """]

    def __init__(self) -> None:
        pass

    def __readConfig(self, pageName, fileName):
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

    def cisco_sendConfigurations(self, args: dict):
        """ Cisco IOS kullanan cihazlara konfigürasyonlarini uygular ve banner yukler.
        Parameters
        ----------
        args: dict
            Metoda verilen paramerelerin bulunduğu dictionary.\n
            "args" ASAGIDAKI ALANLARI ICERMELI:
        - pageName: str
            Sinifin bulunduğu klasörün adi. Özel bir ad olmali.
        - switchIP: str
            Konfigurasyonlarin uygulandigi cihazin IP adresi.
        - selectedBanner: str
            Cihaza hangi banner yuklenecek.
        - bannerSelection: bool
            Cihaza banner yuklenmek isteniyor mu.
        - username: str
            Cihaza konfigurasyon uygulamak için gereken kullanici adi.
        - password: str
            Cihaza konfigurasyon uygulamak için gereken parola.
        - wantToSaveConfig: bool
            Konfigürasyonlar uygulandiktan sonra cihaza kaydedilecek mi?
        """
        try:
            'switchIP' in args and \
            'pageName' in args and \
            'selectedBanner' in args and \
            'bannerSelection' in args and \
            'username' in args and \
            'password' in args and \
            'wantToSaveConfig' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'wantToSaveConfig', 'selectedBanner' ve 'bannerSelection' alanlarini icermeli.""")
            return

        switchIP = args['switchIP']
        pageName = args['pageName']

        # Komutların çıktılarının depolandığı alt klasör
        if not os.path.isdir(f"./{pageName}commandOutputs"):
            os.mkdir(f"./{pageName}commandOutputs")

        # Yüklenecek banner
        match args['selectedBanner']:
            case "Arçelik":
                activeBanner = self.arcelikBanner
            case "Beko":
                activeBanner = self.bekoBanner
            case "Defy":
                activeBanner = self.defyBanner
            case "IHP":
                activeBanner = self.ihpaBanner
            case "Arctic":
                activeBanner = self.arcticBanner
            case _:
                activeBanner = None
        
        # Uygulanacak konfigürasyonlar
        configList = self.__readConfig(pageName, "configFile_cisco.txt")

        try:
            ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                        'username': args['username'], 'password': args['password'],
                        'secret': args['password'], 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitch)
            ssh.enable()
            Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)
            Logger.logCommandOutputs(pageName, ssh.send_config_set(configList), switchIP)
            
            # Banner yüklenecek mi
            if args['bannerSelection']:
                Logger.logCommandOutputs(pageName, ssh.send_config_set(activeBanner, cmd_verify=False), switchIP)
            Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon listesi uygulandi.")
            
            # Konfigürasyonlar cihaza kaydedilecek mi
            if args['wantToSaveConfig']:
                Logger.logCommandOutputs(pageName, ssh.send_command("write"), switchIP)
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
            
            ssh.disconnect()
            Logger.writeToLogfile(pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
        except:
            Logger.writeToLogfile(pageName, "HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)

    def huawei_sendConfigurations(self, args: dict):
        """ Huawei cihazlara konfigürasyonlarini uygular ve banner yukler.
        Parameters
        ----------
        args: dict
            Metoda verilen paramerelerin bulunduğu dictionary.\n
            "args" ASAGIDAKI ALANLARI ICERMELI:
        - pageName: str
            Sinifin bulunduğu klasörün adi. Özel bir ad olmali.
        - switchIP: str
            Konfigurasyonlarin uygulandigi cihazin IP adresi.
        - selectedBanner: str
            Cihaza hangi banner yuklenecek.
        - bannerSelection: bool
            Cihaza banner yuklenmek isteniyor mu.
        - username: str
            Cihaza konfigurasyon uygulamak için gereken kullanici adi.
        - password: str
            Cihaza konfigurasyon uygulamak için gereken parola.
        - wantToSaveConfig: bool
            Konfigürasyonlar uygulandiktan sonra cihaza kaydedilecek mi?
        """
        try:
            'switchIP' in args and \
            'pageName' in args and \
            'selectedBanner' in args and \
            'bannerSelection' in args and \
            'username' in args and \
            'password' in args and \
            'wantToSaveConfig' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'wantToSaveConfig', 'selectedBanner' ve 'bannerSelection' alanlarini icermeli.""")
            return

        switchIP = args['switchIP']
        pageName = args['pageName']

        # Komutların çıktılarının depolandığı alt klasör
        if not os.path.isdir(f"./{pageName}commandOutputs"):
            os.mkdir(f"./{pageName}commandOutputs")

        # Yüklenecek banner
        match args['selectedBanner']:
            case "Arçelik":
                activeBanner = f"./{pageName}banners/arcelikBanner.txt"
            case "Beko":
                activeBanner = f"./{pageName}banners/bekoBanner.txt"
            case "Defy":
                activeBanner = f"./{pageName}banners/defyBanner.txt"
            case "IHP":
                activeBanner = f"./{pageName}banners/ihpaBanner.txt"
            case "Arctic":
                activeBanner = f"./{pageName}banners/arcticBanner.txt"
            case _:
                activeBanner = None
        
        # Uygulanacak konfigürasyonlar
        configList =self.__readConfig(pageName, "configFile_huawei.txt")
        
        try:
            huaweiSwitch = {'device_type': 'huawei', 'host': args['switchIP'],
                        'username': args['username'], 'password': args['password'], 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitch)
            ssh.config_mode()
            Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)

            # Konfigürasyon komutlarını gönder
            for configCommand in configList:
                configCommandOutput = ssh.send_command_timing(configCommand)
                # Komut ayrı bir prompt (sonu [Y/N] ile biten) gönderiyorsa cevap gönder
                if re.search(r'\[Y/N\]', configCommandOutput):
                    configCommandOutput += ssh.send_command_timing("Y")
                Logger.logCommandOutputs(pageName, configCommandOutput, switchIP)

            if args['bannerSelection']:
                destinationPath = "banner.txt"
                
                # Banner dosyasını göndermek için ssh client hazırla
                sshClient = SSHClient()
                sshClient.set_missing_host_key_policy(AutoAddPolicy())
                sshClient.connect(hostname=switchIP, username=args['username'], password=args['password'], port=22)

                # SFTP client ile dosyayı gönder
                sftpClient = sshClient.open_sftp()
                sendBannerFileOutput = sftpClient.put(activeBanner, destinationPath)
                Logger.logCommandOutputs(pageName, sendBannerFileOutput, switchIP)

                # Gönderilen banner dosyasını switch'in banner'ı olarak ayarla
                setActiveBannerOutput = ssh.send_command_timing(f"header login file flash:/{destinationPath}")
                if re.search(r'\[Y/N\]', setActiveBannerOutput):
                    setActiveBannerOutput += ssh.send_command_timing("Y")
                Logger.logCommandOutputs(pageName, setActiveBannerOutput, switchIP)
                Logger.writeToLogfile(pageName, "Banner dosyasi gonderildi.")

                sshClient.close()
            Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon listesi uygulandi.")
            
            # Konfigürasyonlar cihaza kaydedilecek mi
            if args['wantToSaveConfig']:
                saveConfigOutput = ssh.send_command_timing("save current-configuration")
                if re.search(r'\[Y/N\]', saveConfigOutput):
                    saveConfigOutput += ssh.send_command_timing("Y")
                Logger.logCommandOutputs(pageName, saveConfigOutput, switchIP)
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
            ssh.disconnect()
            Logger.writeToLogfile(pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
        except Exception as e:
            Logger.writeToLogfile(pageName, f"HATA: Switch (%s) konfigure edilirken hata olustu. {e}" % switchIP)
        Logger.writeToLogfile(pageName, "BILGI: Islem tamamlandi.")

    def cisco_sendConfigurationsMulti(self, args: dict):
        """ Cisco IOS kullanan cihazlara konfigürasyonlarini uygular ve banner yukler.
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
        - configurations: str
            Verilen IP adresindeki cihazlara yüklenecek konfigurasyonlar. 
        """
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'wantToSaveConfig' in args and \
                'configurations' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'wantToSaveConfig' ve 'configurations' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']

        # Komut çıktılarının depolandığı alt klasör
        if not os.path.isdir(f"./{pageName}commandOutputs"):
            os.mkdir(f"./{pageName}commandOutputs")

        try:
            ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                        'username': args['username'], 'password': args['password'],
                        'secret': args['password'], 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitch)
            ssh.enable()
            Logger.writeToLogfile(pageName,"BILGI: %s IP adresli switch'e baglanildi." % switchIP)
            
            # Cihaza uygulanacak konfigurasyonlar
            configList = args['configurations']

            # Konfigurasyonlari cihaza gonder
            Logger.logCommandOutputs(pageName,ssh.send_config_set(configList), switchIP)
            Logger.writeToLogfile(pageName,"BILGI: Konfigurasyon listesi uygulandi.")

            # Konfigürasyonlar cihaza kaydedilecek mi
            if args['wantToSaveConfig']:
                Logger.logCommandOutputs(pageName,ssh.send_command("write"), switchIP)
                Logger.writeToLogfile(pageName,"BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
            ssh.disconnect()
            Logger.writeToLogfile(pageName,"BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
        except:
            Logger.writeToLogfile(pageName,"HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)

    def huawei_sendConfigurationsMulti(self, args: dict):
        """ Huawei cihazlara konfigurasyonlarini uygular ve banner yukler.
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
        - configurations: str
            Verilen IP adresindeki cihazlara yüklenecek konfigurasyonlar. 
        """
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'wantToSaveConfig' in args and \
                'configurations' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'wantToSaveConfig' ve 'configurations' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']

        try:
            huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                        'username': args['username'], 'password': args['password'], 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitch)
            ssh.enable()
            Logger.writeToLogfile(pageName,"BILGI: %s IP adresli switch'e baglanildi." % switchIP)

            # Cihaza uygulanacak konfigurasyonlar
            configList = args['configurations']

            # Konfigurasyonlari cihaza gonder
            for configurationCommand in configList:
                configOutput = ssh.send_command_timing(configurationCommand)
                if re.search(r'\[Y/N\]', configOutput):
                    configOutput += ssh.send_command_timing("Y")
                Logger.logCommandOutputs(pageName, configOutput, switchIP)
            Logger.writeToLogfile(pageName,"BILGI: Konfigurasyon listesi uygulandi.")

            # Konfigürasyonlar cihaza kaydedilecek mi
            if args['wantToSaveConfig']:
                saveConfigOutput = ssh.send_command_timing("save current-configuration")
                if re.search(r'\[Y/N\]', saveConfigOutput):
                    saveConfigOutput += ssh.send_command_timing("Y")
                Logger.logCommandOutputs(pageName, saveConfigOutput, switchIP)
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
            ssh.disconnect()
            Logger.writeToLogfile(pageName,"BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
        except:
            Logger.writeToLogfile(pageName,"HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)
