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
    configListNew = []
    configListOld = []
    try:
        with open(f"./{userArgs.pageName.strip()}configFileNew.txt") as file:
            for line in file:
                if len(line) > 1:
                    configListNew.append(line.strip())
        writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi olusturuldu (Yeni syntax).")
    except:
        writeToLogfile(userArgs.pageName, "HATA: Konfigurasyon bilgileri alinamadi. Iptal ediliyor...")
        exit(1)
    try:
        with open(f"./{userArgs.pageName.strip()}configFileOld.txt") as file:
            for line in file:
                if len(line) > 1:
                    configListOld.append(line.strip())
        writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi olusturuldu (Eski Syntax).")
    except:
        writeToLogfile(userArgs.pageName, "HATA: Konfigurasyon bilgileri alinamadi. Iptal ediliyor...")
        exit(1)
    # Listelerin bos olmadigina emin ol
    if len(switchList) == 0 or len(configListNew) == 0 or len(configListOld) == 0:
        writeToLogfile(userArgs.pageName, "HATA: IP ya da konfigurasyon dosyalarinda eksik bilgi. Iptal ediliyor...")
        exit(1)

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
    writeToLogfile(userArgs.pageName, "HATA: On bilgiler alinamadi. Iptal ediliyor...")
    os.abort()

# Switchleri konfigure et
for switchIP in switchList:
    isNewSyntax = False
    try:
        try:
            # SSH ile baglanmayi dene
            ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                           'username': user, 'password': password,
                           'secret': enablePassword, 'port': 22, }
            ssh = ConnectHandler(**ciscoSwitch)
            ssh.enable()
            swName = ssh.find_prompt()
            swName = swName[:-1]
            if "Invalid input" in ssh.send_command("show run aaa"):
                isNewSyntax = False
            else:
                isNewSyntax = True
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e baglanildi. Hostname: %s" %(switchIP,swName))
            if isNewSyntax:
                logCommandOutputs(userArgs.pageName, ssh.send_config_set(configListNew), switchIP)
                writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi uygulandi (Yeni syntax).")
            else:
                logCommandOutputs(userArgs.pageName, ssh.send_config_set(configListOld), switchIP)
                writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi uygulandi (Eski syntax).")
            if wantToSaveConfig:
                logCommandOutputs(userArgs.pageName, ssh.send_command("write"), switchIP)
                writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
            ssh.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
        except:
            # SSH basarisiz olursa telnet ile baglanmayi dene
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) SSH ile baglanilamadi. Telnet deneniyor." % switchIP)
            ciscoSwitch = {'device_type': 'cisco_ios_telnet', 'host': switchIP,
                           'username': user, 'password': password,
                           'secret': enablePassword, 'port': 23, }
            telnet = ConnectHandler(**ciscoSwitch)
            telnet.enable()
            swName = telnet.find_prompt()
            swName = swName[:-1]
            if "Invalid input" in telnet.send_command("show run aaa"):
                isNewSyntax = False
            else:
                isNewSyntax = True
            writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e baglanildi. Hostname: %s" %(switchIP,swName))
            if isNewSyntax:
                logCommandOutputs(userArgs.pageName, telnet.send_config_set(configListNew), switchIP)
                writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi uygulandi (Yeni syntax).")
            else:
                logCommandOutputs(userArgs.pageName, telnet.send_config_set(configListOld), switchIP)
                writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi uygulandi (Eski syntax).")
            if wantToSaveConfig:
                logCommandOutputs(userArgs.pageName, telnet.send_command("write"), switchIP)
                writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
            telnet.disconnect()
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)

writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")
