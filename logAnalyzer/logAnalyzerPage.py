import streamlit as st
from common.frontend.script_runner import run_script
from common.frontend.init_page_state import init_page_state
from common.scriptStrategies.ScriptStrategy import LogAnalyserStrategy
from common.ScriptRunner import ScriptRunner
import os

page_name = "logAnalyzer"
description = "Verilen log dosyasindan firewall kurallari çikarir. Oluşan kural dosyalarını indirmek için ve yeni firewall loglarının yüklemek için Data Edit sayfasını kullanın. Ayrıca lütfen log dosyalarına göre interface listesini düzenlemeniz gerekebileceğini unutmayın."
scriptStrategy = LogAnalyserStrategy()

page_state = init_page_state(page_name)

st.header("Açıklama", divider="grey")
st.write(description)

st.header("Girdiler", divider="grey")

scriptArguments = {}

logFileList = [f for f in os.listdir(f"./{page_name}/packetLogFiles") if f.endswith(".xlsx")]

if "log_file_path" not in page_state:
    page_state["log_file_path"] = ""
st.selectbox(
    "Log Dosyasinin Adi",
    options=logFileList,
    index=None,
    key=f"{page_name}_log_file_path_input",
    on_change=lambda: page_state.update({
        "log_file_path": st.session_state[f"{page_name}_log_file_path_input"]
    })
)

if "destport_threshold" not in page_state:
    page_state["destport_threshold"] = 0
st.text_input(
    "Destination Port Alt Siniri",
    type="default",
    value=page_state["destport_threshold"],
    key=f"{page_name}_destport_threshold_input",
    on_change=lambda: page_state.update({
        "destport_threshold": st.session_state[f"{page_name}_destport_threshold_input"]
    })
)

if "interface_threshold" not in page_state:
    page_state["interface_threshold"] = 0
st.text_input(
    "Interface Trafigi Alt Siniri",
    type="default",
    value=page_state["interface_threshold"],
    key=f"{page_name}_interface_threshold_input",
    on_change=lambda: page_state.update({
        "interface_threshold": st.session_state[f"{page_name}_interface_threshold_input"]
    })
)

def prepare_command(scriptArguments):
    scriptArguments['logFilePath'] = page_state["log_file_path"]
    scriptArguments['portThreshold'] = int(page_state["destport_threshold"])
    scriptArguments['interfaceThreshold'] = int(page_state["interface_threshold"])
    scriptArguments['pageName'] = page_name
prepare_command(scriptArguments=scriptArguments)

page_state["script_runner"] = ScriptRunner(page_name, scriptStrategy, scriptArguments=scriptArguments)

run_script(page_name, page_state, scriptArguments=scriptArguments, scriptType="l")
