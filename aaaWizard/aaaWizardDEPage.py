from common.frontend.template_DEpage import use_DEpage

# Sayfa için ID gibi davranır, özel isim olması önemli
pageName = "aaaWizard"
fileList = ["switchList.txt", "configFileOld.txt", "configFileNew.txt"]

# Klasörün altında bulunan değiştirilebilen dosyaların listesi
use_DEpage(pageName=pageName, fileNameList=fileList)