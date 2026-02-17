import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json

# ================= AYARLAR =================
GRAM_MIKTAR = 0.04
URL = "https://altin.doviz.com/halkbank"

TOKEN = os.environ.get("8475330105:AAGNqb6B93UJr6X5_8TEB9onDVKk3JRs6nA")
CHAT_ID = os.environ.get("8388070696")

BORSANIN_ACILISI = 8 * 60 + 50
BORSANIN_KAPANISI = 18 * 60

DATA_FILE = "state.json"
LOG_FILE = "bot_log.txt"


# ================= LOG SİSTEMİ =================
def log_yaz(mesaj):
    zaman = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{zaman}] {mesaj}\n")


# ================= TELEGRAM =================
def telegram_mesaj_gonder(text):
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
        if response.status_code != 200:
            log_yaz(f"Telegram hata: {response.text}")
    except Exception as e:
        log_yaz(f"Telegram exception: {e}")


# ================= FİYAT ÇEK =================
def gram_altin_getir():
    try:
        r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.find_all("tr"):
            if "Gram Altın" in row.text:
                cells = row.find_all("td")
                fiyat_text = cells[1].text.strip().replace(".", "").replace(",", ".")
                return float(fiyat_text)
        return None
    except Exception as e:
        log_yaz(f"Fiyat çekme hatası: {e}")
        return None


# ================= STATE YÖNETİMİ =================
def state_oku():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def state_kaydet(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# ================= ANA KONTROL =================
def kontrol_et():

    if not TOKEN or not CHAT_ID:
        log_yaz("TOKEN veya CHAT_ID tanımlı değil.")
        return

    now = datetime.now()
    dakika = now.hour * 60 + now.minute

    if not (BORSANIN_ACILISI <= dakika < BORSANIN_KAPANISI):
        log_yaz("Borsa kapalı.")
        return

    fiyat = gram_altin_getir()
    if fiyat is None:
        log_yaz("Fiyat alınamadı.")
        return

    state = state_oku()
    onceki_fiyat = state.get("son_fiyat")

    if onceki_fiyat == fiyat:
        log_yaz("Fiyat değişmedi.")
        return

    toplam = fiyat * GRAM_MIKTAR
    zaman = now.strftime("%d-%m-%Y %H:%M:%S")

    if onceki_fiyat:
        if fiyat > onceki_fiyat:
            trend = "📈 YÜKSELİŞ 🔥"
        else:
            trend = "📉 DÜŞÜŞ ⚡"
    else:
        trend = "🚀 İLK VERİ"

    mesaj = (
        f"💰 ALTIN TAKIP 💰\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🕒 {zaman}\n"
        f"🏦 Halkbank Gram Alış: {fiyat} TL\n"
        f"🪙 {GRAM_MIKTAR} gr Değer: {toplam:.2f} TL\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{trend}"
    )

    telegram_mesaj_gonder(mesaj)
    log_yaz("Mesaj gönderildi.")
    state["son_fiyat"] = fiyat
    state_kaydet(state)


# ================= BAŞLAT =================
if __name__ == "__main__":
    kontrol_et()