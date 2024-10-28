from common.frontend.template_page import use_template
from common.scriptStrategies.ScriptStrategy import SendEnableCommandsStrategy

pageName = "enableCommandSender"
description = "switchList listesindeki her switch için enable modda script çalıştırıldığında girilen komutu çalıştırır ve çıktılarını dosyaya yazar."
scriptStrategy = SendEnableCommandsStrategy()

use_template(pageName, description, scriptStrategy, in_command=True)
