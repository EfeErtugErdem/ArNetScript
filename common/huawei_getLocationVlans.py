from netmiko import ConnectHandler
from datetime import datetime
import os.path
import textfsm

def writeToLogfile(pageName, log):
    """Girilen log metnini txt dosyasina kaydeder ve konsola yazdirir."""
    log_data = "{}: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), log)
    with open(f"./{pageName}logs.txt", "a") as log_file:
        log_file.write(log_data)
    log_file.close()
    print(log_data)

def getVlanListToWorkOn(pageName, vlanCommandOutput):
    """sh vlan ciktisina ve kullanici girdisine gore islem yapilacak vlanlari liste formatinda return eder."""
    try:
        # Vlan listesini kullaniciyla paylas ve lokasyon vlan listesini olustur
        locationVlanList = []
        writeToLogfile(pageName, "Lokasyon vlan bilgileri")
        for item in vlanCommandOutput:
            writeToLogfile(pageName, "Vlan ID: %s, Vlan Name: %s" %(item['VID'], item['Description']))
            locationVlanList.append(item['VID'])
        return locationVlanList
    except:
        writeToLogfile(pageName, "HATA: Vlan listesi olusturulamadi.")
        return None

def getLocationVlans(in_username: str, in_password: str, sharedState, pageName: str):
    try:
        # Switch giris bilgilerini al
        user = in_username
        password = in_password
        # switchList.txt dosyasindan IP adreslerini oku ve listeye ekle
        switchList = []
        try:
            with open(f"./{pageName}switchList.txt") as file:
                for line in file:
                    if len(line) > 1:
                        switchList.append(line.strip())
            # Listenin bos olmadigina emin ol
            if len(switchList) == 0:
                writeToLogfile(pageName, "HATA: Switch IP dosyasinda eksik bilgi. Iptal ediliyor...")
                sharedState["task_done"] = True
                exit(1)
            writeToLogfile(pageName, "BILGI: Switch IP listesi olusturuldu. %d switch bulundu." % len(switchList))
        except:
            writeToLogfile(pageName, "HATA: Switch IP bilgileri alinamadi. Iptal ediliyor...")
            sharedState["task_done"] = True
            exit(1)
        # Komut ciktilarinin saklanacagi klasoru olustur
        if not os.path.isdir(f"./{pageName}commandOutputs"):
            os.mkdir(f"./{pageName}commandOutputs")

        # Ilk switch'e baglanarak vlan bilgilerini cek
        try:
            try:
                # SSH ile baglanmayi dene
                switchIP = switchList[0]
                huaweiSwitchSSH = {'device_type': 'huawei', 'host': switchIP,
                        'username': user, 'password': password, 'port': 22, }
                ssh = ConnectHandler(**huaweiSwitchSSH)
                ssh.config_mode()
                writeToLogfile(pageName, "BILGI: Vlan listesi icin switche baglanildi.")
                shVlanOutput = ssh.send_command("display vlan")

                with open("./common/textfsmTemplates/huaweiVlanTemplate.textfsm") as vlanTemplateFile:
                    vlanOutputTemplate = textfsm.TextFSM(vlanTemplateFile)
                    parsedVlanOutput = vlanOutputTemplate.ParseText(shVlanOutput)
                    vlanHeaders = vlanOutputTemplate.header

                VLANDict = [dict(zip(vlanHeaders, row)) for row in parsedVlanOutput]
                # SSH baglantisini sonlandir
                ssh.disconnect()
            except:
                # SSH basarisiz olursa telnet ile baglanmayi dene
                writeToLogfile(pageName, "BILGI: SSH basarisiz, telnet deneniyor.")
                switchIP = switchList[0]
                huaweiSwitchTelnet = {'device_type': 'huawei_telnet', 'host': switchIP,
                            'username': user, 'password': password, 'port': 23, }
                telnet = ConnectHandler(**huaweiSwitchTelnet)
                telnet.config_mode()
                writeToLogfile(pageName, "BILGI: Vlan listesi icin switche telnet ile baglanildi.")
                shVlanOutput = telnet.send_command("display vlan")

                with open("./common/textfsmTemplates/huaweiVlanTemplate.textfsm") as vlanTemplateFile:
                    vlanOutputTemplate = textfsm.TextFSM(vlanTemplateFile)
                    parsedVlanOutput = vlanOutputTemplate.ParseText(shVlanOutput)
                    vlanHeaders = vlanOutputTemplate.header

                VLANDict = [dict(zip(vlanHeaders, row)) for row in parsedVlanOutput]
                # SSH baglantisini sonlandir
                telnet.disconnect()
        except:
            writeToLogfile(pageName, "HATA: Vlan listesi alinirken hata olustu.")
            sharedState["task_done"] = True
            exit(1)

        # Kullaniciya hangi vlan'larda islem yapılacagini sor ve vlan listesini olustur
        dot1xVlanList = getVlanListToWorkOn(pageName, VLANDict)

        sharedState["vlan_list"] = dot1xVlanList
        sharedState["task_done"] = True
    except Exception as e:
        writeToLogfile(pageName, f"HATA: On bilgiler alinamadi. Iptal ediliyor... Exception: {e}")
        sharedState["task_done"] = True
        exit(1)