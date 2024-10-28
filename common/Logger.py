from datetime import datetime
import os

class Logger():
    @staticmethod
    def writeToLogfile(pageName, log):
        """Girilen log metnini txt dosyasina kaydeder ve konsola yazdirir."""
        log_data = "({}) {}: {}\n".format(pageName, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), log)
        with open(f"./{pageName}/logs.txt", "a") as log_file:
            log_file.write(log_data)
        log_file.close()
        print(log_data)

    @staticmethod
    def logCommandOutputs(pageName, log, switch):
        """configBackups klasorune switch konfigurasyonunu kaydeder."""
        try:
            fileName = "commandOutputs_" + switch.replace(".", "_") + ".txt"
            path = f"./{pageName}/commandOutputs"
            configPath = os.path.join(path, fileName)
            with open(configPath, "a", encoding="utf-8") as configFile:
                configFile.write(log)
            configFile.close()
            return log
        except:
            Logger.writeToLogfile(pageName, "HATA: Switch konfigurasyon dosyasi olusturulamadi.")

