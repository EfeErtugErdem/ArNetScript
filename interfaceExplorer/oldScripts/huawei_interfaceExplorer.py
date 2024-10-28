# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ
# Developed on April 2023

from netmiko import ConnectHandler
from datetime import datetime
import argparse
import os.path
import xlsxwriter
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

############################################################################
# Uygulama beyni
############################################################################

# Konfigurasyon icin ortami hazirla
try:
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", dest="username", help="Kullanıcı Adı")
    parser.add_argument("-p", "--password", dest="password", help="Parola")
    parser.add_argument("--page-name", "--page-name", dest="pageName", help="Sayfa Adı")

    userArgs = parser.parse_args()
    # Switch giris bilgilerini al
    user = userArgs.username
    password = userArgs.password
    enablePassword = password
    templateBasePath = "./common/textfsmTemplates"
    # switchList.txt dosyasindan IP adreslerini oku ve listeye ekle
    switchList = []
    try:
        with open(f"./{userArgs.pageName.strip()}switchList.txt") as file:
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

    # Ilk switch'e baglanarak vlan bilgilerini cek, vlan bilgisini paylas
    try:
        try:
            # SSH ile baglanmayi dene
            switchIP = switchList[0]
            huaweiSwitchSSH = {'device_type': 'huawei', 'host': switchIP,
                       'username': user, 'password': password, 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitchSSH)
            ssh.config_mode()
            interfaceVlanOutput = ssh.send_command("display port vlan")
            nameVlanOutput = ssh.send_command("display vlan")
            # SSH baglantisini sonlandir
            ssh.disconnect()
        except:
            # SSH basarisiz olursa telnet ile baglanmayi dene
            switchIP = switchList[0]
            ciscoSwitchTelnet = {'device_type': 'huawei_telnet', 'host': switchIP,
                        'username': user, 'password': password, 'port': 23, }
            telnet = ConnectHandler(**ciscoSwitchTelnet)
            telnet.config_mode()
            interfaceVlanOutput = telnet.send_command("display port vlan")
            nameVlanOutput = telnet.send_command("display vlan")
            # Telnet baglantisini sonlandir
            telnet.disconnect()

        # Excel dosyasini olustur
        writeToLogfile(userArgs.pageName, "BILGI: Excel dosyasi olusturuluyor.")
        fileName = f"./{userArgs.pageName.strip()}interfaceExplorerReport_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        excelWorkbook = xlsxwriter.Workbook(fileName)
        excelWorksheet = excelWorkbook.add_worksheet(name="INTERFACE-INFO")
        excelWorksheet.write(0, 0, "Switch Info")
        columnNumber = 1
        excludedVlans = ["1002","1003","1004","1005"]

        # Vlan'lari excel'e ekle, Vlan listesini kullaniciyla paylas ve lokasyon vlan listesini olustur
        locationVlanList = []
        writeToLogfile(userArgs.pageName, "Lokasyon vlan bilgileri")

        with open(f'{templateBasePath}/vlanTemplate.textfsm') as vlanTemplateFile:
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
        for vlanPort in interfaceVLANDict:
            interfaceNameVlanDict[vlanPort["PVID"]]["ports"] += f"{vlanPort['Port']},"

        for item in VLANDict:
            if item['VID'] not in excludedVlans:
                columnName = "%s (%s)" %(item['VID'], item['Description'])
                excelWorksheet.write(0, columnNumber, columnName)
                columnNumber += 1
                writeToLogfile(userArgs.pageName, "Vlan ID: %s, Vlan Name: %s" %(item['VID'], item['Description']))
                locationVlanList.append(item['VID'])
        print(locationVlanList)
    except:
        writeToLogfile(userArgs.pageName, "HATA: Vlan listesi alinirken hata oluştu.")
        os.abort()
except:
    writeToLogfile(userArgs.pageName, "HATA: Uygulama icin ortam hazirlanamadi.")

# Switch vlan bilgilerini excel'e tasi
rowNumber = 1
for switchIP in switchList:
    try:
        try:
            # Switch'e ssh ile baglan
            huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                            'username': user, 'password': password, 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitch)
            ssh.config_mode()
            swName = ssh.find_prompt()[1:-1]
            swRowName = "%s_%s" %(swName, switchIP)
            # Switch adini ilk sutuna yaz
            excelWorksheet.write(rowNumber, 0, swRowName)
            writeToLogfile(userArgs.pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))
            # Komut ciktisindaki bilgileri Excel'e tasi
            for vlanNumber in interfaceNameVlanDict.keys():
                if vlanNumber not in excludedVlans:
                    columnNumber = locationVlanList.index(vlanNumber) + 1
                    interfaceInfo = interfaceNameVlanDict[vlanNumber]['ports']
                    excelWorksheet.write(rowNumber, columnNumber, interfaceInfo)
            # SSH baglantisini sonlandir
            ssh.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: SSH ile switch vlan bilgileri alindi ve Excel'e islendi.")
        except:
            # SSH hata verirse switch'e telnet ile baglan
            huaweiSwitch = {'device_type': 'huawei_telnet', 'host': switchIP,
                            'username': user, 'password': password, 'port': 23, }
            telnet = ConnectHandler(**huaweiSwitch)
            telnet.config_mode()
            swName = telnet.find_prompt()[1:-1]
            swRowName = "%s_%s" %(swName, switchIP)
            # Switch adini ilk sutuna yaz
            excelWorksheet.write(rowNumber, 0, swRowName)
            writeToLogfile(userArgs.pageName, "BILGI: Switch'e SSH ile baglanildi. %s %s" %(swName, switchIP))
            # Komut ciktisindaki bilgileri Excel'e tasi
            for vlanNumber in interfaceNameVlanDict.keys():
                if vlanNumber not in excludedVlans:
                    columnNumber = locationVlanList.index(vlanNumber) + 1
                    interfaceInfo = interfaceNameVlanDict[vlanNumber]['ports']
                    excelWorksheet.write(rowNumber, columnNumber, interfaceInfo)
            # telnet baglantisini sonlandir
            telnet.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Telnet ile switch vlan bilgileri alindi ve Excel'e islendi.")
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch vlan bilgileri islenirken hata olustu.")
    rowNumber += 1
# Excel'i kaydet
excelWorkbook.close()

writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")
    
            

