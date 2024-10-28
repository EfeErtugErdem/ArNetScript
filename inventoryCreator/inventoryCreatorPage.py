from common.frontend.template_page import use_template
from common.scriptStrategies.ScriptStrategy import InventoryCreatorStrategy

pageName = "inventoryCreator"
description = "switchList listesindeki her switch için \"show inventory\" komutu çalıştırılıp içerik bilgisi Excel dosyasına kaydedilir."
scriptPath = InventoryCreatorStrategy()

use_template(pageName, description, scriptPath)