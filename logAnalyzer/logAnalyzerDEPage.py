from common.frontend.template_DEpage import use_DEpage
import os
import streamlit as st

pageName = "logAnalyzer"
fileList = []

def list_files(pageName, directory=None):
    if directory is None:
        return [f for f in os.listdir(f"./{pageName}") if os.path.isfile(f"./{pageName}/{f}") and (not f.endswith(".py"))]    
    return [f"{directory}/{f}" for f in os.listdir(f"./{pageName}/{directory}") if os.path.isfile(f"./{pageName}/{directory}/{f}") and (not f.endswith(".py"))]

fileList += list_files(pageName, "ruleFiles")
fileList += list_files(pageName)

use_DEpage(pageName=pageName, fileNameList=fileList)

st.header("Dosya Yükleme")
st.write("Lütfen yüklemek istediğiniz firewall log dosyasını buradan yükleyiniz.")

uploaded_file = st.file_uploader(
    "Log Dosyası Seçiniz",
    type=['xlsx'], 
    accept_multiple_files=False)
if st.button("Yükle") and uploaded_file is not None:
    with open(f"./{pageName}/packetLogFiles/{uploaded_file.name}", "wb") as logFile:
        logFile.write(uploaded_file.read())
    if os.path.isfile(f"./{pageName}/packetLogFiles/{uploaded_file.name}"):
        st.write("Dosya başarıyla yüklendi.")
