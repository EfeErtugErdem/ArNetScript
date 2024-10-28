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
arcelikBanner = ["""
banner login ^CC
############################################################################
#                      .++          _    ____   ____ _____ _     ___ _  __ #
#                    -*%%%-        / \  |  _ \ / ___| ____| |   |_ _| |/ / #
#                .-+#%%%%%#.      / _ \ | |_) | |   |  _| | |    | || ' /  #
#            .:=*%%%%%%%%%%*     / ___ \|  _ <| |___| |___| |___ | || . \  #
#      .:-=*#%%%%%%%%%%%%%%%=   /_/   \_\_| \_\\\____|_____|_____|___|_|\_\ #
# =##%%%%%%%%%%%%%%%%%%%%%%%%:                                             #
# .#%%%%%%%%%%%%%%%%%%%%%%%%%#   Yetkisiz erisim yasaktir. Yapilan tum     #
#  -%%%%%%%%%%%%%%%%%%%%%%%%%%*  islemler veya denemeler kayitlanmaktadir. #
#   *%%%%%%%%%%%%%%%%%%%%%%%%%%-                                           #
#   .%%%%%%%%%%%%%%%%%%%%%%%%#-  Unauthorized access is forbidden.         #
#    -%%%%%%%%%%%%%%%%%%%%%#+:   All actions taken or trials done on this  #
#     *%%%%%%%%%%%%%%%%%#+:      device are logged.                        #
#     .#%%%%%%%%%%%%#+=.                                                   #
#      -%%%%%%%%%%+-:.           Email: SYND_ORG_00101026@arcelik.com      #
#        \%%%**                                                            #
############################################################################
^C
!
"""]

bekoBanner = ["""
banner login ^CC
##################################################################
#                                                                #
#  *****                          *****                          #
#  *****                          *****                          #
#  **********::       .:*****:.   *****   :****:   .:*****:.     #
#  **************   .***********  *****  ******  ************:   #
#  *****:    *****  ****    .**** ***** *****.  *****    :****:  #
#  *****     .****:**************.*********:   .****.     *****  #
#  *****     .****:************** **********   :****.     *****  #
#  :****:    ***** .****.         ***** :****:  *****    .****:  #
#   :************   .***********  *****  .*****. ************.   #
#     .:*****::       .:*******:  :***:    :****:  :******:.     #
#                                                          ..    #
#                                            ...::::*********    #
#                              ...:::************************    #
#                ...:::****************************:::....       #
#  ...:::****************************:::...                      #
#  ********************:::...                                    #
#  ******:::...                                                  #
#                                                                #
# Yetkisiz erisim yasaktir. Yapilan tum islemler veya denemeler  #
# kayit altina alinmaktadir.                                     #
#                                                                #
# Unauthorized access is forbidden. All actions taken or trials  #
# done on this device are logged.                                #
#                                                                #
# Email: SYND_ORG_00101026@arcelik.com                           #
#                                                                #
##################################################################
^C
!
"""]

defyBanner = ["""
banner login ^CC
##########################################################################
#                                                                        #
#          .##################################################.          #
#        ########################################################        #
#      #####                                                  #####      #
#     ####    ########.    #########  #########  ###     ###    ####     #
#    ####     ##########   ###        ###         ###   ###      ####    #
#   ####      ###     ###  ###        ###          ###-###        ####   #
#  :####      ###      ##: #########  #########      ###          ####:  #
#   ####      ###     ###  ###        ###            ###          ####   #
#    ####     ##########   ###        ###            ###         ####    #
#     ####    ########'    #########  ###            ###        ####     #
#      #####                                                  #####      #
#        ########################################################        #
#          '##################################################'          #
#                                                                        #
#  Yetkisiz erisim yasaktir. Yapilan tum islemler veya denemeler kayit   #
#  altina alinmaktadir.                                                  #
#                                                                        #
#  Unauthorized access is forbidden. All actions taken or trials done    #
#  on this device are logged.                                            #
#                                                                        #
#  Email: SYND_ORG_00101026@arcelik.com                                  #
#                                                                        #
##########################################################################
^C
!
"""]


