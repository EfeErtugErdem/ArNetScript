# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ
# Developed on April 2023

from netmiko import ConnectHandler
from datetime import datetime
import os.path
import argparse
import re
import textfsm

############################################################################
# Fonksiyonlari tanimla
############################################################################

def writeToLogfile(pageName, log):
    """Girilen log metnini txt dosyasina kaydeder ve konsola yazdirir."""
    log_data = "{}: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), log)
    with open(f"./{pageName}logs.txt", "a") as log_file:
        log_file.write(log_data)
    log_file.close()
    print(log_data)

def logCommandOutputs(pageName, log, switch):
    """configBackups klasorune switch konfigurasyonunu kaydeder."""
    try:
        fileName = "commandOutputs_" + switch.replace(".", "_") + ".txt"
        path = f"./{pageName}commandOutputs"
        configPath = os.path.join(path, fileName)
        with open(configPath, "a", encoding="utf-8") as configFile:
            configFile.write(log)
        configFile.close()
        return log
    except:
        writeToLogfile(pageName, "HATA: Switch konfigurasyon dosyasi olusturulamadi.")

def getTrunkInterfacesFromCdpOutput(pageName, cdpOutput):
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
                writeToLogfile(pageName, "CDP ciktisina göre %s interface'i listeye eklendi. Bagli cihaz: %s" %(portInfo, hostnameInfo))
        writeToLogfile(pageName, "BILGI: CDP trunk interface listesi basariyla olusturuldu.")
        return cdpTrunkList
    except:
        writeToLogfile(pageName, "HATA: CDP trunk interface listesi olusturulamadi.")
        return None

def getAllInterfaces(pageName, intStatusOutput):
    """sh int status ciktisina gore interface listesi olusturup return eder."""
    try:
        with open('./common/textfsmTemplates/huaweiVLANInterfaceTemplate.textfsm') as interfaceVLANTemplateFile:
            interfaceVlanTemplate = textfsm.TextFSM(interfaceVLANTemplateFile)
            parsedInterfaceVlanOutput = interfaceVlanTemplate.ParseText(intStatusOutput)
            interfaceVlanHeaders = interfaceVlanTemplate.header

        interfaceVLANDict = [dict(zip(interfaceVlanHeaders, row)) for row in parsedInterfaceVlanOutput] 
        return interfaceVLANDict
    except:
        writeToLogfile(pageName, "HATA: Interface listesi olusturulamadi.")
        return None

def getUserAnswer(answer):
    """Kullaniciya sorulan e/h sorusunun cevabini return eder."""
    if answer == "e":
        return True
    return False

def getVlanListToWorkOn(pageName, vlanCommandOutput, userVlanList):
    """sh vlan ciktisina ve kullanici girdisine gore islem yapilacak vlanlari liste formatinda return eder."""
    try:
        # Vlan listesini kullaniciyla paylas ve lokasyon vlan listesini olustur
        locationVlanList = []
        writeToLogfile(pageName, "Lokasyon vlan bilgileri")
        for item in vlanCommandOutput:
            writeToLogfile(pageName, "Vlan ID: %s, Vlan Name: %s" %(item['VID'], item['Description']))
            locationVlanList.append(item['VID'])

        # Kullaniciya islem yapilacak vlan'lari sor
        userAnswer = userVlanList
        userAnswerVlanList = userAnswer.split(',')

        # Mukerrer kayitlari sil ve final listeyi olustur
        finalVlanList = []
        for item in userAnswerVlanList:
            if item not in finalVlanList:
                finalVlanList.append(item)

        # Son listeyi kullanici ile paylas
        writeToLogfile(pageName, "Islem yapilacak vlan listesi: %s" %(str(finalVlanList)))
        return finalVlanList
    except:
        writeToLogfile(pageName, "HATA: Vlan listesi olusturulamadi.")
        return None
    
############################################################################
# Uygulama beyni
############################################################################

