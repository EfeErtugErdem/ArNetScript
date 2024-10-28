from netmiko import ConnectHandler
from common.Logger import Logger
import re
import textfsm

class Dot1xWizardRepository:
    def __init__(self) -> None:
        pass

    def __getAllInterfaces(self, pageName, intStatusOutput):
        """sh int status ciktisina gore interface listesi olusturup return eder."""
        try:
            # Listeyi olustur
            intList = []

            for interface in intStatusOutput:
                portInfo = interface['port'].replace(" ","")
                intList.append(portInfo)
            Logger.writeToLogfile(pageName, "BILGI: Interface listesi basariyla olusturuldu.")
            return intList
        except:
            Logger.writeToLogfile(pageName, "HATA: Interface listesi olusturulamadi.")
            return None
        
    def __getTrunkInterfacesFromCdpOutput(self, pageName, cdpOutput):
        """CDP ciktisina gore trunk interfaceleri liste formatinda return eder"""
        try:
            # Listeyi oluştur
            cdpTrunkList = []

            for cdpDevice in cdpOutput:
                portInfo = cdpDevice['local_interface'].replace(" ","")
                hostnameInfo = cdpDevice['neighbor'].replace(" ","")
                # IP telefonlari CDP tablosundan cikart
                if not (hostnameInfo.startswith("SEP") or hostnameInfo.startswith("T2")):
                    # Isımlendirilmemis AP'leri tum ismi ile al (MAC adresi) ve switch domain name'i sil
                    if "." in hostnameInfo and not hostnameInfo.startswith("AP"):
                        hostnameInfo = hostnameInfo[:(hostnameInfo.find("."))]
                    # Interface'leri standardize et
                    if "Gig" in portInfo:
                        portInfo = portInfo.replace("Gig","Gi")
                    if "Ten" in portInfo:
                        portInfo = portInfo.replace("Ten","Te")
                    if "Fas" in portInfo:
                        portInfo = portInfo.replace("Fas","Fa")
                    # Interface'leri listeye ekle
                    cdpTrunkList.append(portInfo)
                    Logger.writeToLogfile(pageName, "CDP ciktisina göre %s interface'i listeye eklendi. Bagli cihaz: %s" %(portInfo, hostnameInfo))
            Logger.writeToLogfile(pageName, "BILGI: CDP trunk interface listesi basariyla olusturuldu.")
            return cdpTrunkList
        except:
            Logger.writeToLogfile(pageName, "HATA: CDP trunk interface listesi olusturulamadi.")
            return None
        
    def __getTrunkInterfacesFromCdpOutput_huawei(self, pageName, cdpOutput):
        """CDP ciktisina gore trunk interfaceleri liste formatinda return eder"""
        with open("./common/textfsmTemplates/lldpTemplate.textfsm") as lldpTemplateFile:
            lldpTemplate = textfsm.TextFSM(lldpTemplateFile)
            lldpParsedOutput = lldpTemplate.ParseText(cdpOutput)
            lldpHeaders = lldpTemplate.header

        lldpDict = [dict(zip(lldpHeaders, row)) for row in lldpParsedOutput]

        try:
            # Listeyi oluştur
            cdpTrunkList = []

            for cdpDevice in lldpDict:
                portInfo = cdpDevice['Local_Intf'].replace(" ","")
                hostnameInfo = cdpDevice['Neighbor_Dev'].replace(" ","")
                # IP telefonlari CDP tablosundan cikart
                if not (hostnameInfo.startswith("SEP") or hostnameInfo.startswith("T2")):
                    # Isımlendirilmemis AP'leri tum ismi ile al (MAC adresi) ve switch domain name'i sil
                    if "." in hostnameInfo and not hostnameInfo.startswith("AP"):
                        hostnameInfo = hostnameInfo[:(hostnameInfo.find("."))]
                    # Interface'leri listeye ekle
                    cdpTrunkList.append(portInfo)
                    Logger.writeToLogfile(pageName, "CDP ciktisina göre %s interface'i listeye eklendi. Bagli cihaz: %s" %(portInfo, hostnameInfo))
            Logger.writeToLogfile(pageName, "BILGI: CDP trunk interface listesi basariyla olusturuldu.")
            return cdpTrunkList
        except:
            Logger.writeToLogfile(pageName, "HATA: CDP trunk interface listesi olusturulamadi.")
            return None
        
    def __getAllInterfaces_huawei(self, pageName, intStatusOutput):
        """sh int status ciktisina gore interface listesi olusturup return eder."""
        try:
            with open('./common/textfsmTemplates/huaweiVLANInterfaceTemplate.textfsm') as interfaceVLANTemplateFile:
                interfaceVlanTemplate = textfsm.TextFSM(interfaceVLANTemplateFile)
                parsedInterfaceVlanOutput = interfaceVlanTemplate.ParseText(intStatusOutput)
                interfaceVlanHeaders = interfaceVlanTemplate.header

            interfaceVLANDict = [dict(zip(interfaceVlanHeaders, row)) for row in parsedInterfaceVlanOutput] 
            return interfaceVLANDict
        except:
            Logger.writeToLogfile(pageName, "HATA: Interface listesi olusturulamadi.")
            return None

    def cisco_dot1xConfigurator(self, args: dict):
        pageName = args['pageName']
        switchIP = args['switchIP']
        macRegex = r'[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}'
        dot1xVlanList = args['vlanList'].split(',')
        voiceVlanId = args['voiceVlan']
        voiceVlanId = voiceVlanId.replace(" ","")
        if not voiceVlanId.isdigit():
            Logger.writeToLogfile(pageName, "HATA: Hatali voice vlan ID. Iptal ediliyor...")
            exit(1)

        authOpenSupported = True
        try:
            # Switch'e baglan
            ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                            'username': args['username'], 'password': args['password'],
                            'secret': args['password'], 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitch)
            ssh.enable()
            swName = ssh.find_prompt()[:-1]
            Logger.writeToLogfile(pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))

            # CDP ciktisini al ve uplink portlarini listeye ekle
            cdpCommandOutput = ssh.send_command("show cdp neighbors", use_textfsm=True)
            if isinstance(cdpCommandOutput, str):
                cdpIntList = []
            else:
                cdpIntList = self.__getTrunkInterfacesFromCdpOutput(pageName, cdpCommandOutput)

            # Switch interface listesini al
            intCommandOutput = ssh.send_command("show int status", use_textfsm=True)
            switchIntList = self.__getAllInterfaces(pageName, intCommandOutput)
            Logger.writeToLogfile(pageName, "BILGI: Interface listeleri olusturuldu.")
            
            # Islem yapilacak vlan listesine göre vlanID:[int] seklinde dict olustur
            intToConfigureDict = {}
            switchShVlanOutput = ssh.send_command("show vlan", use_textfsm=True)
            for vlanInfo in switchShVlanOutput:
                if (vlanInfo['vlan_id'] in dot1xVlanList) and (len(vlanInfo['interfaces']) > 0):
                    intToConfigureDict[vlanInfo['vlan_id']] = vlanInfo['interfaces']
            Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon yapilacak interface dictionary'si olusturuldu.")
            print(intToConfigureDict)
            
            # Dictionary key listesi uzerinden (vlan id) dongu ile portlari konfigure et
            for vlan in list(intToConfigureDict.keys()):
                # Vlan'a dahil interface listesi uzerinden dongu ile portlari konfigure et
                for interface in intToConfigureDict[vlan]:
                    if args['selectedOption'] == "c":
                        interfaceConfig = ssh.send_command("show run int %s" %interface, use_textfsm=True)
                        # auth open komutu calismiyorsa 'authOpenSupported' false don
                        if ("switchport mode trunk" not in interfaceConfig) and ("channel-group" not in interfaceConfig) and (interface not in cdpIntList):
                            authOpenConfigSet = ["interface %s" %interface,
                                                "switchport mode access",
                                                "authentication open"]
                            authOpenCommandOutput = ssh.send_config_set(authOpenConfigSet, cmd_verify=True)
                            Logger.logCommandOutputs(pageName, authOpenCommandOutput, switchIP)
                            if "Invalid input" in authOpenCommandOutput:
                                authOpenSupported = False
                                Logger.writeToLogfile(pageName, "BILGI: Switch (%s), interface %s 'authentication open' destegi bulunmuyor." %(switchIP, interface))
            
                        # Emniyet sibobu. Uplink interface olma ihtimali olan portlara dokunma
                        if ("switchport mode trunk" not in interfaceConfig) and ("channel-group" not in interfaceConfig) and (interface not in cdpIntList) and authOpenSupported:
                            # Port konfigurasyonu
                            configSet = ["interface %s" %interface,
                                        "no switchport port-security",
                                        "no switchport port-security maximum 3",
                                        "switchport mode access",
                                        "authentication open",
                                        "authentication event fail action next-method",
                                        "authentication event server dead action reinitialize vlan %s" %vlan,
                                        "authentication event server dead action authorize voice",
                                        "authentication event server alive action reinitialize",
                                        "authentication order dot1x mab",
                                        "authentication priority dot1x mab",
                                        "authentication port-control auto",
                                        "authentication host-mode multi-auth",
                                        "authentication periodic",
                                        "authentication timer reauthenticate server",
                                        "authentication violation restrict",
                                        "mab",
                                        "dot1x pae authenticator",
                                        "dot1x timeout tx-period 10",
                                        "spanning-tree bpduguard enable"]
                            Logger.logCommandOutputs(pageName, ssh.send_config_set(configSet, cmd_verify=True), switchIP)
                            Logger.writeToLogfile(pageName, "BILGI: Switch: %s, VlanID: %s, Interface: %s dot1x konfigurasyonu yapildi." %(swName, vlan, interface))
                    elif args['selectedOption'] == "m":
                        intMacAddress = ssh.send_command("show mac address-table int %s" %interface)
                        tempMacList = re.findall(macRegex,intMacAddress)
                        Logger.writeToLogfile(pageName, "BILGI: Switch: %s, Int: %s, MAC: %s" %(switchIP,interface,str(tempMacList)))
                    elif args['selectedOption'] == "r":
                        interfaceConfig = ssh.send_command("show run int %s" %interface, use_textfsm=True)
                        # Emniyet sibobu. Uplink interface olma ihtimali olan portlara dokunma
                        if ("switchport mode trunk" not in interfaceConfig) and ("channel-group" not in interfaceConfig) and (interface not in cdpIntList):
                            # Port konfigurasyonu
                            configSet = ["interface %s" %interface,
                                        "no authentication event fail action next-method",
                                        "no authentication event server dead action reinitialize vlan %s" %vlan,
                                        "no authentication event server dead action authorize voice",
                                        "no authentication event server alive action reinitialize",
                                        "no authentication host-mode multi-auth",
                                        "no authentication order dot1x mab",
                                        "no authentication priority dot1x mab",
                                        "no authentication port-control auto",
                                        "no authentication periodic",
                                        "no authentication timer reauthenticate server",
                                        "no authentication violation restrict",
                                        "no mab",
                                        "no dot1x pae authenticator",
                                        "no dot1x timeout tx-period 10",
                                        "no spanning-tree bpduguard enable",
                                        "no authentication open"]
                            Logger.logCommandOutputs(pageName, ssh.send_config_set(configSet, cmd_verify=True), switchIP)
                            Logger.writeToLogfile(pageName, "BILGI: Switch: %s, VlanID: %s, Interface: %s dot1x konfigurasyonu silindi." %(swName, vlan, interface))  
            if args['wantToSaveConfig']:
                Logger.logCommandOutputs(pageName, ssh.send_command("write"), switchIP)
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
        except:
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch konfigure edilirken hata olustu. Exception: %s" %switchIP)
        Logger.writeToLogfile(pageName, "BILGI: Islem tamamlandi.")

    def huawei_dot1xConfigurator(self, args: dict):
        pageName = args['pageName']
        switchIP = args['switchIP']
        macRegex = r'[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}'
        dot1xVlanList = args['vlanList'].split(',')
        voiceVlanId = args['voiceVlan']
        voiceVlanId = voiceVlanId.replace(" ","")
        if not voiceVlanId.isdigit():
            Logger.writeToLogfile(pageName, "HATA: Hatali voice vlan ID. Iptal ediliyor...")
            exit(1)

        authOpenSupported = True
        try:
            # Switch'e baglan
            huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                            'username': args['username'], 'password': args['password'], 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitch)
            ssh.config_mode()
            swName = ssh.find_prompt()[1:-1]
            Logger.writeToLogfile(pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))

            # CDP ciktisini al ve uplink portlarini listeye ekle
            cdpCommandOutput = ssh.send_command("display lldp neighbors brief")
            cdpIntList = self.__getTrunkInterfacesFromCdpOutput_huawei(pageName, cdpCommandOutput)

            # Switch interface listesini al
            intCommandOutput = ssh.send_command("display port vlan")
            switchIntList = self.__getAllInterfaces_huawei(pageName, intCommandOutput)
            Logger.writeToLogfile(pageName, "BILGI: Interface listeleri olusturuldu.")
            
            # Islem yapilacak vlan listesine göre vlanID:[int] seklinde dict olustur
            intToConfigureDict = {}
            switchShVlanOutput = ssh.send_command("display vlan")

            with open("./huaweiScripts/vlanTemplate.textfsm") as vlanTemplateFile:
                vlanOutputTemplate = textfsm.TextFSM(vlanTemplateFile)
                parsedVlanOutput = vlanOutputTemplate.ParseText(switchShVlanOutput)
                vlanHeaders = vlanOutputTemplate.header

            VLANDict = [dict(zip(vlanHeaders, row)) for row in parsedVlanOutput]

            vlanInterfaceDict = {}
            for vlanName in VLANDict:
                vlanInterfaceDict.update({
                    vlanName["VID"]: {"name": vlanName["Description"], "ports": ""}
                })
            for vlanPort in switchIntList:
                vlanInterfaceDict[vlanPort["PVID"]]["ports"] += f"{vlanPort['Port']},"

            for vlanNumber in vlanInterfaceDict.keys():
                if (vlanNumber in dot1xVlanList) and (len(vlanInterfaceDict[vlanNumber]['ports']) > 0):
                    intToConfigureDict[vlanNumber] = vlanInterfaceDict[vlanNumber]['ports'].split(',')
            Logger.writeToLogfile(pageName, "BILGI: Konfigurasyon yapilacak interface dictionary'si olusturuldu.")
            print(intToConfigureDict)
            
            # Dictionary key listesi uzerinden (vlan id) dongu ile portlari konfigure et
            for vlan in list(intToConfigureDict.keys()):
                # Vlan'a dahil interface listesi uzerinden dongu ile portlari konfigure et
                for interface in intToConfigureDict[vlan]:
                    if args['selectedOption'] == "c":
                        interfaceConfig = ssh.send_command(f"display current-configuration interface {interface}")
                        # auth open komutu calismiyorsa 'authOpenSupported' false don
                        if ("port link-type trunk" not in interfaceConfig) and ("eth-trunk" not in interfaceConfig) and (interface not in cdpIntList):
                            authOpenConfigSet = ["interface %s" %interface,
                                                "port link-type access",
                                                "authentication open"]
                            authOpenCommandOutput = ssh.send_config_set(authOpenConfigSet, cmd_verify=True)
                            Logger.logCommandOutputs(pageName, authOpenCommandOutput, switchIP)
                            if "Invalid input" in authOpenCommandOutput:
                                authOpenSupported = False
                                Logger.writeToLogfile(pageName, "BILGI: Switch (%s), interface %s 'authentication open' destegi bulunmuyor." %(switchIP, interface))
            
                        # Emniyet sibobu. Uplink interface olma ihtimali olan portlara dokunma
                        if ("port link-type trunk" not in interfaceConfig) and ("eth-trunk" not in interfaceConfig) and (interface not in cdpIntList) and authOpenSupported:
                            # Port konfigurasyonu
                            configSet = [f"interface {interface}",
                                        "undo port-security enable",
                                        "port link-type access",
                                        "authentication open",
                                        "authentication event fail action next-method",
                                        "authentication event server dead action reinitialize vlan %s" %vlan,
                                        "authentication event server dead action authorize voice",
                                        "authentication event server alive action reinitialize",
                                        "authentication host-mode multi-auth",
                                        "authentication port-control auto",
                                        f"dot1x reauthenticate interface {interface}",
                                        "authentication timer reauthenticate server",
                                        "authentication violation restrict",
                                        "mab",
                                        "dot1x authentication-method eap (??)",
                                        "dot1x timer tx-period 10 (system view)",
                                        "stp bpdu-protection (system viewdan yapılacak)"]
                            Logger.logCommandOutputs(pageName, ssh.send_config_set(configSet, cmd_verify=True), switchIP)
                            Logger.writeToLogfile(pageName, "BILGI: Switch: %s, VlanID: %s, Interface: %s dot1x konfigurasyonu yapildi." %(swName, vlan, interface))
                    elif args['selectedOption'] == "m":
                        intMacAddress = ssh.send_command(f"display mac-address interface {interface}")
                        tempMacList = re.findall(macRegex,intMacAddress)
                        Logger.writeToLogfile(pageName, "BILGI: Switch: %s, Int: %s, MAC: %s" %(switchIP,interface,str(tempMacList)))
                    elif args['selectedOption'] == "r":
                        interfaceConfig = ssh.send_command(f"display current-configuration interface {interface}")
                        # Emniyet sibobu. Uplink interface olma ihtimali olan portlara dokunma
                        if ("port link-type trunk" not in interfaceConfig) and ("eth-trunk" not in interfaceConfig) and (interface not in cdpIntList):
                            # Port konfigurasyonu
                            configSet = ["interface %s" %interface,
                                        "no authentication event fail action next-method",
                                        "no authentication event server dead action reinitialize vlan %s" %vlan,
                                        "no authentication event server dead action authorize voice",
                                        "no authentication event server alive action reinitialize",
                                        "no authentication host-mode multi-auth",
                                        "no authentication order dot1x mab",
                                        "no authentication priority dot1x mab",
                                        "no authentication port-control auto",
                                        "no authentication periodic",
                                        "no authentication timer reauthenticate server",
                                        "no authentication violation restrict",
                                        "no mab",
                                        "no dot1x pae authenticator",
                                        "no dot1x timeout tx-period 10",
                                        "no spanning-tree bpduguard enable",
                                        "no authentication open"]
                            Logger.logCommandOutputs(pageName, ssh.send_config_set(configSet, cmd_verify=True), switchIP)
                            Logger.writeToLogfile(pageName, "BILGI: Switch: %s, VlanID: %s, Interface: %s dot1x konfigurasyonu silindi." %(swName, vlan, interface))  

            if args['wantToSaveConfig']:
                Logger.logCommandOutputs(pageName, ssh.send_command("write"), switchIP)
                Logger.writeToLogfile(pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
        except:
            Logger.writeToLogfile(pageName, "HATA: %s IP adresli switch konfigure edilirken hata olustu. Exception: %s" %switchIP)
            return
        Logger.writeToLogfile(pageName, "Islem tamamlandi.")