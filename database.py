import json
import os
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

import kategoriler as kat

# PostgreSQL bağlantısı (Render'da DATABASE_URL çevre değişkeni kullanılır)
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    from psycopg2 import sql
    import urllib.parse

    # Render PostgreSQL URL'sini parse et
    parsed = urllib.parse.urlparse(DATABASE_URL)
    DB_CONFIG = {
        "dbname": parsed.path[1:],
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port or 5432,
    }
    USE_POSTGRES = True
else:
    # Yerel geliştirme için JSON dosyası
    DOSYA_YOLU = os.path.join(os.path.dirname(__file__), "oyuncular.json")
    USE_POSTGRES = False

ADMIN_KULLANICI = "TicYapAdmin"
ADMIN_SIFRE = "admin2026"
ADMIN_BAKIYE = 9_999_999_999

GECERLI_URUNLER = tuple(kat.tum_urunler())
URUN_ADLARI = kat.URUN_ADLARI
REFERANS_FIYATLAR = kat.REFERANS_FIYATLAR

_LEGACY_MULK_MAP = {
    "bahce_tarla": "bahce_bugday",
    "hammadde_orman": "hammadde_ormancilik",
    "hammadde_maden": "hammadde_demir_maden",
}

CRAFT_TARIFLERI = {
    "un": {
        "ad": "Un",
        "girdi": {"bugday": 3},
        "cikti": {"un": 1},
        "bina": "degirmen_sayisi",
        "mesaj": "3 Buğday → 1 Un üretildi.",
    },
    "celik_kiris": {
        "ad": "Çelik Kiriş",
        "girdi": {"demir": 3},
        "cikti": {"celik_kiris": 1},
        "bina": "dokumhane_sayisi",
        "mesaj": "3 Demir → 1 Çelik Kiriş üretildi.",
    },
}


def _simdi():
    return datetime.now(timezone.utc)


def _varsayilan_mulkler():
    mulkler = {alan: 0 for alan in kat.tum_mulk_alanlari()}
    # Her tesis için seviye bilgisi ekle
    for alan in list(mulkler.keys()):
        mulkler[f"{alan}_seviye"] = 1
    return mulkler


def _varsayilan_enerji():
    return {
        "stok": {t: 0 for t in kat.ENERJI_TURLERI},
        "kapasite": dict(kat.VARSAYILAN_ENERJI_KAPASITE),
    }


def _varsayilan_oyuncu(kullanici_adi):
    return {
        "kullanici_adi": kullanici_adi,
        "bakiye": 1000,
        "ciftlik_sayisi": 0,
        "demir_ocagi_sayisi": 0,
        "degirmen_sayisi": 0,
        "dokumhane_sayisi": 0,
        "mulkler": _varsayilan_mulkler(),
        "araziler": [],
        "enerji": _varsayilan_enerji(),
        "urunler": {urun: 0 for urun in GECERLI_URUNLER},
        "bekleyen_urunler": {urun: 0 for urun in GECERLI_URUNLER},  # Toplanmayı bekleyen ürünler
        "son_uretim": _simdi().isoformat(),
        "sifre_hash": "",
        "is_admin": False,
        "seviye": 1,  # Genel oyuncu seviyesi
        "seviye_puani": 0,  # Seviye atlamak için gereken puan
        "klup": None,  # Üye olduğu klüp
        "fabrika_uretim_durumu": {},  # Fabrika üretim durumu (arazi_id -> {baslatildi: bool, baslama_zamani: str, bekleyen_miktar: int})
        "tesis_uretim_durumu": {},  # Tüm tesisler için üretim durumu (tesis_alani -> {baslatildi: bool, baslama_zamani: str, bekleyen_miktar: int})
    }


