# Netmiko ile network otomasyonu
# by Rauf KARAKAŞ

from netmiko import ConnectHandler
from netmiko.exceptions import NetMikoTimeoutException
from netmiko.exceptions import AuthenticationException
from paramiko.ssh_exception import SSHException
from datetime import datetime
import os.path
from pyvis import network as net
from IPython.display import display, HTML
import argparse

# Fonksiyonlari tanimla
def getCdpItems(pageName, output):
    """CDP'de gorunen cihazları port:hostname şeklinde dictionary olarak return eder."""
    try:
        cdpDict = {}
        # CDP ciktisinda "Port ID\n" kelimesinin index'ini bulup, kalan string'i elde et
        cdpOutput = output[(output.find("Port ID\n") + 7):]

        # Gereksiz karakterleri sil, string'i listeye cevir
        while "  " in cdpOutput:
            cdpOutput = cdpOutput.replace("  ", " ")
        cdpOutput = cdpOutput.split(" ")

        # Liste uzerinde "\n" karakterini iceren ogeler ve sonraki 2 ogeyi dict'e ekle
        # Swname\n Eth 0/1
        for i in range(len(cdpOutput)):
            if "\n" in cdpOutput[i]:
                swName = cdpOutput[i].replace("\n", "")
                while "/" in swName:
                    swName = swName[(swName.find("/") + 1):]
                while swName[0].isdigit() or swName[0] == ".":
                    swName = swName[1:]
                if not swName.startswith("SEP"):  # IP telefonlari CDP tablosundan cikar
                    # Isımlendirilmemis AP'leri tum ismi ile al (MAC adresi)
                    # Switch domain name'i sil
                    if "." in swName and not swName.startswith("AP"):
                        swName = swName[:(swName.find("."))]
                    # arswitch1.ar.arcelik
                    # 
                    if i + 2 < len(cdpOutput):
                        portName = cdpOutput[i + 1] + " " + cdpOutput[i + 2]
                        cdpDict[portName] = swName
                        i = i + 2
        if "cdp entries" in cdpDict:
            cdpDict.pop("cdp entries")
        writeToLogfile(pageName, "BILGI: CDP dictionary basariyla olusturuldu.")
        return cdpDict
    except:
        writeToLogfile(pageName, "HATA: CDP dictionary olusturulamadı.")
        return None

def getFullConfig(pageName, session):
    """Cihazda 'show run' ciktisini çalıştırıp, return eder."""
    try:
        deviceConfig = session.send_command("show running-config")
        writeToLogfile(pageName, "BILGI: Cihaz konfigurasyonu SSH ile basariyla alindi.")
        return deviceConfig
    except:
        writeToLogfile(pageName, "HATA: Cihaz konfigurasyonu SSH ile alinamadi.")
        return None

def createConfigBackupFile(pageName, configString, switch):
    """configBackups klasorune switch konfigurasyonunu kaydeder."""
    try:
        fileName = "configBackup_" + switch.replace(".", "_") + ".txt"
        path = f"./{pageName}configBackups"
        configPath = os.path.join(path, fileName)
        with open(configPath, "w", encoding="utf-8") as configFile:
            configFile.write(configString)
        configFile.close()
    except:
        writeToLogfile(pageName, "HATA: Switch konfigurasyon dosyasi olusturulamadi.")

def writeToLogfile(pageName, log):
    """Girilen log metnini txt dosyasina kaydeder ve konsola yazdirir."""
    log_data = "{}: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), log)
    with open(f"./{pageName}logs.txt", "a") as log_file:
        log_file.write(log_data)
    log_file.close()
    print(log_data)

def getUserAnswer(answer):
    """Kullaniciya sorulan e/h sorusunun cevabini return eder."""
    if answer == "e":
        return True
    return False

# Konfigurasyon icin ortami hazirla
try:
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--save-config", dest="saveConfig", help="Konfigürasyon kaydedilsin mi?")
    parser.add_argument("--create-topology", "--create-topology", dest="createTopology", help="Topoloji olusturulsun mu?")
    parser.add_argument("-u", "--username", dest="username", help="Kullanıcı Adı")
    parser.add_argument("-p", "--password", dest="password", help="Parola")
    parser.add_argument("--page-name", "--page-name", dest="pageName", help="Sayfa Adı")

    userArgs = parser.parse_args()
    # Komut istemcisi inputları
    configBackupRequested = getUserAnswer(userArgs.saveConfig)
    topologyRequested = getUserAnswer(userArgs.createTopology)
    if not configBackupRequested and not topologyRequested:
        writeToLogfile(userArgs.pageName, "BILGI: Ister yok. Iptal ediliyor...")
        exit(1)
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
        exit(1)
    # Switch giris bilgilerini al
    user = userArgs.username
    password = userArgs.password
    enablePassword = password
    if configBackupRequested:
        if not os.path.isdir(f"./{userArgs.pageName}configBackups"):
            os.mkdir(f"./{userArgs.pageName}configBackups")
