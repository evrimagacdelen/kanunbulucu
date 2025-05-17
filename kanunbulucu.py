import streamlit as st
import re
from io import BytesIO
from PyPDF2 import PdfReader

# === Sayfa Ayarı ===
st.set_page_config(page_title="Kanun ve Kamu Zararı Ayıklayıcı", layout="wide")
st.title("📄 PDF'ten Kanun ve Kamu Zararı Tespiti")

# === Geliştirilmiş Regex: Türkçe madde biçimlerini kapsar ===
KANUN_REGEX = (
    r"\b(?P<kanun>\d{4})\s*sayılı"                # Sadece 4 haneli rakam
    r"(?:.*?)"                                    # Araya giren metin (gerekirse DOTALL ile)
    r"(?:madde|maddesi)?\s*"                      # Opsiyonel "madde"/"maddesi"
    r"(?P<madde>\d{1,3})\b"                       # 1–3 haneli madde numarası
)

# === PDF'ten Metin Çekme Fonksiyonu ===
def oku_pdf(uploaded_file):
    """
    Yüklenen PDF dosyasını bellekten okuyup metni birleştirir.
    """
    data = uploaded_file.read()
    reader = PdfReader(BytesIO(data))
    metin = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            metin.append(text)
    return "\n".join(metin)

# === Kanun Ayıklama Fonksiyonu ===
def kanunlari_ayikla(metin):
    """
    Verilen metinden '1234 sayılı ... madde 12' biçimindeki kanun ve madde referanslarını ayıklar.
    """
    eslesenler = re.findall(
        KANUN_REGEX,
        metin,
        flags=re.IGNORECASE | re.DOTALL
    )
    # Tekilleştir ve 'kanun/madde' formatında döndür
    return sorted({f"{k}/{m}" for k, m in eslesenler})

# === Geliştirilmiş Kamu Zararı Tahmini (Regex Destekli) ===
def kamu_zarari_tahmini(metin):
    """
    Basit kalıplar ile kamu zararı var mı yok mu tahmin eder.
    """
    text = metin.lower()

    zarar_var = [
        r"ödettirilmesine",
        r"kamu zararına.*?neden olunmuştur",
        r"faiziyle.*?tahsil edilmesine"
    ]

    zarar_yok = [
        r"ilişilecek husus bulunmadığına",
        r"mevzuata aykırılık bulunmamıştır",
        r"zarar oluşmamıştır",
        r"tahsil edildiğinden",
        r"husus bulunmadığına",
        r"ilişilecek husus kalmadığına",
        r"kamu zararı oluşmadığından",
        r"herhangi bir kamu zararı.*?oluşmadığından",
        r"kamu zararı olduğu.*?ilişilecek husus bulunmadığına",
        r"… tl.*?ilişilecek husus bulunmadığına",
        r"ilişilecek.*?husus bulunmadığına",
        r"sorumlularından müştereken ve müteselsilen tazminine karar verilmesi uygun olur"
    ]

    # Eğer herhangi bir 'var' kalıbı bulunursa
    for kalip in zarar_var:
        if re.search(kalip, text):
            return "Kamu Zararı VAR"

    # Eğer herhangi bir 'yok' kalıbı bulunursa
    for kalip in zarar_yok:
        if re.search(kalip, text):
            return "Kamu Zararı YOK"

    # Tanımlı kalıplar dışında kalanlar
    return "Tahmin edilemedi"

# === PDF Yükleyici Arayüz ===
pdf_dosyasi = st.file_uploader("📥 PDF Karar Dosyasını Yükleyin", type="pdf")

if pdf_dosyasi:
    try:
        # PDF'i oku ve metni al
        metin = oku_pdf(pdf_dosyasi)
    except Exception as e:
        st.error(f"❌ PDF okunurken hata oluştu: {e}")
        st.stop()

    # Kanun ve madde ayıklama
    kanunlar = kanunlari_ayikla(metin)
    # Kamu zararı tahmini
    zarar = kamu_zarari_tahmini(metin)

    st.subheader("🔍 Tahminler")

    # === Kanunlar ===
    if kanunlar:
        st.success("✅ Tespit Edilen Kanunlar:")
        st.code(", ".join(kanunlar), language="text")
    else:
        st.warning("❌ PDF içinde kanun/madde ifadesi bulunamadı.")

    # === Kamu Zararı ===
    if zarar == "Kamu Zararı VAR":
        st.error(f"💥 {zarar}")
    elif zarar == "Kamu Zararı YOK":
        st.success(f"✅ {zarar}")
    else:
        st.warning("⚠️ Kamu zararı durumu net anlaşılamadı.")