def _postgres_baglan():
    """PostgreSQL bağlantısı oluştur"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"PostgreSQL bağlantı hatası: {e}")
        return None


def _postgres_tablo_olustur():
    """PostgreSQL tablolarını oluştur"""
    conn = _postgres_baglan()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            # Oyuncular tablosu
            cur.execute("""
                CREATE TABLE IF NOT EXISTS oyuncular (
                    kullanici_adi VARCHAR(50) PRIMARY KEY,
                    bakiye INTEGER DEFAULT 1000,
                    ciftlik_sayisi INTEGER DEFAULT 0,
                    demir_ocagi_sayisi INTEGER DEFAULT 0,
                    degirmen_sayisi INTEGER DEFAULT 0,
                    dokumhane_sayisi INTEGER DEFAULT 0,
                    mulkler JSONB DEFAULT '{}',
                    araziler JSONB DEFAULT '[]',
                    enerji JSONB DEFAULT '{}',
                    urunler JSONB DEFAULT '{}',
                    bekleyen_urunler JSONB DEFAULT '{}',
                    son_uretim TIMESTAMP,
                    sifre_hash VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE,
                    seviye INTEGER DEFAULT 1,
                    seviye_puani INTEGER DEFAULT 0,
                    klup VARCHAR(50),
                    fabrika_uretim_durumu JSONB DEFAULT '{}',
                    tesis_uretim_durumu JSONB DEFAULT '{}'
                )
            """)
        return True
    except Exception as e:
        print(f"Tablo oluşturma hatası: {e}")
        return False
    finally:
        conn.close()


def _postgres_oyuncu_ekle(oyuncu):
    """PostgreSQL'e oyuncu ekle"""
    conn = _postgres_baglan()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO oyuncular (
                    kullanici_adi, bakiye, ciftlik_sayisi, demir_ocagi_sayisi, degirmen_sayisi,
                    dokumhane_sayisi, mulkler, araziler, enerji, urunler, bekleyen_urunler,
                    son_uretim, sifre_hash, is_admin, seviye, seviye_puani, klup,
                    fabrika_uretim_durumu, tesis_uretim_durumu
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (kullanici_adi) DO NOTHING
            """, (
                oyuncu["kullanici_adi"],
                oyuncu["bakiye"],
                oyuncu["ciftlik_sayisi"],
                oyuncu["demir_ocagi_sayisi"],
                oyuncu["degirmen_sayisi"],
                oyuncu["dokumhane_sayisi"],
                json.dumps(oyuncu["mulkler"]),
                json.dumps(oyuncu["araziler"]),
                json.dumps(oyuncu["enerji"]),
                json.dumps(oyuncu["urunler"]),
                json.dumps(oyuncu["bekleyen_urunler"]),
                oyuncu["son_uretim"],
                oyuncu["sifre_hash"],
                oyuncu["is_admin"],
                oyuncu["seviye"],
                oyuncu["seviye_puani"],
                oyuncu["klup"],
                json.dumps(oyuncu["fabrika_uretim_durumu"]),
                json.dumps(oyuncu["tesis_uretim_durumu"]),
            ))
        return True
    except Exception as e:
        print(f"Oyuncu ekleme hatası: {e}")
        return False
    finally:
        conn.close()


def _postgres_oyuncu_guncelle(oyuncu):
    """PostgreSQL'de oyuncu güncelle"""
    conn = _postgres_baglan()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE oyuncular SET
                    bakiye = %s,
                    ciftlik_sayisi = %s,
                    demir_ocagi_sayisi = %s,
                    degirmen_sayisi = %s,
                    dokumhane_sayisi = %s,
                    mulkler = %s,
                    araziler = %s,
                    enerji = %s,
                    urunler = %s,
                    bekleyen_urunler = %s,
                    son_uretim = %s,
                    sifre_hash = %s,
                    is_admin = %s,
                    seviye = %s,
                    seviye_puani = %s,
                    klup = %s,
                    fabrika_uretim_durumu = %s,
                    tesis_uretim_durumu = %s
                WHERE kullanici_adi = %s
            """, (
                oyuncu["bakiye"],
                oyuncu["ciftlik_sayisi"],
                oyuncu["demir_ocagi_sayisi"],
                oyuncu["degirmen_sayisi"],
                oyuncu["dokumhane_sayisi"],
                json.dumps(oyuncu["mulkler"]),
                json.dumps(oyuncu["araziler"]),
                json.dumps(oyuncu["enerji"]),
                json.dumps(oyuncu["urunler"]),
                json.dumps(oyuncu["bekleyen_urunler"]),
                oyuncu["son_uretim"],
                oyuncu["sifre_hash"],
                oyuncu["is_admin"],
                oyuncu["seviye"],
                oyuncu["seviye_puani"],
                oyuncu["klup"],
                json.dumps(oyuncu["fabrika_uretim_durumu"]),
                json.dumps(oyuncu["tesis_uretim_durumu"]),
                oyuncu["kullanici_adi"],
            ))
        return True
    except Exception as e:
        print(f"Oyuncu güncelleme hatası: {e}")
        return False
    finally:
        conn.close()


def _postgres_tum_oyuncular():
    """PostgreSQL'den tüm oyuncuları getir"""
    conn = _postgres_baglan()
    if not conn:
        return {}

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM oyuncular")
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            oyuncular = {}
            for row in rows:
                oyuncu = dict(zip(columns, row))
                # JSON alanlarını decode et
                for field in ["mulkler", "araziler", "enerji", "urunler", "bekleyen_urunler", "fabrika_uretim_durumu", "tesis_uretim_durumu"]:
                    if oyuncu[field]:
                        oyuncu[field] = json.loads(oyuncu[field])
                oyuncular[oyuncu["kullanici_adi"]] = oyuncu
            return oyuncular
    except Exception as e:
        print(f"Oyuncular getirme hatası: {e}")
        return {}
    finally:
        conn.close()


def admin_mi(oyuncu):
    if not oyuncu:
        return False
    return oyuncu.get("is_admin") or oyuncu.get("kullanici_adi") == ADMIN_KULLANICI


def admin_bakiye_uygula(oyuncu):
    if admin_mi(oyuncu):
        oyuncu["is_admin"] = True
        oyuncu["bakiye"] = ADMIN_BAKIYE
    return oyuncu


def _legacy_mulk_aktar(oyuncu):
    mulkler = oyuncu.setdefault("mulkler", _varsayilan_mulkler())
    for alan in kat.tum_mulk_alanlari():
        mulkler.setdefault(alan, 0)

    if oyuncu.get("ciftlik_sayisi", 0) > 0:
        mulkler["bahce_bugday"] = max(
            mulkler.get("bahce_bugday", 0), oyuncu["ciftlik_sayisi"]
        )
    if oyuncu.get("demir_ocagi_sayisi", 0) > 0:
        mulkler["hammadde_demir_maden"] = max(
            mulkler.get("hammadde_demir_maden", 0), oyuncu["demir_ocagi_sayisi"]
        )

    for eski, yeni in _LEGACY_MULK_MAP.items():
        if eski in mulkler and eski != yeni:
            mulkler[yeni] = max(mulkler.get(yeni, 0), mulkler.pop(eski, 0))

    oyuncu.setdefault("araziler", [])
    oyuncu.setdefault("enerji", _varsayilan_enerji())
    enerji = oyuncu["enerji"]
    enerji.setdefault("stok", {t: 0 for t in kat.ENERJI_TURLERI})
    enerji.setdefault("kapasite", dict(kat.VARSAYILAN_ENERJI_KAPASITE))
    return oyuncu


def _oyuncu_normalize(oyuncu):
    urunler = oyuncu.setdefault("urunler", {})
    for urun in GECERLI_URUNLER:
        urunler.setdefault(urun, 0)

    # Bekleyen ürünleri normalize et
    bekleyen_urunler = oyuncu.setdefault("bekleyen_urunler", {})
    for urun in GECERLI_URUNLER:
        bekleyen_urunler.setdefault(urun, 0)

    if "demir_ocagi_sayisi" not in oyuncu:
        oyuncu["demir_ocagi_sayisi"] = oyuncu.pop("fabrika_sayisi", 0)

    oyuncu.setdefault("degirmen_sayisi", 0)
    oyuncu.setdefault("dokumhane_sayisi", 0)
    oyuncu.setdefault("ciftlik_sayisi", 0)
    oyuncu.setdefault("son_uretim", _simdi().isoformat())
    oyuncu.setdefault("sifre_hash", "")
    oyuncu.setdefault("is_admin", False)
    oyuncu.setdefault("seviye", 1)
    oyuncu.setdefault("seviye_puani", 0)
    oyuncu.setdefault("fabrika_uretim_durumu", {})
    oyuncu.setdefault("tesis_uretim_durumu", {})
    _legacy_mulk_aktar(oyuncu)

    # Tesis seviyelerini normalize et
    mulkler = oyuncu.setdefault("mulkler", _varsayilan_mulkler())
    for alan in kat.tum_mulk_alanlari():
        mulkler.setdefault(f"{alan}_seviye", 1)

    # Fabrika üretim durumunu normalize et
    for arazi in oyuncu.get("araziler", []):
        arazi_id = arazi.get("id")
        if arazi_id and arazi.get("fabrika"):
            durum = oyuncu["fabrika_uretim_durumu"].setdefault(str(arazi_id), {
                "baslatildi": False,
                "baslama_zamani": None,
                "bekleyen_miktar": 0
            })

    # Tüm tesisler için üretim durumunu normalize et
    for kategori in kat.KATEGORILER.values():
        for anahtar, oge in kategori["ogeler"].items():
            tesis_alani = oge["alan"]
            if oyuncu["mulkler"].get(tesis_alani, 0) > 0:
                durum = oyuncu["tesis_uretim_durumu"].setdefault(tesis_alani, {
                    "baslatildi": False,
                    "baslama_zamani": None,
                    "bekleyen_miktar": 0
                })

    return admin_bakiye_uygula(oyuncu)


def _veri_normalize(veriler):
    veriler.setdefault("oyuncular", {})
    veriler.setdefault("pazar", [])
    veriler.setdefault("klupler", [])
    veriler.setdefault("chat_mesajlari", [])
    for ad in veriler["oyuncular"]:
        _oyuncu_normalize(veriler["oyuncular"][ad])
    return veriler


def verileri_yukle():
    if USE_POSTGRES:
        # PostgreSQL kullan
        _postgres_tablo_olustur()
        oyuncular = _postgres_tum_oyuncular()
        return {"oyuncular": oyuncular, "pazar": [], "klupler": [], "chat_mesajlari": []}
    else:
        # JSON dosyası kullan
        if not os.path.exists(DOSYA_YOLU):
            bos = {"oyuncular": {}, "pazar": []}
            verileri_kaydet(bos)
            return bos

        with open(DOSYA_YOLU, "r", encoding="utf-8") as dosya:
            return _veri_normalize(json.load(dosya))


def verileri_kaydet(veriler):
    if USE_POSTGRES:
        # PostgreSQL kullan - sadece oyuncuları güncelle
        for kullanici_adi, oyuncu in veriler["oyuncular"].items():
            # Önce oyuncu var mı kontrol et
            conn = _postgres_baglan()
            if conn:
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT kullanici_adi FROM oyuncular WHERE kullanici_adi = %s", (kullanici_adi,))
                        if cur.fetchone():
                            # Var - güncelle
                            _postgres_oyuncu_guncelle(oyuncu)
                        else:
                            # Yok - ekle
                            _postgres_oyuncu_ekle(oyuncu)
                finally:
                    conn.close()
    else:
        # JSON dosyası kullan
        with open(DOSYA_YOLU, "w", encoding="utf-8") as dosya:
            json.dump(veriler, dosya, ensure_ascii=False, indent=2)


def oyuncu_getir(kullanici_adi):
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is not None:
        return _oyuncu_normalize(oyuncu)
    return None


def oyuncu_kaydet(oyuncu):
    veriler = verileri_yukle()
    veriler["oyuncular"][oyuncu["kullanici_adi"]] = oyuncu
    verileri_kaydet(veriler)


def oyuncu_olustur(kullanici_adi, sifre):
    oyuncu = _varsayilan_oyuncu(kullanici_adi)
    oyuncu["sifre_hash"] = generate_password_hash(sifre)
    oyuncu_kaydet(oyuncu)
    return oyuncu


def kayit_ol(kullanici_adi, sifre):
    if kullanici_adi == ADMIN_KULLANICI:
        return False, "Bu kullanıcı adı rezerve edilmiş."

    if oyuncu_var_mi(kullanici_adi):
        return False, "Bu kullanıcı adı zaten alınmış."

    if len(sifre) < 4:
        return False, "Şifre en az 4 karakter olmalı."

    oyuncu_olustur(kullanici_adi, sifre)
    return True, f"Hesabın oluşturuldu! {oyuncu_getir(kullanici_adi)['bakiye']} TL ile başladın."


def giris_yap(kullanici_adi, sifre):
    oyuncu = oyuncu_getir(kullanici_adi)
    if oyuncu is None:
        return False, "Kullanıcı bulunamadı. Önce kayıt ol."

    if not sifre:
        return False, "Şifre gerekli."

    if not oyuncu.get("sifre_hash"):
        if len(sifre) < 4:
            return False, "Eski hesap için en az 4 karakterli bir şifre belirle."
        oyuncu["sifre_hash"] = generate_password_hash(sifre)
        oyuncu_kaydet(oyuncu)
        return True, f"Şifren kaydedildi. Hoş geldin, {kullanici_adi}!"

    if not check_password_hash(oyuncu["sifre_hash"], sifre):
        return False, "Hatalı şifre."

    return True, f"Tekrar hoş geldin, {kullanici_adi}!"


def admin_hesabi_hazirla():
    if oyuncu_var_mi(ADMIN_KULLANICI):
        oyuncu = oyuncu_getir(ADMIN_KULLANICI)
    else:
        oyuncu = _varsayilan_oyuncu(ADMIN_KULLANICI)

    oyuncu["is_admin"] = True
    oyuncu["bakiye"] = ADMIN_BAKIYE
    oyuncu["sifre_hash"] = generate_password_hash(ADMIN_SIFRE)
    oyuncu_kaydet(oyuncu)
    return oyuncu


def oyuncu_var_mi(kullanici_adi):
    return oyuncu_getir(kullanici_adi) is not None


def _enerji_ekle(oyuncu, tur, miktar):
    stok = oyuncu["enerji"]["stok"]
    kapasite = oyuncu["enerji"]["kapasite"]
    stok[tur] = min(kapasite[tur], stok[tur] + miktar)


def _enerji_yeterli(oyuncu, ihtiyac):
    stok = oyuncu["enerji"]["stok"]
    return all(stok.get(t, 0) >= m for t, m in ihtiyac.items())


def _enerji_tuket(oyuncu, ihtiyac):
    for tur, miktar in ihtiyac.items():
        oyuncu["enerji"]["stok"][tur] -= miktar


def _girdi_yeterli(oyuncu, girdi):
    return all(oyuncu["urunler"].get(u, 0) >= m for u, m in girdi.items())


def _girdi_tuket(oyuncu, girdi):
    for urun, miktar in girdi.items():
        oyuncu["urunler"][urun] -= miktar


def _cikti_ekle(oyuncu, cikti):
    for urun, miktar in cikti.items():
        oyuncu["urunler"][urun] += miktar


def _pasif_mulk_uretim(oyuncu, dakika):
    uretim_yapildi = False
    for kategori in kat.KATEGORILER.values():
        for oge in kategori["ogeler"].values():
            adet = oyuncu["mulkler"].get(oge["alan"], 0)
            if adet <= 0:
                continue

            # Üretim durumu kontrolü
            durum = oyuncu["tesis_uretim_durumu"].get(oge["alan"], {})
            if not durum.get("baslatildi", False):
                continue

            # Kapasite kontrolü
            kapasite = oge.get("kapasite", 0)
            bekleyen = durum.get("bekleyen_miktar", 0)
            if bekleyen >= kapasite:
                continue  # Kapasite dolu, üretim durduruldu

            # Seviye çarpanını hesapla
            seviye = oyuncu["mulkler"].get(f"{oge['alan']}_seviye", 1)
            uretim_carpani = kat.SEVIYE_SISTEMI["uretim_carpani"]
            seviye_bonusu = 1 + (seviye - 1) * uretim_carpani

            for _ in range(dakika):
                girdi_ihtiyac = oge.get("girdi_tuketim")
                if girdi_ihtiyac:
                    olcekli = {u: int(m * adet * seviye_bonusu) for u, m in girdi_ihtiyac.items()}
                    if not _girdi_yeterli(oyuncu, olcekli):
                        continue
                    _girdi_tuket(oyuncu, olcekli)

                carpan = 1.0
                yem_destek = oge.get("yem_destek")
                if yem_destek:
                    urun = "yem"
                    miktar = yem_destek.get("yem", 1)
                    ihtiyac = {urun: int(miktar * adet * seviye_bonusu)}
                    if _girdi_yeterli(oyuncu, ihtiyac):
                        _girdi_tuket(oyuncu, ihtiyac)
                        carpan = 1 + yem_destek.get("bonus", 0.5)

                for urun, miktar in oge.get("uretim", {}).items():
                    temel = int(adet * miktar * seviye_bonusu)
                    if carpan > 1:
                        temel += int(temel * (carpan - 1))
                    # Ürünleri bekleyen ürünlere ekle (doğrudan envantere değil)
                    oyuncu["bekleyen_urunler"][urun] += temel
                    durum["bekleyen_miktar"] = durum.get("bekleyen_miktar", 0) + temel
                for tur, miktar in oge.get("enerji_uretim", {}).items():
                    _enerji_ekle(oyuncu, tur, int(adet * miktar * seviye_bonusu))

                uretim_yapildi = True

                # Kapasite kontrolü
                if durum.get("bekleyen_miktar", 0) >= kapasite:
                    break

            oyuncu["tesis_uretim_durumu"][oge["alan"]] = durum

    oyuncu["urunler"]["bugday"] += oyuncu.get("ciftlik_sayisi", 0) * dakika
    oyuncu["urunler"]["demir"] += oyuncu.get("demir_ocagi_sayisi", 0) * dakika

    # Üretim yapıldıysa XP kazan
    if uretim_yapildi:
        xp_kazan(oyuncu, "uretim_yap")


def _fabrika_uretim(oyuncu, dakika):
    for arazi in oyuncu.get("araziler", []):
        arazi_id = str(arazi.get("id"))
        tip = arazi.get("fabrika")
        if not tip or tip not in kat.FABRIKA_TANIMLARI:
            continue

        fab = kat.FABRIKA_TANIMLARI[tip]
        durum = oyuncu["fabrika_uretim_durumu"].get(arazi_id, {})

        # Üretim başlatılmadıysa atla
        if not durum.get("baslatildi", False):
            continue

        # Kapasite kontrolü
        saatlik_uretim = fab.get("saatlik_uretim", 0)
        kapasite = fab.get("kapasite", 0)
        bekleyen = durum.get("bekleyen_miktar", 0)

        if bekleyen >= kapasite:
            continue  # Kapasite dolu, üretim durduruldu

        for _ in range(dakika):
            if not _enerji_yeterli(oyuncu, fab["enerji_tuketim"]):
                continue
            if not _girdi_yeterli(oyuncu, fab["girdi"]):
                continue

            _enerji_tuket(oyuncu, fab["enerji_tuketim"])
            _girdi_tuket(oyuncu, fab["girdi"])

            # Ürünleri bekleyen ürünlere ekle (doğrudan envantere değil)
            for urun, miktar in fab["cikti"].items():
                oyuncu["bekleyen_urunler"][urun] += miktar
                durum["bekleyen_miktar"] = durum.get("bekleyen_miktar", 0) + miktar

            # Kapasite kontrolü
            if durum.get("bekleyen_miktar", 0) >= kapasite:
                break

        oyuncu["fabrika_uretim_durumu"][arazi_id] = durum


def uretim_hesapla(oyuncu, dakikada_uretim=1):
    oyuncu = _oyuncu_normalize(oyuncu)

    son = datetime.fromisoformat(oyuncu["son_uretim"])
    if son.tzinfo is None:
        son = son.replace(tzinfo=timezone.utc)

    gecen_saniye = (_simdi() - son).total_seconds()
    gecen_dakika = int(gecen_saniye // 60)

    if gecen_dakika > 0:
        _pasif_mulk_uretim(oyuncu, gecen_dakika * dakikada_uretim)
        _fabrika_uretim(oyuncu, gecen_dakika * dakikada_uretim)
        yeni_zaman = son.timestamp() + (gecen_dakika * 60)
        oyuncu["son_uretim"] = datetime.fromtimestamp(
            yeni_zaman, tz=timezone.utc
        ).isoformat()

    return oyuncu


def ekonomik_durum_hesapla(oyuncu):
    oyuncu = _oyuncu_normalize(oyuncu)
    dakika_degeri = 0

    for kategori in kat.KATEGORILER.values():
        for oge in kategori["ogeler"].values():
            adet = oyuncu["mulkler"].get(oge["alan"], 0)
            for urun, miktar in oge.get("uretim", {}).items():
                dakika_degeri += adet * miktar * REFERANS_FIYATLAR.get(urun, 0)

    dakika_degeri += oyuncu.get("ciftlik_sayisi", 0) * REFERANS_FIYATLAR["bugday"]
    dakika_degeri += oyuncu.get("demir_ocagi_sayisi", 0) * REFERANS_FIYATLAR["demir"]

    fabrika_sayisi = sum(1 for a in oyuncu.get("araziler", []) if a.get("fabrika"))
    enerji_tesisi = sum(
        oyuncu["mulkler"].get(oge["alan"], 0)
        for oge in kat.KATEGORILER["enerji"]["ogeler"].values()
    )

    return {
        "dakika_degeri": dakika_degeri,
        "fabrika_sayisi": fabrika_sayisi,
        "bos_arazi": sum(1 for a in oyuncu.get("araziler", []) if not a.get("fabrika")),
        "aciklama": (
            f"Dakikada ~{dakika_degeri} TL ham madde üretimi. "
            f"{fabrika_sayisi} fabrika, {enerji_tesisi} enerji tesisi aktif. "
            f"Fabrikalar elektrik/su/doğalgaz olmadan çalışmaz."
        ),
    }


def craft_yap(kullanici_adi, tarif_anahtari):
    if tarif_anahtari not in CRAFT_TARIFLERI:
        return False, "Geçersiz üretim tarifi.", None

    tarif = CRAFT_TARIFLERI[tarif_anahtari]
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))

    if oyuncu[tarif["bina"]] <= 0:
        bina_adi = "Un Değirmeni" if tarif["bina"] == "degirmen_sayisi" else "Demir Dökümhane"
        return False, f"Önce bir {bina_adi} satın almalısın.", None

    for urun, miktar in tarif["girdi"].items():
        if oyuncu["urunler"][urun] < miktar:
            return False, f"Yeterli {URUN_ADLARI[urun]} yok.", None

    for urun, miktar in tarif["girdi"].items():
        oyuncu["urunler"][urun] -= miktar
    for urun, miktar in tarif["cikti"].items():
        oyuncu["urunler"][urun] += miktar

    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)
    return True, tarif["mesaj"], oyuncu


