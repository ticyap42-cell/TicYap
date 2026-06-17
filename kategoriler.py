# TicYap — Tam ekonomi haritası ve üretim zincirleri

ARAZI_FIYATI = 15000

ENERJI_TURLERI = ("elektrik", "su", "dogalgaz")
ENERJI_ADLARI = {
    "elektrik": "Elektrik",
    "su": "Su",
    "dogalgaz": "Doğalgaz",
}
VARSAYILAN_ENERJI_KAPASITE = {
    "elektrik": 2000,
    "su": 1500,
    "dogalgaz": 1500,
}

# ── SEVİYE SİSTEMİ ──────────────────────────────────────────────
SEVIYE_SISTEMI = {
    "maks_seviye": 20,  # Maksimum seviye artırıldı
    "maliyet_carpani": 1.8,  # Her seviye için maliyet çarpanı
    "uretim_carpani": 0.20,  # Her seviye için üretim artışı (%20)
    "xp_per_seviye": 150,  # Her seviye için gereken XP (artırıldı)
}

# XP kazanma kaynakları
XP_KAYNAKLARI = {
    "tesis_satin_al": 25,  # Tesis satın alınca (artırıldı)
    "tesis_yukselt": 15,  # Tesis seviye atlayınca (artırıldı)
    "uretim_yap": 2,  # Her dakika üretim için (artırıldı)
    "pazar_satis": 5,  # Pazar satışı için (artırıldı)
    "pazar_satin_al": 3,  # Pazar alımı için (artırıldı)
    "fabrika_kur": 30,  # Fabrika kurulunca
    "uretim_baslat": 5,  # Üretim başlatınca
    "urun_topla": 3,  # Ürün toplayınca
}

# Her tesis için seviye gereksinimleri (hangi seviyeden sonra alınabilir)
SEVIYE_GEREKSINIMLERI = {
    # Bahçe seviyeleri
    "bahce_elma": 1,
    "bahce_armut": 1,
    "bahce_antep_fistigi": 3,
    "bahce_zeytin": 2,
    "bahce_portakal": 2,
    "bahce_uzum": 2,
    "bahce_muz": 4,
    "bahce_findik": 3,
    "bahce_badem": 4,
    "bahce_kiraz": 2,
    "bahce_bugday": 1,
    "bahce_pamuk": 2,
    "bahce_seker_pancari": 2,
    "bahce_aycicegi": 2,
    "bahce_misir": 1,
    "bahce_tutun": 3,
    "bahce_cay": 3,
    "bahce_kahve": 4,
    "bahce_kakao": 5,
    "bahce_patates": 1,
    "bahce_soya": 2,
    "bahce_domates": 2,
    "bahce_biber": 2,
    "bahce_salatalik": 2,
    "bahce_cilek": 3,
    "bahce_sogan": 1,
    "bahce_gul": 4,
    "bahce_lavanta": 4,
    "bahce_mantar": 3,
    "bahce_nane": 2,
    # Çiftlik seviyeleri
    "ciftlik_buyukbas": 2,
    "ciftlik_kucukbas": 2,
    "ciftlik_tavuk": 1,
    "ciftlik_aricilik": 2,
    "ciftlik_ipek": 5,
    "ciftlik_mandira": 3,
    "ciftlik_at": 6,
    "ciftlik_balik": 3,
    "ciftlik_hindi": 3,
    "ciftlik_devekus": 8,
    # Hammadde seviyeleri
    "hammadde_ormancilik": 2,
    "hammadde_demir_maden": 3,
    "hammadde_komur_maden": 3,
    "hammadde_bakir_maden": 4,
    "hammadde_boksit": 4,
    "hammadde_mermer": 3,
    "hammadde_kirec": 3,
    "hammadde_kuvars": 3,
    # Enerji seviyeleri
    "enerji_gunes": 3,
    "enerji_su": 2,
    "enerji_dogalgaz": 4,
    "enerji_termik": 5,
    "enerji_ruzgar": 4,
}


def _mulk(ad, fiyat, alan, ikon, aciklama, uretim=None, enerji_uretim=None,
          girdi_tuketim=None, mesaj=None, kapasite=None, saatlik_uretim=None):
    oge = {
        "ad": ad,
        "fiyat": fiyat,
        "alan": alan,
        "ikon": ikon,
        "aciklama": aciklama,
        "mesaj": mesaj or f"{ad} kuruldu!",
    }
    if uretim:
        oge["uretim"] = uretim
    if enerji_uretim:
        oge["enerji_uretim"] = enerji_uretim
    if girdi_tuketim:
        oge["girdi_tuketim"] = girdi_tuketim
    if kapasite:
        oge["kapasite"] = kapasite
    if saatlik_uretim:
        oge["saatlik_uretim"] = saatlik_uretim
    return oge


