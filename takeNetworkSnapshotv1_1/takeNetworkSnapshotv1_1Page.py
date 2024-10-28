from common.frontend.template_page import use_template
from common.scriptStrategies.ScriptStrategy import TakeNetworkSnapshotStrategy

pageName = "takeNetworkSnapshotv1_1"
description = "switchList.txt dosyasında IP adresleri belirtilen switchlere bağlanarak konfigürasyon yedeklerini alır. Switchlere bağlı, CDP'de görünen diğer cihazların listesini tutar ve bağlantıların topolojisini çıkarır. Yedek alınması ve topoloji çıkarılması tek başına da uygulanabilir."
scriptStrategy = TakeNetworkSnapshotStrategy()

use_template(pageName, description, scriptStrategy, save_config=True, in_topology=True)