def _yeni_arazi_id(oyuncu):
    if not oyuncu.get("araziler"):
        return 1
    return max(a["id"] for a in oyuncu["araziler"]) + 1


def mulk_satin_al(kullanici_adi, kategori, oge_anahtari):
    kat_data = kat.KATEGORILER.get(kategori)
    if not kat_data:
        return False, "Geçersiz kategori.", None

    oge = kat_data["ogeler"].get(oge_anahtari)
    if not oge:
        return False, "Geçersiz yatırım.", None

    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))

    # Aynı tesis türünden birden fazla almayı engelle
    mevcut_adet = oyuncu["mulkler"].get(oge["alan"], 0)
    if mevcut_adet >= 1:
        return False, f"Bu tesis türünden zaten sahipsin. Her tesis türünden sadece bir tane alabilirsin.", None

    # Seviye kontrolü
    gerekli_seviye = kat.SEVIYE_GEREKSINIMLERI.get(oge["alan"], 1)
    if oyuncu["seviye"] < gerekli_seviye:
        return False, f"Bu tesis için Seviye {gerekli_seviye} gerekiyor. Şu anki seviyen: {oyuncu['seviye']}", None

    if not admin_mi(oyuncu) and oyuncu["bakiye"] < oge["fiyat"]:
        return False, f"Yetersiz bakiye! {oge['ad']} için {oge['fiyat']} TL gerekli.", None

    if not admin_mi(oyuncu):
        oyuncu["bakiye"] -= oge["fiyat"]
    oyuncu["mulkler"][oge["alan"]] = 1  # Sadece 1 tane olabilir

    # XP kazan
    xp_kazan(oyuncu, "tesis_satin_al")

    oyuncu = admin_bakiye_uygula(oyuncu)
    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)
    return True, oge["mesaj"], oyuncu