# ── ÜRÜN TANIMLARI ──────────────────────────────────────────────
URUN_TANIMLARI = {
    # Bahçe ham maddeleri
    "elma": {"ad": "Elma", "fiyat": 18, "kategori": "ham"},
    "armut": {"ad": "Armut", "fiyat": 17, "kategori": "ham"},
    "antep_fistigi": {"ad": "Antep Fıstığı", "fiyat": 80, "kategori": "ham"},
    "zeytin": {"ad": "Zeytin", "fiyat": 22, "kategori": "ham"},
    "portakal": {"ad": "Portakal", "fiyat": 20, "kategori": "ham"},
    "uzum": {"ad": "Üzüm", "fiyat": 19, "kategori": "ham"},
    "muz": {"ad": "Muz", "fiyat": 25, "kategori": "ham"},
    "findik": {"ad": "Fındık", "fiyat": 45, "kategori": "ham"},
    "badem": {"ad": "Badem", "fiyat": 50, "kategori": "ham"},
    "kiraz": {"ad": "Kiraz", "fiyat": 28, "kategori": "ham"},
    "bugday": {"ad": "Buğday", "fiyat": 15, "kategori": "ham"},
    "pamuk": {"ad": "Pamuk", "fiyat": 30, "kategori": "ham"},
    "seker_pancari": {"ad": "Şeker Pancarı", "fiyat": 18, "kategori": "ham"},
    "aycicegi": {"ad": "Ayçiçeği", "fiyat": 16, "kategori": "ham"},
    "misir": {"ad": "Mısır", "fiyat": 14, "kategori": "ham"},
    "tutun": {"ad": "Tütün", "fiyat": 35, "kategori": "ham"},
    "cay": {"ad": "Çay Yaprağı", "fiyat": 32, "kategori": "ham"},
    "kahve": {"ad": "Kahve Çekirdeği", "fiyat": 55, "kategori": "ham"},
    "kakao": {"ad": "Kakao", "fiyat": 70, "kategori": "ham"},
    "patates": {"ad": "Patates", "fiyat": 12, "kategori": "ham"},
    "soya": {"ad": "Soya", "fiyat": 20, "kategori": "ham"},
    "domates": {"ad": "Domates", "fiyat": 14, "kategori": "ham"},
    "biber": {"ad": "Biber", "fiyat": 15, "kategori": "ham"},
    "salatalik": {"ad": "Salatalık", "fiyat": 13, "kategori": "ham"},
    "cilek": {"ad": "Çilek", "fiyat": 30, "kategori": "ham"},
    "sogan": {"ad": "Soğan", "fiyat": 10, "kategori": "ham"},
    "gul": {"ad": "Gül", "fiyat": 40, "kategori": "ham"},
    "lavanta": {"ad": "Lavanta", "fiyat": 38, "kategori": "ham"},
    "mantar": {"ad": "Mantar", "fiyat": 22, "kategori": "ham"},
    "nane": {"ad": "Nane", "fiyat": 12, "kategori": "ham"},
    # Çiftlik
    "sut": {"ad": "Süt", "fiyat": 25, "kategori": "ham"},
    "et": {"ad": "Et", "fiyat": 40, "kategori": "ham"},
    "deri": {"ad": "Ham Deri", "fiyat": 35, "kategori": "ham"},
    "yun": {"ad": "Yün", "fiyat": 30, "kategori": "ham"},
    "yumurta": {"ad": "Yumurta", "fiyat": 12, "kategori": "ham"},
    "tavuk_et": {"ad": "Tavuk Eti", "fiyat": 28, "kategori": "ham"},
    "bal": {"ad": "Bal", "fiyat": 45, "kategori": "ham"},
    "balmumu": {"ad": "Balmumu", "fiyat": 20, "kategori": "ham"},
    "ipek": {"ad": "Ham İpek", "fiyat": 90, "kategori": "ham"},
    "peynir": {"ad": "Peynir", "fiyat": 35, "kategori": "islenmis"},
    "at": {"ad": "At", "fiyat": 200, "kategori": "luks"},
    "balik": {"ad": "Balık", "fiyat": 32, "kategori": "ham"},
    "hindi_et": {"ad": "Hindi Eti", "fiyat": 30, "kategori": "ham"},
    "tuy": {"ad": "Tüy", "fiyat": 18, "kategori": "ham"},
    "deve_et": {"ad": "Deve Eti", "fiyat": 120, "kategori": "luks"},
    "deve_yumurtasi": {"ad": "Deve Yumurtası", "fiyat": 150, "kategori": "luks"},
  # Hammadde
    "tomruk": {"ad": "Tomruk", "fiyat": 22, "kategori": "ham"},
    "odun": {"ad": "Odun", "fiyat": 20, "kategori": "ham"},
    "demir_cevheri": {"ad": "Demir Cevheri", "fiyat": 35, "kategori": "ham"},
    "demir": {"ad": "Demir", "fiyat": 50, "kategori": "ham"},
    "komur": {"ad": "Kömür", "fiyat": 28, "kategori": "ham"},
    "bakir_cevheri": {"ad": "Bakır Cevheri", "fiyat": 45, "kategori": "ham"},
    "boksit": {"ad": "Boksit", "fiyat": 40, "kategori": "ham"},
    "mermer": {"ad": "Mermer", "fiyat": 38, "kategori": "ham"},
    "kirec": {"ad": "Kireç Taşı", "fiyat": 25, "kategori": "ham"},
    "kuvars": {"ad": "Kuvars/Kum", "fiyat": 18, "kategori": "ham"},
    # İşlenmiş / lüks
    "un": {"ad": "Un", "fiyat": 60, "kategori": "islenmis"},
    "celik": {"ad": "Çelik Külçe", "fiyat": 200, "kategori": "islenmis"},
    "celik_kiris": {"ad": "Çelik Kiriş", "fiyat": 200, "kategori": "islenmis"},
    "kereste": {"ad": "Kereste", "fiyat": 55, "kategori": "islenmis"},
    "kagit_hamuru": {"ad": "Kağıt Hamuru", "fiyat": 40, "kategori": "islenmis"},
    "tahta": {"ad": "Tahta", "fiyat": 55, "kategori": "islenmis"},
    "kumas": {"ad": "Kumaş", "fiyat": 75, "kategori": "islenmis"},
    "seker": {"ad": "Şeker", "fiyat": 35, "kategori": "islenmis"},
    "sivi_yag": {"ad": "Sıvı Yağ", "fiyat": 45, "kategori": "islenmis"},
    "cikolata": {"ad": "Çikolata", "fiyat": 250, "kategori": "luks"},
    "cam": {"ad": "Cam/Şişe", "fiyat": 30, "kategori": "islenmis"},
    "konserve": {"ad": "Konserve", "fiyat": 65, "kategori": "islenmis"},
    "meyve_suyu": {"ad": "Meyve Suyu", "fiyat": 55, "kategori": "islenmis"},
    "islenmis_deri": {"ad": "İşlenmiş Deri", "fiyat": 90, "kategori": "islenmis"},
    "kitap": {"ad": "Kitap/Ambalaj", "fiyat": 50, "kategori": "islenmis"},
    "elektronik": {"ad": "Elektronik Parça", "fiyat": 180, "kategori": "islenmis"},
    "yem": {"ad": "Hayvan Yemi", "fiyat": 25, "kategori": "islenmis"},
    "mobilya": {"ad": "Mobilya", "fiyat": 300, "kategori": "luks"},
}

