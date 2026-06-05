import streamlit as st
import sys
from pathlib import Path
import asyncio

backend_path = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.orchestrator import Orchestrator

st.set_page_config(page_title="Voice Notes", page_icon="🎤", layout="wide")
st.title("🎤 Voice Note Ingestion")

@st.cache_resource
def get_orchestrator():
    return Orchestrator()

orch = get_orchestrator()

st.write("Upload a voice note (mp3, wav, m4a) detailing the invoice. The system will transcribe and process it.")

audio_file = st.file_uploader("Upload Voice Note", type=['mp3', 'wav', 'm4a'])

if audio_file and st.button("🎙️ Transcribe & Extract"):
    with st.spinner("Processing voice note..."):
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / audio_file.name
        temp_path.write_bytes(audio_file.read())

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                orch.process_invoice(
                    str(temp_path),
                    source_type='voice'
                )
            )

            if result.get('status') == 'success':
                st.success("✅ Voice note processed successfully!")

                tab1, tab2, tab3 = st.tabs(["📋 Extracted Data", "⚖️ Compliance", "🎯 Strategy"])

                with tab1:
                    st.json(result.get('ingestion', {}).get('extraction', {}))

                with tab2:
                    compliance = result.get('compliance', {}).get('compliance', {})
                    if compliance.get('alert_level', 'none') != 'none':
                        st.warning(f"⚠️ Alert: {compliance['alert_level']}")
                    st.json(compliance)

                with tab3:
                    strategy = result.get('strategy', {})
                    st.info(f"**Recommendation**: {strategy.get('recommendation')}\n\n**Reasoning**: {strategy.get('reasoning')}")
            else:
                st.error(f"Failed to process: {result.get('error')}")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            loop.close()
