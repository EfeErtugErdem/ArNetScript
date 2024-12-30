import pandas as pd
import numpy as np
import re
import ipaddress
from common.Logger import Logger

class LogAnalyserRepository():
    """
    LogAnalyserRepository sınıfı, firewall loglarını analiz etmek, temizlemek,
    gruplamak ve nihai kuralları bir Excel dosyasına kaydetmek için tasarlanmıştır.
    """
    def __init__(self):
        """
        Sınıfın başlatıcısıdır. Herhangi bir işlem yapmaz.
        """
        pass

    def analyseFirewallLogs(self, args: dict):
        """
        Firewall log dosyalarını analiz eder, filtreler ve sonuçları bir Excel dosyasına kaydeder.

        Args:
            args (dict): Analiz için gerekli parametreleri içeren bir sözlük.
                - pageName (str): Log işlemleri sırasında kullanılan sayfa ismi.
                - logFilePath (str): Analiz edilecek log dosyasının yolu.
                - portThreshold (int): Destinasyon port gruplama alt eşiği.
                - interfaceThreshold (int): Interface gruplama alt eşiği.

        İşlevler:
            1. Log dosyasını okuma.
            2. Sütun isimlerini düzenleme.
            3. Veriyi temizleme.
            4. Logları sütunlarına göre gruplama.
            5. Subnet bilgisi ekleme.
            6. Son gruplama ve subnet bilgisi işlemleri.
            7. Nihai kuralları oluşturma ve kaydetme.

        Hata Yönetimi:
            - Her adımda oluşan hatalar yakalanır ve loglanır.
            - Hata durumunda işlem durdurulur.

        Not:
            Firewall'dan gelen log dosyaları logAnalyzer/packetLogFiles klasörü içinde aranır.
            Kural dosyaları logAnalyzer/ruleFiles klasörüne yazılır.
        """
        try:
            # 1. Kullanıcı girdilerini al
            pageName = args['pageName']
            logFilePath = args['logFilePath']
            portThreshold = args['portThreshold']
            interfaceThreshold = args['interfaceThreshold']

            input_directory = "packetLogFiles"
            output_directory = "ruleFiles"

            # 2. Firewall'dan gelen log dosyasını oku
            try:
                Logger.writeToLogfile(pageName, "Log dosyasi okunuyor.")
                firewall_log_file = pd.read_excel(f"{pageName}/{input_directory}/{logFilePath}")
                Logger.writeToLogfile(pageName, "Log dosyasi basariyla okundu.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Log dosyasi okunurken hata: {e}.")
                exit(1)

            # 3. Sütun isimlerini düzenle ve gereksiz sütunları kaldır
            try:
                cleaned_column_names = []

                for col_name in list(firewall_log_file.iloc[0]):
                    if col_name is not np.nan:
                        cleaned_column_names.append(col_name.split('=')[0])
                    else:
                        cleaned_column_names.append("None")

                # Düzenlenmiş sütun isimlerini log dosyasına uygula
                firewall_log_file.columns = cleaned_column_names
                Logger.writeToLogfile(pageName, "Sütun isimleri düzenlendi.")

                # Gereksiz sütunları kaldır
                firewall_log_file = firewall_log_file[['action', 'app', 'dstintf', 'dstip', 'dstport', 'srcintf', 'srcip']]
                Logger.writeToLogfile(pageName, "Gereksiz sütunlar silindi.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Sütun isimleri düzenlenirken hata: {e}")
                exit(1)

            # 4. Veri temizleme işlemleri
            try:
                def find_and_replace(cleaned_string):
                    """
                    Verilerde istenmeyen karakterleri kaldırır ve düzenler.

                    Args:
                        cleaned_string (str): Temizlenecek metin.

                    Returns:
                        str: Düzenlenmiş metin.
                    """
                    if cleaned_string is not np.nan:
                        pattern = r'[A-Za-z]+="?([^"]*)"?'
                        return re.findall(pattern, cleaned_string)[0]
                    else:
                        return "None"

                # Tüm sütunlardaki verileri temizle
                for column_name in list(firewall_log_file.columns):
                    firewall_log_file[column_name] = firewall_log_file[column_name].apply(find_and_replace)

                # Geçersiz olan (None) verileri kaldır
                firewall_log_file = firewall_log_file.loc[firewall_log_file['dstport'] != 'None']
                Logger.writeToLogfile(pageName, "Veriler basariyla temizlendi.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Veri temizlenirken hata: {e}")
                exit(1)

            # 5. Logları sütunlarına göre grupla ve dstport'a (destination port) göre filtrele
            try:
                # Destinasyon port bazında logları grupla
                grouped_by_dstport = firewall_log_file \
                                                .groupby(['dstport'], as_index=False)['dstport'] \
                                                .size()
                
                # Detaylı gruplama işlemi yap
                detailed_grouped_logs = firewall_log_file \
                                    .groupby(['dstport', 'srcip', 'srcintf', 'dstip', 'dstintf', 'app'], as_index=False) \
                                    .size()
                Logger.writeToLogfile(pageName, "Log dosyasi gruplandi.")
                
                # Eşik değere göre destinasyon portları filtrele
                filtered_dstport_logs = grouped_by_dstport[grouped_by_dstport['size'] > portThreshold]
                dstport_list = list(filtered_dstport_logs['dstport'])

                # Filtrelenmiş port listesine göre log dosyasını düzenle
                filtered_logs_by_dstport = detailed_grouped_logs[detailed_grouped_logs['dstport'].isin(dstport_list)]
                Logger.writeToLogfile(pageName, "Log dosyasi dstport alt sinirina göre düzenlendi.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Log dosyasi gruplanirken hata: {e}")
                exit(1)

            # 6. Subnet bilgisi yükleme ve eşleme
            try:
                # Subnet listesini dosyadan yükle
                subnetList = []
                with open(f"./{pageName}/interfaceList.txt") as interfaceFile:
                    for line in interfaceFile:
                        if len(line) > 1:
                            subnetList.append(line.strip())
                Logger.writeToLogfile(pageName, "Subnet listesi olusturuldu.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Subnet listesi olusturulurken hata: {e}")
                exit(1)

            def add_source_subnet_info(row):
                """
                Kaynağın subnet bilgisini belirler.

                Args:
                    row (pd.Series): Kaynağın IP bilgisi.

                Returns:
                    str: Subnet bilgisi veya "Unknown".
                """
                ipAddress = row['srcip']
                for subnet in subnetList:
                    subnetPart = subnet.split('-')[0]
                    if ipaddress.ip_address(ipAddress) in ipaddress.ip_network(subnetPart, False):
                        return subnet
                return "Unknown"
            
            def add_destination_subnet_info(row):
                """
                Hedefin subnet bilgisini belirler.

                Args:
                    row (pd.Series): Hedefin IP bilgisi.

                Returns:
                    str: Subnet bilgisi veya "Unknown".
                """
                ipAddress = row['dstip']
                for subnet in subnetList:
                    subnetPart = subnet.split('-')[0]
                    if ipaddress.ip_address(ipAddress) in ipaddress.ip_network(subnetPart, False):
                        return subnet
                return "Unknown"
            
            # Source ve Destination IP adreslerini subnetlere göre grupla
            try:
                subnet_classified_logs = filtered_logs_by_dstport.copy(deep=True)

                # Subnet bilgilerini ekle
                subnet_classified_logs["SourceSubnet"] = subnet_classified_logs.apply(add_source_subnet_info, axis=1)
                subnet_classified_logs["DestinationSubnet"] = subnet_classified_logs.apply(add_destination_subnet_info, axis=1)
                Logger.writeToLogfile(pageName, "Source ve Destination subnet siniflamalari olusturuldu.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Source ve Destination subnet siniflamalari yapilirken hata: {e}")
                exit(1)

            #7. Nihai gruplamaları gerçekleştir ve sonuçları kaydet
            try:
                # IP adreslerini gruplandır ve birleştir
                aggregated_subnet_logs = \
                    subnet_classified_logs \
                    .groupby(['dstport', 'srcintf', 'dstintf', 'SourceSubnet', 'DestinationSubnet'], as_index=False) \
                    .agg({
                        'srcip': lambda x: ','.join(x.unique()),
                        'dstip': lambda x: ','.join(x.unique()),
                        'app': lambda x: ','.join(x.unique()),
                        'size': 'sum'
                    })
                Logger.writeToLogfile(pageName, "Log dosyasi IP adreslerine göre toplandi.")
                
                # Filtreleme işlemini gerçekleştir
                high_traffic_subnet_logs = aggregated_subnet_logs[aggregated_subnet_logs['size'] > interfaceThreshold]
                Logger.writeToLogfile(pageName, "Subnet gruplarina alt sinir uygulandi.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Subnet gruplamasi yapilirken hata: {e}")
                exit(1)

            final_grouped_logs = high_traffic_subnet_logs.copy(deep=True)

            def final_groupings_destination(row):
                """
                Hedef subnetlerin nihai gruplamasını belirler.

                Args:
                    row (pd.Series): Hedef subnet bilgisi.

                Returns:
                    str: Gruplama sonucu subnet bilgisi.
                """
                if row['DestinationSubnet'] == "Unknown":
                    return row['dstip']
                ip_addresses = [ip for ip in row['dstip'].split(',')]
                if len(ip_addresses) < 4:
                    return f"{row['dstip']} ({row['DestinationSubnet']})"
                else:
                    return row['DestinationSubnet']
            
            def final_groupings_source(row):
                """
                Kaynak subnetlerin nihai gruplamasını belirler.

                Args:
                    row (pd.Series): Kaynak subnet bilgisi.

                Returns:
                    str: Gruplama sonucu subnet bilgisi.
                """
                if row['SourceSubnet'] == "Unknown":
                    return row['srcip']
                ip_addresses = [ip for ip in row['srcip'].split(',')]
                if len(ip_addresses) < 4:
                    return f"{row['srcip']} ({row['SourceSubnet']})"
                else:
                    return row['SourceSubnet']
            
            #Source ve Destination sütunlarını oluştur
            try:
                final_grouped_logs['DestinationSubnetGrouped'] = final_grouped_logs \
                                                        .apply(final_groupings_destination, axis=1)
                final_grouped_logs['SourceSubnetGrouped'] = final_grouped_logs \
                                                        .apply(final_groupings_source, axis=1)
                
                final_grouped_logs = final_grouped_logs[
                    ['dstport', 'srcintf', 'dstintf', 'SourceSubnetGrouped', 'DestinationSubnetGrouped', 'app', 'size']
                ]
                Logger.writeToLogfile(pageName, "Source ve Destination sütunlari olusturuldu.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Source ve Destination olusturulurken hata: {e}")

            #Son kural dosyasının oluştur
            try:
                intermediate_grouped_logs = final_grouped_logs \
                                    .groupby(['dstport', 'srcintf', 'dstintf', 'DestinationSubnetGrouped'], as_index=False) \
                                    .agg({
                                        'SourceSubnetGrouped': lambda x: ', '.join(x.unique()),
                                        'app': lambda x: ', '.join(x.unique()),
                                        'size': 'sum'
                                    })
                
                final_rule_file = intermediate_grouped_logs \
                                    .groupby(['dstport', 'srcintf', 'dstintf', 'SourceSubnetGrouped'], as_index=False) \
                                    .agg({
                                        'DestinationSubnetGrouped': lambda x: ', '.join(x.unique()),
                                        'app': lambda x: ', '.join(x.unique()),
                                        'size': 'sum'
                                    })
                
                final_rule_file = final_rule_file[
                    ['dstport', 'srcintf', 'dstintf', 'SourceSubnetGrouped', 'DestinationSubnetGrouped', 'app', 'size']
                ]
                Logger.writeToLogfile(pageName, "Final kural dosyasi olusturuldu.")

                final_rule_file.to_excel(f"./{pageName}/{output_directory}/{logFilePath.split('.')[0]}_rules.xlsx", index=False)
                Logger.writeToLogfile(pageName, "Nihai kurallar excel dosyasina kaydedildi.")
            except Exception as e:
                Logger.writeToLogfile(pageName, f"Nihai kurallar olusturulurken hata: {e}")
        except Exception as e:
            Logger.writeToLogfile(pageName, f"Script çalisirken hata: {e}")