# Konfigurasyon icin ortami hazirla
try:
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--save-config", dest="saveConfig", help="Konfigürasyon kaydedilsin mi?")
    parser.add_argument("-u", "--username", dest="username", help="Kullanıcı Adı")
    parser.add_argument("-p", "--password", dest="password", help="Parola")
    parser.add_argument("--voice-vlan", "--voice-vlan", dest="voiceVlan", help="Voice VLAN Numarası")
    parser.add_argument("--vlan-list", "--vlan-list", dest="vlanList", help="VLAN Listesi")
    parser.add_argument("--page-name", "--page-name", dest="pageName", help="Sayfa Adı")
    parser.add_argument("--selected-option", "--selected-option", dest="selectedOption", help="Konfigürasyon seçeneği")
    # c - Configurator, m - MacExplorer, r - Remover

    userArgs = parser.parse_args()
    # Konfigurasyonun kaydedilmesi isteniyor mu, bilgi al
    wantToSaveConfig = userArgs.saveConfig
    # Voice vlan bilgisini al
    voiceVlanId = userArgs.voiceVlan
    voiceVlanId = voiceVlanId.replace(" ","")
    if not voiceVlanId.isdigit():
        writeToLogfile(userArgs.pageName, "HATA: Hatali voice vlan ID. Iptal ediliyor...")
        exit(1)
    # MAC regex
    macRegex = r'[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}'
    # Switch giris bilgilerini al
    user = userArgs.username
    password = userArgs.password

    # switchList.txt dosyasindan IP adreslerini oku ve listeye ekle
    switchList = []
    try:
        with open(f"./{userArgs.pageName}switchList.txt") as file:
            for line in file:
                if len(line) > 1:
                    switchList.append(line.strip())
        # Listenin bos olmadigina emin ol
        if len(switchList) == 0:
            writeToLogfile(userArgs.pageName, "HATA: Switch IP dosyasinda eksik bilgi. Iptal ediliyor...")
            exit(1)
        writeToLogfile(userArgs.pageName, "BILGI: Switch IP listesi olusturuldu. %d switch bulundu." % len(switchList))
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch IP bilgileri alinamadi. Iptal ediliyor...")
        exit(1)
    # Komut ciktilarinin saklanacagi klasoru olustur
    if not os.path.isdir(f"./{userArgs.pageName}commandOutputs"):
        os.mkdir(f"./{userArgs.pageName}commandOutputs")

    # Ilk switch'e baglanarak vlan bilgilerini cek
    try:
        try:
            # SSH ile baglanmayi dene
            switchIP = switchList[0]
            huaweiSwitchSSH = {'device_type': 'huawei', 'host': switchIP,
                       'username': user, 'password': password, 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitchSSH)
            ssh.config_mode()
            shVlanOutput = ssh.send_command("display vlan", use_textfsm=True)
            # SSH baglantisini sonlandir
            ssh.disconnect()
        except:
            # SSH basarisiz olursa telnet ile baglanmayi dene
            switchIP = switchList[0]
            huaweiSwitchTelnet = {'device_type': 'huawei_telnet', 'host': switchIP,
                        'username': user, 'password': password, 'port': 23, }
            telnet = ConnectHandler(**huaweiSwitchTelnet)
            telnet.config_mode()
            shVlanOutput = telnet.send_command("display vlan", use_textfsm=True)
            # SSH baglantisini sonlandir
            telnet.disconnect()
    except:
        writeToLogfile(userArgs.pageName, f"HATA: Vlan listesi alinirken hata olustu.")
        exit(1)

    with open("./common/textfsmTemplates/vlanTemplate.textfsm") as vlanTemplateFile:
        vlanOutputTemplate = textfsm.TextFSM(vlanTemplateFile)
        parsedVlanOutput = vlanOutputTemplate.ParseText(shVlanOutput)
        vlanHeaders = vlanOutputTemplate.header

    VLANDict = [dict(zip(vlanHeaders, row)) for row in parsedVlanOutput]

    # Kullaniciya hangi vlan'larda islem yapılacagini sor ve vlan listesini olustur
    dot1xVlanList = getVlanListToWorkOn(userArgs.pageName, VLANDict, userArgs.vlanList)
except:
    writeToLogfile(userArgs.pageName, f"HATA: On bilgiler alinamadi. Iptal ediliyor...")
    exit(1)