URUN_ADLARI = {k: v["ad"] for k, v in URUN_TANIMLARI.items()}
REFERANS_FIYATLAR = {k: v["fiyat"] for k, v in URUN_TANIMLARI.items()}


# ── BAHÇE (30) ──────────────────────────────────────────────────
_BAHCE = [
    ("elma", "Elma Bahçesi", "elma", 700, "bi-apple", "Unlu tatlı ve meyve suyu fabrikasına gider."),
    ("armut", "Armut Bahçesi", "armut", 700, "bi-apple", "Meyve suyu ve konserve için."),
    ("antep_fistigi", "Antep Fıstığı Bahçesi", "antep_fistigi", 1200, "bi-flower1", "Çikolata fabrikasının lüks girdisi."),
    ("zeytin", "Zeytinliği", "zeytin", 900, "bi-circle", "Bitkisel yağ fabrikasına gider."),
    ("portakal", "Portakal Bahçesi", "portakal", 850, "bi-brightness-high", "Meyve suyu fabrikası için."),
    ("uzum", "Üzüm Bağı", "uzum", 800, "bi-droplet-half", "Kuru üzüm, şarap ve meyve suyu için."),
    ("muz", "Muz Plantasyonu", "muz", 1100, "bi-emoji-smile", "Tropikal meyve ve içecek üretimi."),
    ("findik", "Fındık Ocağı", "findik", 1000, "bi-nut", "Çikolata ve ezme üretimi için."),
    ("badem", "Bademliği", "badem", 1100, "bi-nut-fill", "Lüks gıda ve çikolata girdisi."),
    ("kiraz", "Kiraz/Visne Bahçesi", "kiraz", 950, "bi-circle-fill", "Reçel ve konserve için."),
    ("bugday", "Buğday Tarlası", "bugday", 400, "bi-grid-3x3-gap", "Un fabrikası ve yem fabrikasının temeli."),
    ("pamuk", "Pamuk Tarlası", "pamuk", 600, "bi-cloud", "Tekstil fabrikasının ana girdisi."),
    ("seker_pancari", "Şeker Pancarı Tarlası", "seker_pancari", 550, "bi-grid", "Şeker fabrikası için."),
    ("aycicegi", "Ayçiçeği Tarlası", "aycicegi", 500, "bi-sun", "Sıvı yağ fabrikası için."),
    ("misir", "Mısır Tarlası", "misir", 450, "bi-grid-1x2", "Yem ve yağ üretimi için çok yönlü."),
    ("tutun", "Tütün Tarlası", "tutun", 800, "bi-flower2", "Özel işleme tesisleri için."),
    ("cay", "Çay Plantasyonu", "cay", 900, "bi-cup-hot", "Kurutma ve paketleme için."),
    ("kahve", "Kahve Tarlası", "kahve", 1100, "bi-cup", "Kavurma ve içecek tesisi için."),
    ("kakao", "Kakao Plantasyonu", "kakao", 1300, "bi-gift", "Çikolata fabrikasının kalbi."),
    ("patates", "Patates Tarlası", "patates", 400, "bi-egg", "Cips ve dondurulmuş gıda için."),
    ("soya", "Soya Fasulyesi Tarlası", "soya", 500, "bi-circle", "Yem ve kimya sanayi girdisi."),
    ("domates", "Domates Serası", "domates", 500, "bi-brightness-alt-high", "Salça ve konserve fabrikası için."),
    ("biber", "Biber Serası", "biber", 480, "bi-fire", "Salça ve konserve için."),
    ("salatalik", "Salatalık Tarlası", "salatalik", 450, "bi-flower3", "Turşu ve konserve için."),
    ("cilek", "Çilek Serası", "cilek", 700, "bi-heart", "Reçel ve lüks gıda için."),
    ("sogan", "Soğan & Sarımsak Tarlası", "sogan", 350, "bi-layers", "Temel mutfak girdisi."),
    ("gul", "Gül Bahçesi", "gul", 1000, "bi-flower1", "Kozmetik fabrikası için gül yağı."),
    ("lavanta", "Lavanta Tarlası", "lavanta", 950, "bi-flower2", "Kozmetik ve ilaç sanayi."),
    ("mantar", "Mantar Kültür Tesisi", "mantar", 800, "bi-moisture", "Konserve sanayi girdisi."),
    ("nane", "Tıbbi Nane & Kekik Bahçesi", "nane", 400, "bi-flower3", "İlaç ve baharat sanayi."),
]

