import pandas as pd
import numpy as np
import re
import argparse
from datetime import datetime
import ipaddress

################################# ORTAK FONKSİYONLAR ###################################

def writeToLogfile(log, pageName=""):
    """Girilen log metnini txt dosyasina kaydeder ve konsola yazdirir."""
    log_data = "{}: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), log)
    with open(f"./{pageName}logs.txt", "a") as log_file:
        log_file.write(log_data)
    log_file.close()
    print(log_data)

########################################################################################
################################### UYGULAMA BEYNİ #####################################
########################################################################################

try:
    # Kullanıcı girdilerini al
    try:
        parser = argparse.ArgumentParser()

        parser.add_argument("-l", "--log-file", dest="logFile", help="Kuralların çıkarılacağı log dosyası.")
        parser.add_argument("-p", "--port-threshold", dest="portThreshold", help="Destination port'un kabul edilmesi için alt sınır")
        parser.add_argument("-i", "--interface-threshold", dest="interfaceThreshold", help="Interface'in kabul edilmesi için alt sınır")
        
        userArgs = parser.parse_args()
        writeToLogfile("Kullanici girdileri okundu.")
    except Exception as e:
        writeToLogfile(f"Kullanici girdileri olunamadi. Exception: {e}")
        exit(1)

    logFilePath = userArgs.logFile
    portThreshold = int(userArgs.portThreshold)
    interfaceThreshold = int(userArgs.interfaceThreshold)

    #Log dosyasını oku
    try:
        writeToLogfile("Log dosyasi okunuyor.")
        log_file = pd.read_excel(logFilePath)
        writeToLogfile("Log dosyasi basariyla okundu.")
    except Exception as e:
        writeToLogfile(f"Log dosyasi okunurken hata: {e}.")
        exit(1)

    #Sütun isimlerini düzenle
    try:
        column_name_list = []

        for col_name in list(log_file.iloc[0]):
            if col_name is not np.nan:
                column_name_list.append(col_name.split('=')[0])
            else:
                column_name_list.append("None")

        log_file.columns = column_name_list
        writeToLogfile("Sütun isimleri düzenlendi.")

        log_file = log_file[['action', 'app', 'dstintf', 'dstip', 'dstport', 'srcintf', 'srcip']]
        writeToLogfile("Gereksiz sütunlar silindi.")
    except Exception as e:
        writeToLogfile(f"Sütun isimleri düzenlenirken hata: {e}")
        exit(1)

    #Veri temizleme
    try:
        def find_and_replace(cleaned_string):
            if cleaned_string is not np.nan:
                pattern = r'[A-Za-z]+="?([^"]*)"?'
                return re.findall(pattern, cleaned_string)[0]
            else:
                return "None"

        for column_name in list(log_file.columns):
            log_file[column_name] = log_file[column_name].apply(find_and_replace)

        log_file = log_file.loc[log_file['dstport'] != 'None']
        writeToLogfile("Veriler basariyla temizlendi.")
    except Exception as e:
        writeToLogfile(f"Veri temizlenirken hata: {e}")
        exit(1)

    #Logları sütunlarına göre grupla ve dstporta göre filtrele
    try:
        dstport_grouped_log_file = log_file \
                                        .groupby(['dstport'], as_index=False)['dstport'] \
                                        .size()
        grouped_log_file = log_file \
                            .groupby(['dstport', 'srcip', 'srcintf', 'dstip', 'dstintf', 'app'], as_index=False) \
                            .size()
        writeToLogfile("Log dosyasi gruplandi.")
        
        dstport_grouped_log_file_filtered = \
            dstport_grouped_log_file[dstport_grouped_log_file['size'] > portThreshold]
        dstport_list = list(dstport_grouped_log_file_filtered['dstport'])

        filtered_grouped_log_file = grouped_log_file[grouped_log_file['dstport'].isin(dstport_list)]
        writeToLogfile("Log dosyasi dstport alt sinirina göre düzenlendi.")
    except Exception as e:
        writeToLogfile(f"Log dosyasi gruplanirken hata: {e}")
        exit(1)

    rule_stage_log_file = filtered_grouped_log_file.copy(deep=True)

    try:
        subnetList = []
        with open("interfaceList.txt") as interfaceFile:
            for line in interfaceFile:
                if len(line) > 1:
                    subnetList.append(line.strip())
        writeToLogfile("Subnet listesi olusturuldu.")
    except Exception as e:
        writeToLogfile(f"Subnet listesi olusturulurken hata: {e}")
        exit(1)

    def add_source_subnet_info(row):
        ipAddress = row['srcip']
        for subnet in subnetList:
            subnetPart = subnet.split('-')[0]
            if ipaddress.ip_address(ipAddress) in ipaddress.ip_network(subnetPart, False):
                return subnet
        return "Unknown"
    
    def add_destination_subnet_info(row):
        ipAddress = row['dstip']
        for subnet in subnetList:
            subnetPart = subnet.split('-')[0]
            if ipaddress.ip_address(ipAddress) in ipaddress.ip_network(subnetPart, False):
                return subnet
        return "Unknown"
    
    # Source ve Destination IP adreslerini subnetlere göre grupla
    try:
        rule_stage_log_file["SourceSubnet"] = rule_stage_log_file.apply(add_source_subnet_info, axis=1)
        rule_stage_log_file["DestinationSubnet"] = rule_stage_log_file.apply(add_destination_subnet_info, axis=1)
        writeToLogfile("Source ve Destination subnet siniflamalari olusturuldu.")
    except Exception as e:
        writeToLogfile(f"Source ve Destination subnet siniflamalari yapilirken hata: {e}")
        exit(1)

    #IP adreslerini bir araya topla
    try:
        int_grouped_rule_stage_log_file = \
            rule_stage_log_file \
            .groupby(['dstport', 'srcintf', 'dstintf', 'SourceSubnet', 'DestinationSubnet'], as_index=False) \
            .agg({
                'srcip': lambda x: ','.join(x.unique()),
                'dstip': lambda x: ','.join(x.unique()),
                'app': lambda x: ','.join(x.unique()),
                'size': 'sum'
            })
        writeToLogfile("Log dosyasi IP adreslerine göre toplandi.")
        
        int_grouped_rule_stage_log_file_highcount = \
            int_grouped_rule_stage_log_file[int_grouped_rule_stage_log_file['size'] > interfaceThreshold]
        writeToLogfile("Subnet gruplarina alt sinir uygulandi.")
    except Exception as e:
        writeToLogfile(f"Subnet gruplamasi yapilirken hata: {e}")
        exit(1)

    final_stage_rule_file = int_grouped_rule_stage_log_file_highcount

    def final_groupings_destination(row):
            if row['DestinationSubnet'] == "Unknown":
                return row['dstip']
            ip_addresses = [ip for ip in row['dstip'].split(',')]
            if len(ip_addresses) < 4:
                return f"{row['dstip']} ({row['DestinationSubnet']})"
            else:
                return row['DestinationSubnet']
    
    def final_groupings_source(row):
                if row['SourceSubnet'] == "Unknown":
                    return row['srcip']
                ip_addresses = [ip for ip in row['srcip'].split(',')]
                if len(ip_addresses) < 4:
                    return f"{row['srcip']} ({row['SourceSubnet']})"
                else:
                    return row['SourceSubnet']
    
    #Source ve Destination sütunlarını oluştur
    try:
        final_stage_rule_file['DestinationSubnetGrouped'] = final_stage_rule_file \
                                                .apply(final_groupings_destination, axis=1)
        final_stage_rule_file['SourceSubnetGrouped'] = final_stage_rule_file \
                                                .apply(final_groupings_source, axis=1)
        
        final_stage_rule_file = final_stage_rule_file[
            ['dstport', 'srcintf', 'dstintf', 'SourceSubnetGrouped', 'DestinationSubnetGrouped', 'app', 'size']
        ]
        writeToLogfile("Source ve Destination sütunlari olusturuldu.")
    except Exception as e:
        writeToLogfile(f"Source ve Destination olusturulurken hata: {e}")

    #Son kural dosyasının oluştur
    try:
        final_rule_file_pre = final_stage_rule_file \
                            .groupby(['dstport', 'srcintf', 'dstintf', 'DestinationSubnetGrouped'], as_index=False) \
                            .agg({
                                'SourceSubnetGrouped': lambda x: ', '.join(x.unique()),
                                'app': lambda x: ', '.join(x.unique()),
                                'size': 'sum'
                            })
        
        final_rule_file = final_rule_file_pre \
                            .groupby(['dstport', 'srcintf', 'dstintf', 'SourceSubnetGrouped'], as_index=False) \
                            .agg({
                                'DestinationSubnetGrouped': lambda x: ', '.join(x.unique()),
                                'app': lambda x: ', '.join(x.unique()),
                                'size': 'sum'
                            })
        
        final_rule_file = final_rule_file[
            ['dstport', 'srcintf', 'dstintf', 'SourceSubnetGrouped', 'DestinationSubnetGrouped', 'app', 'size']
        ]
        writeToLogfile("Final kural dosyasi olusturuldu.")

        final_rule_file.to_excel("final_rules.xlsx", index=False)
        writeToLogfile("Nihai kurallar excel dosyasina kaydedildi.")
    except Exception as e:
        writeToLogfile(f"Nihai kurallar olusturulurken hata: {e}")
except Exception as e:
    writeToLogfile(f"Script çalisirken hata: {e}")