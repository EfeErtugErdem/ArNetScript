import streamlit as st
import os
from common.frontend.template_DEpage import use_DEpage

pageName = "takeNetworkSnapshotv1_1"
fileList = ["switchList.txt"]

use_DEpage(pageName=pageName, fileNameList=fileList)

st.divider()
st.header("Veri İndirme")

def list_inventory_files(directory):
    return [f for f in os.listdir(directory) if f.endswith(".html")]

@st.cache_data
def read_inventory_file(file_path):
    with open(file_path, "rb") as file:
        return file.read()
    
inventory_dir_path = f"./{pageName}/Reports"
inventory_file_list = list_inventory_files(inventory_dir_path)

selected_file = st.selectbox("İndirmek istediğiniz snapshot dosyasını seçiniz", inventory_file_list)

if selected_file:
    inventory_file_path = os.path.join(inventory_dir_path, selected_file)

    inventory_file_content = read_inventory_file(inventory_file_path)

    st.download_button(
        label="Network Snapshot İndir",
        data=inventory_file_content,
        file_name=selected_file,
        mime="text/html"
    )