# ── ÇİFTLİK (10) ────────────────────────────────────────────────
_CIFTLIK = [
    ("buyukbas", "Büyükbaş Hayvan Çiftliği", None, 2500, "bi-emoji-smile",
     "Et, süt ve deri üretir. Deri tabakhaneye gider.",
     {"sut": 1, "et": 1, "deri": 1}),
    ("kucukbas", "Küçükbaş Çiftliği", None, 1800, "bi-emoji-wink",
     "Yün, süt ve et. Tekstil fabrikasına yün sağlar.",
     {"yun": 1, "sut": 1, "et": 1}),
    ("tavuk", "Tavuk & Yumurta Çiftliği", None, 1500, "bi-egg-fried",
     "Yumurta ve beyaz et. Gıda fabrikaları için.",
     {"yumurta": 2, "tavuk_et": 1}),
    ("aricilik", "Arıcılık Kompleksi", None, 1200, "bi-bug",
     "Bal ve balmumu. Kozmetik ve gıda için.",
     {"bal": 1, "balmumu": 1}),
    ("ipek", "İpekböceği Çiftliği", None, 3000, "bi-stars",
     "Ham ipek. Lüks tekstil fabrikası için.", {"ipek": 1}),
    ("mandira", "Süt Mandırası", None, 2200, "bi-cup-straw",
     "Sütten peynir üretir. Süt gerekir.", None, {"sut": 2}, {"peynir": 1}),
    ("at", "At Çiftliği", None, 5000, "bi-speedometer2",
     "Lüks binek ve lojistik. Yüksek değerli ticaret.", {"at": 1}),
    ("balik", "Balık Çiftliği", None, 2000, "bi-water",
     "Alabalık/somon. Konserve ve gıda pazarına.", {"balik": 2}),
    ("hindi", "Hindi/Ördek Çiftliği", None, 1600, "bi-feather",
     "Alternatif et ve tüy. Tekstil/yastık için.", {"hindi_et": 1, "tuy": 1}),
    ("devekus", "Devekuşu Çiftliği", None, 8000, "bi-gem",
     "Lüks et, yumurta ve deri. Geç aşama çiftliği.",
     {"deve_et": 1, "deve_yumurtasi": 1, "deri": 1}),
]

