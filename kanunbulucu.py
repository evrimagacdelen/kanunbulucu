import streamlit as st
import re
import io
from pypdf import PdfReader

# === Sayfa Ayarı ===
st.set_page_config(page_title="Kanun ve Kamu Zararı Ayıklayıcı", layout="wide")
st.title("📄 PDF'ten Kanun ve Kamu Zararı Tespiti")

# === Geliştirilmiş Regex: Türkçe madde biçimlerini kapsar ===
KANUN_REGEX = (
    r"\b(?P<kanun>\d{4})\s*sayılı"                # Sadece 4 haneli rakam
    r"(?:.*?)"                                    # Araya giren metin
    r"(?:madde|maddesi)?\s*"                      # Opsiyonel "madde"/"maddesi"
    r"(?P<madde>\d{1,3})\b"                       # 1–3 haneli madde numarası
)

# === Kanun Ayıklama Fonksiyonu ===
def kanunlari_ayikla(metin):
    eslesenler = re.findall(KANUN_REGEX, metin)
    return sorted(set(f"{k}/{m}" for k, m in eslesenler))

# === PDF'ten Metin Çek ===
def oku_pdf(pdf_file):
    try:
        # PDF içeriğini oku
        pdf_bytes = pdf_file.getvalue()
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        
        # Tüm sayfaları birleştir
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
        
        return text
    except Exception as e:
        st.error(f"PDF okuma hatası: {str(e)}")
        return ""

# === Geliştirilmiş Kamu Zararı Tahmini (Regex Destekli) ===
def kamu_zarari_tahmini(metin):
    metin = metin.lower()

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

    for kalip in zarar_var:
        if re.search(kalip, metin):
            return "Kamu Zararı VAR"

    for kalip in zarar_yok:
        if re.search(kalip, metin):
            return "Kamu Zararı YOK"

    return "Tahmin edilemedi"

# === Gerekli kütüphaneleri kontrol et ===
with st.sidebar:
    st.subheader("Hakkında")
    st.write("Bu uygulama, yüklenen PDF dosyalarından kanun referanslarını ve kamu zararı durumunu tespit eder.")
    st.write("Geliştirici: [İletişim](mailto:ornek@mail.com)")

# === PDF Yükleyici Arayüz ===
st.subheader("📥 PDF Karar Dosyası Yükleyin")
pdf_dosyasi = st.file_uploader("", type="pdf")

if pdf_dosyasi:
    with st.spinner("PDF işleniyor..."):
        try:
            metin = oku_pdf(pdf_dosyasi)
            
            if not metin:
                st.error("PDF içeriği okunamadı veya boş.")
            else:
                kanunlar = kanunlari_ayikla(metin)
                zarar = kamu_zarari_tahmini(metin)

                st.subheader("🔍 Tahminler")

                # === Kanunlar ===
                if kanunlar:
                    virgullu = ", ".join(kanunlar)
                    st.success("✅ Tespit Edilen Kanunlar:")
                    st.code(virgullu, language="text")
                else:
                    st.warning("❌ PDF içinde kanun/madde ifadesi bulunamadı.")

                # === Kamu Zararı ===
                if zarar == "Kamu Zararı VAR":
                    st.error(f"💥 {zarar}")
                elif zarar == "Kamu Zararı YOK":
                    st.success(f"✅ {zarar}")
                else:
                    st.warning("⚠️ Kamu zararı durumu net anlaşılamadı.")
                
                # İsterseniz debug için metin içeriğini gösterin
                with st.expander("Çıkarılan Metin İçeriği (Debug)"):
                    st.text(metin[:1000] + "..." if len(metin) > 1000 else metin)
        
        except Exception as e:
            st.error(f"İşlem sırasında bir hata oluştu: {str(e)}")
