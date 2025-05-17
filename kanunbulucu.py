import streamlit as st
import re
from io import BytesIO
from PyPDF2 import PdfReader

# — Page setup —
st.set_page_config(page_title="Kanun ve Kamu Zararı Ayıklayıcı", layout="wide")
st.title("📄 PDF'ten Kanun ve Kamu Zararı Tespiti")

KANUN_REGEX = (
    r"\b(?P<kanun>\d{4})\s*sayılı"
    r"(?:.*?)"
    r"(?:madde|maddesi)?\s*"
    r"(?P<madde>\d{1,3})\b"
)

def oku_pdf(uploaded_file):
    data = uploaded_file.read()
    reader = PdfReader(BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def kanunlari_ayikla(metin):
    eslesenler = re.findall(KANUN_REGEX, metin, flags=re.IGNORECASE | re.DOTALL)
    return sorted({f"{k}/{m}" for k, m in eslesenler})

def kamu_zarari_tahmini(metin):
    text = metin.lower()
    var = [r"ödettirilmesine", r"kamu zararına.*?neden olunmuştur", r"faiziyle.*?tahsil edilmesine"]
    yok = [r"ilişilecek husus bulunmadığına", r"mevzuata aykırılık bulunmamıştır", r"zarar oluşmamıştır", …]
    for p in var:
        if re.search(p, text):
            return "Kamu Zararı VAR"
    for p in yok:
        if re.search(p, text):
            return "Kamu Zararı YOK"
    return "Tahmin edilemedi"

pdf_dosyasi = st.file_uploader("📥 PDF Karar Dosyasını Yükleyin", type="pdf")
if pdf_dosyasi:
    try:
        metin = oku_pdf(pdf_dosyasi)
    except Exception as e:
        st.error(f"❌ PDF okunurken hata oluştu: {e}")
        st.stop()

    kanunlar = kanunlari_ayikla(metin)
    zarar    = kamu_zarari_tahmini(metin)

    st.subheader("🔍 Tahminler")
    if kanunlar:
        st.success("✅ Tespit Edilen Kanunlar:")
        st.code(", ".join(kanunlar), language="text")
    else:
        st.warning("❌ PDF içinde kanun/madde ifadesi bulunamadı.")

    if zarar == "Kamu Zararı VAR":
        st.error(f"💥 {zarar}")
    elif zarar == "Kamu Zararı YOK":
        st.success(f"✅ {zarar}")
    else:
        st.warning("⚠️ Kamu zararı durumu net anlaşılamadı.")
