import os

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

import database as db
import kategoriler as kat

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ticyap-gelistirme-anahtari")

BASLANGIC_BAKIYESI = 1000

# Eski dükkan — geriye dönük uyumluluk
MULK_ROTA = {
    "ciftlik": "ciftlik_al",
    "demir_ocagi": "demir_ocagi_al",
    "degirmen": "degirmen_al",
    "dokumhane": "dokumhane_al",
}

DUKKAN = {
    "ciftlik": {
        "fiyat": 500,
        "alan": "ciftlik_sayisi",
        "ad": "Çiftlik (Eski)",
        "ikon": "bi-flower1",
        "aciklama": "Eski sistem çiftliği. Yeni tarla için Bahçe kategorisine bak.",
        "mesaj": "Çiftlik satın alındı!",
    },
    "demir_ocagi": {
        "fiyat": 2000,
        "alan": "demir_ocagi_sayisi",
        "ad": "Demir Ocağı (Eski)",
        "ikon": "bi-fire",
        "aciklama": "Eski sistem. Yeni maden için Hammadde kategorisine bak.",
        "mesaj": "Demir Ocağı satın alındı!",
    },
    "degirmen": {
        "fiyat": 5000,
        "alan": "degirmen_sayisi",
        "ad": "Un Değirmeni",
        "ikon": "bi-wind",
        "aciklama": "Manuel craft: 3 buğday → 1 un.",
        "mesaj": "Un Değirmeni satın alındı!",
    },
    "dokumhane": {
        "fiyat": 8000,
        "alan": "dokumhane_sayisi",
        "ad": "Demir Dökümhane",
        "ikon": "bi-building",
        "aciklama": "Manuel craft: 3 demir → 1 çelik kiriş.",
        "mesaj": "Demir Dökümhane satın alındı!",
    },
}


def giris_yapilmis_mi():
    return "kullanici_adi" in session


def aktif_oyuncu():
    if not giris_yapilmis_mi():
        return None

    oyuncu = db.oyuncu_getir(session["kullanici_adi"])
    if oyuncu is None:
        session.clear()
        return None

    oyuncu = db.uretim_hesapla(oyuncu)
    oyuncu = db.admin_bakiye_uygula(oyuncu)
    db.oyuncu_kaydet(oyuncu)
    return oyuncu


def ajax_istegi_mi():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def islem_cevabi(basarili, mesaj, oyuncu=None, ekstra=None):
    if ajax_istegi_mi():
        veri = {"basarili": basarili, "mesaj": mesaj}
        if oyuncu is not None:
            veri["oyuncu"] = db.oyuncu_ozet(oyuncu)
        veri["pazar_ilanlari"] = db.pazar_ilanlari_getir()
        if ekstra:
            veri.update(ekstra)
        return jsonify(veri)

    if basarili:
        return redirect(url_for("ana_sayfa", mesaj=mesaj))
    return redirect(url_for("ana_sayfa", hata=mesaj))


def mulk_satin_al_legacy(mulk_tipi):
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    urun = DUKKAN.get(mulk_tipi)
    if urun is None:
        return islem_cevabi(False, "Geçersiz ürün.")

    oyuncu = aktif_oyuncu()
    if not db.admin_mi(oyuncu) and oyuncu["bakiye"] < urun["fiyat"]:
        return islem_cevabi(
            False,
            f"Yetersiz bakiye! {urun['ad']} için {urun['fiyat']} TL gerekli.",
        )

    if not db.admin_mi(oyuncu):
        oyuncu["bakiye"] -= urun["fiyat"]
    oyuncu[urun["alan"]] += 1
    oyuncu = db.admin_bakiye_uygula(oyuncu)
    db.oyuncu_kaydet(oyuncu)
    return islem_cevabi(True, urun["mesaj"], oyuncu)


@app.route("/", methods=["GET"])
def ana_sayfa():
    oyuncu = aktif_oyuncu()
    mesaj = request.args.get("mesaj")
    hata = request.args.get("hata")
    ekonomi = db.ekonomik_durum_hesapla(oyuncu) if oyuncu else None
    return render_template(
        "index.html",
        oyuncu=oyuncu,
        mesaj=mesaj,
        hata=hata,
        kategoriler=kat.KATEGORILER,
        fabrikalar=kat.FABRIKA_TANIMLARI,
        arazi_fiyati=kat.ARAZI_FIYATI,
        enerji_adlari=kat.ENERJI_ADLARI,
        dukkan=DUKKAN,
        mulk_rota=MULK_ROTA,
        pazar_ilanlari=db.pazar_ilanlari_getir(),
        urun_adlari=db.URUN_ADLARI,
        referans_fiyatlar=db.REFERANS_FIYATLAR,
        ekonomi=ekonomi,
        zincir_rehberi=kat.ZINCIR_REHBERI,
        urun_tanimlari=kat.URUN_TANIMLARI,
    )


