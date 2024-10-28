from common.frontend.template_page import use_template
from common.scriptStrategies.ScriptStrategy import ConfigSenderScriptStrategy

pageName = "configSender"
description = "switchList listesindeki her switch için configFile dosyasındaki konfigürasyonu uygular."
scriptStrategy = ConfigSenderScriptStrategy()

use_template(pageName, description, scriptStrategy, save_config=True, in_config=True)
