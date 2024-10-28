from netmiko import ConnectHandler
import textfsm
from common.Logger import Logger

class InterfaceExplorerRepository:
    def __init__(self):
        pass

    def __pullLocationVlans(self, args: dict):
        try:
            # SSH ile baglanmayi dene
            ciscoSwitchSSH = {'device_type': 'cisco_ios', 'host': args['switchIP'],
                       'username': args['username'], 'password': args['password'],
                       'secret': args['password'], 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitchSSH)
            ssh.enable()
            shVlanOutput = ssh.send_command("show vlan", use_textfsm=True)
            # SSH baglantisini sonlandir
            ssh.disconnect()
        except:
            # SSH basarisiz olursa telnet ile baglanmayi dene
            ciscoSwitchTelnet = {'device_type': 'cisco_ios_telnet', 'host': args['switchIP'],
                        'username': args['username'], 'password': args['password'],
                        'secret': args['password'], 'port': 23, }
            telnet = ConnectHandler(**ciscoSwitchTelnet)
            telnet.enable()
            shVlanOutput = telnet.send_command("show vlan", use_textfsm=True)
            # SSH baglantisini sonlandir
            telnet.disconnect()

        return shVlanOutput
    
    def __pullLocationVlans_huawei(self, args: dict):
        templateBasePath = "./common/textfsmTemplates"
        
        try:
            # SSH ile baglanmayi dene
            huaweiSwitchSSH = {'device_type': 'huawei', 'host': args['switchIP'],
                       'username': args['username'], 'password': args['password'], 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitchSSH)
            ssh.config_mode()
            interfaceVlanOutput = ssh.send_command("display port vlan")
            nameVlanOutput = ssh.send_command("display vlan")
            # SSH baglantisini sonlandir
            ssh.disconnect()
        except:
            # SSH basarisiz olursa telnet ile baglanmayi dene
            ciscoSwitchTelnet = {'device_type': 'huawei_telnet', 'host': args['switchIP'],
                        'username': args['username'], 'password': args['password'], 'port': 23, }
            telnet = ConnectHandler(**ciscoSwitchTelnet)
            telnet.config_mode()
            interfaceVlanOutput = telnet.send_command("display port vlan")
            nameVlanOutput = telnet.send_command("display vlan")
            # Telnet baglantisini sonlandir
            telnet.disconnect()

        with open(f'{templateBasePath}/huaweiVlanTemplate.textfsm') as vlanTemplateFile:
            vlanOutputTemplate = textfsm.TextFSM(vlanTemplateFile)
            parsedVlanOutput = vlanOutputTemplate.ParseText(nameVlanOutput)
            vlanHeaders = vlanOutputTemplate.header
        with open(f'{templateBasePath}/huaweiVLANInterfaceTemplate.textfsm') as interfaceVLANTemplateFile:
            interfaceVlanTemplate = textfsm.TextFSM(interfaceVLANTemplateFile)
            parsedInterfaceVlanOutput = interfaceVlanTemplate.ParseText(interfaceVlanOutput)
            interfaceVlanHeaders = interfaceVlanTemplate.header

        # Port'ların hangi VLAN'lara ait olduğunu belirtir
        interfaceVLANDict = [dict(zip(interfaceVlanHeaders, row)) for row in parsedInterfaceVlanOutput] 

        # VLAN'ların isimlerini belirtir
        VLANDict = [dict(zip(vlanHeaders, row)) for row in parsedVlanOutput]

        # VLAN'ların isimlerini ve hangi portlara atandığını belirtir
        interfaceNameVlanDict = {}
        for vlanName in VLANDict:
            interfaceNameVlanDict.update({
                vlanName["VID"]: {"name": vlanName["Description"], "ports": ""}
            })
        interfaceNameVlanDict["0"] = {"name": "Default trunk vlan??", "ports": ""}
        for vlanPort in interfaceVLANDict:  
            interfaceNameVlanDict[vlanPort["PVID"]]["ports"] += f"{vlanPort['Port']},"

        return interfaceNameVlanDict
    
    def huawei_prepareWorksheet(self, args: dict):
        pageName = args['pageName']
        VLANDict = self.__pullLocationVlans_huawei(args)
        columnNumber = 1
        excludedVlans = ["1002","1003","1004","1005"]

        locationVlanList = []

        for vlanID in VLANDict.keys():
            if vlanID not in excludedVlans:
                columnName = "%s (%s)" %(vlanID, VLANDict[vlanID]['name'])
                args['worksheet'].write(0, columnNumber, columnName)
                args['vlanLocations'].update({
                    vlanID: columnNumber
                })
                columnNumber += 1
                Logger.writeToLogfile(pageName, "Vlan ID: %s, Vlan Name: %s" %(vlanID, VLANDict[vlanID]['name'].strip()))
                locationVlanList.append(vlanID)
    
    def cisco_prepareWorksheet(self, args: dict):
        pageName = args['pageName']
        shVlanOutput = self.__pullLocationVlans(args)
        excludedVlans = ["1002","1003","1004","1005"]
        columnNumber = 1

        Logger.writeToLogfile(pageName, "Lokasyon vlan bilgileri")
        for item in shVlanOutput:
            if item['vlan_id'] not in excludedVlans:
                columnName = "%s (%s)" %(item['vlan_name'], item['vlan_id'])
                args['worksheet'].write(0, columnNumber, columnName)
                args['vlanLocations'].update({
                    item['vlan_id']: columnNumber
                })
                columnNumber += 1
                Logger.writeToLogfile(pageName, "Vlan ID: %s, Vlan Name: %s" %(item['vlan_id'], item['vlan_name']))

    def cisco_interfaceExplorer(self, args: dict):
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

        switchIP = args['switchIP']
        rowNumber = args['row']
        pageName = args['pageName']
        shVlanOutput = self.__pullLocationVlans(args)
        excludedVlans = ["1002","1003","1004","1005"]

        locationVlanList = []
        for item in shVlanOutput:
            locationVlanList.append(item['vlan_id'])

        try:
            try:
                # Switch'e ssh ile baglan
                ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                                'username': args['username'], 'password': args['password'],
                                'secret': args['password'], 'port': 22, }
                ssh = ConnectHandler(**ciscoSwitch)
                ssh.enable()
                swName = ssh.find_prompt()[:-1]
                swRowName = "%s_%s" %(swName, switchIP)
                # Switch adini ilk sutuna yaz
                args['worksheet'].write(rowNumber, 0, swRowName)
                Logger.writeToLogfile(pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))
                # Komutu calistir
                shVlanOutput = ssh.send_command("show vlan", use_textfsm=True)
                # Komut ciktisindaki bilgileri Excel'e tasi
                for item in shVlanOutput:
                    if item['vlan_id'] not in excludedVlans and item['vlan_id'] in args['vlanLocations'].keys():
                        columnNumber = args['vlanLocations'][item['vlan_id']]
                        interfaceInfo = str(item["interfaces"]).replace("[","").replace("]","")
                        args['worksheet'].write(rowNumber, columnNumber, interfaceInfo)
                # SSH baglantisini sonlandir
                ssh.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: SSH ile switch vlan bilgileri alindi ve Excel'e islendi.")
            except:
                # SSH hata verirse switch'e telnet ile baglan
                ciscoSwitch = {'device_type': 'cisco_ios_telnet', 'host': switchIP,
                                'username': args['username'], 'password': args['password'],
                                'secret': args['password'], 'port': 23, }
                telnet = ConnectHandler(**ciscoSwitch)
                telnet.enable()
                swName = telnet.find_prompt()[:-1]
                swRowName = "%s_%s" %(swName, switchIP)
                # Switch adini ilk sutuna yaz
                args['worksheet'].write(rowNumber, 0, swRowName)
                Logger.writeToLogfile(pageName, "BILGI: Switch'e telnet ile baglanildi. %s %s" %(swName, switchIP))
                # Komutu calistir
                shVlanOutput = telnet.send_command("show vlan", use_textfsm=True)
                # Komut ciktisindaki bilgileri Excel'e tasi
                for item in shVlanOutput:
                    if item['vlan_id'] not in excludedVlans and item['vlan_id'] in args['vlanLocations'].keys():
                        columnNumber = args['vlanLocations'][item['vlan_id']]
                        interfaceInfo = str(item["interfaces"]).replace("[","").replace("]","")
                        args['worksheet'].write(rowNumber, columnNumber, interfaceInfo)
                # telnet baglantisini sonlandir
                telnet.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Telnet ile switch vlan bilgileri alindi ve Excel'e islendi.")
        except:
            Logger.writeToLogfile(pageName, "HATA: Switch vlan bilgileri islenirken hata olustu.")
        args['row'] += 1
        Logger.writeToLogfile(pageName, "BILGI: Islem tamamlandi.")

    def huawei_interfaceExplorer(self, args: dict):
        try:
            assert \
                'pageName' in args and \
                'switchIP' in args and \
                'username' in args and \
                'password' in args and \
                'row' in args and \
                'worksheet' in args and \
                'workbook' in args and \
                'vlanLocations' in args
        except AssertionError:
            Logger.writeToLogfile(pageName, f"""HATA: Eksik girdi: {list(args.keys())}; 
                girdi 'pageName', 'switchIP', 'username', 'password', 'row', 'worksheet' ve 'workbook' alanlarini icermeli.""")
            return

        pageName = args['pageName']
        switchIP = args['switchIP']
        rowNumber = args['row']
        interfaceNameVlanDict = self.__pullLocationVlans_huawei(args)
        excludedVlans = ["1002","1003","1004","1005"]

        locationVlanList = []
        Logger.writeToLogfile(pageName, "Lokasyon vlan bilgileri")

        for vlanID in interfaceNameVlanDict.keys():
            locationVlanList.append(vlanID)

        try:
            try:
                # Switch'e ssh ile baglan
                huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                                'username': args['username'], 'password': args['password'], 'port': 22, }
                ssh = ConnectHandler(**huaweiSwitch)
                ssh.config_mode()
                swName = ssh.find_prompt()[1:-1]
                swRowName = "%s_%s" %(swName, switchIP)
                # Switch adini ilk sutuna yaz
                args['worksheet'].write(rowNumber, 0, swRowName)
                Logger.writeToLogfile(pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))
                # Komut ciktisindaki bilgileri Excel'e tasi
                for vlanNumber in interfaceNameVlanDict.keys():
                    if vlanNumber not in excludedVlans and vlanNumber in args['vlanLocations'].keys():
                        columnNumber = args['vlanLocations'][vlanNumber]
                        interfaceInfo = interfaceNameVlanDict[vlanNumber]['ports']
                        args['worksheet'].write(rowNumber, columnNumber, interfaceInfo)
                # SSH baglantisini sonlandir
                ssh.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: SSH ile switch vlan bilgileri alindi ve Excel'e islendi.")
            except:
                # SSH hata verirse switch'e telnet ile baglan
                huaweiSwitch = {'device_type': 'huawei_telnet', 'host': switchIP,
                                'username': args['username'], 'password': args['password'], 'port': 23, }
                telnet = ConnectHandler(**huaweiSwitch)
                telnet.config_mode()
                swName = telnet.find_prompt()[1:-1]
                swRowName = "%s_%s" %(swName, switchIP)
                # Switch adini ilk sutuna yaz
                args['worksheet'].write(rowNumber, 0, swRowName)
                Logger.writeToLogfile(pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))
                # Komut ciktisindaki bilgileri Excel'e tasi
                for vlanNumber in interfaceNameVlanDict.keys():
                    if vlanNumber not in excludedVlans and vlanNumber in args['vlanLocations'].keys():
                        columnNumber = locationVlanList.index(vlanNumber) + 1
                        interfaceInfo = interfaceNameVlanDict[vlanNumber]['ports']
                        args['worksheet'].write(rowNumber, columnNumber, interfaceInfo)
                # telnet baglantisini sonlandir
                telnet.disconnect()
                Logger.writeToLogfile(pageName, "BILGI: Telnet ile switch vlan bilgileri alindi ve Excel'e islendi.")
        except:
            Logger.writeToLogfile(pageName, "HATA: Switch vlan bilgileri islenirken hata olustu.")
        args['row'] += 1
        Logger.writeToLogfile(pageName, "BILGI: Islem tamamlandi.")