@app.route("/giris", methods=["POST"])
def giris():
    kullanici_adi = request.form.get("kullanici_adi", "").strip()
    sifre = request.form.get("sifre", "")

    if not kullanici_adi:
        return redirect(url_for("ana_sayfa", hata="Lütfen kullanıcı adı girin."))

    if len(kullanici_adi) > 20:
        return redirect(
            url_for("ana_sayfa", hata="Kullanıcı adı en fazla 20 karakter olabilir.")
        )

    basarili, mesaj = db.giris_yap(kullanici_adi, sifre)
    if not basarili:
        return redirect(url_for("ana_sayfa", hata=mesaj))

    session["kullanici_adi"] = kullanici_adi
    return redirect(url_for("ana_sayfa", mesaj=mesaj))


@app.route("/kayit", methods=["POST"])
def kayit():
    kullanici_adi = request.form.get("kullanici_adi", "").strip()
    sifre = request.form.get("sifre", "")

    if not kullanici_adi:
        return redirect(url_for("ana_sayfa", hata="Lütfen kullanıcı adı girin."))

    if len(kullanici_adi) > 20:
        return redirect(
            url_for("ana_sayfa", hata="Kullanıcı adı en fazla 20 karakter olabilir.")
        )

    basarili, mesaj = db.kayit_ol(kullanici_adi, sifre)
    if not basarili:
        return redirect(url_for("ana_sayfa", hata=mesaj))

    session["kullanici_adi"] = kullanici_adi
    return redirect(url_for("ana_sayfa", mesaj=mesaj))


@app.route("/cikis", methods=["POST"])
def cikis():
    session.clear()
    return redirect(url_for("ana_sayfa", mesaj="Başarıyla çıkış yaptın."))


@app.route("/mulk-al", methods=["POST"])
def mulk_al():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    kategori = request.form.get("kategori", "").strip()
    oge = request.form.get("oge", "").strip()
    basarili, mesaj, oyuncu = db.mulk_satin_al(
        session["kullanici_adi"], kategori, oge
    )
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/arazi-al", methods=["POST"])
def arazi_al():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    basarili, mesaj, oyuncu = db.arazi_satin_al(session["kullanici_adi"])
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/fabrika-kur", methods=["POST"])
def fabrika_kur():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    try:
        arazi_id = int(request.form.get("arazi_id", 0))
    except ValueError:
        return islem_cevabi(False, "Geçersiz arazi.")

    fabrika_tipi = request.form.get("fabrika", "").strip()
    basarili, mesaj, oyuncu = db.fabrika_kur(
        session["kullanici_adi"], arazi_id, fabrika_tipi
    )
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/ciftlik-al", methods=["POST"])
def ciftlik_al():
    return mulk_satin_al_legacy("ciftlik")


@app.route("/demir-ocagi-al", methods=["POST"])
def demir_ocagi_al():
    return mulk_satin_al_legacy("demir_ocagi")


@app.route("/fabrika-al", methods=["POST"])
def fabrika_al():
    return mulk_satin_al_legacy("demir_ocagi")


@app.route("/degirmen-al", methods=["POST"])
def degirmen_al():
    return mulk_satin_al_legacy("degirmen")


@app.route("/dokumhane-al", methods=["POST"])
def dokumhane_al():
    return mulk_satin_al_legacy("dokumhane")


@app.route("/craft", methods=["POST"])
def craft():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    tarif = request.form.get("tarif", "").strip()
    basarili, mesaj, oyuncu = db.craft_yap(session["kullanici_adi"], tarif)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/pazar-ilan", methods=["POST"])
def pazar_ilan():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    aktif_oyuncu()

    urun = request.form.get("urun", "").strip()
    try:
        miktar = int(request.form.get("miktar", 0))
        birim_fiyat = int(request.form.get("birim_fiyat", 0))
    except ValueError:
        return islem_cevabi(False, "Miktar ve fiyat sayı olmalı.")

    basarili, mesaj = db.pazar_ilan_ver(
        session["kullanici_adi"], urun, miktar, birim_fiyat
    )
    oyuncu = aktif_oyuncu() if basarili else None
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/pazar-satin-al", methods=["POST"])
def pazar_satin_al():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    try:
        ilan_id = int(request.form.get("ilan_id", 0))
    except ValueError:
        return islem_cevabi(False, "Geçersiz ilan.")

    basarili, mesaj = db.pazar_satin_al(session["kullanici_adi"], ilan_id)
    oyuncu = aktif_oyuncu() if basarili else None
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/api/durum", methods=["GET"])
def api_durum():
    oyuncu = aktif_oyuncu()
    if oyuncu is None:
        return {"giris": False}

    ozet = db.oyuncu_ozet(oyuncu)
    return {
        "giris": True,
        **ozet,
        "pazar_ilanlari": db.pazar_ilanlari_getir(),
        "urun_adlari": db.URUN_ADLARI,
        "fabrika_tanimlari": kat.FABRIKA_TANIMLARI,
    }


