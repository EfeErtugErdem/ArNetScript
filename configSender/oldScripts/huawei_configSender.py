# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ

from netmiko import ConnectHandler
from datetime import datetime
import argparse
import os.path
import re
import paramiko

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
    parser.add_argument("--banner-selection", "--banner-selection", dest="bannerSelection", help="Banner gönderilecek mi?")
    parser.add_argument("--selected-banner", "--selected-banner", dest="selectedBanner", help="Gönderilmek istenen banner")
    parser.add_argument("--page-name", "--page-name", dest="pageName", help="Sayfa Adı")

    userArgs = parser.parse_args()
    # switchList.txt dosyasindan IP adreslerini oku ve listeye ekle
    match userArgs.selectedBanner:
        case "Arçelik":
            activeBanner = f"./{userArgs.pageName.strip()}banners/arcelikBanner.txt"
        case "Beko":
            activeBanner = f"./{userArgs.pageName.strip()}banners/bekoBanner.txt"
        case "Defy":
            activeBanner = f"./{userArgs.pageName.strip()}banners/defyBanner.txt"
        case "IHP":
            activeBanner = f"./{userArgs.pageName.strip()}banners/ihpaBanner.txt"
        case "Arctic":
            activeBanner = f"./{userArgs.pageName.strip()}banners/arcticBanner.txt"
        case _:
            activeBanner = None

    switchList = []
    try:
        with open(f"./{userArgs.pageName.strip()}switchList.txt") as file:
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
        writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi olusturuldu.")
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
    enablePassword = password
    # Komut ciktilarinin saklanacagi klasoru olustur
    if not os.path.isdir(f"./{userArgs.pageName}commandOutputs"):
        os.mkdir(f"./{userArgs.pageName}commandOutputs")
except:
    writeToLogfile(userArgs.pageName, "HATA: On bilgiler alinamadi. Iptal ediliyor...")
    exit(1)

# Switchleri konfigure et
for switchIP in switchList:
    try:
        huaweiSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                       'username': user, 'password': password, 'port': 22, }
        ssh = ConnectHandler(**huaweiSwitch)
        ssh.config_mode()
        writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)

        # Konfigürasyon komutlarını gönder
        for configCommand in configList:
            configCommandOutput = ssh.send_command_timing(configCommand)
            # Komut ayrı bir prompt (sonu [Y/N] ile biten) gönderiyorsa cevap gönder
            if re.search(r'\[Y/N\]', configCommandOutput):
                configCommandOutput += ssh.send_command_timing("Y")
            logCommandOutputs(userArgs.pageName, configCommandOutput, switchIP)

        if userArgs.bannerSelection == "e":
            destinationPath = "activeBanner.txt"
            
            # Banner dosyasını göndermek için ssh client hazırla
            sshClient = paramiko.SSHClient()
            sshClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            sshClient.connect(hostname=switchIP, username=user, password=password, port=22)

            # SFTP client ile dosyayı gönder
            sftpClient = sshClient.open_sftp()
            sendBannerFileOutput = sftpClient.put(activeBanner, destinationPath)
            logCommandOutputs(userArgs.pageName, sendBannerFileOutput, switchIP)

            # Gönderilen banner dosyasını switch'in banner'ı olarak ayarla
            setActiveBannerOutput = ssh.send_command_timing(f"header login file flash:{destinationPath}")
            if re.search(r'\[Y/N\]', setActiveBannerOutput):
                setActiveBannerOutput += ssh.send_command_timing("Y")
            logCommandOutputs(userArgs.pageName, setActiveBannerOutput, switchIP)
        writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi uygulandi.")
        
        if wantToSaveConfig:
            saveConfigOutput = ssh.send_command_timing("save current-configuration")
            if re.search(r'\[Y/N\]', saveConfigOutput):
                saveConfigOutput += ssh.send_command_timing("Y")
            logCommandOutputs(userArgs.pageName, saveConfigOutput, switchIP)
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
        ssh.disconnect()
        writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)
writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")
