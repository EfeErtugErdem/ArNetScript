from netmiko.ssh_autodetect import SSHDetect
from netmiko import ConnectHandler
from common.Logger import Logger

class DeviceDetector():
    def __init__(self):
        pass
    
    @staticmethod
    def detectDevice(ipAddress: str, pageName: str, args: dict) -> str:
        try:
            potentialHuaweiDevice = {
                'device_type': 'cisco_ios',
                'host': ipAddress,
                'username': args['username'],
                'password': args['password'],
                'secret': args['password']
            }

            Logger.writeToLogfile(pageName, "Cihaz profili cisco_ios icin test ediliyor.")

            ssh = ConnectHandler(**potentialHuaweiDevice)
            ssh.enable()

            Logger.writeToLogfile(pageName, f"En olasi cihaz profili 'cisco_ios'.")
            ssh.disconnect()

            return "cisco_ios"
        except:
            Logger.writeToLogfile(pageName, f"Cisco basarisiz, huawei profili deneniyor.")
            try:
                potentialHuaweiDevice = {
                    'device_type': 'huawei',
                    'host': ipAddress,
                    'username': args['username'],
                    'password': args['password'],
                    'secret': args['password']
                }

                Logger.writeToLogfile(pageName, "Cihaz profili huawei icin test ediliyor.")

                ssh = ConnectHandler(**potentialHuaweiDevice)
                ssh.config_mode()

                Logger.writeToLogfile(pageName, f"En olasi cihaz profili 'huawei'.")
                ssh.disconnect()

                return "huawei"
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Profil belirlerken hata: {e}")
                return

