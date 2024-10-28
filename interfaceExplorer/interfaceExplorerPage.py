from common.frontend.template_page import use_template
from common.scriptStrategies.ScriptStrategy import InterfaceExplorerStrategy

pageName = "interfaceExplorer"
description = \
"""
switchList listesindeki her switch için hangi interface'lerin hangi VLAN'a dahil olduğunu Excel dosyasına yazar. 
Not: Ofis bazlı çalıştırılmalı. Farklı ofis switchleri switchList içinde bulunmamalı.
Lütfen core switch'i (veya VTP sunucusunu) listenin en üstüne yerleştirin, VLANların varlığı en üstteki cihaz ile belirleniyor.
"""
scriptStrategy = InterfaceExplorerStrategy()

use_template(pageName, description, scriptStrategy)