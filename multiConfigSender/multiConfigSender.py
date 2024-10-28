# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ

from netmiko import ConnectHandler
from datetime import datetime
import os.path
import argparse

# Kullanılacak fonksiyonlari tanimla
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
        writeToLogfile(pageName,"HATA: Switch konfigurasyon dosyasi olusturulamadi.")

def getUserAnswer(answer):
    """Kullaniciya sorulan e/h sorusunun cevabini return eder."""
    if answer == "e":
        return True
    return False

# Konfigurasyon icin ortami hazirla
try:
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--save-config", dest="saveConfig", help="Konfigürasyon kaydedilsin mi?")
    parser.add_argument("-u", "--username", dest="username", help="Kullanıcı Adı")
    parser.add_argument("-p", "--password", dest="password", help="Parola")
    parser.add_argument("--page-name", "--page-name", dest="pageName", help="Sayfa Adı")

    userArgs = parser.parse_args()
    # configFile.txt dosyasindan uygulanacak konfigurasyonlari ve IP adreslerini oku, dict'e ekle
    configDict = {}
    try:
        with open(f"./{userArgs.pageName}multiConfigFile.txt") as file:
            for line in file:
                if len(line) > 1:
                    # Satir basindaki ve sonundaki bosluklari sil
                    line = line.strip()
                    # IP belirteci (#) olan satiri dict'e key olarak ekle ve karsiligina bos liste ata
                    # Dict yapisi IP-adresi : [config] seklinde olacak
                    if line.startswith("#"):
                        currentKey = line.replace("#", "").strip()
                        configDict[currentKey] = []
                    else:  # Dict value'a konfigurasyonlari ekle
                        configDict[currentKey].append(line)
        writeToLogfile(userArgs.pageName,"BILGI: Konfigurasyon veritabani olusturuldu. %d switch bulundu." % len(configDict))
    except:
        writeToLogfile(userArgs.pageName,"HATA: Konfigurasyon bilgileri alinamadi. Iptal ediliyor...")
        os.abort()
    # Listelerin bos olmadigina emin ol
    if len(configDict) == 0:
        writeToLogfile(userArgs.pageName,"HATA: Switch IP adresi bulunamadi. Iptal ediliyor...")
        os.abort()
    # Konfigurasyonun kaydedilmesi isteniyor mu, bilgi al
    wantToSaveConfig = getUserAnswer(userArgs.saveConfig)
    # Switch giris bilgilerini al
    user = userArgs.username
    password = userArgs.password
    enablePassword = password
    # Komut ciktilarinin saklanacagi klasoru olustur
    if not os.path.isdir(f"./{userArgs.pageName}commandOutputs"):
        os.mkdir(f"./{userArgs.pageName}commandOutputs")
except:
    writeToLogfile(userArgs.pageName,"HATA: On bilgiler alinamadi. Iptal ediliyor...")
    os.abort()

# Switchleri konfigure et
switchList = list(configDict.keys())
for switchIP in switchList:
    try:
        ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                       'username': user, 'password': password,
                       'secret': enablePassword, 'port': 22, }
        ssh = ConnectHandler(**ciscoSwitch)
        ssh.enable()
        writeToLogfile(userArgs.pageName,"BILGI: %s IP adresli switch'e baglanildi." % switchIP)
        configList = configDict[switchIP]
        logCommandOutputs(userArgs.pageName,ssh.send_config_set(configList), switchIP)
        writeToLogfile(userArgs.pageName,"BILGI: Konfigurasyon listesi uygulandi.")
        if wantToSaveConfig:
            logCommandOutputs(userArgs.pageName,ssh.send_command("write"), switchIP)
            writeToLogfile(userArgs.pageName,"BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
        ssh.disconnect()
        writeToLogfile(userArgs.pageName,"BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
    except:
        writeToLogfile(userArgs.pageName,"HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)

writeToLogfile(userArgs.pageName,"BILGI: Islem tamamlandi.")