def arazi_satin_al(kullanici_adi):
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))
    fiyat = kat.ARAZI_FIYATI

    if not admin_mi(oyuncu) and oyuncu["bakiye"] < fiyat:
        return False, f"Yetersiz bakiye! Arazi için {fiyat} TL gerekli.", None

    if not admin_mi(oyuncu):
        oyuncu["bakiye"] -= fiyat
    yeni_id = _yeni_arazi_id(oyuncu)
    oyuncu["araziler"].append(
        {"id": yeni_id, "fabrika": None, "ad": f"Arazi #{yeni_id}"}
    )
    oyuncu = admin_bakiye_uygula(oyuncu)
    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)
    return True, "Üretim arazisi satın alındı! Üzerine fabrika kurabilirsin.", oyuncu


def fabrika_kur(kullanici_adi, arazi_id, fabrika_tipi):
    fab = kat.FABRIKA_TANIMLARI.get(fabrika_tipi)
    if not fab:
        return False, "Geçersiz fabrika türü.", None

    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))
    arazi = next((a for a in oyuncu["araziler"] if a["id"] == arazi_id), None)
    if arazi is None:
        return False, "Arazi bulunamadı.", None
    if arazi.get("fabrika"):
        return False, "Bu arazide zaten fabrika var.", None

    if not admin_mi(oyuncu) and oyuncu["bakiye"] < fab["fiyat"]:
        return False, f"Yetersiz bakiye! {fab['ad']} için {fab['fiyat']} TL gerekli.", None

    if not admin_mi(oyuncu):
        oyuncu["bakiye"] -= fab["fiyat"]
    arazi["fabrika"] = fabrika_tipi

    # XP kazan
    xp_kazan(oyuncu, "fabrika_kur")

    # Fabrika üretim durumunu başlat
    arazi_id_str = str(arazi_id)
    oyuncu["fabrika_uretim_durumu"][arazi_id_str] = {
        "baslatildi": False,
        "baslama_zamani": None,
        "bekleyen_miktar": 0
    }

    oyuncu = admin_bakiye_uygula(oyuncu)
    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)
    return True, fab["mesaj"], oyuncu


