import streamlit as st
from PIL import Image
import pytesseract
import requests
import json
from openai import OpenAI
import certifi
import shutil

# 발표용 PC에서도 경로를 자동으로 확인하고 설정
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    # 윈도우 기본 설치 경로 (예: 발표용 노트북에 직접 설치해둔 경우)
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# API 키 불러오기
PERSPECTIVE_API_KEY = st.secrets["PERSPECTIVE_API_KEY"]
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🎯 민감도 향상된 TOXICITY 분석 함수
def analyze_toxicity_sensitive(text, api_key):
    url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={api_key}"
    data = {
        'comment': {'text': text},
        'languages': ['ko'],
        'requestedAttributes': {
            'TOXICITY': {},
            'SEVERE_TOXICITY': {},
            'INSULT': {},
            'PROFANITY': {},
            'THREAT': {}
        }
    }
    response = requests.post(url, data=json.dumps(data), verify=certifi.where())
    result = response.json()
    scores = {
        k: result['attributeScores'][k]['summaryScore']['value']
        for k in result['attributeScores']
    }
    max_score = max(scores.values())
    return max_score, scores

# 💡 GPT 문장 수정 제안
def suggest_rewrite(text):
    prompt = f"다음 문장은 공격적으로 보일 수 있습니다. 공손하고 부드럽게 다시 써 주세요:\n\n\"{text}\"\n\n공손한 문장:"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# 🧩 Streamlit 앱 구성
st.set_page_config(page_title="SNS 게시글 분석기 with GPT", layout="centered")
st.title("📛 SNS 게시글 위험도 분석기 + 문장 수정 제안")

# ✍️ 텍스트 입력
text_input = st.text_area("게시글 내용을 입력하세요:", height=150)

# 🖼️ 이미지 업로드 및 OCR 처리
uploaded_image = st.file_uploader("이미지 업로드 (선택)", type=["png", "jpg", "jpeg"])
image_text = ""
if uploaded_image is not None:
    image = Image.open(uploaded_image)
    st.image(image, caption="업로드한 이미지", use_column_width=True)

    try:
        gray = image.convert("L")
        bw = gray.point(lambda x: 0 if x < 150 else 255, '1')
        image_text = pytesseract.image_to_string(bw)
        st.markdown("🔍 이미지 내 텍스트:")
        st.code(image_text.strip())
    except Exception as e:
        st.warning(f"⚠️ 이미지에서 텍스트를 추출할 수 없습니다. ({e})")

# 🚨 분석 버튼
if st.button("위험 분석 실행하기"):
    if not text_input.strip() and not image_text.strip():
        st.warning("분석할 내용이 없습니다.")
    else:
        combined_text = text_input + "\n" + image_text
        try:
            score, breakdown = analyze_toxicity_sensitive(combined_text, PERSPECTIVE_API_KEY)
            st.markdown(f"### 🧠 최고 위험도 점수: `{score:.2f}`")
           # st.markdown("**📊 항목별 점수:**")
           # for key, value in breakdown.items():
           #     st.markdown(f"- **{key}**: `{value:.2f}`")

            if score > 0.7:
                st.error("⚠️ 이 게시글은 매우 공격적일 수 있습니다. 게시글을 삭제하거나 수정해 주세요.")
            elif score > 0.4:
                st.warning("⚠️ 다소 거친 표현이 있을 수 있습니다.")
            else:
                st.success("✅ 안전한 표현입니다.")

            # 💬 GPT 수정 제안
            st.markdown("💬 **공손한 문장 제안 (OpenAI GPT):**")
            suggestion = suggest_rewrite(combined_text)
            st.info(suggestion)

        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
