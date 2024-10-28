from common.frontend.template_page import use_template

pageName = "multiConfigSender"
description = "multiConfigFile.txt dosyasını girdi olarak alır. Dosyada switch IP adresi başına # karakteri eklenerek yazılır. Altına ilgili IP adresli switch'e uygulanacak konfigürasyon eklenir. Bu sayede farklı switchlere farklı konfigürasyon uygulanabilmiş olur."
scriptPath = "./multiConfigSender/multiConfigSender.py"

use_template(pageName, description, scriptPath, save_config=True)
