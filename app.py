import streamlit as st
import google.generativeai as genai
from PIL import Image
import re
import datetime

# --- 1. ตั้งค่าหน้าเว็บพรีเมียม ---
st.set_page_config(
    page_title="VIP Football Ticket Verification System",
    page_icon="⚽",
    layout="wide"
)

# ตกแต่ง CSS
st.markdown("""
<style>
    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #0F172A;
        text-align: center;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 16px;
        color: #64748B;
        text-align: center;
        margin-bottom: 25px;
    }
    .stMetric {
        background-color: #F8FAFC;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. ตัวแปรเก็บประวัติใน Session State ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- 3. Sidebar ตั้งค่าระบบและคู่มือ ---
with st.sidebar:
    st.markdown("### ⚙️ ระบบจัดการและตั้งค่า")
    api_key = st.text_input("Gemini API Key", type="password", help="ใส่ API Key ของคุณเพื่อเริ่มใช้งาน AI ตรวจสอบบิล")
    st.markdown("---")
    st.markdown("### 📋 คู่มือเงื่อนไขโปรโมชั่น 🏆")
    st.info(
        "**เงื่อนไขหลัก:**\n"
        "• ยอดเดิมพันขั้นต่ำ: **100 บาท** 💵\n\n"
        "🔥 **สเต็ปตาย 1 คู่:**\n"
        "  • 5 คู่: คืน 1 เท่า\n"
        "  • 6 คู่: คืน 3 เท่า\n"
        "  • 7 คู่: เครดิตฟรี 2,000 ฿ 🥉\n"
        "  • 8 คู่: เครดิตฟรี 5,000 ฿ 🥈\n"
        "  • 9 คู่: เครดิตฟรี 10,000 ฿ 🥇\n"
        "  • 10 คู่: เครดิตฟรี 15,000 ฿ 💎\n"
        "  • 12 คู่: iPhone 16 Pro Max 📱🔥\n\n"
        "💥 **สเต็ปผิดหมดทุกคู่:**\n"
        "  • 5 คู่: x2 | 6 คู่: x5 | 7 คู่: x7\n"
        "  • 8 คู่: x10 | 9 คู่: x15 | 10 คู่: x30 🚀"
    )

# --- 4. หัวข้อหลัก ---
st.markdown('<p class="main-title">⚽🏆 VIP Football Ticket Verification 🏟️🔥</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">ระบบตรวจสอบและบันทึกสลีปบิลฟุตบอลอัจฉริยะด้วย AI ⚡</p>', unsafe_allow_html=True)

# --- 5. แดชบอร์ดสรุปสถิติภาพรวม ---
total_checks = len(st.session_state.history)
total_pass = sum(1 for item in st.session_state.history if item['is_pass'])
total_fail = total_checks - total_pass

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("📊 ตรวจสอบทั้งหมด", f"{total_checks} บิล")
col_m2.metric("🎉 ผ่านเงื่อนไขโปรโมชั่น", f"{total_pass} บิล")
col_m3.metric("❌ ไม่ผ่านเงื่อนไข", f"{total_fail} บิล")

st.markdown("---")

# --- 6. ฟังก์ชันตรวจสอบเงื่อนไขโปรโมชั่น ---
def check_bill_reward(bet_amount, total_matches, lose_count):
    if bet_amount < 100:
        return False, f"ยอดเดิมพัน {bet_amount:,.2f} ฿ ไม่ถึงขั้นต่ำ 100 บาท ❌"
    
    if total_matches == 0:
        return False, "ไม่พบรายการแข่งขันในบิล ⚠️"

    # เงื่อนไขสเต็ปตาย 1 คู่
    if lose_count == 1:
        rewards = {
            5: "รับเครดิตคืน 1 เท่าของยอดบิล 💵",
            6: "รับเครดิตคืน 3 เท่าของยอดบิล 💰",
            7: "รับรางวัลเครดิตฟรี 2,000 บาท 🥉",
            8: "รับรางวัลเครดิตฟรี 5,000 บาท 🥈",
            9: "รับรางวัลเครดิตฟรี 10,000 บาท 🥇",
            10: "รับรางวัลเครดิตฟรี 15,000 บาท 💎",
            12: "รับรางวัลใหญ่ iPhone 16 Pro Max 📱🔥"
        }
        if total_matches in rewards:
            return True, f"สเต็ปตาย 1 คู่ ({total_matches} คู่) — {rewards[total_matches]}"
        elif total_matches >= 5:
            return True, f"สเต็ปตาย 1 คู่ ({total_matches} คู่) — เข้าเงื่อนไขโปรโมชั่นพิเศษ 🎉"
            
    # เงื่อนไขสเต็ปผิดหมดทุกคู่
    elif lose_count == total_matches:
        multipliers = {5: 2, 6: 5, 7: 7, 8: 10, 9: 15, 10: 30}
        if total_matches in multipliers:
            return True, f"สเต็ปผิดหมดทุกคู่ ({total_matches} คู่) — คืนเครดิต {multipliers[total_matches]} เท่า 🚀"
        elif total_matches >= 5:
            return True, f"สเต็ปผิดหมดทุกคู่ ({total_matches} คู่) — เข้าเงื่อนไขคืนเครดิตพิเศษ 🌟"

    return False, f"ผลบิลสเต็ป {total_matches} คู่ (เสีย {lose_count} คู่) ไม่ผ่านเกณฑ์เงื่อนไขโปรโมชั่น 📉"

# --- 7. ส่วนอัปโหลดรูปภาพและวิเคราะห์ ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 📤 อัปโหลดสลีปบิลฟุตบอล 🎫")
    uploaded_file = st.file_uploader("ลากและวางไฟล์รูปภาพที่นี่ หรือคลิกเพื่อเลือกไฟล์", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="สลีปบิลของคุณ 📸", use_container_width=True)

with col2:
    st.markdown("### 🔍 ผลการตรวจสอบสถานะ ⚡")
    
    if uploaded_file is not None:
        if st.button("🚀 เริ่มวิเคราะห์บิลด้วย AI 🤖", type="primary", use_container_width=True):
            if not api_key:
                st.warning("⚠️ กรุณากรอก Gemini API Key ในแถบด้านซ้ายก่อนทำการตรวจสอบ")
            else:
                with st.spinner("🤖 ระบบกำลังประมวลผลและตรวจสอบข้อมูลสลีปบอล... ⚽"):
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-3.8-flash')
                        
                        prompt = """
                        ช่วยอ่านสลิปบิลฟุตบอลในรูปภาพนี้ แล้วตอบกลับมาเป็นข้อความตามรูปแบบนี้เป๊ะๆ:
                        ยอดเดิมพัน: [ใส่ตัวเลขยอดเงิน เช่น 100]
                        จำนวนคู่ทั้งหมด: [ใส่ตัวเลขจำนวนคู่ เช่น 7]
                        จำนวนคู่ที่เสีย: [ใส่ตัวเลขจำนวนคู่ที่เสีย เช่น 1]
                        """
                        response = model.generate_content([image, prompt])
                        text_result = response.text.strip()
                        
                        bet_amount = 100.0
                        total_matches = 7
                        lose_count = 1
                        
                        for line in text_result.split('\n'):
                            if "ยอดเดิมพัน" in line:
                                nums = re.findall(r'\d+\.?\d*', line)
                                if nums: bet_amount = float(nums[0])
                            elif "จำนวนคู่ทั้งหมด" in line:
                                nums = re.findall(r'\d+', line)
                                if nums: total_matches = int(nums[0])
                            elif "จำนวนคู่ที่เสีย" in line:
                                nums = re.findall(r'\d+', line)
                                if nums: lose_count = int(nums[0])

                        is_pass, desc = check_bill_reward(bet_amount, total_matches, lose_count)
                        
                        # บันทึกข้อมูลลง Session History
                        st.session_state.history.insert(0, {
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "bet_amount": bet_amount,
                            "matches": f"สเต็ป {total_matches} คู่ (เสีย {lose_count} คู่)",
                            "is_pass": is_pass,
                            "status_text": "ผ่านเงื่อนไข 🎉" if is_pass else "ไม่ผ่าน ❌",
                            "reward_detail": desc
                        })

                        # แสดงผลลัพธ์ทันทีฝั่งขวามือ (โดยไม่ใช้ st.rerun())
                        st.markdown("---")
                        if is_pass:
                            st.success("### 🎉 ยินดีด้วย! ผ่านเงื่อนไขโปรโมชั่นระดับ VIP 🏆⚽")
                            st.markdown(f"""
                            - 💵 **ยอดเดิมพันสุทธิ:** `{bet_amount:,.2f} บาท`
                            - ⚽ **วิเคราะห์บิล:** สเต็ป `{total_matches}` คู่ (เสีย `{lose_count}` คู่)
                            - 🎁 **สิทธิประโยชน์ที่ได้รับ:** **{desc}**
                            """)
                        else:
                            st.error("### ❌ เสียใจด้วยครับ ไม่ผ่านเกณฑ์เงื่อนไขโปรโมชั่น 📉")
                            st.markdown(f"""
                            - 💵 **ยอดเดิมพันสุทธิ:** `{bet_amount:,.2f} บาท`
                            - ⚽ **วิเคราะห์บิล:** สเต็ป `{total_matches}` คู่ (เสีย `{lose_count}` คู่)
                            - 📌 **เหตุผล:** `{desc}`
                            """)
                    except Exception as e:
                        st.error(f"❌ เกิดข้อผิดพลาดในการวิเคราะห์รูปภาพ: {e}")
    else:
        st.info("💡 กรุณาอัปโหลดรูปภาพสลีปบิลทางด้านซ้าย เพื่อเริ่มต้นการตรวจสอบระบบ ⚽✨")

st.markdown("---")

# --- 8. ตารางประวัติการตรวจสอบย้อนหลัง ---
st.markdown("### 📜 บันทึกประวัติการตรวจสอบบิลย้อนหลัง")

if st.session_state.history:
    table_data = []
    for idx, item in enumerate(st.session_state.history, 1):
        table_data.append({
            "ลำดับ": idx,
            "เวลาที่ตรวจสอบ": item["time"],
            "ยอดเดิมพัน (บาท)": f"{item['bet_amount']:,.2f}",
            "รายละเอียดบิล": item["matches"],
            "ผลการตรวจสอบ": item["status_text"],
            "รายละเอียดโปรโมชั่น / เหตุผล": item["reward_detail"]
        })
    
    st.dataframe(table_data, use_container_width=True)
    
    if st.button("🗑️ ล้างประวัติทั้งหมด"):
        st.session_state.history = []
        st.rerun()
else:
    st.info("ยังไม่มีข้อมูลบันทึกประวัติในระบบ เริ่มต้นอัปโหลดสลีปบิลเพื่อบันทึกรายการได้ทันทีครับ")