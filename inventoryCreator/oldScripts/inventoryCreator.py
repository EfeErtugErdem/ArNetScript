# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ

from netmiko import ConnectHandler
from datetime import datetime
import argparse
import os.path
import xlsxwriter


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
    fileName = f"./{userArgs.pageName}inventoryReport_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
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
            ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                           'username': user, 'password': password,
                           'secret': enablePassword, 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitch)
            ssh.enable()
            swName = ssh.find_prompt()[:-1]
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e (%s) SSH ile baglanildi." % (switchIP, swName))
            commandOutput = ssh.send_command("sh inventory | inc SN:")
            commandOutputWithoutSpaces = commandOutput.replace(" ","")
            swInventoryList = commandOutputWithoutSpaces.splitlines()
            for item in swInventoryList:
                if "SN:" in item:
                    excelWorksheet.write(rowNumber, 0, item[item.find("SN:")+3:])
                    excelWorksheet.write(rowNumber, 1, item[(item.find("PID:")+4):(item.find(","))])
                    excelWorksheet.write(rowNumber, 2, swName)
                    excelWorksheet.write(rowNumber, 3, switchIP)
                    rowNumber+=1
            writeToLogfile(userArgs.pageName, "BILGI: Switch envanter bilgisi alindi.")
            ssh.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Switch %s (%s) baglantisi kapatildi." % (switchIP, swName))
        except:
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e (%s) telnet ile baglanti deneniyor." % (switchIP, swName))
            ciscoSwitch = {'device_type': 'cisco_ios_telnet', 'host': switchIP,
                       'username': user, 'password': password,
                       'secret': enablePassword, 'port': 23, }
            telnet = ConnectHandler(**ciscoSwitch)
            telnet.enable()
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e (%s) telnet ile baglanildi." % (switchIP, swName))
            commandOutput = telnet.send_command("sh inventory | inc SN:")
            commandOutputWithoutSpaces = commandOutput.replace(" ","")
            swInventoryList = commandOutputWithoutSpaces.splitlines()
            for item in swInventoryList:
                if "SN:" in item:
                    excelWorksheet.write(rowNumber, 0, item[item.find("SN:")+3:])
                    excelWorksheet.write(rowNumber, 1, item[(item.find("PID:")+4):(item.find(","))])
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