# ── HAMMADDE (8) ────────────────────────────────────────────────
_HAMMADDE = [
    ("ormancilik", "Ormancılık İşletmesi", "tomruk", 1500, "bi-tree-fill",
     "Tomruk üretir. Odun işleme fabrikasına gider."),
    ("demir_maden", "Demir Madeni Ocağı", "demir_cevheri", 3000, "bi-gem",
     "Demir cevheri. Çelik fabrikasının ana girdisi."),
    ("komur_maden", "Kömür Madeni", "komur", 3500, "bi-layers-half",
     "Enerji ve çelik fabrikaları için kömür."),
    ("bakir_maden", "Bakır Madeni", "bakir_cevheri", 4000, "bi-lightning",
     "Elektronik ve kablo fabrikası için."),
    ("boksit", "Boksit (Alüminyum) Ocağı", "boksit", 4500, "bi-box",
     "Hafif sanayi ve otomotiv ham maddesi."),
    ("mermer", "Mermer & Taş Ocağı", "mermer", 3200, "bi-bricks",
     "İnşaat ve çimento sektörü için."),
    ("kirec", "Kireç ve Alçı Taşı Ocağı", "kirec", 2800, "bi-building",
     "Kimya ve yapı malzemeleri fabrikası."),
    ("kuvars", "Kuvars & Kum Ocağı", "kuvars", 2500, "bi-hourglass",
     "Cam fabrikasının temel hammaddesi."),
]

# ── ENERJİ (5) ──────────────────────────────────────────────────
_ENERJI = [
    ("gunes", "Güneş Enerjisi Paneli", None, 2500, "bi-sun",
     "Temiz elektrik. Ham madde istemez.", None, {"elektrik": 8}),
    ("su", "Su Arıtma Tesisi", None, 1800, "bi-droplet",
     "Tarım ve fabrikalar için temiz su.", None, {"su": 6}),
    ("dogalgaz", "Doğalgaz Sondaj Ünitesi", None, 4000, "bi-fire",
     "Isıtma ve fabrika enerjisi.", None, {"dogalgaz": 5}),
    ("termik", "Termik Santral (Kömürlü)", None, 6000, "bi-cloud-haze2",
     "Kömür yakarak yüksek elektrik üretir.", {"komur": 2}, {"elektrik": 25}),
    ("ruzgar", "Rüzgar Türbini Tarlası", None, 5000, "bi-wind",
     "Temiz ve sabit elektrik kaynağı.", None, {"elektrik": 12}),
]


def _bahce_ogeleri():
    ogeler = {}
    for anahtar, ad, urun, fiyat, ikon, aciklama in _BAHCE:
        # Kapasite ve saatlik üretim değerleri
        kapasite = 3000
        saatlik_uretim = 300
        ogeler[anahtar] = _mulk(
            ad, fiyat, f"bahce_{anahtar}", ikon, aciklama, uretim={urun: 1},
            kapasite=kapasite, saatlik_uretim=saatlik_uretim
        )
    return ogeler


def _ciftlik_ogeleri():
    yem_destekli = {"buyukbas", "kucukbas", "tavuk", "hindi", "devekus"}
    ogeler = {}
    for item in _CIFTLIK:
        anahtar, ad, _, fiyat, ikon, aciklama = item[:6]
        uretim = item[6] if len(item) > 6 else None
        girdi = item[7] if len(item) > 7 else None
        uretim2 = item[8] if len(item) > 8 else None
        # Kapasite ve saatlik üretim değerleri
        kapasite = 2500
        saatlik_uretim = 250
        oge = _mulk(
            ad, fiyat, f"ciftlik_{anahtar}", ikon, aciklama,
            uretim=uretim2 or uretim, girdi_tuketim=girdi,
            kapasite=kapasite, saatlik_uretim=saatlik_uretim
        )
        if anahtar in yem_destekli:
            oge["yem_destek"] = {"yem": 1, "bonus": 0.5}
        ogeler[anahtar] = oge
    return ogeler


