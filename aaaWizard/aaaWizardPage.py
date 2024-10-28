from common.frontend.template_page import use_template
from common.scriptStrategies.ScriptStrategy import AAAScriptStrategy

# Sayfa için ID gibi davranır, özel isim olması önemli.
pageName = "aaaWizard"
description = "configFileNew ve configFileOld dosyalarına eski ve yeni syntax AAA konfigürasyonları yükenir. Script switchList listesindeki her switch için enable modda \"show run aaa\" komutunu çalıştırmaya çalışır. Komut çalışıyorsa yeni syntax konfigürasyonu, çalışmıyorsa eski syntax konfigürasyonu uygular."
scriptStrategy = AAAScriptStrategy()

# Kullanıcı adı, parola ve konfigürasyon kaydetme seceneğini içerir
use_template(pageName, description, scriptStrategy, save_config=True)
