# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ

from netmiko import ConnectHandler
from datetime import datetime
import os.path
import argparse
import re


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
        writeToLogfile(pageName, "HATA: Switch konfigurasyon dosyasi olusturulamadi.")


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
    # switchList.txt dosyasindan IP adreslerini oku ve listeye ekle
    switchList = []
    try:
        with open(f"./{userArgs.pageName.strip()}/switchList.txt") as file:
            for line in file:
                if len(line) > 1:
                    switchList.append(line.strip())
        writeToLogfile(userArgs.pageName, "BILGI: Switch IP listesi olusturuldu. %d switch bulundu." % len(switchList))
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch IP bilgileri alinamadi. Iptal ediliyor...")
        exit(1)
    # configFile.txt dosyasindan uygulanacak konfigurasyonlari oku ve listeye ekle
    configList = []
    try:
        with open(f"./{userArgs.pageName.strip()}configFile.txt") as file:
            for line in file:
                if len(line) > 1:
                    configList.append(line.strip())
        writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi olusturuldu (Yeni syntax).")
    except:
        writeToLogfile(userArgs.pageName, "HATA: Konfigurasyon bilgileri alinamadi. Iptal ediliyor...")
        exit(1)
    # Listelerin bos olmadigina emin ol
    if len(switchList) == 0 or len(configList) == 0:
        writeToLogfile(userArgs.pageName, "HATA: IP ya da konfigurasyon dosyalarinda eksik bilgi. Iptal ediliyor...")
        exit(1)

    # Konfigurasyonun kaydedilmesi isteniyor mu, bilgi al
    wantToSaveConfig = getUserAnswer(userArgs.saveConfig)
    # Switch giris bilgilerini al
    user = userArgs.username
    password = userArgs.password
    # Komut ciktilarinin saklanacagi klasoru olustur
    if not os.path.isdir(f"./{userArgs.pageName}commandOutputs"):
        os.mkdir(f"./{userArgs.pageName}commandOutputs")
except:
    writeToLogfile(userArgs.pageName, "HATA: On bilgiler alinamadi. Iptal ediliyor...")
    exit(1)

# Switchleri konfigure et
for switchIP in switchList:
    try:
        try:
            # SSH ile baglanmayi dene
            huaweiSwitch = {'device_type': 'huawei', 'host': switchIP,
                           'username': user, 'password': password, 'port': 22, }
            ssh = ConnectHandler(**huaweiSwitch)
            ssh.config_mode()
            swName = ssh.find_prompt()
            swName = swName[1:-1]
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e baglanildi. Hostname: %s" %(switchIP,swName))
            # Konfigürasyonları uygula
            for configCommand in configList:
                configCommandOutput = ssh.send_command_timing(configCommand)
                # Komut ayrı bir prompt (sonu [Y/N] ile biten) gönderiyorsa cevap gönder
                if re.search(r'\[Y/N\]', configCommandOutput):
                    configCommandOutput += ssh.send_command_timing("Y")
                logCommandOutputs(userArgs.pageName, configCommandOutput, switchIP)
            # "current-configuration'u" startup'a kaydet
            if wantToSaveConfig:
                saveConfigOutput = ssh.send_command_timing("save current-configuration")
                if re.search(r'\[Y/N\]', saveConfigOutput):
                    saveConfigOutput += ssh.send_command_timing("Y")
                logCommandOutputs(userArgs.pageName, saveConfigOutput, switchIP)
                writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
            ssh.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
        except:
            # SSH basarisiz olursa telnet ile baglanmayi dene
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) SSH ile baglanilamadi. Telnet deneniyor." % switchIP)
            huaweiSwitch = {'device_type': 'huawei_telnet', 'host': switchIP,
                           'username': user, 'password': password, 'port': 23, }
            telnet = ConnectHandler(**huaweiSwitch)
            telnet.config_mode()
            swName = telnet.find_prompt()
            swName = swName[1:-1]
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e baglanildi. Hostname: %s" %(switchIP,swName))
            # Konfigürasyonları uygula
            for configCommand in configList:
                configCommandOutput = telnet.send_command_timing(configCommand)
                # Komut ayrı bir prompt (sonu [Y/N] ile biten) gönderiyorsa cevap gönder
                if re.search(r'\[Y/N\]', configCommandOutput):
                    configCommandOutput += telnet.send_command_timing("Y")
                logCommandOutputs(userArgs.pageName, configCommandOutput, switchIP)
            # "current-configuration'u" startup'a kaydet
            if wantToSaveConfig:
                saveConfigOutput = telnet.send_command_timing("save current-configuration")
                if re.search(r'\[Y/N\]', saveConfigOutput):
                    saveConfigOutput += telnet.send_command_timing("Y")
                logCommandOutputs(userArgs.pageName, saveConfigOutput, switchIP)
                writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
            telnet.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)
writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")
