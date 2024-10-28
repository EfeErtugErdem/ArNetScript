# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ

from netmiko import ConnectHandler
from datetime import datetime
import argparse
import os.path
import xlsxwriter
import textfsm


# Kullanılacak fonksiyonlari tanimla

def writeToLogfile(pageName, log):
    """Girilen log metnini txt dosyasina kaydeder ve konsola yazdirir."""
    log_data = "{}: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), log)
    with open(f"./{pageName}logs.txt", "a") as log_file:
        log_file.write(log_data)
    log_file.close()
    print(log_data)

# Konfigurasyon icin ortami hazirla
try:
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", dest="username", help="Kullanıcı Adı")
    parser.add_argument("-p", "--password", dest="password", help="Parola")
    parser.add_argument("--page-name", "--page-name", dest="pageName", help="Sayfa Adı")

    userArgs = parser.parse_args()
    # switchList.txt dosyasindan IP adreslerini oku ve listeye ekle
    switchList = []
    try:
        with open(f"./{userArgs.pageName}switchList.txt") as file:
            for line in file:
                if len(line) > 1:
                    switchList.append(line.strip())
        writeToLogfile(userArgs.pageName, "BILGI: Switch IP listesi olusturuldu. %d switch bulundu." % len(switchList))
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch IP bilgileri alinamadi. Iptal ediliyor...")
        os.abort()
    # Listelerin bos olmadigina emin ol
    if len(switchList) == 0:
        writeToLogfile(userArgs.pageName, "HATA: IP dosyasinda eksik bilgi. Iptal ediliyor...")
        os.abort()
    # Switch giris bilgilerini al
    user = userArgs.username
    password = userArgs.password
    enablePassword = password
    # Ciktilarin saklanacagi excel dosyasini olustur
    fileName = f"./{userArgs.pageName.strip()}inventoryReport_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    excelWorkbook = xlsxwriter.Workbook(fileName)
    excelWorksheet = excelWorkbook.add_worksheet(name="INVENTORY")
    excelWorksheet.write(0, 0, "Seri No")
    excelWorksheet.write(0, 1, "Cihaz Detay")
    excelWorksheet.write(0, 2, "Switch Hostname")
    excelWorksheet.write(0, 3, "Switch IP")
except:
    writeToLogfile(userArgs.pageName, "HATA: On bilgiler alinamadi. Iptal ediliyor...")
    os.abort()

# Switchlere baglan ve bilgileri excel dosyasına yaz
rowNumber = 1
for switchIP in switchList:
    try:
        try:
            huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                           'username': user, 'password': password, 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitch)
            ssh.config_mode()
            swName = ssh.find_prompt()[1:-1]
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e (%s) SSH ile baglanildi." % (switchIP, swName))

            manufactureOutput = ssh.send_command("display device manufacture-info")
            deviceOutput = ssh.send_command("display device")

            with open("./common/textfsmTemplates/huaweiManufactureInfoTemplate.textfsm") as manufactureInfoTemplateFile:
                manufactureInfoTemplate = textfsm.TextFSM(manufactureInfoTemplateFile)
                parsedOutput = manufactureInfoTemplate.ParseText(manufactureOutput)
                manufactureHeaders = manufactureInfoTemplate.header
            manufactureDict = [dict(zip(manufactureHeaders, row)) for row in parsedOutput]

            with open("./common/textfsmTemplates/huaweiDeviceInfoTemplate.textfsm") as deviceInfoTemplateFile:
                deviceInfoTemplate = textfsm.TextFSM(deviceInfoTemplateFile)
                parsedDeviceOutput = deviceInfoTemplate.ParseText(deviceOutput)
                deviceHeaders = deviceInfoTemplate.header
            deviceDict = [dict(zip(deviceHeaders, row)) for row in parsedDeviceOutput] 

            keysList = ["Slot", "Serial_number", "Type"]
            swInventoryList = []
            for i in range(0, min(len(manufactureDict), len(deviceDict))):
                mergedDict = {key: (manufactureDict[i] | deviceDict[i])[key] for key in keysList}
                swInventoryList.append(mergedDict)

            for item in swInventoryList:
                if "Serial_number" in item.keys():
                    excelWorksheet.write(rowNumber, 0, item["Serial_number"])
                    excelWorksheet.write(rowNumber, 1, item["Type"])
                    excelWorksheet.write(rowNumber, 2, swName)
                    excelWorksheet.write(rowNumber, 3, switchIP)
                    rowNumber+=1
            writeToLogfile(userArgs.pageName, "BILGI: Switch envanter bilgisi alindi.")
            ssh.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Switch %s (%s) baglantisi kapatildi." % (switchIP, swName))
        except:
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e (%s) telnet ile baglanti deneniyor." % (switchIP, swName))
            huaweiSwitch = {'device_type': 'huawei_telnet', 'host': switchIP,
                       'username': user, 'password': password, 'port': 23, }
            telnet = ConnectHandler(**huaweiSwitch)
            telnet.config_mode()
            swName = ssh.find_prompt()[1:-1]
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e (%s) telnet ile baglanildi." % (switchIP, swName))

            manufactureOutput = ssh.send_command("display device manufacture-info")
            deviceOutput = ssh.send_command("display device")

            with open("./common/textfsmTemplates/huaweiManufactureInfoTemplate.textfsm") as manufactureInfoTemplateFile:
                manufactureInfoTemplate = textfsm.TextFSM(manufactureInfoTemplateFile)
                parsedOutput = manufactureInfoTemplate.ParseText(manufactureOutput)
                manufactureHeaders = manufactureInfoTemplate.header
            manufactureDict = [dict(zip(manufactureHeaders, row)) for row in parsedOutput]

            with open("./common/textfsmTemplates/huaweiDeviceInfoTemplate.textfsm") as deviceInfoTemplateFile:
                deviceInfoTemplate = textfsm.TextFSM(deviceInfoTemplateFile)
                parsedDeviceOutput = deviceInfoTemplate.ParseText(deviceOutput)
                deviceHeaders = deviceInfoTemplate.header
            deviceDict = [dict(zip(deviceHeaders, row)) for row in parsedDeviceOutput] 

            keysList = ["Slot", "Serial_number", "Type"]
            swInventoryList = []
            for i in range(0, min(len(manufactureDict), len(deviceDict))):
                mergedDict = {key: (manufactureDict[i] | deviceDict[i])[key] for key in keysList}
                swInventoryList.append(mergedDict)
            
            for item in swInventoryList:
                if "Serial_number" in item:
                    excelWorksheet.write(rowNumber, 0, item["Serial_number"])
                    excelWorksheet.write(rowNumber, 1, item["Type"])
                    excelWorksheet.write(rowNumber, 2, swName)
                    excelWorksheet.write(rowNumber, 3, switchIP)
                    rowNumber+=1
            writeToLogfile(userArgs.pageName, "BILGI: Switch envanter bilgisi alindi.")
            telnet.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Switch %s (%s) baglantisi kapatildi." % (switchIP, swName))
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch (%s) envanter bilgisi alinirken hata olustu." % switchIP)
try:
    excelWorkbook.close()
    writeToLogfile(userArgs.pageName, "BILGI: Excel dosyasi olusturuldu.")
except:
    writeToLogfile(userArgs.pageName, "HATA: Excel dosyasi kaydedilirken hata olustu.")
writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")
