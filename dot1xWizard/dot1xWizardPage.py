from common.frontend.template_page import use_template
from common.scriptStrategies.ScriptStrategy import Dot1xWizardStrategy

# Sayfa için ID gibi davranır, özel isim olması önemli.
pageName = "dot1xWizard"
description = "Dot1x konfigürasyonları için wizard."
scriptStrategy = Dot1xWizardStrategy()

# Kullanıcı adı, parola, konfigürasyon kaydetme ve VLAN seceneklerini içerir
use_template(pageName, description, scriptStrategy, save_config=True, in_vlan=True)