def _hammadde_ogeleri():
    ogeler = {}
    for anahtar, ad, urun, fiyat, ikon, aciklama in _HAMMADDE:
        # Kapasite ve saatlik üretim değerleri
        kapasite = 4000
        saatlik_uretim = 400
        ogeler[anahtar] = _mulk(
            ad, fiyat, f"hammadde_{anahtar}", ikon, aciklama, uretim={urun: 1},
            kapasite=kapasite, saatlik_uretim=saatlik_uretim
        )
    return ogeler


def _enerji_ogeleri():
    ogeler = {}
    for item in _ENERJI:
        anahtar, ad, _, fiyat, ikon, aciklama = item[:6]
        girdi = None
        enerji = None
        if len(item) > 7:
            girdi = item[6] if item[6] else None
            enerji = item[7]
        elif len(item) > 6 and item[6]:
            enerji = item[6]
        # Kapasite ve saatlik üretim değerleri
        kapasite = 6000
        saatlik_uretim = 600
        ogeler[anahtar] = _mulk(
            ad, fiyat, f"enerji_{anahtar}", ikon, aciklama,
            enerji_uretim=enerji, girdi_tuketim=girdi,
            kapasite=kapasite, saatlik_uretim=saatlik_uretim
        )
    return ogeler


KATEGORILER = {
    "bahce": {
        "ad": "Bahçe",
        "ikon": "bi-flower2",
        "aciklama": "30 bitkisel ham madde. Fabrikaların ve çiftliklerin tedarikçisi.",
        "ogeler": _bahce_ogeleri(),
    },
    "ciftlik": {
        "ad": "Çiftlikler",
        "ikon": "bi-house-heart",
        "aciklama": "Hayvansal ürünler. Bahçeden yem alır, fabrikalara et/süt/deri sağlar.",
        "ogeler": _ciftlik_ogeleri(),
    },
    "hammadde": {
        "ad": "Hammadde Kaynakları",
        "ikon": "bi-minecart-loaded",
        "aciklama": "Doğal kaynak çıkarımı. Ağır sanayi ve enerji için şart.",
        "ogeler": _hammadde_ogeleri(),
    },
    "enerji": {
        "ad": "Enerji Tesisleri",
        "ikon": "bi-lightning-charge",
        "aciklama": "Fabrikalar enerji olmadan çalışmaz. Elektrik, su ve doğalgaz üretir.",
        "ogeler": _enerji_ogeleri(),
    },
}


