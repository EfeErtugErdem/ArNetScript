import streamlit as st
import pandas as pd

def use_DEpage(pageName, fileNameList):
    st.header("Veri Düzenleme ve Görüntüleme", divider="grey")

    st.write("ONEMLI: Tablo değiştirmeden önce değişikliklerinizi kaydedin.")

    selection = st.selectbox(
        "Düzenlenecek dosyayi seçiniz",
        (fileName for fileName in fileNameList)
    )
    
    if selection.endswith(".xlsx"):
        currentTable = pd.read_excel(f"./{pageName}/{selection}")
    else:
        currentTable = pd.read_table(f"./{pageName}/{selection}", delimiter='\t', header=None)

    editedTable = st.data_editor(currentTable, num_rows="dynamic")
    editedInText = st.checkbox("Dosyayı text olarak düzenle") 
    if editedInText:
        editedText = st.text_area(label="Dosya", 
                                  value="\n".join(editedTable.apply(lambda row: " ".join([str(item).ljust(10) for item in row]), axis=1))
                                 )

    def read_file(file_path):
        with open(file_path, "rb") as file:
            return file.read()

    saveButtonLocation, downloadButtonLocation = st.columns(2)
    with saveButtonLocation:
        saveButton = st.button("Kaydet")
        if saveButton:
            if editedInText:
                with open(f"./{pageName}/{selection}", "w") as file:
                    file.write(editedText)
            else:
                editedTable.to_csv(f"./{pageName}/{selection}", sep='\t', index=False, header=False)

    if selection:
        with downloadButtonLocation:
            file_path = f"./{pageName}/{selection}"
            file_content = read_file(file_path=file_path)
            st.download_button(
                label="İndir",
                data=file_content,
                file_name=selection.split('/')[len(selection.split('/'))-1],
                mime="text/html"
            )