for switchIP in switchList:
    # auth open destekleyip desteklemedigini kontrol et
    authOpenSupported = True
    try:
        # Switch'e baglan
        huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                        'username': user, 'password': password, 'port': 22, }
        ssh = ConnectHandler(**huaweiSwitch)
        ssh.config_mode()
        swName = ssh.find_prompt()[1:-1]
        writeToLogfile(userArgs.pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))

        # CDP ciktisini al ve uplink portlarini listeye ekle
        cdpCommandOutput = ssh.send_command("display lldp neighbors brief")
        cdpIntList = getTrunkInterfacesFromCdpOutput(userArgs.pageName, cdpCommandOutput)

        # Switch interface listesini al
        intCommandOutput = ssh.send_command("display port vlan")
        switchIntList = getAllInterfaces(userArgs.pageName, intCommandOutput)
        writeToLogfile(userArgs.pageName, "BILGI: Interface listeleri olusturuldu.")
        
        # Islem yapilacak vlan listesine göre vlanID:[int] seklinde dict olustur
        intToConfigureDict = {}
        switchShVlanOutput = ssh.send_command("display vlan")

        with open("./huaweiScripts/vlanTemplate.textfsm") as vlanTemplateFile:
            vlanOutputTemplate = textfsm.TextFSM(vlanTemplateFile)
            parsedVlanOutput = vlanOutputTemplate.ParseText(switchShVlanOutput)
            vlanHeaders = vlanOutputTemplate.header

        VLANDict = [dict(zip(vlanHeaders, row)) for row in parsedVlanOutput]
        VLANlist = [item["VID"] for item in VLANDict]

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
        writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon yapilacak interface dictionary'si olusturuldu.")
        print(intToConfigureDict)
        
        # Dictionary key listesi uzerinden (vlan id) dongu ile portlari konfigure et
        for vlan in list(intToConfigureDict.keys()):
            # Vlan'a dahil interface listesi uzerinden dongu ile portlari konfigure et
            for interface in intToConfigureDict[vlan]:
                if userArgs.selectedOption == "c":
                    interfaceConfig = ssh.send_command(f"display current-configuration interface {interface}")
                    # auth open komutu calismiyorsa 'authOpenSupported' false don
                    if ("port link-type trunk" not in interfaceConfig) and ("eth-trunk" not in interfaceConfig) and (interface not in cdpIntList):
                        authOpenConfigSet = ["interface %s" %interface,
                                            "port link-type access",
                                            "authentication open"]
                        authOpenCommandOutput = ssh.send_config_set(authOpenConfigSet, cmd_verify=True)
                        logCommandOutputs(userArgs.pageName, authOpenCommandOutput, switchIP)
                        if "Invalid input" in authOpenCommandOutput:
                            authOpenSupported = False
                            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s), interface %s 'authentication open' destegi bulunmuyor." %(switchIP, interface))
        
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
                        logCommandOutputs(userArgs.pageName, ssh.send_config_set(configSet, cmd_verify=True), switchIP)
                        writeToLogfile(userArgs.pageName, "BILGI: Switch: %s, VlanID: %s, Interface: %s dot1x konfigurasyonu yapildi." %(swName, vlan, interface))
                elif userArgs.selectedOption == "m":
                    intMacAddress = ssh.send_command(f"display mac-address interface {interface}")
                    tempMacList = re.findall(macRegex,intMacAddress)
                    writeToLogfile(userArgs.pageName, "BILGI: Switch: %s, Int: %s, MAC: %s" %(switchIP,interface,str(tempMacList)))
                elif userArgs.selectedOption == "r":
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
                        logCommandOutputs(userArgs.pageName, ssh.send_config_set(configSet, cmd_verify=True), switchIP)
                        writeToLogfile(userArgs.pageName, "BILGI: Switch: %s, VlanID: %s, Interface: %s dot1x konfigurasyonu silindi." %(swName, vlan, interface))  

        if wantToSaveConfig:
            logCommandOutputs(userArgs.pageName, ssh.send_command("write"), switchIP)
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
    except:
        writeToLogfile(userArgs.pageName, "HATA: %s IP adresli switch konfigure edilirken hata olustu. Exception: %s" %switchIP)
        continue
# Islemin tamamlandigini bilgi ver
writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")
