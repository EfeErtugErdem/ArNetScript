# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ
# Developed on April 2023

from netmiko import ConnectHandler
from datetime import datetime
import os.path
import argparse
import re

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
                writeToLogfile(pageName, "CDP ciktisina göre %s interface'i listeye eklendi. Bagli cihaz: %s" %(portInfo, hostnameInfo))
        writeToLogfile(pageName, "BILGI: CDP trunk interface listesi basariyla olusturuldu.")
        return cdpTrunkList
    except:
        writeToLogfile(pageName, "HATA: CDP trunk interface listesi olusturulamadi.")
        return None

def getAllInterfaces(pageName, intStatusOutput):
    """sh int status ciktisina gore interface listesi olusturup return eder."""
    try:
        # Listeyi olustur
        intList = []

        for interface in intStatusOutput:
            portInfo = interface['port'].replace(" ","")
            intList.append(portInfo)
        writeToLogfile(pageName, "BILGI: Interface listesi basariyla olusturuldu.")
        return intList
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
            writeToLogfile(pageName, "Vlan ID: %s, Vlan Name: %s" %(item['vlan_id'], item['vlan_name']))
            locationVlanList.append(item['vlan_id'])

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
        os.abort()
    # MAC regex
    macRegex = r'[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}'
    # Switch giris bilgilerini al
    user = userArgs.username
    password = userArgs.password
    enablePassword = password

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
            os.abort()
        writeToLogfile(userArgs.pageName, "BILGI: Switch IP listesi olusturuldu. %d switch bulundu." % len(switchList))
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch IP bilgileri alinamadi. Iptal ediliyor...")
        os.abort()
    # Komut ciktilarinin saklanacagi klasoru olustur
    if not os.path.isdir(f"./{userArgs.pageName}commandOutputs"):
        os.mkdir(f"./{userArgs.pageName}commandOutputs")

    # Ilk switch'e baglanarak vlan bilgilerini cek
    try:
        try:
            # SSH ile baglanmayi dene
            switchIP = switchList[0]
            ciscoSwitchSSH = {'device_type': 'cisco_ios', 'host': switchIP,
                       'username': user, 'password': password,
                       'secret': enablePassword, 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitchSSH)
            ssh.enable()
            shVlanOutput = ssh.send_command("show vlan", use_textfsm=True)
            # SSH baglantisini sonlandir
            ssh.disconnect()
        except:
            # SSH basarisiz olursa telnet ile baglanmayi dene
            switchIP = switchList[0]
            ciscoSwitchTelnet = {'device_type': 'cisco_ios_telnet', 'host': switchIP,
                        'username': user, 'password': password,
                        'secret': enablePassword, 'port': 23, }
            telnet = ConnectHandler(**ciscoSwitchTelnet)
            telnet.enable()
            shVlanOutput = telnet.send_command("show vlan", use_textfsm=True)
            # SSH baglantisini sonlandir
            telnet.disconnect()
    except:
        writeToLogfile(userArgs.pageName, f"HATA: Vlan listesi alinirken hata olustu.")
        os.abort()

    # Kullaniciya hangi vlan'larda islem yapılacagini sor ve vlan listesini olustur
    dot1xVlanList = getVlanListToWorkOn(userArgs.pageName, shVlanOutput, userArgs.vlanList)
except:
    writeToLogfile(userArgs.pageName, f"HATA: On bilgiler alinamadi. Iptal ediliyor...")
    os.abort()

for switchIP in switchList:
    # auth open destekleyip desteklemedigini kontrol et
    authOpenSupported = True
    try:
        # Switch'e baglan
        ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                        'username': user, 'password': password,
                        'secret': enablePassword, 'port': 22, }
        ssh = ConnectHandler(**ciscoSwitch)
        ssh.enable()
        swName = ssh.find_prompt()[:-1]
        writeToLogfile(userArgs.pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))

        # CDP ciktisini al ve uplink portlarini listeye ekle
        cdpCommandOutput = ssh.send_command("show cdp neighbors", use_textfsm=True)
        if isinstance(cdpCommandOutput, str):
            cdpIntList = []
        else:
            cdpIntList = getTrunkInterfacesFromCdpOutput(userArgs.pageName, cdpCommandOutput)

        # Switch interface listesini al
        intCommandOutput = ssh.send_command("show int status", use_textfsm=True)
        switchIntList = getAllInterfaces(userArgs.pageName, intCommandOutput)
        writeToLogfile(userArgs.pageName, "BILGI: Interface listeleri olusturuldu.")
        
        # Islem yapilacak vlan listesine göre vlanID:[int] seklinde dict olustur
        intToConfigureDict = {}
        switchShVlanOutput = ssh.send_command("show vlan", use_textfsm=True)
        for vlanInfo in switchShVlanOutput:
            if (vlanInfo['vlan_id'] in dot1xVlanList) and (len(vlanInfo['interfaces']) > 0):
                intToConfigureDict[vlanInfo['vlan_id']] = vlanInfo['interfaces']
        writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon yapilacak interface dictionary'si olusturuldu.")
        print(intToConfigureDict)
        
        # Dictionary key listesi uzerinden (vlan id) dongu ile portlari konfigure et
        for vlan in list(intToConfigureDict.keys()):
            # Vlan'a dahil interface listesi uzerinden dongu ile portlari konfigure et
            for interface in intToConfigureDict[vlan]:
                if userArgs.selectedOption == "c":
                    interfaceConfig = ssh.send_command("show run int %s" %interface, use_textfsm=True)
                    # auth open komutu calismiyorsa 'authOpenSupported' false don
                    if ("switchport mode trunk" not in interfaceConfig) and ("channel-group" not in interfaceConfig) and (interface not in cdpIntList):
                        authOpenConfigSet = ["interface %s" %interface,
                                            "switchport mode access",
                                            "authentication open"]
                        authOpenCommandOutput = ssh.send_config_set(authOpenConfigSet, cmd_verify=True)
                        logCommandOutputs(userArgs.pageName, authOpenCommandOutput, switchIP)
                        if "Invalid input" in authOpenCommandOutput:
                            authOpenSupported = False
                            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s), interface %s 'authentication open' destegi bulunmuyor." %(switchIP, interface))
        
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
                                    "authentication host-mode multi-auth",
                                    "authentication order dot1x mab",
                                    "authentication priority dot1x mab",
                                    "authentication port-control auto",
                                    "authentication periodic",
                                    "authentication timer reauthenticate server",
                                    "authentication violation restrict",
                                    "mab",
                                    "dot1x pae authenticator",
                                    "dot1x timeout tx-period 10",
                                    "spanning-tree bpduguard enable"]
                        logCommandOutputs(userArgs.pageName, ssh.send_config_set(configSet, cmd_verify=True), switchIP)
                        writeToLogfile(userArgs.pageName, "BILGI: Switch: %s, VlanID: %s, Interface: %s dot1x konfigurasyonu yapildi." %(swName, vlan, interface))
                elif userArgs.selectedOption == "m":
                    intMacAddress = ssh.send_command("show mac address-table int %s" %interface)
                    tempMacList = re.findall(macRegex,intMacAddress)
                    writeToLogfile(userArgs.pageName, "BILGI: Switch: %s, Int: %s, MAC: %s" %(switchIP,interface,str(tempMacList)))
                elif userArgs.selectedOption == "r":
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