def oyuncu_ozet(oyuncu):
    oyuncu = _oyuncu_normalize(oyuncu)
    ekonomi = ekonomik_durum_hesapla(oyuncu)
    yonetici = admin_mi(oyuncu)
    return {
        "kullanici_adi": oyuncu["kullanici_adi"],
        "bakiye": oyuncu["bakiye"],
        "bakiye_etiket": "Sınırsız" if yonetici else str(oyuncu["bakiye"]),
        "is_admin": yonetici,
        "ciftlik_sayisi": oyuncu.get("ciftlik_sayisi", 0),
        "demir_ocagi_sayisi": oyuncu.get("demir_ocagi_sayisi", 0),
        "degirmen_sayisi": oyuncu.get("degirmen_sayisi", 0),
        "dokumhane_sayisi": oyuncu.get("dokumhane_sayisi", 0),
        "mulkler": oyuncu["mulkler"],
        "araziler": oyuncu["araziler"],
        "enerji": oyuncu["enerji"],
        "bugday": oyuncu["urunler"]["bugday"],
        "demir": oyuncu["urunler"]["demir"],
        "un": oyuncu["urunler"]["un"],
        "celik_kiris": oyuncu["urunler"]["celik_kiris"],
        "odun": oyuncu["urunler"]["odun"],
        "demir_cevheri": oyuncu["urunler"]["demir_cevheri"],
        "sut": oyuncu["urunler"]["sut"],
        "yun": oyuncu["urunler"]["yun"],
        "bal": oyuncu["urunler"]["bal"],
        "tahta": oyuncu["urunler"]["tahta"],
        "urunler": oyuncu["urunler"],
        "bekleyen_urunler": oyuncu["bekleyen_urunler"],
        "fabrika_uretim_durumu": oyuncu["fabrika_uretim_durumu"],
        "seviye": oyuncu["seviye"],
        "seviye_puani": oyuncu["seviye_puani"],
        "dakika_degeri": ekonomi["dakika_degeri"],
        "fabrika_sayisi": ekonomi["fabrika_sayisi"],
        "bos_arazi": ekonomi["bos_arazi"],
        "ekonomi_aciklama": ekonomi["aciklama"],
    }


def pazar_ilanlari_getir():
    return verileri_yukle()["pazar"]


def _yeni_ilan_id(veriler):
    pazar = veriler["pazar"]
    if not pazar:
        return 1
    return max(ilan["id"] for ilan in pazar) + 1


def pazar_ilan_ver(satici_adi, urun, miktar, birim_fiyat):
    if urun not in GECERLI_URUNLER:
        return False, "Geçersiz ürün türü."

    if miktar <= 0 or birim_fiyat <= 0:
        return False, "Miktar ve fiyat 0'dan büyük olmalı."

    veriler = verileri_yukle()
    satici = veriler["oyuncular"].get(satici_adi)
    if satici is None:
        return False, "Oyuncu bulunamadı."

    satici = uretim_hesapla(_oyuncu_normalize(satici))
    if satici["urunler"][urun] < miktar:
        return False, f"Yeterli {URUN_ADLARI[urun]} yok."

    satici["urunler"][urun] -= miktar
    veriler["oyuncular"][satici_adi] = satici
    veriler["pazar"].append(
        {
            "id": _yeni_ilan_id(veriler),
            "satici": satici_adi,
            "urun": urun,
            "miktar": miktar,
            "birim_fiyat": birim_fiyat,
            "tarih": _simdi().isoformat(),
        }
    )
    verileri_kaydet(veriler)
    return True, "İlan pazara eklendi."