except:
    writeToLogfile(userArgs.pageName, "HATA: On bilgiler alinamadi. Iptal ediliyor...")
    exit(1)

# Her switch icin CDP ciktisini al
switchTreeDict = {}  # Switch altindaki switchlerin tutuldugu dict
switchTreeDatailedDict = {}  # Switch altindaki switchlerin port numaralariyla birlikte tutuldugu dict
for switchIP in switchList:
    try:
        ciscoSwitch = {'device_type': 'cisco_ios', 'host': switchIP,
                       'username': user, 'password': password,
                       'secret': enablePassword, 'port': 22, }
        ssh = ConnectHandler(**ciscoSwitch)
        ssh.enable()
        writeToLogfile(userArgs.pageName, "BILGI: %s IP adresli switch'e baglanildi." % switchIP)
        swName = ssh.find_prompt()
        swName = swName[:-1]
        writeToLogfile(userArgs.pageName, "BILGI: Switch hostname: %s " % swName)

        if configBackupRequested:  # Switch konfigurasyon yedegi al
            rawSwConfig = getFullConfig(userArgs.pageName, ssh)
            createConfigBackupFile(userArgs.pageName, rawSwConfig, switchIP)
            writeToLogfile(userArgs.pageName, "BILGI: Switch konfigurasyonu 'configBackups' klasorune kaydedildi.")
        
        if topologyRequested:
            cdpOutput = ssh.send_command("show cdp neighbors")
            cdpDict = getCdpItems(userArgs.pageName, cdpOutput)
            switchTreeDict[swName] = list(cdpDict.values())
            switchTreeDatailedDict[swName] = cdpDict
        # SSH baglantisini sonlandir
        ssh.disconnect()
    except (NetMikoTimeoutException):
        writeToLogfile(userArgs.pageName, "HATA: %s IP adresli switch'e baglanilamadi. Timeout." % switchIP)
        continue
    except (AuthenticationException):
        writeToLogfile(userArgs.pageName, "HATA: %s IP adresli switch'e baglanilamadi. Parola hatali." % switchIP)
        continue
    except (SSHException):
        writeToLogfile(userArgs.pageName, "HATA: %s IP adresli switch'e SSH ile baglanilamadi. Telnet ile deneyin." % switchIP)
        continue
    except:
        writeToLogfile(userArgs.pageName, "HATA: %s IP adresli switch işlenirken hata oluştu." % switchIP)
        continue

# Topolojiyi ciz
if topologyRequested:
    try:
        graphOptions = {
            "edges": {
                "color": {
                    "inherit": True
                },
                "smooth": False
            },
            "manipulation": {
                "enabled": True
            },
            "interaction": {
                "hover": True
            },
            "physics": {
                "barnesHut": {
                    "damping": 0.6
                },
                "minVelocity": 0.75
            }
        }

        # CDP verisi alinan switchlerin hostname'lerini nodeList'e ekle
        nodeList = list(switchTreeDict.keys())
        # CDP verisi alinan switchlere bagli alt switchleri edgeList'e ekle
        edgeList = list(switchTreeDict.values())
        # Grafik ortamini olustur
        networkGraph = net.Network(height='600px', width='100%', heading='')
        # Node ve edge listesi icindeki tum benzersiz switchleri nodesToAdd listesine ekle
        nodesToAdd = []
        for node in nodeList:
            if node not in nodesToAdd:
                nodesToAdd.append(node)
        for subList in edgeList:
            for edge in subList:
                if edge not in nodesToAdd:
                    nodesToAdd.append(edge)
        # Benzersiz switch'leri ve AP'leri node olarak ekle
        for node in nodesToAdd:
            nodeDetail = node
            if node in nodeList:
                nodeDetail = str(switchTreeDatailedDict[node])
            if "sw" in node.lower():  # Node switch ise varsayılan gorunumu kullan
                networkGraph.add_node(node, title=nodeDetail)
            elif "ap" in node.lower():  # Node AP ise yesile boya
                networkGraph.add_node(node, title=nodeDetail, color="lightgreen")
            else:  # Diger node'lari griye boya
                networkGraph.add_node(node, title=nodeDetail, color="lightgray")
        # nodeList ve edgeList listeleri ile grafigi olustur
        for i in range(len(nodeList)):
            node = nodeList[i]
            for edge in edgeList[i]:
                if node != edge:
                    networkGraph.add_edge(node, edge, color="black")
        networkGraph.toggle_physics(True)
        # networkGraph.show_buttons() # Tum ayar menusunu goster
        networkGraph.options = graphOptions
        networkGraph.show(f"./{userArgs.pageName}networkTopology.html")
        #display(HTML(f"./{userArgs}networkTopology.html"))
        writeToLogfile(userArgs.pageName, "Bilgi: Topolojiye 'networkTopology.html' dosyasindan ulasilabilir.")
    except:
        writeToLogfile(userArgs.pageName, "HATA: Topoloji olusturulurken hata olustu.")

writeToLogfile(userArgs.pageName, "BILGI: Islem tamamlandi.")