ihpaBanner = ["""
banner login ^CC
###################################################################
#                                                                 #
#         ######  ######         ######  ############.            #
#         ######  ######         ######  ##############   .       #
#         ######  ######         ######  #####       ###  #.      #
#         ######  ######         ######  #####       .#.  ##.     #
#         ######  ######         ######  #####       .   .##.     #
#         ######  #####################  #####          .###      #
#         ######  #####################  #####        .####       #
#         ######  ######         ######  #################        #
#         ######  ######         ######  #############*'          #
#         ######  ######         ######  #####                    #
#         ######  ######         ######  #####                    #
#         ######  ######         ######  #####                    #
#                                                                 #
#     _    ____  ____  _     ___    _    _   _  ____ _____ ____   #
#    / \  |  _ \|  _ \| |   |_ _|  / \  | \ | |/ ___| ____/ ___|  #
#   / _ \ | |_) | |_) | |    | |  / _ \ |  \| | |   |  _| \___ \  #
#  / ___ \|  __/|  __/| |___ | | / ___ \| |\  | |___| |___ ___) | #
# /_/   \_\_|   |_|   |_____|___/_/   \_\_| \_|\____|_____|____/  #
#                                                                 #
#   Yetkisiz erisim yasaktir. Yapilan tum islemler veya denemeler #
# kayit altina alinmaktadir.                                      #
#                                                                 #
#   Unauthorized access is forbidden. All actions taken or trials #
# done on this device are logged.                                 #
#                                                                 #
#   Email: SYND_ORG_00101026@arcelik.com                          #
#                                                                 #
###################################################################
^C
"""]

arcticBanner = ["""
banner login ^CC
############################################################################
#                                                                          #
#                                           %%%%                           #
#                                           %%%%                           #
#      .:%%%%%%%:.  .%%%%%%%%   .%%%%%%%%%  %%%%%%%%. %%%%   .%%%%%%%%%    #
#    .%%%%%%%%%%%%  %%%%       %%%%'        %%%%      %%%%  %%%%'          #
#   :%%%'     %%%%  %%%%       %%%%         %%%%      %%%%  %%%%           #
#   :%%%      %%%%  %%%%       %%%%         %%%%      %%%%  %%%%           #
#   .%%%.     %%%%  %%%%       %%%%.        .%%%.     %%%%  %%%%.          #
#    .%%%%%%  %%%%  %%%%        .%%%%%%%%%   '%%%%%%  %%%%   .%%%%%%%%%    #
#                                                                          #
# Yetkisiz erisim yasaktir. Yapilan tum islemler veya denemeler kayit      #
# altina alinmaktadir.                                                     #
#                                                                          #
# Unauthorized access is forbidden. All actions taken or trials done on    #
# this device are logged.                                                  #
#                                                                          #
# Email: SYND_ORG_00101026@arcelik.com                                     #
#                                                                          #
############################################################################
^C
"""]

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
            activeBanner = arcelikBanner
        case "Beko":
            activeBanner = bekoBanner
        case "Defy":
            activeBanner = defyBanner
        case "IHP":
            activeBanner = ihpaBanner
        case "Arctic":
            activeBanner = arcticBanner
        case _:
            activeBanner = None

    switchList = []
    try:
        with open(f"./{userArgs.pageName}switchList.txt") as file:
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
        with open(f"./{userArgs.pageName}configFile.txt") as file:
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
    os.abort()

# Switchleri konfigure et
for switchIP in switchList:
    try:
        ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                       'username': user, 'password': password,
                       'secret': enablePassword, 'port': 22, }
        ssh = ConnectHandler(**ciscoSwitch)
        ssh.enable()
        writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)
        logCommandOutputs(userArgs.pageName, ssh.send_config_set(configList), switchIP)
        if userArgs.bannerSelection == "e":
            logCommandOutputs(userArgs.pageName, ssh.send_config_set(activeBanner, cmd_verify=False), switchIP)
        writeToLogfile(userArgs.pageName, "BILGI: Konfigurasyon listesi uygulandi.")
        if wantToSaveConfig:
            logCommandOutputs(userArgs.pageName, ssh.send_command("write"), switchIP)
            writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) konfigurasyonu kaydedildi." % switchIP)
        ssh.disconnect()
        writeToLogfile(userArgs.pageName, "BILGI: Switch (%s) baglantisi kapatildi." % switchIP)
    except:
        writeToLogfile(userArgs.pageName, "HATA: Switch (%s) konfigure edilirken hata olustu." % switchIP)

writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")