def pazar_satin_al(alici_adi, ilan_id):
    veriler = verileri_yukle()
    ilan = next((i for i in veriler["pazar"] if i["id"] == ilan_id), None)
    if ilan is None:
        return False, "İlan bulunamadı veya satılmış."

    if ilan["satici"] == alici_adi:
        return False, "Kendi ilanını satın alamazsın."

    alici = veriler["oyuncular"].get(alici_adi)
    satici = veriler["oyuncular"].get(ilan["satici"])
    if alici is None or satici is None:
        return False, "Oyuncu bulunamadı."

    alici = uretim_hesapla(_oyuncu_normalize(alici))
    satici = uretim_hesapla(_oyuncu_normalize(satici))

    toplam_fiyat = ilan["miktar"] * ilan["birim_fiyat"]
    if not admin_mi(alici) and alici["bakiye"] < toplam_fiyat:
        return False, f"Yetersiz bakiye! {toplam_fiyat} TL gerekli."

    if not admin_mi(alici):
        alici["bakiye"] -= toplam_fiyat
    else:
        alici = admin_bakiye_uygula(alici)
    satici["bakiye"] += toplam_fiyat
    alici["urunler"][ilan["urun"]] += ilan["miktar"]

    # XP kazan
    xp_kazan(alici, "pazar_satin_al")
    xp_kazan(satici, "pazar_satis")

    veriler["oyuncular"][alici_adi] = alici
    veriler["oyuncular"][ilan["satici"]] = satici
    veriler["pazar"] = [i for i in veriler["pazar"] if i["id"] != ilan_id]
    verileri_kaydet(veriler)

    urun_adi = URUN_ADLARI[ilan["urun"]]
    return True, f"{ilan['miktar']} {urun_adi} satın alındı ({toplam_fiyat} TL)."


def tesis_seviye_atla(kullanici_adi, tesis_alani):
    """Belirli bir tesisin seviyesini artırır"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))
    
    mevcut_seviye = oyuncu["mulkler"].get(f"{tesis_alani}_seviye", 1)
    maks_seviye = kat.SEVIYE_SISTEMI["maks_seviye"]
    
    if mevcut_seviye >= maks_seviye:
        return False, f"Bu tesis zaten maksimum seviyede ({maks_seviye}).", None
    
    if oyuncu["mulkler"].get(tesis_alani, 0) == 0:
        return False, "Bu tesisi satın almadan seviye atlayamazsın.", None
    
    # Seviye atlama maliyeti hesapla
    kategori, anahtar, oge = kat.mulk_tanimi_bul(tesis_alani)
    if not oge:
        return False, "Geçersiz tesis.", None
    
    taban_fiyat = oge["fiyat"]
    maliyet_carpani = kat.SEVIYE_SISTEMI["maliyet_carpani"]
    yukseltme_maliyeti = int(taban_fiyat * (maliyet_carpani ** mevcut_seviye))
    
    if not admin_mi(oyuncu) and oyuncu["bakiye"] < yukseltme_maliyeti:
        return False, f"Yetersiz bakiye! Seviye atlama için {yukseltme_maliyeti} TL gerekli.", None
    
    if not admin_mi(oyuncu):
        oyuncu["bakiye"] -= yukseltme_maliyeti
    
    oyuncu["mulkler"][f"{tesis_alani}_seviye"] = mevcut_seviye + 1
    
    # XP kazan
    xp_kazan(oyuncu, "tesis_yukselt")
    
    oyuncu = admin_bakiye_uygula(oyuncu)
    
    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)
    
    return True, f"{oge['ad']} seviye {mevcut_seviye + 1}'e yükseltildi!", oyuncu


def xp_kazan(oyuncu, kaynak):
    """Oyuncuya XP kazandırır ve seviye atlamasını kontrol eder"""
    if admin_mi(oyuncu):
        return
    
    xp_miktari = kat.XP_KAYNAKLARI.get(kaynak, 0)
    if xp_miktari == 0:
        return
    
    oyuncu["seviye_puani"] += xp_miktari
    
    # Seviye atlama kontrolü
    gerekli_xp = oyuncu["seviye"] * kat.SEVIYE_SISTEMI["xp_per_seviye"]
    maks_seviye = kat.SEVIYE_SISTEMI["maks_seviye"]
    
    while oyuncu["seviye_puani"] >= gerekli_xp and oyuncu["seviye"] < maks_seviye:
        oyuncu["seviye_puani"] -= gerekli_xp
        oyuncu["seviye"] += 1
        gerekli_xp = oyuncu["seviye"] * kat.SEVIYE_SISTEMI["xp_per_seviye"]


def tesis_uretim_detaylari(oyuncu, tesis_alani):
    """Bir tesisin üretim detaylarını hesaplar"""
    oyuncu = _oyuncu_normalize(oyuncu)
    
    kategori, anahtar, oge = kat.mulk_tanimi_bul(tesis_alani)
    if not oge:
        return None
    
    adet = oyuncu["mulkler"].get(tesis_alani, 0)
    if adet == 0:
        return None
    
    seviye = oyuncu["mulkler"].get(f"{tesis_alani}_seviye", 1)
    uretim_carpani = kat.SEVIYE_SISTEMI["uretim_carpani"]
    seviye_bonusu = 1 + (seviye - 1) * uretim_carpani
    
    detaylar = {
        "ad": oge["ad"],
        "adet": adet,
        "seviye": seviye,
        "seviye_bonusu": seviye_bonusu,
        "uretim": {},
        "girdi_tuketim": {},
        "enerji_uretim": {},
    }
    
    # Üretim hesapla
    if oge.get("uretim"):
        for urun, miktar in oge["uretim"].items():
            toplam = int(adet * miktar * seviye_bonusu)
            detaylar["uretim"][urun] = {
                "birim": miktar,
                "toplam": toplam,
                "saatlik": toplam * 60,
                "ad": URUN_ADLARI.get(urun, urun),
            }
    
    # Girdi tüketimi hesapla
    if oge.get("girdi_tuketim"):
        for urun, miktar in oge["girdi_tuketim"].items():
            toplam = int(adet * miktar * seviye_bonusu)
            detaylar["girdi_tuketim"][urun] = {
                "birim": miktar,
                "toplam": toplam,
                "saatlik": toplam * 60,
                "ad": URUN_ADLARI.get(urun, urun),
            }
    
    # Enerji üretimi hesapla
    if oge.get("enerji_uretim"):
        for tur, miktar in oge["enerji_uretim"].items():
            toplam = int(adet * miktar * seviye_bonusu)
            detaylar["enerji_uretim"][tur] = {
                "birim": miktar,
                "toplam": toplam,
                "saatlik": toplam * 60,
                "ad": kat.ENERJI_ADLARI.get(tur, tur),
            }
    
    # Yem desteği varsa
    if oge.get("yem_destek"):
        detaylar["yem_destek"] = {
            "yem_gerekli": oge["yem_destek"]["yem"] * adet,
            "bonus": oge["yem_destek"]["bonus"],
        }
    
    return detaylar


def klup_olustur(kullanici_adi, klup_adi):
    """Yeni bir klüp oluşturur"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None
    
    oyuncu = _oyuncu_normalize(oyuncu)
    
    if oyuncu["klup"] is not None:
        return False, "Zaten bir klüptesin. Önce mevcut klüpten ayrılmalısın.", None
    
    # Klüp adı kontrolü
    klup_adi = klup_adi.strip()
    if len(klup_adi) < 3 or len(klup_adi) > 20:
        return False, "Klüp adı 3-20 karakter arasında olmalıdır.", None
    
    # Aynı isimli klüp kontrolü
    for klup in veriler["klupler"]:
        if klup["ad"].lower() == klup_adi.lower():
            return False, "Bu isimde bir klüp zaten var.", None
    
    # Klüp oluştur
    yeni_klup = {
        "id": str(len(veriler["klupler"]) + 1),
        "ad": klup_adi,
        "kurucu": kullanici_adi,
        "uyeler": [kullanici_adi],
        "kurulus_tarihi": _simdi().isoformat(),
    }
    
    veriler["klupler"].append(yeni_klup)
    oyuncu["klup"] = yeni_klup["id"]
    
    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)
    
    return True, f"{klup_adi} klübü oluşturuldu!", oyuncu


