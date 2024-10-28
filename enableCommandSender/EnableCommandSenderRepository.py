from netmiko import ConnectHandler
from common.Logger import Logger
import re, os

class EnableCommandSenderRepository():
    def __init__(self) -> None:
        pass

    def cisco_sendEnableCommands(self, args: dict):
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'commandToExecute' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password' ve 'commandToExecute' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']
        commandToExecute = args['commandToExecute']
        if len(commandToExecute) <= 3:
            Logger.writeToLogfile(pageName, "HATA: Girilen komut hatali. Iptal ediliyor...")
            return
        if not os.path.isdir(f"./{pageName}commandOutputs"):
            os.mkdir(f"./{pageName}commandOutputs")

        try:
            try:
                ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                            'username': args['username'], 'password': args['password'],
                            'secret': args['password'], 'port': 22, }
                ssh = ConnectHandler(**ciscoSwitch)
                ssh.enable()
                swName = ssh.find_prompt()[:-1]
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)
                commandOutput = ssh.send_command(commandToExecute)
                Logger.logCommandOutputs(pageName, "%s: %s" %(swName,commandOutput), switchIP)
                ssh.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Komut calistirildi, switch (%s) baglantisi kapatildi." % switchIP)
            except:
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e telnet ile baglanti deneniyor." % switchIP)
                ciscoSwitch = {'device_type': 'cisco_ios_telnet', 'host': switchIP,
                        'username': args['username'], 'password': args['password'],
                        'secret': args['password'], 'port': 23, }
                telnet = ConnectHandler(**ciscoSwitch)
                telnet.enable()
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e telnet ile baglanildi." % switchIP)
                commandOutput = telnet.send_command(commandToExecute)
                Logger.logCommandOutputs(pageName, "%s: %s" %(swName,commandOutput), switchIP)
                telnet.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Komut calistirildi, switch (%s) baglantisi kapatildi." % switchIP)
        except Exception as e:
            Logger.writeToLogfile(pageName, f"HATA: Switch ({switchIP}) konfigure edilirken hata olustu. Exception {e}")

    def huawei_sendEnableCommand(self, args: dict):
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'commandToExecute' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password' ve 'commandToExecute' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']

        commandToExecute = args['commandToExecute']
        if len(commandToExecute) <= 3:
            Logger.writeToLogfile(pageName, "HATA: Girilen komut hatali. Iptal ediliyor...")
            return
        if not os.path.isdir(f"./{pageName}/commandOutputs"):
            os.mkdir(f"./{pageName}/commandOutputs")

        try:
            try:
                huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                            'username': args['username'], 'password': args['password'], 'port': 22, }
                ssh = ConnectHandler(**huaweiSwitch)
                ssh.config_mode()
                swName = ssh.find_prompt()[1:-1]
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)

                # Karşı tarafta komutu çalıştır
                commandOutput = ssh.send_command_timing(commandToExecute)
                if re.search(r'\[Y/N\]', commandOutput):
                    commandOutput += ssh.send_command_timing("Y")
                Logger.logCommandOutputs(pageName, "%s: %s" %(swName,commandOutput), switchIP)

                ssh.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Komut calistirildi, switch (%s) baglantisi kapatildi." % switchIP)
            except:
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e telnet ile baglanti deneniyor." % switchIP)
                huaweiSwitch = {'device_type': 'huawei_telnet', 'host': switchIP,
                        'username': args['username'], 'password': args['password'], 'port': 23, }
                telnet = ConnectHandler(**huaweiSwitch)
                telnet.config_mode()
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e telnet ile baglanildi." % switchIP)

                commandOutput = telnet.send_command_timing(commandToExecute)
                if re.search(r'\[Y/N\]', commandOutput):
                    commandOutput += telnet.send_command_timing("Y")
                Logger.logCommandOutputs(pageName, "%s: %s" %(swName,commandOutput), switchIP)

                telnet.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Komut calistirildi, switch (%s) baglantisi kapatildi." % switchIP)
        except Exception as e:
            Logger.writeToLogfile(pageName, f"HATA: Switch ({switchIP}) konfigure edilirken hata olustu. Exception {e}")
        Logger.writeToLogfile(pageName, "BILGI: Islem tamamlandi.")