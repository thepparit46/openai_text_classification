import streamlit as st
import openai
import pandas as pd
from pydantic import ValidationError
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

# ตั้งค่า API Key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# ตั้งค่า LLM Model
llm = ChatOpenAI(temperature=0, model="gpt-4o", openai_api_key=OPENAI_API_KEY)

# หมวดหมู่และคำอธิบายที่เป็นไปได้
CATEGORIES = {
    "Service & Operations": "เกี่ยวกับคุณภาพของการให้บริการ การเดินรถ และเวลาให้บริการ",
    "Incidents & Issues": "ปัญหาหรือเหตุการณ์พิเศษที่เกิดขึ้น เช่น รถไฟเสีย หรือความล่าช้า",
    "Passenger Experience & Sentiment": "ความคิดเห็นและความรู้สึกของผู้โดยสารเกี่ยวกับ BTS",
    "Comparisons & Alternatives": "เปรียบเทียบ BTS กับระบบขนส่งอื่น เช่น MRT หรือรถเมล์",
    "Marketing & Partnerships": "เกี่ยวกับแคมเปญโฆษณา โปรโมชั่น หรือการร่วมมือทางธุรกิจ",
    "Social Trends": "กระแสสังคมหรือประเด็นที่มีคนพูดถึงเกี่ยวกับ BTS",
    "Other": "ข้อความที่ไม่เข้ากับหมวดหมู่อื่น ๆ"
}

tagging_prompt = ChatPromptTemplate.from_template(
    """คุณคือผู้ช่วยด้านการวิเคราะห์ความคิดเห็นของลูกค้าสำหรับโครงการ Social Listening ที่เกี่ยวข้องกับบริการรถไฟฟ้า BTS ในประเทศไทย งานของคุณคือการจัดประเภทข้อความตามเงื่อนไขต่อไปนี้

[1] หมวดหมู่ (categories):
{categories}

[2] เจตนา (intent):
- ร้องเรียน/มีปัญหา
- สอบถาม
- เปรียบเทียบ
- ข้อเสนอแนะ
- แบ่งปันประสบการณ์
- ประชด/เสียดสี
- เจตนาอื่น ๆ

[3] อารมณ์ (sentiment):
- Positive
- Neutral
- Negative

ข้อความที่จะให้วิเคราะห์:
"{post}"
""".format(categories="\n".join(f"- {k}: {v}" for k, v in CATEGORIES.items()))
)

# Schema สำหรับผลลัพธ์
class TaggingSchema(BaseModel):
    category: str = Field(
        description="ระบุหมวดหมู่เดียวที่เกี่ยวข้องมากที่สุด",
    )
    intent: str = Field(
        description="ระบุเจตนาเดียวที่เกี่ยวข้องมากที่สุด",
        enum=['ร้องเรียน/มีปัญหา', 'สอบถาม', 'ข้อเสนอแนะ', 'แบ่งปันประสบการณ์', 'ประชด/เสียดสี', 'เจตนาอื่น ๆ']
    )
    sentiment: str = Field(
        description="ระบุอารมณ์หลักของข้อความ",
        enum=['Positive', 'Negative', 'Neutral']
    )

# ตั้งค่า LLM Model ให้รองรับ Output แบบ Structured
llm_structured = llm.with_structured_output(TaggingSchema)

# ใช้ Chain สำหรับการวิเคราะห์
tagging_chain = tagging_prompt | llm_structured

# ตั้งค่า UI ของ Streamlit
st.title("🚄 BTS Social Listening Analysis")
st.write("🔍 วิเคราะห์ความคิดเห็นเกี่ยวกับ BTS ด้วย AI")

#  เพิ่มส่วนแสดงหมวดหมู่ที่เป็นไปได้
with st.expander("📌 หมวดหมู่ที่เป็นไปได้"):
    for category, desc in CATEGORIES.items():
        st.markdown(f"**{category}**: {desc}")

# ใช้ text_area รองรับข้อความหลายบรรทัด
user_input = st.text_area("📝 ใส่ข้อความที่ต้องการวิเคราะห์ (สามารถใส่หลายบรรทัด)")

# เก็บประวัติการวิเคราะห์
if "history" not in st.session_state:
    st.session_state.history = []

# สร้างปุ่มกด
if st.button("Analyze"):
    if user_input.strip():
        input_texts = user_input.split("\n")  # รองรับการวิเคราะห์หลายข้อความ
        results = []

        for i, text in enumerate(input_texts, start=1):
            try:
                # เรียกใช้ AI เพื่อวิเคราะห์ข้อความ
                chain_output = tagging_chain.invoke(input={'post': text})

                # เก็บผลลัพธ์ลงในประวัติ
                result = {
                    "Message": text,
                    "Category": chain_output.category,
                    "Intent": chain_output.intent,
                    "Sentiment": chain_output.sentiment
                }
                results.append(result)
                st.session_state.history.append(result)

            except ValidationError as e:
                st.error(f"❌ Validation error: {e}")

        #  แสดงผลลัพธ์ในตาราง
        if results:
            df = pd.DataFrame(results)
            st.write("### 🔍 วิเคราะห์ผลลัพธ์")
            st.dataframe(df)

    else:
        st.warning("❗ กรุณากรอกข้อความก่อนกด Analyze")

# แสดงประวัติการวิเคราะห์
if st.session_state.history:
    with st.expander("📜 ประวัติการวิเคราะห์"):
        history_df = pd.DataFrame(st.session_state.history)
        st.dataframe(history_df)