def klup_katil(kullanici_adi, klup_id):
    """Bir klübe katılır"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None
    
    oyuncu = _oyuncu_normalize(oyuncu)
    
    if oyuncu["klup"] is not None:
        return False, "Zaten bir klüptesin. Önce mevcut klüpten ayrılmalısın.", None
    
    klup = next((k for k in veriler["klupler"] if k["id"] == klup_id), None)
    if klup is None:
        return False, "Klüp bulunamadı.", None
    
    if kullanici_adi in klup["uyeler"]:
        return False, "Zaten bu klüptesin.", None
    
    klup["uyeler"].append(kullanici_adi)
    oyuncu["klup"] = klup_id
    
    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)
    
    return True, f"{klup['ad']} klübüne katıldın!", oyuncu


def klup_ayril(kullanici_adi):
    """Klüpten ayrılır"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None
    
    oyuncu = _oyuncu_normalize(oyuncu)
    
    if oyuncu["klup"] is None:
        return False, "Herhangi bir klüpte değilsin.", None
    
    klup = next((k for k in veriler["klupler"] if k["id"] == oyuncu["klup"]), None)
    if klup:
        if kullanici_adi in klup["uyeler"]:
            klup["uyeler"].remove(kullanici_adi)
        
        # Eğer klüp boşsa sil
        if len(klup["uyeler"]) == 0:
            veriler["klupler"] = [k for k in veriler["klupler"] if k["id"] != klup["id"]]
        # Eğer kurucu ayrıldıysa ve üye varsa yeni kurucu ata
        elif klup["kurucu"] == kullanici_adi and klup["uyeler"]:
            klup["kurucu"] = klup["uyeler"][0]
    
    oyuncu["klup"] = None
    
    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)
    
    return True, "Klüpten ayrıldın.", oyuncu


def klupler_getir():
    """Tüm klüpleri döndürür"""
    veriler = verileri_yukle()
    return veriler.get("klupler", [])


def chat_mesaj_ekle(kullanici_adi, mesaj):
    """Genel chat'e mesaj ekler"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı."
    
    mesaj = mesaj.strip()
    if len(mesaj) == 0 or len(mesaj) > 200:
        return False, "Mesaj 1-200 karakter arasında olmalıdır."
    
    yeni_mesaj = {
        "id": str(len(veriler["chat_mesajlari"]) + 1),
        "gonderen": kullanici_adi,
        "mesaj": mesaj,
        "zaman": _simdi().isoformat(),
    }
    
    veriler["chat_mesajlari"].append(yeni_mesaj)
    
    # Sadece son 50 mesajı tut
    if len(veriler["chat_mesajlari"]) > 50:
        veriler["chat_mesajlari"] = veriler["chat_mesajlari"][-50:]
    
    verileri_kaydet(veriler)
    
    return True, "Mesaj gönderildi."


def chat_mesajlari_getir():
    """Son chat mesajlarını döndürür"""
    veriler = verileri_yukle()
    return veriler.get("chat_mesajlari", [])


def fabrika_uretim_baslat(kullanici_adi, arazi_id):
    """Fabrika üretimini başlatır"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))

    arazi = next((a for a in oyuncu["araziler"] if a["id"] == arazi_id), None)
    if arazi is None:
        return False, "Arazi bulunamadı.", None
    if not arazi.get("fabrika"):
        return False, "Bu arazide fabrika yok.", None

    arazi_id_str = str(arazi_id)
    durum = oyuncu["fabrika_uretim_durumu"].get(arazi_id_str, {})

    if durum.get("baslatildi", False):
        return False, "Bu fabrika zaten çalışıyor.", None

    # Kapasite dolu mu kontrol et
    fab = kat.FABRIKA_TANIMLARI[arazi["fabrika"]]
    kapasite = fab.get("kapasite", 0)
    if durum.get("bekleyen_miktar", 0) >= kapasite:
        return False, "Kapasite dolu! Önce ürünleri topla.", None

    # Üretimi başlat
    durum["baslatildi"] = True
    durum["baslama_zamani"] = _simdi().isoformat()
    oyuncu["fabrika_uretim_durumu"][arazi_id_str] = durum

    # XP kazan
    xp_kazan(oyuncu, "uretim_baslat")

    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)

    return True, f"{fab['ad']} üretimi başlatıldı!", oyuncu


