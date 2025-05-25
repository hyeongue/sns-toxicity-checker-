import streamlit as st
from PIL import Image
import pytesseract
import requests
import json

# Perspective API 키 (직접 입력 필요)
PERSPECTIVE_API_KEY = "AIzaSyCDLFHm1zNjKwsaP8oVhWC8ylswhNM6nnM"  # ← 여기에 API 키 입력

def analyze_toxicity(text):
    url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={PERSPECTIVE_API_KEY}"
    data = {
        'comment': {'text': text},
        'languages': ['en'],
        'requestedAttributes': {'TOXICITY': {}}
    }
    response = requests.post(url, data=json.dumps(data))
    result = response.json()
    score = result['attributeScores']['TOXICITY']['summaryScore']['value']
    return score

st.set_page_config(page_title="SNS 게시글 위험도 분석기", layout="centered")
st.title("📛 SNS 게시글 위험도 분석기")
st.markdown("AI가 당신의 글과 이미지를 분석하여 혐오/공격 표현을 판단해줍니다.")

text_input = st.text_area("✍️ 게시글 내용을 입력하세요:", height=150)

uploaded_image = st.file_uploader("🖼️ 이미지 업로드 (선택)", type=["png", "jpg", "jpeg"])
image_text = ""

if uploaded_image is not None:
    image = Image.open(uploaded_image)
    st.image(image, caption="업로드한 이미지", use_column_width=True)
    image_text = pytesseract.image_to_string(image)
    st.markdown("🔍 **이미지 내 텍스트 추출 결과:**")
    st.code(image_text.strip())

if st.button("🚨 분석하기"):
    if not text_input.strip() and not image_text.strip():
        st.warning("분석할 내용이 없습니다. 글 또는 이미지를 입력해주세요.")
    else:
        combined_text = text_input + "\n" + image_text
        try:
            score = analyze_toxicity(combined_text)
            st.markdown(f"### 🧠 TOXICITY 점수: `{score:.2f}`")

            if score > 0.7:
                st.error("⚠️ 위험: 이 게시물은 매우 공격적일 수 있습니다. 수정이 필요합니다.")
            elif score > 0.4:
                st.warning("⚠️ 주의: 일부 표현이 공격적으로 인식될 수 있습니다.")
            else:
                st.success("✅ 안전: 문제가 될 표현이 감지되지 않았습니다.")

            st.markdown("💡 **수정 제안:**")
            st.write("- 감정을 부드럽게 표현해보세요.")
            st.write("- 사실 위주로 쓰고, 비난을 줄여보세요.")
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")
