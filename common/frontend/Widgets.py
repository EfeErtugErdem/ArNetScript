import streamlit as st

'''
Kullanıcı adı ve parola girişleri için widgetları oluşturur ve geri döndürür.
Widgetların değerlerine daha sonra page_state içerisinde verilen keylerden ulaşılabilir.
'''
def createUsernamePasswordFields(page_name: str, page_state: dict, username_key: str, password_key: str):
    if username_key not in page_state:
        page_state[username_key] = None
    usernameWidget = st.text_input(
        label="Kullanıcı Adı", 
        type="default", 
        value=page_state[username_key],
        key=f"{page_name}_{username_key}_input",
        on_change=lambda: page_state.update({
            username_key: st.session_state[f"{page_name}_{username_key}_input"]
        })
    )
    # Parola girişi için oluşturulacak widget
    if password_key not in page_state:
        page_state[password_key] = None
    passwordWidget = st.text_input(
        label="Parola", 
        type=password_key, 
        value=page_state[password_key],
        key=f"{page_name}_{password_key}_input",
        on_change=lambda: page_state.update({
            password_key: st.session_state[f"{page_name}_{password_key}_input"]
        })
    )
    return usernameWidget, passwordWidget

def createTextInputWidget(page_name: str, page_state: dict, label: str, key: str, type="default"):
    if key not in page_state:
        page_state[key] = None
    textInputWidget = st.text_input(
        label=label, 
        type=type, 
        value=page_state[key],
        key=f"{page_name}_{key}_input",
        on_change=lambda: page_state.update({
            key: st.session_state[f"{page_name}_{key}_input"]
        })
    )
    return textInputWidget

def createCheckboxWidget(page_name: str, page_state: dict, label: str, key: str):
    if key not in page_state:
        page_state[key] = False
    checkboxWidget = st.checkbox(
        label=label, 
        value=page_state[key], 
        key=f"{page_name}_{key}_input",
        on_change=lambda: page_state.update({
            key: st.session_state[f"{page_name}_{key}_input"]
        })
    )
    return checkboxWidget

def createSelectboxWidget(page_name: str, page_state: str, key: str, label: str, options: str):
    if f"{key}_index" not in page_state:
        page_state[f"{key}_index"] = 0
    selectboxWidget = st.selectbox(
        label=label,
        options=options,
        index=page_state[f"{key}_index"],
        key=f"{page_name}_{key}_index_input",
        on_change=lambda: page_state.update({
            f"{key}_index": options.index(st.session_state[f"{page_name}_{key}_index_input"])
        })
    )
    return selectboxWidget

def createMultiselectWidget(page_name: str, page_state: str, key: str, label: str, options: list):
    if key not in page_state:
        page_state[key] = []
    multiselectWidget = st.multiselect(
        label=label, 
        options=options, 
        default=page_state[key],
        key=f"{page_name}_{key}_input",
        on_change=lambda: page_state.update({
            key: st.session_state[f"{page_name}_{key}_input"]
        })
    )
    return multiselectWidget