def fabrika_uretim_durdur(kullanici_adi, arazi_id):
    """Fabrika üretimini durdurur"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))

    arazi = next((a for a in oyuncu["araziler"] if a["id"] == arazi_id), None)
    if arazi is None:
        return False, "Arazi bulunamadı.", None
    if not arazi.get("fabrika"):
        return False, "Bu arazide fabrika yok.", None

    arazi_id_str = str(arazi_id)
    durum = oyuncu["fabrika_uretim_durumu"].get(arazi_id_str, {})

    if not durum.get("baslatildi", False):
        return False, "Bu fabrika zaten durdurulmuş.", None

    fab = kat.FABRIKA_TANIMLARI[arazi["fabrika"]]

    # Üretimi durdur
    durum["baslatildi"] = False
    durum["baslama_zamani"] = None
    oyuncu["fabrika_uretim_durumu"][arazi_id_str] = durum

    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)

    return True, f"{fab['ad']} üretimi durduruldu.", oyuncu


def fabrika_urun_topla(kullanici_adi, arazi_id):
    """Fabrikadan bekleyen ürünleri toplar"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))

    arazi = next((a for a in oyuncu["araziler"] if a["id"] == arazi_id), None)
    if arazi is None:
        return False, "Arazi bulunamadı.", None
    if not arazi.get("fabrika"):
        return False, "Bu arazide fabrika yok.", None

    arazi_id_str = str(arazi_id)
    durum = oyuncu["fabrika_uretim_durumu"].get(arazi_id_str, {})
    fab = kat.FABRIKA_TANIMLARI[arazi["fabrika"]]

    bekleyen_miktar = durum.get("bekleyen_miktar", 0)
    if bekleyen_miktar == 0:
        return False, "Toplanacak ürün yok.", None

    # Bekleyen ürünleri envantere aktar
    for urun, miktar in fab["cikti"].items():
        # Bu fabrikadan gelen ürün miktarını hesapla
        urun_miktari = min(bekleyen_miktar, oyuncu["bekleyen_urunler"].get(urun, 0))
        oyuncu["urunler"][urun] += urun_miktari
        oyuncu["bekleyen_urunler"][urun] -= urun_miktari

    # Durumu sıfırla
    durum["bekleyen_miktar"] = 0
    oyuncu["fabrika_uretim_durumu"][arazi_id_str] = durum

    # XP kazan
    xp_kazan(oyuncu, "urun_topla")

    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)

    return True, f"{bekleyen_miktar} ürün envantere eklendi!", oyuncu


def tesis_uretim_baslat(kullanici_adi, tesis_alani):
    """Tesis üretimini başlatır"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))

    # Tesisin sahibi olup olmadığını kontrol et
    if oyuncu["mulkler"].get(tesis_alani, 0) == 0:
        return False, "Bu tesise sahip değilsin.", None

    # Tesis tanımını bul
    kategori, anahtar, oge = kat.mulk_tanimi_bul(tesis_alani)
    if not oge:
        return False, "Geçersiz tesis.", None

    durum = oyuncu["tesis_uretim_durumu"].get(tesis_alani, {})

    if durum.get("baslatildi", False):
        return False, "Bu tesis zaten çalışıyor.", None

    # Kapasite dolu mu kontrol et
    kapasite = oge.get("kapasite", 0)
    if durum.get("bekleyen_miktar", 0) >= kapasite:
        return False, "Kapasite dolu! Önce ürünleri topla.", None

    # Üretimi başlat
    durum["baslatildi"] = True
    durum["baslama_zamani"] = _simdi().isoformat()
    oyuncu["tesis_uretim_durumu"][tesis_alani] = durum

    # XP kazan
    xp_kazan(oyuncu, "uretim_baslat")

    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)

    return True, f"{oge['ad']} üretimi başlatıldı!", oyuncu


def tesis_uretim_durdur(kullanici_adi, tesis_alani):
    """Tesis üretimini durdurur"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))

    # Tesisin sahibi olup olmadığını kontrol et
    if oyuncu["mulkler"].get(tesis_alani, 0) == 0:
        return False, "Bu tesise sahip değilsin.", None

    # Tesis tanımını bul
    kategori, anahtar, oge = kat.mulk_tanimi_bul(tesis_alani)
    if not oge:
        return False, "Geçersiz tesis.", None

    durum = oyuncu["tesis_uretim_durumu"].get(tesis_alani, {})

    if not durum.get("baslatildi", False):
        return False, "Bu tesis zaten durdurulmuş.", None

    # Üretimi durdur
    durum["baslatildi"] = False
    durum["baslama_zamani"] = None
    oyuncu["tesis_uretim_durumu"][tesis_alani] = durum

    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)

    return True, f"{oge['ad']} üretimi durduruldu.", oyuncu


def tesis_urun_topla(kullanici_adi, tesis_alani):
    """Tesisden bekleyen ürünleri toplar"""
    veriler = verileri_yukle()
    oyuncu = veriler["oyuncular"].get(kullanici_adi)
    if oyuncu is None:
        return False, "Oyuncu bulunamadı.", None

    oyuncu = uretim_hesapla(_oyuncu_normalize(oyuncu))

    # Tesisin sahibi olup olmadığını kontrol et
    if oyuncu["mulkler"].get(tesis_alani, 0) == 0:
        return False, "Bu tesise sahip değilsin.", None

    # Tesis tanımını bul
    kategori, anahtar, oge = kat.mulk_tanimi_bul(tesis_alani)
    if not oge:
        return False, "Geçersiz tesis.", None

    durum = oyuncu["tesis_uretim_durumu"].get(tesis_alani, {})

    bekleyen_miktar = durum.get("bekleyen_miktar", 0)
    if bekleyen_miktar == 0:
        return False, "Toplanacak ürün yok.", None

    # Bekleyen ürünleri envantere aktar
    uretim = oge.get("uretim", {})
    for urun, miktar in uretim.items():
        # Bu tesisden gelen ürün miktarını hesapla
        urun_miktari = min(bekleyen_miktar, oyuncu["bekleyen_urunler"].get(urun, 0))
        oyuncu["urunler"][urun] += urun_miktari
        oyuncu["bekleyen_urunler"][urun] -= urun_miktari

    # Durumu sıfırla
    durum["bekleyen_miktar"] = 0
    oyuncu["tesis_uretim_durumu"][tesis_alani] = durum

    # XP kazan
    xp_kazan(oyuncu, "urun_topla")

    veriler["oyuncular"][kullanici_adi] = oyuncu
    verileri_kaydet(veriler)

    return True, f"{bekleyen_miktar} ürün envantere eklendi!", oyuncu


def oyuncu_sil(admin_kullanici_adi, hedef_kullanici_adi):
    """Admin tarafından oyuncu siler"""
    veriler = verileri_yukle()
    admin = veriler["oyuncular"].get(admin_kullanici_adi)
    if admin is None or not admin_mi(admin):
        return False, "Admin yetkiniz yok."

    if hedef_kullanici_adi not in veriler["oyuncular"]:
        return False, "Oyuncu bulunamadı."

    if hedef_kullanici_adi == ADMIN_KULLANICI:
        return False, "Admin hesabı silinemez."

    del veriler["oyuncular"][hedef_kullanici_adi]
    verileri_kaydet(veriler)

    return True, f"{hedef_kullanici_adi} silindi."


def oyuncu_bakiye_ayarla(admin_kullanici_adi, hedef_kullanici_adi, yeni_bakiye):
    """Admin tarafından oyuncu bakiyesini ayarlar"""
    veriler = verileri_yukle()
    admin = veriler["oyuncular"].get(admin_kullanici_adi)
    if admin is None or not admin_mi(admin):
        return False, "Admin yetkiniz yok."

    hedef = veriler["oyuncular"].get(hedef_kullanici_adi)
    if hedef is None:
        return False, "Oyuncu bulunamadı."

    hedef["bakiye"] = yeni_bakiye
    veriler["oyuncular"][hedef_kullanici_adi] = hedef
    verileri_kaydet(veriler)

    return True, f"{hedef_kullanici_adi} bakiyesi {yeni_bakiye} TL olarak ayarlandı."
