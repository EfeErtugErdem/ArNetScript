import streamlit as st

## Uygulamanın giriş noktası burasıdır. Yeni bir arayüz sayfası oluşturulmak istendiğinde 
## aşağıdaki örnekler gibi arayüz sayfası ve veri düzenleme sayfası oluşturulmalıdır.

st.logo("./common/images/beko_logo_1.png", link=None)

# Giriş sayfası
landing_page = st.Page("./landingPage.py", title="Giriş Sayfası", icon=":material/add_circle:")

# AAA konfigürasyonlarını cihazlara uygular.
aaaWizard_page = st.Page("./aaaWizard/aaaWizardPage.py",
                         title="aaaWizard", icon=":material/add_circle:")
aaaWizard_DEpage = st.Page("./aaaWizard/aaaWizardDEPage.py",
                           title="aaaWizard Data Edit", icon=":material/add_circle:")

# Cihazlara kullanıcının istediği konfigürasyonları uygulamak için kullanılır.
configSender_page = st.Page("./configSender/configSenderPage.py",
                            title="configSender", icon=":material/add_circle:")
configSender_DEpage = st.Page("./configSender/configSenderDEPage.py",
                              title="configSender Data Editing", icon=":material/add_circle:")

# Farklı IP adreslerindeki cihazlara farklı konfigürasyonları uygulamak için kullanılır.
multiConfigSender_page = st.Page("./multiConfigSender/multiConfigSenderPage.py", 
                                 title="multiConfigSender", icon=":material/add_circle:")
multiConfigSender_DEpage = st.Page("./multiConfigSender/multiConfigSenderDEPage.py", 
                                   title="multiConfigSender Data Edit", icon=":material/add_circle:")

# Network cihazlarına 892.1X konfigürasyonlarını uygulamak, konfigürasyonları silmek ve interfacelerdeki
# MAC adreslerini çekmek için kullanılır.
dot1xWizard_page = st.Page("./dot1xWizard/dot1xWizardPage.py", 
                                 title="dot1xWizard", icon=":material/add_circle:")
dot1xWizard_DEpage = st.Page("./dot1xWizard/dot1xWizardDEPage.py",
                                 title="dot1xWizard Data Edit", icon=":material/add_circle:")

# Cihazlara yüksek yetkili komut uygulamak için kullanılır.
enableCommandSender_page = st.Page("./enableCommandSender/enableCommandSenderPage.py", 
                                   title="enableCommandSender", icon=":material/add_circle:")
enableCommandSender_DEpage = st.Page("./enableCommandSender/enableCommandSenderDEPage.py", 
                                     title="enableCommandSender Data Editing", icon=":material/add_circle:")

# Cihazlardaki interfaceleri ait oldukları VLAN'lara göre kaydetmek için kullanılır.
interfaceExplorer_page = st.Page("./interfaceExplorer/interfaceExplorerPage.py", 
                                 title="interfaceExplorer", icon=":material/add_circle:")
interfaceExplorer_DEpage = st.Page("./interfaceExplorer/interfaceExplorerDEPage.py",
                                   title="interfaceExplorer Data Edit", icon=":material/add_circle:")

# Cihazlardan envanter dökümü almak için kullanılır.
inventoryCreator_page = st.Page("./inventoryCreator/inventoryCreatorPage.py",
                                title="inventoryCreator", icon=":material/add_circle:")
inventoryCreator_DEpage = st.Page("./inventoryCreator/inventoryCreatorDEPage.py",
                                  title="inventoryCreator Data Edit", icon=":material/add_circle:")

# Kurumsal ağdaki network cihazları arasındaki bağlantıları bir graph halinde kullanıcıya sunar.
takeNetworkSnapshotv1_1_page = st.Page("./takeNetworkSnapshotv1_1/takeNetworkSnapshotv1_1Page.py",
                                       title="takeNetworkSnapshot", icon=":material/add_circle:")
takeNetworkSnapshotv1_1_DEpage = st.Page("./takeNetworkSnapshotv1_1/takeNetworkSnapshotv1_1DEPage.py",
                                         title="takeNetworkSnapshot Data Edit", icon=":material/add_circle:")

# Verilen trafik log dosyasını analiz ederek firewall kuralları oluşturur. 
logAnalyzer_page = st.Page("./logAnalyzer/logAnalyzerPage.py", 
                           title="logAnalyzer", icon=":material/add_circle:")
logAnalyzer_DEpage = st.Page("./logAnalyzer/logAnalyzerDEPage.py", 
                             title="logAnalyzer Data Edit", icon=":material/add_circle:")

# Web arayüzünün sol tarafındaki sayfa navigatörünü oluşturur. 
# Yeni bir sayfa eklendiğinde bu alana eklenmesi zorunludur.
pg = st.navigation(
        {
            "": [landing_page],
            "AAA Wizard": [aaaWizard_page, aaaWizard_DEpage],
            "Config Sender": [configSender_page, configSender_DEpage],
            "Multi Config Sender": [multiConfigSender_page, multiConfigSender_DEpage],
            "802.1x Wizard": [dot1xWizard_page, dot1xWizard_DEpage],
            "Enable Command Sender": [enableCommandSender_page, enableCommandSender_DEpage],
            "Interface Explorer": [interfaceExplorer_page, interfaceExplorer_DEpage],
            "Inventory Creator": [inventoryCreator_page, inventoryCreator_DEpage],
            "Network Snapshot Taker": [takeNetworkSnapshotv1_1_page, takeNetworkSnapshotv1_1_DEpage],
            "Log Analyzer": [logAnalyzer_page, logAnalyzer_DEpage]
        }
    )

pg.run()
