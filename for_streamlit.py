import streamlit as st
import openai
import pandas as pd
from pydantic import ValidationError
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

# ✅ ใช้ Secrets แทน input() สำหรับ OpenAI API Key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# ✅ ตั้งค่า LLM Model
llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)

# ✅ ตั้งค่า UI ของ Streamlit
st.title("🚄 BTS Social Listening Analysis")
st.write("วิเคราะห์ความคิดเห็นเกี่ยวกับ BTS ด้วย AI")

# ✅ รับข้อความจากผู้ใช้
user_input = st.text_area("ใส่ข้อความที่ต้องการวิเคราะห์")

# ✅ ตั้งค่าพรอมต์
tagging_prompt = ChatPromptTemplate.from_template(
    """คุณคือผู้ช่วยด้านการวิเคราะห์ความคิดเห็นของลูกค้าสำหรับโครงการ Social Listening ที่เกี่ยวข้องกับบริการรถไฟฟ้า BTS ในประเทศไทย งานของคุณคือการจัดประเภทข้อความตามเงื่อนไขต่อไปนี้

[1] หมวดหมู่ (categories):
- การให้บริการ (Service & Operations)
- เหตุการณ์พิเศษ / ปัญหาเฉพาะหน้า (Incidents & Issues)
- ประสบการณ์และความคิดเห็นของผู้โดยสาร (Passenger Experience & Sentiment)
- การเปรียบเทียบกับระบบขนส่งอื่น (Comparisons & Alternatives)
- แคมเปญการตลาด / โฆษณา / ความร่วมมือ (Marketing & Partnerships)
- กระแสสังคม / เทรนด์ออนไลน์เกี่ยวกับ BTS
- หมวดหมู่อื่น ๆ

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
"""
)

# ✅ Schema สำหรับผลลัพธ์
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

# ✅ ตั้งค่า LLM Model ให้รองรับ Output แบบ Structured
llm_structured = llm.with_structured_output(TaggingSchema)

# ✅ ใช้ Chain สำหรับการวิเคราะห์
tagging_chain = tagging_prompt | llm_structured

# ✅ สร้างปุ่มกด
if st.button("Analyze"):
    if user_input:
        try:
            # ✅ เรียกใช้ AI เพื่อวิเคราะห์ข้อความ
            chain_output = tagging_chain.invoke(input={'post': user_input})

            # ✅ แสดงผล
            st.write("### 🔍 วิเคราะห์ผลลัพธ์")
            st.json(chain_output.dict())

        except ValidationError as e:
            st.error(f"Validation error: {e}")
    else:
        st.warning("❗ กรุณากรอกข้อความก่อนกด Analyze")