# ── FABRİKALAR (15) ─────────────────────────────────────────────
FABRIKA_TANIMLARI = {
    "un_fabrikasi": {
        "ad": "Un Fabrikası", "fiyat": 15000, "ikon": "bi-wind",
        "aciklama": "Buğday tarlasından buğday alır → un üretir.",
        "enerji_tuketim": {"elektrik": 5, "su": 2},
        "girdi": {"bugday": 3}, "cikti": {"un": 1},
        "kapasite": 5000, "saatlik_uretim": 500,
        "mesaj": "Un fabrikası kuruldu!",
    },
    "celik_fabrikasi": {
        "ad": "Çelik Fabrikası", "fiyat": 30000, "ikon": "bi-building",
        "aciklama": "Demir cevheri + kömür → çelik külçe. İnşaat için.",
        "enerji_tuketim": {"elektrik": 12, "dogalgaz": 6},
        "girdi": {"demir_cevheri": 2, "komur": 2}, "cikti": {"celik": 1},
        "kapasite": 5000, "saatlik_uretim": 500,
        "mesaj": "Çelik fabrikası kuruldu!",
    },
    "odun_isleme": {
        "ad": "Odun İşleme Fabrikası (Hızar)", "fiyat": 14000, "ikon": "bi-hammer",
        "aciklama": "Ormancılıktan tomruk → kereste + kağıt hamuru.",
        "enerji_tuketim": {"elektrik": 5, "su": 3},
        "girdi": {"tomruk": 2}, "cikti": {"kereste": 1, "kagit_hamuru": 1},
        "kapasite": 4000, "saatlik_uretim": 400,
        "mesaj": "Odun işleme fabrikası kuruldu!",
    },
    "tekstil": {
        "ad": "Tekstil & İplik Fabrikası", "fiyat": 18000, "ikon": "bi-scissors",
        "aciklama": "Pamuk + yün → kumaş. Mobilya fabrikasına gider.",
        "enerji_tuketim": {"elektrik": 6, "su": 4},
        "girdi": {"pamuk": 2, "yun": 1}, "cikti": {"kumas": 1},
        "kapasite": 4500, "saatlik_uretim": 450,
        "mesaj": "Tekstil fabrikası kuruldu!",
    },
    "seker_fabrikasi": {
        "ad": "Şeker Fabrikası", "fiyat": 16000, "ikon": "bi-cookie",
        "aciklama": "Şeker pancarı → şeker. Çikolata fabrikasına gider.",
        "enerji_tuketim": {"elektrik": 5, "su": 3},
        "girdi": {"seker_pancari": 3}, "cikti": {"seker": 1},
        "kapasite": 4800, "saatlik_uretim": 480,
        "mesaj": "Şeker fabrikası kuruldu!",
    },
    "yag_fabrikasi": {
        "ad": "Bitkisel Yağ Fabrikası", "fiyat": 17000, "ikon": "bi-droplet-fill",
        "aciklama": "Ayçiçeği + zeytin + mısır → sıvı yağ.",
        "enerji_tuketim": {"elektrik": 5, "su": 2},
        "girdi": {"aycicegi": 2, "zeytin": 1, "misir": 1}, "cikti": {"sivi_yag": 1},
        "kapasite": 4200, "saatlik_uretim": 420,
        "mesaj": "Yağ fabrikası kuruldu!",
    },
    "cikolata_fabrikasi": {
        "ad": "Çikolata & Şekerleme Fabrikası", "fiyat": 35000, "ikon": "bi-gift-fill",
        "aciklama": "Kakao+şeker+süt+fıstık+fındık → lüks çikolata. Çok kârlı!",
        "enerji_tuketim": {"elektrik": 10, "su": 4, "dogalgaz": 2},
        "girdi": {"kakao": 1, "seker": 1, "sut": 1, "antep_fistigi": 1},
        "cikti": {"cikolata": 1},
        "kapasite": 3000, "saatlik_uretim": 300,
        "mesaj": "Çikolata fabrikası kuruldu! En kârlı zincir.",
    },
    "cam_fabrikasi": {
        "ad": "Cam Fabrikası", "fiyat": 20000, "ikon": "bi-window",
        "aciklama": "Kuvars/kum → cam şişe. Konserve ve içecek için.",
        "enerji_tuketim": {"elektrik": 15, "dogalgaz": 5},
        "girdi": {"kuvars": 3}, "cikti": {"cam": 2},
        "kapasite": 5500, "saatlik_uretim": 550,
        "mesaj": "Cam fabrikası kuruldu!",
    },
    "konserve_fabrikasi": {
        "ad": "Konserve & Salça Fabrikası", "fiyat": 19000, "ikon": "bi-box-seam",
        "aciklama": "Domates+biber+cam şişe → konserve gıda.",
        "enerji_tuketim": {"elektrik": 6, "su": 5},
        "girdi": {"domates": 2, "biber": 1, "cam": 1}, "cikti": {"konserve": 1},
        "kapasite": 4600, "saatlik_uretim": 460,
        "mesaj": "Konserve fabrikası kuruldu!",
    },
    "meyve_suyu_fabrikasi": {
        "ad": "Meyve Suyu Fabrikası", "fiyat": 18000, "ikon": "bi-cup-straw",
        "aciklama": "Portakal+üzüm+elma → meyve suyu. Su enerjisi gerekir.",
        "enerji_tuketim": {"elektrik": 5, "su": 6},
        "girdi": {"portakal": 1, "uzum": 1, "elma": 1}, "cikti": {"meyve_suyu": 2},
        "kapasite": 4400, "saatlik_uretim": 440,
        "mesaj": "Meyve suyu fabrikası kuruldu!",
    },
    "deri_fabrikasi": {
        "ad": "Deri İşleme Fabrikası (Tabakhane)", "fiyat": 16000, "ikon": "bi-bag",
        "aciklama": "Büyükbaş çiftliğinden ham deri → işlenmiş deri.",
        "enerji_tuketim": {"elektrik": 4, "su": 5},
        "girdi": {"deri": 2}, "cikti": {"islenmis_deri": 1},
        "kapasite": 3800, "saatlik_uretim": 380,
        "mesaj": "Tabakhane kuruldu!",
    },
    "kagit_fabrikasi": {
        "ad": "Kağıt & Matbaa Fabrikası", "fiyat": 15000, "ikon": "bi-journal",
        "aciklama": "Kağıt hamuru → kitap ve ambalaj.",
        "enerji_tuketim": {"elektrik": 5, "su": 3},
        "girdi": {"kagit_hamuru": 2}, "cikti": {"kitap": 1},
        "kapasite": 4100, "saatlik_uretim": 410,
        "mesaj": "Kağıt fabrikası kuruldu!",
    },
    "elektronik_fabrikasi": {
        "ad": "Elektronik & Kablo Fabrikası", "fiyat": 28000, "ikon": "bi-cpu",
        "aciklama": "Bakır cevheri → elektronik parça.",
        "enerji_tuketim": {"elektrik": 12, "su": 2},
        "girdi": {"bakir_cevheri": 2}, "cikti": {"elektronik": 1},
        "kapasite": 3200, "saatlik_uretim": 320,
        "mesaj": "Elektronik fabrikası kuruldu!",
    },
    "yem_fabrikasi": {
        "ad": "Yem Fabrikası", "fiyat": 14000, "ikon": "bi-basket2",
        "aciklama": "Mısır+soya+buğday → yem. Çiftlik verimini artırır.",
        "enerji_tuketim": {"elektrik": 4, "su": 2},
        "girdi": {"misir": 2, "soya": 1, "bugday": 1}, "cikti": {"yem": 2},
        "kapasite": 4900, "saatlik_uretim": 490,
        "mesaj": "Yem fabrikası kuruldu!",
    },
    "mobilya_fabrikasi": {
        "ad": "Mobilya Fabrikası", "fiyat": 22000, "ikon": "bi-lamp",
        "aciklama": "Kereste + kumaş → mobilya. Yüksek kâr.",
        "enerji_tuketim": {"elektrik": 6, "su": 2},
        "girdi": {"kereste": 2, "kumas": 1}, "cikti": {"mobilya": 1},
        "kapasite": 3500, "saatlik_uretim": 350,
        "mesaj": "Mobilya fabrikası kuruldu!",
    },
}


