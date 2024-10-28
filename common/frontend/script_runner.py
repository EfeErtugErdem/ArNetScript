import streamlit as st
from contextlib import redirect_stdout
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
import time

class WriteProcessor:
    def __init__(self, session_state, page_name):
        self.session_state = session_state
        self.page_name = page_name
        self.buf = ""

    def write(self, buf):
        # emit on each newline
        while buf:
            try:
                newline_index = buf.index("\n")
            except ValueError:
                # no newline, buffer for next call
                self.buf += buf
                break
            # get data to next newline and combine with any buffered data
            data = self.buf + buf[:newline_index + 1]
            self.buf = ""
            buf = buf[newline_index + 1:]
            # perform complex calculations... or just print with a note.
            self.session_state[f"{self.page_name}_output_list"].append(data)

def run_script(page_name: str, page_state: str, scriptArguments: dict, scriptType: str):
    st.header("Çıktılar", divider="grey")

    # Script çıktısı
    if f"{page_name}_output_list" not in st.session_state:
        st.session_state[f"{page_name}_output_list"] = []

    # Script hala yürüyor mu
    if f"{page_name}_script_running" not in st.session_state:
        st.session_state[f"{page_name}_script_running"] = False

    # Script'in yürütüldüğü thread
    if f"{page_name}_script_thread" not in st.session_state:
        st.session_state[f"{page_name}_script_thread"] = None

    stop_event = threading.Event()

    def run_script(scriptArguments, scriptType):
        with redirect_stdout(WriteProcessor(st.session_state, page_name)):
            if scriptType == "n" or scriptType == "network":
                page_state["script_runner"].runNetworkingScripts(scriptArguments, stop_event)
            elif scriptType == "l" or scriptType == "log":
                page_state["script_runner"].runAnalyserScripts(scriptArguments, stop_event)

        st.session_state[f"{page_name}_script_running"] = False
        st.session_state[f"{page_name}_script_process"] = None

    def start_script():
        if not st.session_state[f"{page_name}_script_running"]:
            
            st.session_state[f"{page_name}_output_list"].clear()
            st.session_state[f"{page_name}_script_running"] = True
            st.session_state[f"{page_name}_script_thread"] = None

            script_thread = threading.Thread(target=run_script, args=(scriptArguments, scriptType))
            add_script_run_ctx(script_thread)
            st.session_state[f"{page_name}_script_thread"] = script_thread
            script_thread.start()
            script_thread.join()

    def stop_script():
        if st.session_state[f"{page_name}_script_thread"]:
            stop_event.set()
            st.session_state[f"{page_name}_script_thread"].join()
            stop_event.clear()
            st.session_state[f"{page_name}_script_running"] = False
    
    def display_output():
        output_html = ""
        for line in st.session_state[f"{page_name}_output_list"]:
            output_html += f"<p class='output-line'>{line}</p>"
        st.markdown(f"<div class='output-container'>{output_html}</div>", unsafe_allow_html=True)

    start_button_location, stop_button_location = st.columns(2)
    with start_button_location:
        if st.button("Başlat") and not st.session_state[f"{page_name}_script_running"]:
            start_script()
    with stop_button_location:
        if st.button("Durdur") and st.session_state[f"{page_name}_script_running"]:
            stop_script()
    
    # Script çıktısını formatlama
    st.markdown("""
    <style>
    .output-container {
        height: 400px;
        overflow-y: scroll;
        background-color: #f0f0f0;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
    }
    .output-line {
        font-size: 12px;
        font-family: "Courier New", Courier, monospace;
    }
    </style>
    """, unsafe_allow_html=True)

    # Script çıktısının yazdırıldığı widget. Her saniye yenilenir.
    placeholder = st.empty()
    while st.session_state[f"{page_name}_script_running"]:
        with placeholder.container():
            display_output()
        time.sleep(1)

    with placeholder.container():
        display_output()