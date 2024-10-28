# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ

from netmiko import ConnectHandler
from datetime import datetime
import argparse
import os.path


# Kullanılacak fonksiyonlari tanimla

def writeToLogfile(pageName, log):
    """Girilen log metnini txt dosyasina kaydeder ve konsola yazdirir."""
    log_data = "{}: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), log)
    with open(f"./{pageName}logs.txt", "a") as log_file:
        log_file.write(log_data)
    log_file.close()
    print(log_data)


def logCommandOutputs(pageName, log, switch=None):
    """configBackups klasorune switch konfigurasyonunu kaydeder."""
    try:
        fileName = "allOutput_{}.txt".format(datetime.now().strftime('%Y-%m-%d'))
        path = f"./{pageName}commandOutputs"
        configPath = os.path.join(path, fileName)
        with open(configPath, "a", encoding="utf-8") as configFile:
            configFile.write(log)
        configFile.close()
        return log
    except:
        writeToLogfile(pageName, "HATA: Switch konfigurasyon dosyasi olusturulamadi.")


# Konfigurasyon icin ortami hazirla
try:
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--username", dest="username", help="Kullanıcı Adı")
    parser.add_argument("-p", "--password", dest="password", help="Parola")
    parser.add_argument("-c", "--command", dest="command", help="Cihazda Çalıştırılacak Komut")
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
        writeToLogfile(userArgs.pageName, "HATA: Switch listesinde eksik bilgi. Iptal ediliyor...")
        os.abort()
    # Calistirilacak komut bilgisini al
    commandToExecute = userArgs.command
    if len(commandToExecute) <= 3:
        writeToLogfile(userArgs.pageName, "HATA: Girilen komut hatali. Iptal ediliyor...")
        os.abort()
    # Switch giris bilgilerini al
    user = userArgs.username
    password = userArgs.password
    enablePassword = password
    # Komut ciktilarinin saklanacagi klasoru olustur
    if not os.path.isdir(f"./{userArgs.pageName}commandOutputs"):
        os.mkdir(f"./{userArgs.pageName}commandOutputs")
except:
    writeToLogfile(userArgs.pageName, "HATA: On bilgiler alinamadi. Iptal ediliyor...")
    os.abort()

# Switchleri konfigure et
for switchIP in switchList:
    try:
        try:
            ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                           'username': user, 'password': password,
                           'secret': enablePassword, 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitch)
            ssh.enable()
            swName = ssh.find_prompt()[:-1]
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)
            commandOutput = ssh.send_command(commandToExecute)
            logCommandOutputs(userArgs.pageName, "%s: %s" %(swName,commandOutput), switchIP)
            ssh.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Komut calistirildi, switch (%s) baglantisi kapatildi." % switchIP)
        except:
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e telnet ile baglanti deneniyor." % switchIP)
            ciscoSwitch = {'device_type': 'cisco_ios_telnet', 'host': switchIP,
                       'username': user, 'password': password,
                       'secret': enablePassword, 'port': 23, }
            telnet = ConnectHandler(**ciscoSwitch)
            telnet.enable()
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e telnet ile baglanildi." % switchIP)
            commandOutput = telnet.send_command(commandToExecute)
            logCommandOutputs(userArgs.pageName, "%s: %s" %(swName,commandOutput), switchIP)
            telnet.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Komut calistirildi, switch (%s) baglantisi kapatildi." % switchIP)
    except Exception as e:
        writeToLogfile(userArgs.pageName, f"HATA: Switch ({switchIP}) konfigure edilirken hata olustu. Exception {e}")

writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")