ZINCIR_REHBERI = [
    {
        "ad": "Antep Fıstıklı Çikolata (En Lüks)",
        "adimlar": [
            "Güneş Paneli → elektrik",
            "Doğalgaz Sondaj → doğalgaz (çikolata fabrikası için)",
            "Buğday/Mısır/Soya → Yem Fabrikası → yem",
            "Yem + Büyükbaş Çiftliği → süt (%50 bonus)",
            "Antep Fıstığı + Kakao + Şeker Pancarı → Şeker Fabrikası",
            "Çikolata Fabrikası → çikolata (250 TL+)",
        ],
    },
    {
        "ad": "Çelik & İnşaat",
        "adimlar": [
            "Demir Madeni → demir cevheri",
            "Kömür Madeni → kömür",
            "Termik Santral → elektrik",
            "Çelik Fabrikası → çelik külçe",
        ],
    },
    {
        "ad": "Tekstil & Mobilya",
        "adimlar": [
            "Pamuk Tarlası + Küçükbaş → pamuk + yün",
            "Tekstil Fabrikası → kumaş",
            "Ormancılık → Odun İşleme → kereste",
            "Mobilya Fabrikası → mobilya (300 TL)",
        ],
    },
    {
        "ad": "Konserve Gıda",
        "adimlar": [
            "Domates + Biber serası",
            "Kuvars Ocağı → Cam Fabrikası → şişe",
            "Konserve Fabrikası → konserve",
        ],
    },
    {
        "ad": "Meyve Suyu",
        "adimlar": [
            "Portakal + Üzüm + Elma bahçeleri",
            "Su Arıtma Tesisi → su",
            "Meyve Suyu Fabrikası → içecek",
        ],
    },
]


def tum_mulk_alanlari():
    alanlar = []
    for kat in KATEGORILER.values():
        for oge in kat["ogeler"].values():
            alanlar.append(oge["alan"])
    return alanlar


def tum_urunler():
    return list(URUN_TANIMLARI.keys())


def mulk_tanimi_bul(alan):
    for kategori, kat in KATEGORILER.items():
        for anahtar, oge in kat["ogeler"].items():
            if oge["alan"] == alan:
                return kategori, anahtar, oge
    return None, None, None
