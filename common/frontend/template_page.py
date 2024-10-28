import streamlit as st
from common.getLocationVlans import getLocationVlans
import threading
import time
from streamlit.runtime.scriptrunner import add_script_run_ctx
from common.ScriptRunner import ScriptRunner
from common.scriptStrategies.IScriptStrategy import IScriptStrategy
from contextlib import redirect_stdout
from common.frontend import Widgets

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


def use_template(page_name: str,
                 description: str,
                 scriptStrategy: IScriptStrategy,
                 save_config=False,
                 in_vlan=False,
                 in_command=False,
                 in_topology=False,
                 in_config=False):

    # Sayfaya özel state, script komutunu hazırlamak için gereken verileri tutar. 
    # Widget'ların o anki durumu direkt olarak session_state içerisinde, burada değil.
    if "page_states" not in st.session_state:
        st.session_state["page_states"] = {}
    if page_name not in st.session_state["page_states"]:
        st.session_state["page_states"][page_name] = {}
    page_state = st.session_state["page_states"][page_name]

    # Script açıklamasını yazdır
    st.header("Açıklama", divider="grey")
    st.write(description)

    # Girdi bölümü başlığı
    st.header("Girdiler", divider="grey")

    # Script'i çalıştırmak için gereken argümanlar.
    scriptArguments = {}

    # Konfigürasyon kayıt seçeneği için oluşturulacak widget'lar
    if save_config:
        # Konfigürasyon kayıt seçeneği
        if "save_config" not in page_state:
            page_state["save_config"] = "h"
        st.checkbox(
            "İşlem sonunda konfigürasyon bilgileri kaydedilsin mi?", 
            value=(False if page_state["save_config"] == "h" else True), 
            key=f"{page_name}_save_config_input",
            on_change=lambda: page_state.update(
                {"save_config": (False if st.session_state[f"{page_name}_save_config_input"] == "h" else True)}
            )
        )

    # Topoloji oluşturma seçeneği için gereken widget
    if in_topology:
        # Topoloji oluşturma seçeneği
        if "create_topology" not in page_state:
            page_state["create_topology"] = "h"
        st.checkbox(
            "Topoloji oluşturulsun mu?", 
            value=(False if page_state["create_topology"] == "h" else True), 
            key=f"{page_name}_create_topology_input",
            on_change=lambda: page_state.update(
                {"create_topology": (False if st.session_state[f"{page_name}_create_topology_input"] == "h" else True)}
            )
        )

    # Kullanıcı adı girişi için oluşturulacak widget
    if "username" not in page_state:
        page_state["username"] = None
    st.text_input(
        "Kullanıcı Adı", 
        type="default", 
        value=page_state["username"],
        key=f"{page_name}_username_input",
        on_change=lambda: page_state.update({"username": st.session_state[f"{page_name}_username_input"]})
    )

    # Parola girişi için oluşturulacak widget
    if "password" not in page_state:
        page_state["password"] = None
    st.text_input(
        "Parola", 
        type="password", 
        value=page_state["password"],
        key=f"{page_name}_password_input",
        on_change=lambda: page_state.update({"password": st.session_state[f"{page_name}_password_input"]})
    )

    if in_config:
        bannerOptions = ["Arçelik", "Beko", "Defy", "IHP", "Arctic"]

        if "banner_selection" not in page_state:
            page_state["banner_selection"] = False
        st.checkbox(
            "Banner yüklemek istiyor musunuz?", 
            value=page_state["banner_selection"], 
            key=f"{page_name}_banner_selection_choice",
            on_change=lambda: page_state.update(
                {"banner_selection": st.session_state[f"{page_name}_banner_selection_choice"]}
            )
        )
        if st.session_state[f"{page_name}_banner_selection_choice"]:
            if "selected_banner_index" not in page_state:
                page_state["selected_banner_index"] = 0
            selected_banner = st.selectbox(
                "Banner seçenekleri",
                options=bannerOptions,
                index=page_state["selected_banner_index"],
                key=f"{page_name}_banner_index_input",
                on_change=lambda: page_state.update(
                    {"selected_banner_index": bannerOptions.index(st.session_state[f"{page_name}_banner_index_input"])}
                )
            )

    # VLAN konfigürasyonu için oluşturulacak widget'lar.
    if in_vlan:
        # VLAN butonuna basıldı mı
        if "vlan_button_pressed" not in page_state:
            page_state["vlan_button_pressed"] = False

        # VLAN listesi
        if "vlan_list" not in page_state:
            page_state["vlan_list"] = []

        # Secilen VLANlar
        if "vlan_selection" not in page_state:
            page_state["vlan_selection"] = []

        # "shared_state" VLAN listesini gönderen fonksiyonun da state belirleyebilmesini sağlar
        if "shared_state" not in page_state:
            page_state["shared_state"] = {"task_done": False, "vlan_list": []}
        shared_state = page_state["shared_state"]

        # VLAN listesinin alınıp alınmadığını belirtir
        if "task_done" not in page_state:
            page_state["task_done"] = False

        # Voice VLAN girişi için gereken widgetlar
        if "voice_vlan_selection" not in page_state:
            page_state["voice_vlan_selection"] = False
        st.checkbox(
            "Voice VLAN bilgisi gerekiyor mu?", 
            value=page_state["voice_vlan_selection"], 
            key=f"{page_name}_voice_vlan_selection_choice",
            on_change=lambda: page_state.update(
                {"voice_vlan_selection": st.session_state[f"{page_name}_voice_vlan_selection_choice"]}
            )
        )
        if st.session_state[f"{page_name}_voice_vlan_selection_choice"]:
            if "voice_vlan" not in page_state:
                page_state["voice_vlan"] = ""
            st.text_input(
                "Voice VLAN numarası",
                value=page_state["voice_vlan"],
                key=f"{page_name}_voice_vlan_input",
                on_change=lambda: page_state.update(
                    {"voice_vlan": st.session_state[f"{page_name}_voice_vlan_input"]}
                )
            )

        vlanOperations = ["dot1x Configurator", "dot1x Remover", "MAC Explorer"]

        if "selected_vlan_option_index" not in page_state:
            page_state["selected_vlan_option_index"] = 0
        selected_vlan_option = st.selectbox(
            "VLAN İşlemleri",
            options=vlanOperations,
            index=page_state["selected_vlan_option_index"],
            key=f"{page_name}_vlan_option_index_input",
            on_change=lambda: page_state.update(
                {"selected_vlan_option_index": vlanOperations.index(st.session_state[f"{page_name}_vlan_option_index_input"])}
            )
        )

        # Karşı cihazdaki VLAN listesini al
        vlan_fetch_button_location, vlan_refresh_button_location = st.columns(2)
        with vlan_fetch_button_location:
            if st.button("Vlan Listesini Al") and not page_state["vlan_button_pressed"]:
                page_state["vlan_button_pressed"] = True
                page_state["task_done"] = False

                vlan_fetcher_thread = threading.Thread(
                    target=getLocationVlans, 
                    args=(page_state["username"], page_state["password"], shared_state, f"{page_name}/"))
                vlan_fetcher_thread.start()
        with vlan_refresh_button_location:
            if st.button("VLAN Listesini Sıfırla"):
                page_state["vlan_button_pressed"] = False

        # VLAN listesi alındıysa seçim widet'ını ekrana getir 
        if page_state["vlan_button_pressed"] and shared_state["task_done"]:
            page_state["vlan_list"] = shared_state["vlan_list"]

            st.write("Kullanilabilir VLANlar: ")
            st.write(page_state["vlan_list"])

            st.multiselect(
                label="Vlan seçiniz", 
                options=page_state["vlan_list"], 
                default=page_state["vlan_selection"],
                key=f"{page_name}_vlan_multiselect", # Key değeri verialen bir widget otomatik olarak state içinde oluşturuluyor
                on_change=lambda: page_state.update(
                    {"vlan_selection": st.session_state[f"{page_name}_vlan_multiselect"]}
                )
            )
        # VLAN listesi alınmadıysa ekrana yüklenme bilgisini yazdır
        elif page_state["vlan_button_pressed"] and not shared_state["task_done"]:
            st.write("VLAN listesi alınıyor...")
            time.sleep(1)
            st.rerun()

    # Karşı tarafta komut çalıştırılacaksa oluşturulacak widget'lar
    if in_command:
        if "command_string" not in page_state:
            page_state["command_string"] = None

        # Komut girdisi alanı
        st.text_input(
            "Cihazda Çalıştırılacak Komut", 
            value=page_state["command_string"],
            key=f"{page_name}_command_string_input",
            on_change=lambda: page_state.update(
                {"command_string": st.session_state[f"{page_name}_command_string_input"]}
            )
        )

    # Script argümanlarını hazırlayan fonksiyon 
    def prepare_command(scriptArguments):
        if save_config:
            scriptArguments['wantToSaveConfig'] = True if page_state["save_config"] == "e" else False

        if in_topology:
            scriptArguments["createTopology"] = True
        
        scriptArguments["username"] = page_state["username"]
        scriptArguments["password"] = page_state["password"]
        scriptArguments["pageName"] = f"{page_name}/"

        if in_vlan:
            scriptArguments['vlanList'] = ','.join([str(vlan) for vlan in page_state["vlan_selection"]])
            if st.session_state[f"{page_name}_voice_vlan_selection_choice"]:
                scriptArguments["voiceVlan"] = page_state["voice_vlan"]
            else:
                scriptArguments["voiceVlan"] = None

            if selected_vlan_option == "dot1x Configurator":
                scriptArguments['selectedOption'] = "c"
            elif selected_vlan_option == "dot1x Remover":
                scriptArguments['selectedOption'] = "r"
            elif selected_vlan_option == "MAC Explorer":
                scriptArguments['selectedOption'] = "m"

        if in_command:
            scriptArguments["commandToExecute"] = page_state["command_string"]

        if in_config:
            if page_state["banner_selection"]:
                scriptArguments["bannerSelection"] = True
                scriptArguments["selectedBanner"] = selected_banner
            else:
                scriptArguments["bannerSelection"] = False
                scriptArguments["selectedBanner"] = None


    # Sayfalarda ilgil girdilerin kontrolünü yapar
    def check_valid_input():
        if not page_state["username"]:
            st.warning("Lütfen kullanıcı adı giriniz!")
            return False
        
        if not page_state["password"]:
            st.warning("Lütfen parola giriniz!")
            return False
        
        if in_vlan and not page_state["vlan_list"]:
            st.warning("Lütfen işlem yapılacak VLAN'ları seçiniz!")
            return False
        
        if in_command and not page_state["command_string"]:
            st.warning("Lütfen çalıştırmak istediğiniz komutu girin!")
            return False
        
        return True

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

    def run_script(scriptArguments):
        with redirect_stdout(WriteProcessor(st.session_state, page_name)):
            page_state["script_runner"].runNetworkingScripts(scriptArguments, stop_event)

        st.session_state[f"{page_name}_script_running"] = False
        st.session_state[f"{page_name}_script_process"] = None

    def start_script():
        if not st.session_state[f"{page_name}_script_running"]:
            prepare_command(scriptArguments)

            page_state["script_runner"] = ScriptRunner(page_name, scriptStrategy, scriptArguments)
            
            st.session_state[f"{page_name}_output_list"].clear()
            st.session_state[f"{page_name}_script_running"] = True
            st.session_state[f"{page_name}_script_thread"] = None

            script_thread = threading.Thread(target=run_script, args=(scriptArguments, ))
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
            if check_valid_input():
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

## TODO: Sayfadan çıkarken haber versin
## TODO: önyüzü widgetlara ayır 
