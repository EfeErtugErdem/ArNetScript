from netmiko import ConnectHandler
import textfsm
from common.Logger import Logger
import traceback
import re

class InventoryCreatorRepository():
    def __init__(self) -> None:
        pass

    def cisco_inventoryCreator(self, args: dict):
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'row' in args and \
                'worksheet' in args and\
                'workbook' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'row', 'worksheet' ve 'workbook' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']
        rowNumber = args['row']

        try:
            try:
                ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                            'username': args['username'], 'password': args['password'],
                            'secret': args['password'], 'port': 22, }
                ssh = ConnectHandler(**ciscoSwitch)
                ssh.enable()
                swName = ssh.find_prompt()[:-1]
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e (%s) SSH ile baglanildi." % (switchIP, swName))
                commandOutput = ssh.send_command("sh inventory | inc SN:")
                commandOutputWithoutSpaces = commandOutput.replace(" ","")
                swInventoryList = commandOutputWithoutSpaces.splitlines()

                print(swInventoryList)

                for item in swInventoryList:
                    if "SN:" in item:
                        args['worksheet'].write(rowNumber, 0, item[item.find("SN:")+3:])
                        args['worksheet'].write(rowNumber, 1, item[(item.find("PID:")+4):(item.find(","))])
                        args['worksheet'].write(rowNumber, 2, swName)
                        args['worksheet'].write(rowNumber, 3, switchIP)
                        rowNumber+=1
                Logger.writeToLogfile(pageName, "BILGI: Switch envanter bilgisi alindi.")
                ssh.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Switch %s (%s) baglantisi kapatildi." % (switchIP, swName))
            except:
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e (%s) telnet ile baglanti deneniyor." % (switchIP, swName))
                ciscoSwitch = {'device_type': 'cisco_ios_telnet', 'host': switchIP,
                            'username': args['username'], 'password': args['password'],
                            'secret': args['password'], 'port': 23, }
                telnet = ConnectHandler(**ciscoSwitch)
                telnet.enable()
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e (%s) telnet ile baglanildi." % (switchIP, swName))
                commandOutput = telnet.send_command("sh inventory | inc SN:")
                commandOutputWithoutSpaces = commandOutput.replace(" ","")
                swInventoryList = commandOutputWithoutSpaces.splitlines()
                for item in swInventoryList:
                    if "SN:" in item:
                        args['worksheet'].write(rowNumber, 0, item[item.find("SN:")+3:])
                        args['worksheet'].write(rowNumber, 1, item[(item.find("PID:")+4):(item.find(","))])
                        args['worksheet'].write(rowNumber, 2, swName)
                        args['worksheet'].write(rowNumber, 3, switchIP)
                        rowNumber+=1
                Logger.writeToLogfile(pageName, "BILGI: Switch envanter bilgisi alindi.")
                telnet.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Switch %s (%s) baglantisi kapatildi." % (switchIP, swName))
        except:
            Logger.writeToLogfile(pageName, "HATA: Switch (%s) envanter bilgisi alinirken hata olustu." % switchIP)
        args['row'] = rowNumber
        Logger.writeToLogfile(pageName, "BILGI: Islem tamamlandi.")

    def huawei_inventoryCreator(self, args: dict):
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'row' in args and \
                'worksheet' in args and\
                'workbook' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'row', 'worksheet' ve 'workbook' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']
        rowNumber = args['row']

        try:
            # Try connecting with SSH
            try:
                huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                            'username': args['username'], 'password': args['password'], 'port': 22, }
                ssh = ConnectHandler(**huaweiSwitch)
                ssh.config_mode()
                swName = ssh.find_prompt()[1:-1]
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e (%s) SSH ile baglanildi." % (switchIP, swName))

                deviceOutput = ssh.send_command("display device")

                with open("./common/textfsmTemplates/huaweiDeviceInfoTemplate.textfsm") as deviceInfoTemplateFile:
                    deviceInfoTemplate = textfsm.TextFSM(deviceInfoTemplateFile)
                    parsedDeviceOutput = deviceInfoTemplate.ParseText(deviceOutput)
                    deviceHeaders = deviceInfoTemplate.header
                deviceDict = [dict(zip(deviceHeaders, row)) for row in parsedDeviceOutput]

                if "Primary" in deviceOutput:
                    manufactureOutput = ssh.send_command("display device esn")
                    manufactureDict = []
                    pattern = r'^ESN\sof\sslot\s([0-9]+):\s([0-9]+)$'

                    manufactureOutputLines = manufactureOutput.strip().splitlines()
                    for line in manufactureOutputLines:
                        slotNumber = re.findall(pattern, line)[0]
                        esnNumber = re.findall(pattern, line)[1]
                        manufactureDict.append({
                            "Slot": slotNumber,
                            "Serial_number": esnNumber
                        })
                else:
                    manufactureOutput = ssh.send_command("display device manufacture-info")
                    with open("./common/textfsmTemplates/huaweiManufactureInfoTemplate.textfsm") as manufactureInfoTemplateFile:
                        manufactureInfoTemplate = textfsm.TextFSM(manufactureInfoTemplateFile)
                        parsedOutput = manufactureInfoTemplate.ParseText(manufactureOutput)
                        manufactureHeaders = manufactureInfoTemplate.header
                    manufactureDict = [dict(zip(manufactureHeaders, row)) for row in parsedOutput]

                keysList = ["Slot", "Serial_number", "Type"]
                swInventoryList = []
                for i in range(0, min(len(manufactureDict), len(deviceDict))):
                    mergedDict = {key: (manufactureDict[i] | deviceDict[i])[key] for key in keysList}
                    swInventoryList.append(mergedDict)

                for item in swInventoryList:
                    if "Serial_number" in item.keys():
                        args['worksheet'].write(rowNumber, 0, item["Serial_number"])
                        args['worksheet'].write(rowNumber, 1, item["Type"])
                        args['worksheet'].write(rowNumber, 2, swName)
                        args['worksheet'].write(rowNumber, 3, switchIP)
                        rowNumber+=1
                Logger.writeToLogfile(pageName, "BILGI: Switch envanter bilgisi alindi.")
                ssh.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Switch %s (%s) baglantisi kapatildi." % (switchIP, swName))
            # Try connection with Telnet
            except Exception as e:
                print(traceback.extract_tb())
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e (%s) telnet ile baglanti deneniyor." % (switchIP, swName))
                huaweiSwitch = {'device_type': 'huawei_telnet', 'host': switchIP,
                        'username': args['username'], 'password': args['password'], 'port': 23, }
                telnet = ConnectHandler(**huaweiSwitch)
                telnet.config_mode()
                swName = telnet.find_prompt()[1:-1]
                Logger.writeToLogfile(pageName, "BILGI: %s IP adresli switch'e (%s) telnet ile baglanildi." % (switchIP, swName))

                deviceOutput = telnet.send_command("display device")

                with open("./common/textfsmTemplates/huaweiDeviceInfoTemplate.textfsm") as deviceInfoTemplateFile:
                    deviceInfoTemplate = textfsm.TextFSM(deviceInfoTemplateFile)
                    parsedDeviceOutput = deviceInfoTemplate.ParseText(deviceOutput)
                    deviceHeaders = deviceInfoTemplate.header
                deviceDict = [dict(zip(deviceHeaders, row)) for row in parsedDeviceOutput]

                if "Primary" in deviceOutput:
                    manufactureOutput = telnet.send_command("display device esn")
                    manufactureDict = []
                    pattern = r'^ESN\sof\sslot\s([0-9]+):\s([0-9]+)$'

                    manufactureOutputLines = manufactureOutput.strip().splitlines()
                    for line in manufactureOutputLines:
                        slotNumber = re.findall(pattern, line)[0]
                        esnNumber = re.findall(pattern, line)[1]
                        manufactureDict.append({
                            "Slot": slotNumber,
                            "Serial_number": esnNumber
                        })
                else:
                    manufactureOutput = telnet.send_command("display device manufacture-info")
                    with open("./common/textfsmTemplates/huaweiManufactureInfoTemplate.textfsm") as manufactureInfoTemplateFile:
                        manufactureInfoTemplate = textfsm.TextFSM(manufactureInfoTemplateFile)
                        parsedOutput = manufactureInfoTemplate.ParseText(manufactureOutput)
                        manufactureHeaders = manufactureInfoTemplate.header
                    manufactureDict = [dict(zip(manufactureHeaders, row)) for row in parsedOutput] 

                keysList = ["Slot", "Serial_number", "Type"]
                swInventoryList = []
                for i in range(0, min(len(manufactureDict), len(deviceDict))):
                    mergedDict = {key: (manufactureDict[i] | deviceDict[i])[key] for key in keysList}
                    swInventoryList.append(mergedDict)
                
                for item in swInventoryList:
                    if "Serial_number" in item:
                        args['worksheet'].write(rowNumber, 0, item["Serial_number"])
                        args['worksheet'].write(rowNumber, 1, item["Type"])
                        args['worksheet'].write(rowNumber, 2, swName)
                        args['worksheet'].write(rowNumber, 3, switchIP)
                        rowNumber+=1
                Logger.writeToLogfile(pageName, "BILGI: Switch envanter bilgisi alindi.")
                telnet.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Switch %s (%s) baglantisi kapatildi." % (switchIP, swName))
        except Exception as e:
            Logger.writeToLogfile(pageName, f"HATA: Switch ({switchIP}) envanter bilgisi alinirken hata olustu. {traceback.extract_tb()}")
        try:
            args['row'] = rowNumber
            Logger.writeToLogfile(pageName, "BILGI: Excel dosyasi olusturuldu.")
        except:
            Logger.writeToLogfile(pageName, "HATA: Excel dosyasi kaydedilirken hata olustu.")