@app.route("/tesis-seviye-atla", methods=["POST"])
def tesis_seviye_atla():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    tesis_alani = request.form.get("tesis_alani", "").strip()
    basarili, mesaj, oyuncu = db.tesis_seviye_atla(session["kullanici_adi"], tesis_alani)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/api/tesis-detay", methods=["GET"])
def api_tesis_detay():
    if not giris_yapilmis_mi():
        return {"hata": "Önce giriş yapmalısın."}

    oyuncu = aktif_oyuncu()
    tesis_alani = request.args.get("tesis_alani", "").strip()
    
    detaylar = db.tesis_uretim_detaylari(oyuncu, tesis_alani)
    if detaylar is None:
        return {"hata": "Tesis bulunamadı veya satın alınmamış."}
    
    return detaylar


@app.route("/klup-olustur", methods=["POST"])
def klup_olustur():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    klup_adi = request.form.get("klup_adi", "").strip()
    basarili, mesaj, oyuncu = db.klup_olustur(session["kullanici_adi"], klup_adi)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/klup-katil", methods=["POST"])
def klup_katil():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    klup_id = request.form.get("klup_id", "").strip()
    basarili, mesaj, oyuncu = db.klup_katil(session["kullanici_adi"], klup_id)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/klup-ayril", methods=["POST"])
def klup_ayril():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    basarili, mesaj, oyuncu = db.klup_ayril(session["kullanici_adi"])
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/chat-mesaj-ekle", methods=["POST"])
def chat_mesaj_ekle():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    mesaj = request.form.get("mesaj", "").strip()
    basarili, mesaj_sonuc = db.chat_mesaj_ekle(session["kullanici_adi"], mesaj)
    return islem_cevabi(basarili, mesaj_sonuc)


@app.route("/api/chat-mesajlari", methods=["GET"])
def api_chat_mesajlari():
    return {"mesajlar": db.chat_mesajlari_getir()}


@app.route("/api/klupler", methods=["GET"])
def api_klupler():
    return {"klupler": db.klupler_getir()}


@app.route("/fabrika-uretim-baslat", methods=["POST"])
def fabrika_uretim_baslat():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    try:
        arazi_id = int(request.form.get("arazi_id", 0))
    except ValueError:
        return islem_cevabi(False, "Geçersiz arazi.")

    basarili, mesaj, oyuncu = db.fabrika_uretim_baslat(session["kullanici_adi"], arazi_id)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/fabrika-uretim-durdur", methods=["POST"])
def fabrika_uretim_durdur():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    try:
        arazi_id = int(request.form.get("arazi_id", 0))
    except ValueError:
        return islem_cevabi(False, "Geçersiz arazi.")

    basarili, mesaj, oyuncu = db.fabrika_uretim_durdur(session["kullanici_adi"], arazi_id)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/fabrika-urun-topla", methods=["POST"])
def fabrika_urun_topla():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    try:
        arazi_id = int(request.form.get("arazi_id", 0))
    except ValueError:
        return islem_cevabi(False, "Geçersiz arazi.")

    basarili, mesaj, oyuncu = db.fabrika_urun_topla(session["kullanici_adi"], arazi_id)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/tesis-uretim-baslat", methods=["POST"])
def tesis_uretim_baslat():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    tesis_alani = request.form.get("tesis_alani", "")
    if not tesis_alani:
        return islem_cevabi(False, "Geçersiz tesis.")

    basarili, mesaj, oyuncu = db.tesis_uretim_baslat(session["kullanici_adi"], tesis_alani)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/tesis-uretim-durdur", methods=["POST"])
def tesis_uretim_durdur():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    tesis_alani = request.form.get("tesis_alani", "")
    if not tesis_alani:
        return islem_cevabi(False, "Geçersiz tesis.")

    basarili, mesaj, oyuncu = db.tesis_uretim_durdur(session["kullanici_adi"], tesis_alani)
    return islem_cevabi(basarili, mesaj, oyuncu)


@app.route("/tesis-urun-topla", methods=["POST"])
def tesis_urun_topla():
    if not giris_yapilmis_mi():
        return islem_cevabi(False, "Önce giriş yapmalısın.")

    tesis_alani = request.form.get("tesis_alani", "")
    if not tesis_alani:
        return islem_cevabi(False, "Geçersiz tesis.")

    basarili, mesaj, oyuncu = db.tesis_urun_topla(session["kullanici_adi"], tesis_alani)
    return islem_cevabi(basarili, mesaj, oyuncu)


if __name__ == "__main__":
    db.admin_hesabi_hazirla()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


db.admin_hesabi_hazirla()
