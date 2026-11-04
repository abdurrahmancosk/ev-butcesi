import csv
import datetime
import io
import json
import os
import flet as ft

# ==============================================================================
# Flet 1.0+ ve Eski Sürümler İçin Evrensel Uyumluluk Katmanı
# ==============================================================================
if not hasattr(ft, "ElevatedButton") and hasattr(ft, "Button"):
    ft.ElevatedButton = ft.Button

if not hasattr(ft, "dropdown"):
    class _DropdownNamespace:
        Option = getattr(ft, "DropdownOption", None)
    ft.dropdown = _DropdownNamespace
elif not hasattr(ft.dropdown, "Option") and hasattr(ft, "DropdownOption"):
    ft.dropdown.Option = ft.DropdownOption
if not hasattr(ft, "KeyboardType"):
    class _KeyboardTypeNamespace:
        NUMBER = "number"
        TEXT = "text"
    ft.KeyboardType = _KeyboardTypeNamespace


# Compatibility shims for Flet 1.0+
if hasattr(ft, "Border"):
    if not hasattr(ft, "border"):
        ft.border = ft.Border
    else:
        if not hasattr(ft.border, "all") and hasattr(ft.Border, "all"):
            ft.border.all = ft.Border.all
        elif not hasattr(ft.border, "all"):
            ft.border.all = lambda width=1, color="#e2e8f0": make_border_all(width, color)
        if not hasattr(ft.border, "only") and hasattr(ft.Border, "only"):
            ft.border.only = ft.Border.only
        elif not hasattr(ft.border, "only"):
            ft.border.only = lambda **kwargs: make_border_bottom()

if hasattr(ft, "Alignment"):
    if not hasattr(ft, "alignment"):
        ft.alignment = ft.Alignment
    else:
        if not hasattr(ft.alignment, "center"):
            ft.alignment.center = getattr(ft.Alignment, "CENTER", getattr(ft.Alignment, "center", None))

if hasattr(ft, "Padding"):
    if not hasattr(ft, "padding"):
        ft.padding = ft.Padding
    else:
        if not hasattr(ft.padding, "symmetric"):
            ft.padding.symmetric = getattr(ft.Padding, "symmetric", lambda horizontal=0, vertical=0: make_padding(horizontal, vertical))
        if not hasattr(ft.padding, "only"):
            ft.padding.only = getattr(ft.Padding, "only", lambda **kwargs: make_padding(**kwargs))
        if not hasattr(ft.padding, "all"):
            ft.padding.all = getattr(ft.Padding, "all", lambda val: make_padding(val, val))

def make_border_all(width=1, color="#e2e8f0"):
    """Hem Flet 1.0 (ft.Border.all) hem eski sürümlerle uyumlu kenarlık üretir."""
    if hasattr(ft, "Border") and hasattr(ft.Border, "all"):
        return ft.Border.all(width, color)
    elif hasattr(ft, "border") and hasattr(ft.border, "all"):
        return ft.border.all(width, color)
    return None

def make_border_bottom(width=0.6, color="#f1f5f9"):
    """Hem Flet 1.0 hem eski sürümlerle uyumlu alt kenarlık üretir."""
    side = None
    if hasattr(ft, "BorderSide"):
        side = ft.BorderSide(width, color)
    if hasattr(ft, "Border") and hasattr(ft.Border, "only"):
        return ft.Border.only(bottom=side)
    elif hasattr(ft, "border") and hasattr(ft.border, "only"):
        return ft.border.only(bottom=side)
    return None

def get_alignment_center():
    """Hem Flet 1.0 (ft.Alignment.CENTER) hem eski sürümlerle uyumlu hizalama döner."""
    if hasattr(ft, "Alignment"):
        if hasattr(ft.Alignment, "CENTER"):
            return ft.Alignment.CENTER
        elif hasattr(ft.Alignment, "center"):
            return ft.Alignment.center
    if hasattr(ft, "alignment") and hasattr(ft.alignment, "center"):
        return ft.alignment.center
    return None

def make_padding(horizontal=0, vertical=0, left=None, right=None, top=None, bottom=None, **kwargs):
    """Hem Flet 1.0 (ft.Padding) hem de eski sürümlerle uyumlu padding üretir."""
    l = left if left is not None else horizontal
    r = right if right is not None else horizontal
    t = top if top is not None else vertical
    b = bottom if bottom is not None else vertical
    if hasattr(ft, "Padding"):
        if hasattr(ft.Padding, "symmetric") and left is None and right is None and top is None and bottom is None:
            try:
                return ft.Padding.symmetric(horizontal=horizontal, vertical=vertical)
            except Exception:
                pass
        try:
            return ft.Padding(left=l, right=r, top=t, bottom=b)
        except Exception:
            pass
    return max(horizontal, vertical) if (horizontal and vertical) else (horizontal or vertical)

def make_button(text, icon=None, bgcolor=None, color=None, width=None, height=None, on_click=None, outlined=False, tooltip=None, **kwargs):
    """Hem Flet 1.0 hem de eski sürümlerle %100 hatasız çalışan buton üretir."""
    if outlined:
        btn_cls = getattr(ft, "OutlinedButton", getattr(ft, "Button", None))
    else:
        btn_cls = getattr(ft, "ElevatedButton", getattr(ft, "Button", None))
    if btn_cls is None:
        btn_cls = getattr(ft, "Button", getattr(ft, "OutlinedButton", getattr(ft, "ElevatedButton", None)))

    denemeler = [
        {"content": text, "icon": icon, "bgcolor": bgcolor, "color": color, "width": width, "height": height, "on_click": on_click, "tooltip": tooltip},
        {"text": text, "icon": icon, "bgcolor": bgcolor, "color": color, "width": width, "height": height, "on_click": on_click, "tooltip": tooltip},
        {"content": text, "icon": icon, "bgcolor": bgcolor, "color": color, "width": width, "height": height, "on_click": on_click},
        {"text": text, "icon": icon, "bgcolor": bgcolor, "color": color, "width": width, "height": height, "on_click": on_click},
        {"content": text, "width": width, "height": height, "on_click": on_click},
        {"text": text, "width": width, "height": height, "on_click": on_click},
        {"content": text},
        {"text": text},
    ]

    for p in denemeler:
        clean_p = {k: v for k, v in p.items() if v is not None}
        try:
            return btn_cls(**clean_p)
        except TypeError:
            continue
        except Exception:
            continue

    try:
        return btn_cls(text)
    except Exception:
        return ft.Container(content=ft.Text(str(text)), on_click=on_click)

def make_option(key_or_text):
    """Hem Flet 1.0 (ft.DropdownOption) hem eski (ft.dropdown.Option) ile uyumlu seçenek üretir."""
    if hasattr(ft, "DropdownOption"):
        return ft.DropdownOption(text=str(key_or_text), key=str(key_or_text))
    elif hasattr(ft, "dropdown") and hasattr(ft.dropdown, "Option"):
        return ft.dropdown.Option(str(key_or_text))
    return ft.DropdownOption(str(key_or_text))

def make_dropdown(options, value=None, label=None, width=None, on_change=None, dense=True, **kwargs):
    """Hem Flet 1.0 (on_select) hem 0.x (on_change) ile uyumlu Dropdown üretir."""
    opts = [make_option(opt) if isinstance(opt, str) else opt for opt in options]
    kwargs = {
        "options": opts,
        "value": value,
        "width": width,
    }
    if label:
        kwargs["label"] = label
    if dense:
        kwargs["dense"] = dense

    if on_change:
        if hasattr(ft.Dropdown, "on_select") or not hasattr(ft.Dropdown, "on_change"):
            kwargs["on_select"] = on_change
        else:
            kwargs["on_change"] = on_change

    try:
        dd = ft.Dropdown(**kwargs)
    except TypeError:
        kwargs.pop("on_select", None)
        kwargs.pop("on_change", None)
        dd = ft.Dropdown(**kwargs)
        if on_change:
            if hasattr(dd, "on_select"):
                dd.on_select = on_change
            elif hasattr(dd, "on_change"):
                dd.on_change = on_change

    return dd


def show_app_dialog(page, dialog):
    """Hem Flet 1.0 (page.open / page.show_dialog) hem Flet 0.x (page.dialog) ile %100 uyumlu diyalog açar."""
    opened = False
    if hasattr(page, "open"):
        try:
            page.open(dialog)
            opened = True
        except Exception:
            pass
    if not opened and hasattr(page, "show_dialog"):
        try:
            page.show_dialog(dialog)
            opened = True
        except Exception:
            pass
    if not opened:
        page.dialog = dialog
        dialog.open = True
    try:
        page.update()
    except Exception:
        pass

def close_app_dialog(page, dialog=None):
    """Hem Flet 1.0 (page.close / page.pop_dialog) hem Flet 0.x ile %100 uyumlu diyalog kapatır."""
    closed = False
    if hasattr(page, "close") and dialog:
        try:
            page.close(dialog)
            closed = True
        except Exception:
            pass
    if not closed and hasattr(page, "pop_dialog"):
        try:
            page.pop_dialog()
            closed = True
        except Exception:
            pass
    if dialog:
        dialog.open = False
    if hasattr(page, "dialog") and page.dialog:
        page.dialog.open = False
    try:
        page.update()
    except Exception:
        pass

def show_app_snackbar(page, text, color=None):
    """Hem Flet 1.0 hem 0.x ile uyumlu SnackBar bildirimi gösterir."""
    content = ft.Text(text, color="white")
    sb = ft.SnackBar(content=content, bgcolor=color if color else "#1e293b", open=True)
    shown = False
    if hasattr(page, "open"):
        try:
            page.open(sb)
            shown = True
        except Exception:
            pass
    if not shown and hasattr(page, "show_snack_bar"):
        try:
            page.show_snack_bar(sb)
            shown = True
        except Exception:
            pass
    if not shown:
        page.snack_bar = sb
    try:
        page.update()
    except Exception:
        pass
def set_button_label(btn, new_text):
    """Buton etiketini sürüm bağımsız günceller."""
    if hasattr(btn, "text") and btn.text is not None:
        btn.text = new_text
    else:
        btn.content = new_text

# ==============================================================================
# Oturum Yönetimi (Beni Hatırla)
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() or "__file__" in globals() else "."
OTURUM_DOSYASI = os.path.join(BASE_DIR, "oturum.json")

def oturum_oku():
    if os.path.exists(OTURUM_DOSYASI):
        try:
            with open(OTURUM_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def oturum_kaydet(kullanici, yonetici_mi):
    try:
        with open(OTURUM_DOSYASI, "w", encoding="utf-8") as f:
            json.dump({"kullanici": kullanici, "yonetici_mi": yonetici_mi}, f, ensure_ascii=False)
    except Exception:
        pass

def oturum_sil():
    if os.path.exists(OTURUM_DOSYASI):
        try:
            os.remove(OTURUM_DOSYASI)
        except Exception:
            pass

# ==============================================================================
# Supabase Bulut Veritabanı Bağlantısı
# ==============================================================================
SUPABASE_URL = "https://ivngkowxxafkyvvzhdob.supabase.co"
SUPABASE_KEY = "sb_publishable_0pVRLE1ceJ0FlI32XGzbsw_Z_mldcXe"

supabase = None
try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase bulut veritabanına başarıyla bağlanıldı.")
except Exception as e:
    print("⚠️ Supabase bağlantısı başlatılamadı (yerel modda çalışılacak):", e)


# ==============================================================================
# Google Gemini AI Fiş Tarama Entegrasyonu
# ==============================================================================

# ==============================================================================
# Standart Harcama Kategorileri
# ==============================================================================
GIDER_KATEGORILERI = [
    "Market & Temel Gıda",
    "Ev & Faturalar",
    "Ulaşım / Yakıt",
    "Abur Cubur & Atıştırmalık",
    "Giyim & Kişisel",
    "Sağlık",
    "Eğlence & Restoran",
    "Eğitim & Okul",
    "Sigara/Tütün",
    "Temizlik",
    "Transfer / Birikim",
    "Yatırım",
    "Yatırım / Altın",
    "Diğer"
]
kategoriler = GIDER_KATEGORILERI

GEMINI_API_KEY = "AQ.Ab8RN6INNOQBkceaWeS3U1xKw8cLWYtnlW4dEm9x6sAw9HSpZw"

def gemini_aktif_modelleri_bul(api_key, ssl_context=None):
    """Kullanıcının API anahtarına tanımlı modelleri Google'dan çeker ve yalnızca ücretsiz/hızlı Gemini Flash modellerini seçer."""
    import urllib.request
    import json
    bulunanlar = []
    kw = {"timeout": 10}
    if ssl_context:
        kw["context"] = ssl_context

    for ver in ["v1beta", "v1"]:
        url = f"https://generativelanguage.googleapis.com/{ver}/models"
        req = urllib.request.Request(url, headers={"x-goog-api-key": api_key})
        try:
            with urllib.request.urlopen(req, **kw) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        m_name = m.get("name", "").replace("models/", "")
                        m_low = m_name.lower()
                        # Yalnızca saf Gemini modelleri (gemma vb. hariç)
                        if not m_low.startswith("gemini-"):
                            continue
                        # Ücretsiz planda kotası 0 olan veya görsel almayan modelleri filtrele
                        if any(x in m_low for x in ["-tts", "embedding", "aqa", "imagen", "-image", "-pro"]):
                            continue
                        if "flash" in m_low:
                            bulunanlar.append((ver, m_name))
                if bulunanlar:
                    print(f"📋 Google'dan {len(bulunanlar)} adet aktif Gemini Flash modeli listelendi ({ver}).")
                    break
        except Exception as ex:
            print(f"ListModels ({ver}) denemesi:", ex)

    # En güncel, kotası bol ve hızlı Flash modellerini sırala
    oncelik = [
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash"
    ]
    sirali = []
    for p in oncelik:
        for v, name in bulunanlar:
            if p == name or p in name:
                if (v, name) not in sirali:
                    sirali.append((v, name))
    for item in bulunanlar:
        if item not in sirali:
            sirali.append(item)

    if not sirali:
        sirali = [
            ("v1beta", "gemini-3.5-flash-lite"),
            ("v1beta", "gemini-3.8-flash"),
            ("v1beta", "gemini-flash-latest"),
            ("v1beta", "gemini-2.0-flash"),
            ("v1", "gemini-1.5-flash")
        ]
    return sirali

def gemini_fis_analiz_et(gorsel_yolu, api_key=GEMINI_API_KEY, status_cb=None):
    """Fiş veya fatura görselini/PDF'ini Google Gemini Flash modeli ile analiz eder."""
    import base64
    import urllib.request
    import urllib.error
    import ssl
    import io

    if not api_key:
        return {"hata": "Gemini API anahtarı tanımlanmamış."}

    if not os.path.exists(gorsel_yolu):
        return {"hata": f"Dosya bulunamadı: {gorsel_yolu}"}

    ext = os.path.splitext(gorsel_yolu)[1].lower()
    mime_type = "image/jpeg"

    if status_cb:
        status_cb("📸 Görsel hazırlanıyor...")

    try:
        with open(gorsel_yolu, "rb") as f:
            img_bytes = f.read()
    except Exception as e:
        return {"hata": f"Dosya okunamadı: {e}"}

    # Görsel optimizasyonu (Yüksek çözünürlüklü fotoğrafları 1600px'e küçültüp hızlı yükleme)
    if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
        try:
            from PIL import Image
            im = Image.open(io.BytesIO(img_bytes))
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            max_dim = 1600
            if max(im.size) > max_dim:
                scale = max_dim / max(im.size)
                new_size = (int(im.size[0] * scale), int(im.size[1] * scale))
                im = im.resize(new_size, Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=85, optimize=True)
            img_bytes = buf.getvalue()
            mime_type = "image/jpeg"
            print(f"🖼️ Görsel optimize edildi: {im.size[0]}x{im.size[1]}, {len(img_bytes):,} bayt")
        except Exception as ex_opt:
            print("Pillow optimizasyon uyarısı:", ex_opt)
            if ext == ".png":
                mime_type = "image/png"
            elif ext == ".webp":
                mime_type = "image/webp"
    elif ext == ".pdf":
        mime_type = "application/pdf"
        print(f"📄 PDF belgesi yüklendi: {len(img_bytes):,} bayt")

    b64_data = base64.b64encode(img_bytes).decode("utf-8")

    prompt = """Sen uzman bir market, mağaza ve alışveriş fişi/faturası analiz asistanısın. Bu fiş veya fatura belgesindeki bilgileri oku. Yalnızca geçerli bir JSON nesnesi döndür (markdown kod blokları ekleme, doğrudan saf json döndür).
JSON yapısı:
{
  "firma": "Market/Mağaza Adı (örn: BİM, Migros, A101, ŞOK, Eczane)",
  "tarih": "GG.AA.YYYY formatında fiş tarihi (örn: 03.11.2026, bulunamazsa bugünün tarihi)",
  "saat": "SS:DD formatında fiş saati (örn: 14:35, bulunamazsa 12:00)",
  "urunler": [
    {
      "urun": "Ürün/Hizmet Adı (kısaltmaları düzelt)",
      "miktar": "Miktar (örn: 1 Adet, 1.5 kg, 2 Paket)",
      "birim_fiyat": 25.50,
      "tutar": 51.00,
      "kategori": "Harcama Kategorisi (Aşağıdakilerden en uygununu seç: Market & Temel Gıda, Sağlık, Ulaşım & Akaryakıt, Fatura (Elektrik/Su/Doğalgaz), Giyim & Ayakkabı, Ev & Yaşam, Eğitim & Kırtasiye, Kültür, Eğlence & Hobi, Yeme & İçme (Restoran/Kafe), Kişisel Bakım & Kozmetik, Teknoloji & Elektronik, Kira & Aidat, Diğer)"
    }
  ],
  "toplam_tutar": 51.00
}"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json"
        }
    }

    body = json.dumps(payload).encode("utf-8")

    ssl_context = None
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    except Exception:
        pass

    if status_cb:
        status_cb("🔍 Aktif Gemini modelleri taranıyor...")

    modeller = gemini_aktif_modelleri_bul(api_key, ssl_context)
    son_hata = ""

    for api_ver, model in modeller:
        if status_cb:
            status_cb(f"🌐 Fiş okunuyor ({model})...")

        url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model}:generateContent"
        print(f"🤖 Gemini ({api_ver}/{model}) modeline istek gönderiliyor...")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key
            },
            method="POST"
        )
        try:
            kw = {"timeout": 25}
            if ssl_context:
                kw["context"] = ssl_context
            with urllib.request.urlopen(req, **kw) as resp:
                resp_text = resp.read().decode("utf-8")
                resp_json = json.loads(resp_text)
                candidates = resp_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text_val = parts[0].get("text", "").strip()
                        if text_val.startswith("```json"):
                            text_val = text_val[7:]
                        if text_val.startswith("```"):
                            text_val = text_val[3:]
                        if text_val.endswith("```"):
                            text_val = text_val[:-3]
                        text_val = text_val.strip()
                        parsed = json.loads(text_val)
                        print(f"✅ Fiş başarıyla çözümlendi ({model}): {parsed.get('firma')} - {len(parsed.get('urunler', []))} ürün")
                        return parsed
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
            print(f"⚠️ {model} HTTP Hatası ({e.code}):", err_body[:160])
            son_hata = f"HTTP {e.code}: {err_body[:160]}"
            # 503 (geçici yoğunluk), 429 (kota sınırı), 404 (model kapalı), 400 (desteklenmeyen girdi) durumlarında vakit kaybetmeden sonraki çalışan modele geç
            continue
        except Exception as e:
            print(f"⚠️ {model} Bağlantı Hatası:", e)
            son_hata = str(e)
            continue

    return {"hata": f"Fiş analiz edilemedi: {son_hata}"}

islemler = []

def aktif_butce_donemini_bul(ref_tarih=None):
    """Herhangi bir tarihin veya bugünün ait olduğu bütçe dönemini (15'i - 14'ü) bulur."""
    bugun = ref_tarih or datetime.date.today()
    yil = bugun.year
    ay = bugun.month
    if bugun.day >= 15:
        baslangic = datetime.date(yil, ay, 15)
        bitis = datetime.date(yil + 1, 1, 14) if ay == 12 else datetime.date(yil, ay + 1, 14)
    else:
        baslangic = datetime.date(yil - 1, 12, 15) if ay == 1 else datetime.date(yil, ay - 1, 15)
        bitis = datetime.date(yil, ay, 14)
    return baslangic, bitis

def standart_tarih_yap(tarih_str):
    """Her türlü tarih formatını (YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY) GG.AA.YYYY formatına çevirir."""
    if not tarih_str:
        return datetime.date.today().strftime("%d.%m.%Y")
    t_clean = str(tarih_str).split(" ")[0].strip()
    for sep in ["-", "/", "."]:
        if sep in t_clean:
            parts = t_clean.split(sep)
            if len(parts) == 3:
                try:
                    if len(parts[0]) == 4:
                        return f"{int(parts[2]):02d}.{int(parts[1]):02d}.{int(parts[0])}"
                    else:
                        return f"{int(parts[0]):02d}.{int(parts[1]):02d}.{int(parts[2])}"
                except Exception:
                    pass
    return datetime.date.today().strftime("%d.%m.%Y")

def stringden_tarih_al(tarih_str):
    """Metin halindeki tarihi her formattan datetime.date nesnesine güvenle çevirir."""
    if not tarih_str:
        return None
    try:
        std = standart_tarih_yap(tarih_str)
        d, m, y = map(int, std.split("."))
        return datetime.date(y, m, d)
    except Exception:
        return None

def main(page: ft.Page):
    page.title = "Hane Bütçesi Takip Sistemi"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    try:
        if hasattr(page, "window"):
            page.window.width = 450
            page.window.height = 860
        else:
            page.window_width = 450
            page.window_height = 860
    except Exception:
        pass

    def picker_ac(dlg):
        if hasattr(page, "show_dialog"):
            page.show_dialog(dlg)
        elif hasattr(page, "open"):
            page.open(dlg)
        else:
            dlg.open = True
            page.update()

    def picker_kapat(dlg):
        if hasattr(page, "pop_dialog"):
            page.pop_dialog()
        elif hasattr(page, "close"):
            page.close(dlg)
        else:
            dlg.open = False
            page.update()

    def ana_ekrana_git(kullanici, yonetici_mi):
        page.clean()
        page.scroll = ft.ScrollMode.AUTO

        # Aktif Bütçe Dönemi Durumu
        varsayilan_bas, varsayilan_bit = aktif_butce_donemini_bul()
        secilen_donem_bas = [varsayilan_bas]
        secilen_donem_bit = [varsayilan_bit]
        tum_zamanlar_modu = [False]
        siralama_en_yeni = [False]  # False = Kronolojik (Eskiden yeniye)

        # Buluttan mevcut kayıtları çek
        if supabase:
            try:
                res = supabase.table("islemler").select("*").order("id", desc=True).execute()
                if res.data is not None:
                    islemler.clear()
                    islemler.extend(res.data)
            except Exception as ex:
                print("Buluttan veri çekme hatası:", ex)

        # Tarih ve saat durum değişkenleri
        secilen_gelir_tarih = [datetime.date.today()]
        secilen_gelir_saat = [datetime.datetime.now().strftime("%H:%M")]
        secilen_gider_tarih = [datetime.date.today()]
        secilen_gider_saat = [datetime.datetime.now().strftime("%H:%M")]
        secilen_aktarim_tarih = [datetime.date.today()]

        # --- GELİR TARİH VE SAAT SEÇİCİ ---
        def gelir_tarih_degisti(e):
            if gelir_date_picker.value:
                val = gelir_date_picker.value
                secilen = val.date() if isinstance(val, datetime.datetime) else val
                secilen_gelir_tarih[0] = secilen
                set_button_label(gelir_tarih_btn, f"📅 {secilen.strftime('%d.%m.%Y')}")
                page.update()

        gelir_date_picker = ft.DatePicker(
            on_change=gelir_tarih_degisti,
            first_date=datetime.datetime(2020, 1, 1),
            last_date=datetime.datetime(2035, 12, 31),
        )

        gelir_tarih_btn = make_button(
            f"📅 {datetime.date.today().strftime('%d.%m.%Y')}",
            icon=ft.Icons.CALENDAR_MONTH,
            width=150,
            outlined=True,
            on_click=lambda _: picker_ac(gelir_date_picker)
        )

        def gelir_saat_degisti(e):
            if gelir_time_picker.value:
                val = gelir_time_picker.value
                saat_str = val.strftime("%H:%M") if hasattr(val, "strftime") else str(val)[:5]
                secilen_gelir_saat[0] = saat_str
                set_button_label(gelir_saat_btn, f"🕒 {saat_str}")
                page.update()

        gelir_time_picker = ft.TimePicker(
            confirm_text="Tamam",
            cancel_text="İptal",
            help_text="Saat Seçiniz",
            on_change=gelir_saat_degisti
        )

        gelir_saat_btn = make_button(
            f"🕒 {secilen_gelir_saat[0]}",
            width=110,
            outlined=True,
            on_click=lambda _: picker_ac(gelir_time_picker)
        )

        def gelir_anlik_saat_ayarla(e):
            su_an = datetime.datetime.now().strftime("%H:%M")
            secilen_gelir_saat[0] = su_an
            set_button_label(gelir_saat_btn, f"🕒 {su_an}")
            page.update()

        gelir_anlik_saat_btn = ft.IconButton(
            icon=ft.Icons.ACCESS_TIME_FILLED,
            icon_color="blue",
            tooltip="Şu anki saati al",
            on_click=gelir_anlik_saat_ayarla
        )

        gelir_tarih_saat_satiri = ft.Row(
            [gelir_tarih_btn, gelir_saat_btn, gelir_anlik_saat_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # --- GİDER TARİH VE SAAT SEÇİCİ ---
        def gider_tarih_degisti(e):
            if gider_date_picker.value:
                val = gider_date_picker.value
                secilen = val.date() if isinstance(val, datetime.datetime) else val
                secilen_gider_tarih[0] = secilen
                set_button_label(gider_tarih_btn, f"📅 {secilen.strftime('%d.%m.%Y')}")
                page.update()

        gider_date_picker = ft.DatePicker(
            on_change=gider_tarih_degisti,
            first_date=datetime.datetime(2020, 1, 1),
            last_date=datetime.datetime(2035, 12, 31),
        )

        gider_tarih_btn = make_button(
            f"📅 {datetime.date.today().strftime('%d.%m.%Y')}",
            icon=ft.Icons.CALENDAR_MONTH,
            width=150,
            outlined=True,
            on_click=lambda _: picker_ac(gider_date_picker)
        )

        def gider_saat_degisti(e):
            if gider_time_picker.value:
                val = gider_time_picker.value
                saat_str = val.strftime("%H:%M") if hasattr(val, "strftime") else str(val)[:5]
                secilen_gider_saat[0] = saat_str
                set_button_label(gider_saat_btn, f"🕒 {saat_str}")
                page.update()

        gider_time_picker = ft.TimePicker(
            confirm_text="Tamam",
            cancel_text="İptal",
            help_text="Saat Seçiniz",
            on_change=gider_saat_degisti
        )

        gider_saat_btn = make_button(
            f"🕒 {secilen_gider_saat[0]}",
            width=110,
            outlined=True,
            on_click=lambda _: picker_ac(gider_time_picker)
        )

        def gider_anlik_saat_ayarla(e):
            su_an = datetime.datetime.now().strftime("%H:%M")
            secilen_gider_saat[0] = su_an
            set_button_label(gider_saat_btn, f"🕒 {su_an}")
            page.update()

        gider_anlik_saat_btn = ft.IconButton(
            icon=ft.Icons.ACCESS_TIME_FILLED,
            icon_color="blue",
            tooltip="Şu anki saati al",
            on_click=gider_anlik_saat_ayarla
        )

        gider_tarih_saat_satiri = ft.Row(
            [gider_tarih_btn, gider_saat_btn, gider_anlik_saat_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # --- AKTARIM TARİH SEÇİCİ ---
        def aktarim_tarih_degisti(e):
            if aktarim_date_picker.value:
                val = aktarim_date_picker.value
                secilen = val.date() if isinstance(val, datetime.datetime) else val
                secilen_aktarim_tarih[0] = secilen
                set_button_label(aktarim_tarih_btn, f"📅 {secilen.strftime('%d.%m.%Y')}")
                page.update()

        aktarim_date_picker = ft.DatePicker(
            on_change=aktarim_tarih_degisti,
            first_date=datetime.datetime(2020, 1, 1),
            last_date=datetime.datetime(2035, 12, 31),
        )

        aktarim_tarih_btn = make_button(
            f"📅 {datetime.date.today().strftime('%d.%m.%Y')}",
            icon=ft.Icons.CALENDAR_MONTH,
            width=320,
            outlined=True,
            on_click=lambda _: picker_ac(aktarim_date_picker)
        )

        # --- GELİR ALANLARI ---
        gelir_kaynagi = ft.TextField(label="Gelir Kaynağı (Örn: Şirket, Kiracı)", width=320, dense=True)
        gelir_turu = make_dropdown(
            label="Gelir Türü",
            options=["Maaş", "Ek Gelir / Serbest", "Kira Geliri", "Yatırım / Faiz", "Diğer"],
            value="Maaş",
            width=320,
            dense=True
        )
        gelir_aciklamasi = ft.TextField(label="Açıklama (Örn: Kasım ayı maaş ödemesi)", width=320, dense=True)
        gelir_tutari = ft.TextField(label="Tutar (TL)", width=320, dense=True, keyboard_type=ft.KeyboardType.NUMBER)

        gelir_form_kutusu = ft.Column([
            ft.Text("Tarih ve Saat Seçimi:", size=12, color="grey"),
            gelir_tarih_saat_satiri,
            gelir_kaynagi,
            gelir_turu,
            gelir_aciklamasi,
            gelir_tutari
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # --- GİDER ALANLARI ---
        gider_firma = ft.TextField(label="Firma / Market (Örn: BİM, Migros)", width=320, dense=True)
        gider_urun = ft.TextField(label="Ürün / Hizmet (Örn: Süt, Ekmek, Elektrik)", width=320, dense=True)
        gider_kategori = make_dropdown(
            label="Kategori",
            options=[
                "Market & Temel Gıda",
                "Ev & Faturalar",
                "Ulaşım / Yakıt",
                "Abur Cubur & Atıştırmalık",
                "Giyim & Kişisel",
                "Sağlık",
                "Eğlence & Restoran",
                "Eğitim & Okul",
                "Sigara/Tütün",
                "Temizlik",
                "Transfer / Birikim",
                "Diğer"
            ],
            value="Market & Temel Gıda",
            width=320,
            dense=True
        )

        gider_miktar = ft.TextField(label="Miktar", width=115, dense=True, keyboard_type=ft.KeyboardType.NUMBER)
        birim_listesi = ["adet", "litre", "kg", "g", "ml", "paket", "koli", "demet", "kutu", "porsiyon", "metre"]
        gider_birim_secimi = make_dropdown(label="Birim", options=birim_listesi, value=None, width=140, dense=True)

        def yeni_birim_dialog_ac(e):
            yeni_birim_input = ft.TextField(label="Yeni Birim (Örn: rulo, kova)", autofocus=True, width=280)
            birim_uyari = ft.Text("", color="red", size=12)

            def birim_kaydet(ev):
                yeni_val = yeni_birim_input.value.strip().lower()
                if not yeni_val:
                    birim_uyari.value = "Lütfen bir birim adı giriniz."
                    page.update()
                    return

                mevcut_birimler = [opt.key if hasattr(opt, "key") and opt.key else getattr(opt, "text", "") for opt in gider_birim_secimi.options]
                if yeni_val not in mevcut_birimler:
                    gider_birim_secimi.options.append(make_option(yeni_val))

                gider_birim_secimi.value = yeni_val
                picker_kapat(birim_dialog)
                page.update()

            birim_dialog = ft.AlertDialog(
                title=ft.Text("Yeni Birim Ekle"),
                content=ft.Column([
                    ft.Text("Listeye eklemek istediğiniz ölçü birimini yazınız:"),
                    yeni_birim_input,
                    birim_uyari
                ], tight=True),
                actions=[
                    make_button("İptal", outlined=True, on_click=lambda _: picker_kapat(birim_dialog)),
                    make_button("Ekle", bgcolor="green", color="white", on_click=birim_kaydet),
                ]
            )
            picker_ac(birim_dialog)

        birim_ekle_btn = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            icon_color="blue",
            tooltip="Yeni Birim Ekle",
            on_click=yeni_birim_dialog_ac
        )

        miktar_birim_satiri = ft.Row(
            [gider_miktar, gider_birim_secimi, birim_ekle_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        gider_birim_fiyat = ft.TextField(label="Birim Fiyat (TL)", width=155, dense=True, keyboard_type=ft.KeyboardType.NUMBER)
        gider_toplam_tutar = ft.TextField(label="Toplam Tutar (TL)", width=155, dense=True, keyboard_type=ft.KeyboardType.NUMBER)

        # 3'lü Dinamik Hesaplama
        hesaplaniyor = [False]
        kullanici_girdileri = []

        def kayit_ekle(alan):
            if alan in kullanici_girdileri:
                kullanici_girdileri.remove(alan)
            kullanici_girdileri.append(alan)

        def kayit_sil(alan):
            if alan in kullanici_girdileri:
                kullanici_girdileri.remove(alan)

        def sayi_formatla(val):
            if val == int(val):
                return str(int(val))
            formatted = f"{val:.2f}"
            return formatted.rstrip("0").rstrip(".") if formatted.endswith("0") else formatted

        def float_al(val_str):
            if not val_str:
                return None
            try:
                return float(val_str.strip().replace(",", "."))
            except ValueError:
                return None

        def hesapla_ve_guncelle(tetikleyen_alan):
            if hesaplaniyor[0]:
                return

            m_val = float_al(gider_miktar.value)
            bf_val = float_al(gider_birim_fiyat.value)
            t_val = float_al(gider_toplam_tutar.value)

            if m_val is None:
                kayit_sil("M")
            if bf_val is None:
                kayit_sil("BF")
            if t_val is None:
                kayit_sil("T")

            if tetikleyen_alan == "M" and m_val is not None:
                kayit_ekle("M")
            elif tetikleyen_alan == "BF" and bf_val is not None:
                kayit_ekle("BF")
            elif tetikleyen_alan == "T" and t_val is not None:
                kayit_ekle("T")

            if len(kullanici_girdileri) >= 2:
                aktif_1 = kullanici_girdileri[-1]
                aktif_2 = kullanici_girdileri[-2]

                girdi_kumesi = {aktif_1, aktif_2}
                kalan_hedef = list({"M", "BF", "T"} - girdi_kumesi)[0]

                hesaplaniyor[0] = True
                try:
                    if kalan_hedef == "T":
                        if m_val is not None and bf_val is not None:
                            gider_toplam_tutar.value = f"{m_val * bf_val:.2f}"
                    elif kalan_hedef == "M":
                        if t_val is not None and bf_val is not None and bf_val > 0:
                            gider_miktar.value = sayi_formatla(t_val / bf_val)
                    elif kalan_hedef == "BF":
                        if t_val is not None and m_val is not None and m_val > 0:
                            gider_birim_fiyat.value = f"{t_val / m_val:.2f}"
                finally:
                    hesaplaniyor[0] = False
                page.update()

        gider_miktar.on_change = lambda e: hesapla_ve_guncelle("M")
        gider_birim_fiyat.on_change = lambda e: hesapla_ve_guncelle("BF")
        gider_toplam_tutar.on_change = lambda e: hesapla_ve_guncelle("T")

        fiyat_satiri = ft.Row([gider_birim_fiyat, gider_toplam_tutar], alignment=ft.MainAxisAlignment.CENTER)

        gider_form_kutusu = ft.Column([
            ft.Text("Tarih ve Saat:", size=12, color="grey"),
            gider_tarih_saat_satiri,
            gider_firma,
            gider_urun,
            gider_kategori,
            miktar_birim_satiri,
            fiyat_satiri
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # --- PARA AKTARIMI ALANLARI ---
        aktarim_alici = make_dropdown(
            label="Kime Para Aktarılacak?",
            options=["Aile Üyesi", "Ahmet", "Ayşe", "Mehmet", "Diğer"],
            value="Aile Üyesi",
            width=320,
            dense=True
        )
        aktarim_tutari = ft.TextField(label="Aktarılan Tutar (TL)", width=320, dense=True, keyboard_type=ft.KeyboardType.NUMBER)
        aktarim_aciklamasi = ft.TextField(label="Açıklama (Örn: Haftalık harçlık, pazar bütçesi)", width=320, dense=True)

        aktarim_form_kutusu = ft.Column([
            ft.Text("Para Aktarımı Tarihi:", size=12, color="grey"),
            aktarim_tarih_btn,
            aktarim_alici,
            aktarim_tutari,
            aktarim_aciklamasi
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        dinamik_form_alani = ft.Container(content=gider_form_kutusu)

        def islem_turu_degisti(e):
            secim = e.control.value if hasattr(e, "control") and e.control else islem_turu.value
            if secim == "Gelir":
                dinamik_form_alani.content = gelir_form_kutusu
            elif secim == "Para Aktarımı":
                dinamik_form_alani.content = aktarim_form_kutusu
            else:
                dinamik_form_alani.content = gider_form_kutusu
            page.update()

        tur_secenekleri = ["Gider", "Gelir", "Para Aktarımı"] if yonetici_mi else ["Gider"]
        islem_turu = make_dropdown(
            options=tur_secenekleri,
            value="Gider",
            width=320,
            on_change=islem_turu_degisti
        )

        # --- MODERN DASHBOARD KARTI & BİLEŞENLERİ ---
        kasa_baslik_metni = ft.Text("ELDEKİ TOPLAM PARA (KASA)", size=10, weight=ft.FontWeight.BOLD, color="#94a3b8")
        kasa_tutar_metni = ft.Text("0,00 TL", size=24, weight=ft.FontWeight.BOLD, color="white")

        bu_ay_gelir_txt = ft.Text("+0,00 TL", size=12, weight=ft.FontWeight.BOLD, color="#10b981")
        bu_ay_gider_txt = ft.Text("-0,00 TL", size=12, weight=ft.FontWeight.BOLD, color="#f87171")
        bu_ay_fark_txt = ft.Text("0,00 TL", size=12, weight=ft.FontWeight.BOLD, color="#38bdf8")

        uye_cuzdan_metni = ft.Text("", size=11, color="#cbd5e1")

        bakiye_karti = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        kasa_baslik_metni,
                        kasa_tutar_metni
                    ], spacing=2),
                    ft.Container(
                        content=ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET_ROUNDED, color="#38bdf8", size=28),
                        bgcolor="#1e293b",
                        border_radius=12,
                        padding=8
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=14, color="#334155"),
                ft.Row([
                    ft.Column([
                        ft.Text("Bu Ay Gelir", size=10, color="#94a3b8"),
                        bu_ay_gelir_txt
                    ], spacing=1),
                    ft.Column([
                        ft.Text("Bu Ay Gider", size=10, color="#94a3b8"),
                        bu_ay_gider_txt
                    ], spacing=1),
                    ft.Column([
                        ft.Text("Aylık Net Fark", size=10, color="#94a3b8"),
                        bu_ay_fark_txt
                    ], spacing=1),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                uye_cuzdan_metni
            ], spacing=2),
            bgcolor="#0f172a",
            border_radius=16,
            padding=16,
            width=360,
        )

        bakiye_metni = ft.Text("", visible=False)
        donem_metni = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="blue")
        liste_arayuzu = ft.ListView(height=420, spacing=2)
        bilgi_mesaji = ft.Text("", size=12)

        # --- FİLTRELEME BUTONLARI (Tümü / Gelirler / Giderler) ---
        secilen_filtre = ["Tümü"]

        def filtre_sec(f_adi):
            secilen_filtre[0] = f_adi
            filtre_butonlari_guncelle()
            arayuzu_guncelle()

        filtre_tumu_btn = ft.Container(
            content=ft.Text("Tümü", size=11, weight=ft.FontWeight.BOLD, color="white"),
            bgcolor="#2563eb",
            border_radius=20,
            padding=make_padding(12, 6),
            on_click=lambda _: filtre_sec("Tümü")
        )
        filtre_gelir_btn = ft.Container(
            content=ft.Text("🟢 Gelirler", size=11, weight=ft.FontWeight.BOLD, color="#64748b"),
            bgcolor="#f1f5f9",
            border_radius=20,
            padding=make_padding(12, 6),
            on_click=lambda _: filtre_sec("Gelir")
        )
        filtre_gider_btn = ft.Container(
            content=ft.Text("🔴 Giderler", size=11, weight=ft.FontWeight.BOLD, color="#64748b"),
            bgcolor="#f1f5f9",
            border_radius=20,
            padding=make_padding(12, 6),
            on_click=lambda _: filtre_sec("Gider")
        )

        def filtre_butonlari_guncelle():
            f = secilen_filtre[0]
            filtre_tumu_btn.bgcolor = "#2563eb" if f == "Tümü" else "#f1f5f9"
            filtre_tumu_btn.content.color = "white" if f == "Tümü" else "#64748b"

            filtre_gelir_btn.bgcolor = "#10b981" if f == "Gelir" else "#f1f5f9"
            filtre_gelir_btn.content.color = "white" if f == "Gelir" else "#047857"

            filtre_gider_btn.bgcolor = "#ef4444" if f == "Gider" else "#f1f5f9"
            filtre_gider_btn.content.color = "white" if f == "Gider" else "#b91c1c"
            try:
                filtre_tumu_btn.update()
                filtre_gelir_btn.update()
                filtre_gider_btn.update()
            except Exception:
                pass

        filtre_bari = ft.Container(
            content=ft.Row([
                filtre_tumu_btn,
                filtre_gelir_btn,
                filtre_gider_btn
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
            padding=make_padding(0, 4)
        )

        # --- KATEGORİ FİLTRELEME ---
        secilen_kategori = ["Tüm Kategoriler"]

        kategori_filtre_listesi = [
            "Tüm Kategoriler",
            "Market & Temel Gıda",
            "Ev & Faturalar",
            "Sağlık",
            "Eğitim & Okul",
            "Giyim",
            "Sigara/Tütün",
            "Temizlik",
            "Abur Cubur & Atıştırmalık",
            "Dışarıda Yemek / Eğlence",
            "Ulaşım",
            "Ulaşım / Spor & Hobi",
            "Transfer / Birikim",
            "Borç / Kredi Kartı",
            "Maaş",
            "Ödenek",
            "Ek Ders",
            "Yatırım",
            "Yatırım / Altın",
            "Aile / Harçlık",
            "Aile / Yardımlaşma",
            "Aile / Diğer Gelir",
            "Devir / Nakit",
            "Kişisel Bakım & Kozmetik",
            "Evcil Hayvan (Pamuk)",
            "Elektronik & Diğer",
            "Yardım",
            "Diğer"
        ]

        def kategori_filtre_degisti(e):
            secilen_kategori[0] = kategori_filtre_dropdown.value or "Tüm Kategoriler"
            arayuzu_guncelle()

        def kategori_filtre_sifirla(e=None):
            secilen_kategori[0] = "Tüm Kategoriler"
            kategori_filtre_dropdown.value = "Tüm Kategoriler"
            try:
                kategori_filtre_dropdown.update()
            except Exception:
                pass
            arayuzu_guncelle()

        kategori_filtre_dropdown = make_dropdown(
            options=kategori_filtre_listesi,
            value="Tüm Kategoriler",
            width=285,
            dense=True,
            on_change=kategori_filtre_degisti
        )

        kategori_filtre_bari = ft.Container(
            content=ft.Row([
                kategori_filtre_dropdown,
                ft.IconButton(
                    icon=ft.Icons.CLEAR_ROUNDED,
                    icon_size=18,
                    tooltip="Kategori Filtresini Sıfırla",
                    on_click=kategori_filtre_sifirla
                )
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),
            padding=make_padding(0, 2)
        )

        kategori_ozet_metni = ft.Container(
            content=ft.Text("", size=11.5, weight=ft.FontWeight.BOLD, color="#1e40af"),
            bgcolor="#eff6ff",
            border=make_border_all(1, "#bfdbfe"),
            border_radius=8,
            padding=make_padding(10, 5),
            visible=False,
            alignment=get_alignment_center(),
            width=360
        )

        # --- AÇILIR / KAPANIR İŞLEM EKLEME FORMU ---
        form_acik = [False]

        def form_toggle(e):
            form_acik[0] = not form_acik[0]
            form_govdesi.visible = form_acik[0]
            set_button_label(form_ac_kapat_btn, "✕ Formu Kapat" if form_acik[0] else "➕ Yeni İşlem Ekle")
            form_ac_kapat_btn.bgcolor = "#64748b" if form_acik[0] else "#2563eb"
            liste_arayuzu.height = 240 if form_acik[0] else 420
            try:
                form_govdesi.update()
                form_ac_kapat_btn.update()
                liste_arayuzu.update()
            except Exception:
                page.update()

        form_ac_kapat_btn = make_button("➕ Yeni İşlem Ekle", bgcolor="#2563eb", color="white", height=36, on_click=form_toggle)

        form_govdesi = ft.Container(
            content=ft.Column([
                ft.Container(height=4),
                islem_turu,
                dinamik_form_alani,
                bilgi_mesaji,
                make_button("İşlemi Kaydet", icon=ft.Icons.SAVE, bgcolor="green", color="white", width=320, height=40, on_click=lambda e: islem_kaydet(e)),
                ft.Container(height=4),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            visible=False,
            bgcolor="#f8fafc",
            border_radius=12,
            border=make_border_all(1, "#e2e8f0"),
            padding=10,
            width=360
        )

        # --- ONAYLI İŞLEM SİLME ---
        def islem_sil(item):
            target_id = item.get("id")
            if supabase and target_id:
                try:
                    supabase.table("islemler").delete().eq("id", target_id).execute()
                except Exception as ex:
                    print("Buluttan silme hatası:", ex)

            # Hem ID, hem referans, hem de içerik üzerinden garantili bellek silme
            silindi = False
            if target_id is not None:
                for idx, it in enumerate(islemler):
                    if it.get("id") == target_id:
                        islemler.pop(idx)
                        silindi = True
                        break

            if not silindi:
                for idx, it in enumerate(islemler):
                    if it is item:
                        islemler.pop(idx)
                        silindi = True
                        break

            if not silindi and item in islemler:
                islemler.remove(item)
                silindi = True

            if not silindi:
                for idx, it in enumerate(islemler):
                    if (it.get("tarih") == item.get("tarih") and
                        str(it.get("tutar")) == str(item.get("tutar")) and
                        (it.get("urun") == item.get("urun") or it.get("aciklama") == item.get("aciklama"))):
                        islemler.pop(idx)
                        silindi = True
                        break

            bilgi_mesaji.value = "🗑️ İşlem başarıyla silindi!"
            bilgi_mesaji.color = "blue"
            arayuzu_guncelle()

        def silme_onayi_iste(item):
            aciklama_metni = item.get("urun") or item.get("aciklama") or item.get("kaynak") or "İşlem"
            tutar_goster = f"{float(item.get('tutar') or 0):,.2f} TL"

            def onaylandi(ev):
                picker_kapat(onay_dialog)
                islem_sil(item)

            onay_dialog = ft.AlertDialog(
                title=ft.Text("İşlemi Sil"),
                content=ft.Column([
                    ft.Text("Bu işlemi silmek istediğinizden emin misiniz?"),
                    ft.Text(f"• Tür: {item.get('tur')}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"• Detay: {aciklama_metni}"),
                    ft.Text(f"• Tutar: {tutar_goster}", color="red")
                ], tight=True),
                actions=[
                    make_button("İptal", outlined=True, on_click=lambda _: picker_kapat(onay_dialog)),
                    make_button("Evet, Sil", bgcolor="red", color="white", on_click=onaylandi),
                ]
            )
            picker_ac(onay_dialog)

        # --- TOPLU İŞLEM SİLME VE ONAY MEKANİZMASI ---
        def toplu_silme_onayi_iste(e=None):
            bas_str = secilen_donem_bas[0].strftime("%d.%m.%Y")
            bit_str = secilen_donem_bit[0].strftime("%d.%m.%Y")

            kapsam_options = [
                f"Seçili Dönem ({bas_str} - {bit_str})",
                "Tüm Dönemler (Bütün Geçmiş)"
            ]
            tur_options = [
                "Tüm Türler (Gelir + Gider + Aktarım)",
                "Sadece Giderler",
                "Sadece Gelirler",
                "Sadece Para Aktarımları"
            ]

            sayac_metni = ft.Text("", size=13, weight=ft.FontWeight.BOLD, color="red")
            uyari_metni = ft.Text(
                "⚠️ Bu işlem geri alınamaz! Supabase bulut veritabanından da silinecektir.",
                size=12,
                color="red"
            )

            def silinecekleri_bul():
                hedef_liste = []
                is_donem = (kapsam_secimi.value == kapsam_options[0])
                tur_val = tur_secimi.value

                for it in islemler:
                    if is_donem:
                        t_date = stringden_tarih_al(it.get("tarih"))
                        if not t_date or not (secilen_donem_bas[0] <= t_date <= secilen_donem_bit[0]):
                            continue
                    t_tur = it.get("tur")
                    if tur_val == "Sadece Giderler" and t_tur != "Gider":
                        continue
                    if tur_val == "Sadece Gelirler" and t_tur != "Gelir":
                        continue
                    if tur_val == "Sadece Para Aktarımları" and t_tur != "Para Aktarımı":
                        continue
                    hedef_liste.append(it)
                return hedef_liste

            def sayaci_guncelle(ev=None):
                bulunanlar = silinecekleri_bul()
                sayac_metni.value = f"🗑️ Silinecek İşlem Sayısı: {len(bulunanlar)} adet"
                try:
                    sayac_metni.update()
                except Exception:
                    pass
                try:
                    page.update()
                except Exception:
                    pass

            kapsam_secimi = make_dropdown(
                label="Silme Kapsamı",
                options=kapsam_options,
                value=kapsam_options[0],
                width=320,
                on_change=sayaci_guncelle
            )

            tur_secimi = make_dropdown(
                label="İşlem Türü",
                options=tur_options,
                value=tur_options[0],
                width=320,
                on_change=sayaci_guncelle
            )

            onay_kutusu = ft.Checkbox(
                label="Seçilen verileri kalıcı olarak silmeyi onaylıyorum.",
                value=False
            )

            def toplu_sil_onaylandi(ev):
                if not onay_kutusu.value:
                    uyari_metni.value = "⚠️ Lütfen silme işlemini onaylamak için kutucuğu işaretleyin!"
                    uyari_metni.weight = ft.FontWeight.BOLD
                    try:
                        uyari_metni.update()
                    except Exception:
                        pass
                    page.update()
                    return

                silinecek_kayitlar = silinecekleri_bul()
                if not silinecek_kayitlar:
                    picker_kapat(toplu_dialog)
                    bilgi_mesaji.value = "⚠️ Seçilen kriterlere uygun silinecek kayıt bulunamadı."
                    bilgi_mesaji.color = "orange"
                    page.update()
                    return

                # Supabase bulut veritabanından toplu silme
                ids_to_del = [it["id"] for it in silinecek_kayitlar if it.get("id")]
                if supabase and ids_to_del:
                    for i in range(0, len(ids_to_del), 50):
                        chunk = ids_to_del[i:i + 50]
                        try:
                            supabase.table("islemler").delete().in_("id", chunk).execute()
                        except Exception as ex:
                            print("Buluttan toplu silme hatası:", ex)

                # Yerel bellekten garantili toplu silme
                silinecek_idler = {it.get("id") for it in silinecek_kayitlar if it.get("id")}
                islemler[:] = [it for it in islemler if (it.get("id") not in silinecek_idler if it.get("id") else it not in silinecek_kayitlar)]

                picker_kapat(toplu_dialog)
                bilgi_mesaji.value = f"🗑️ {len(silinecek_kayitlar)} adet kayıt başarıyla silindi!"
                bilgi_mesaji.color = "blue"
                arayuzu_guncelle()

            toplu_dialog = ft.AlertDialog(
                title=ft.Text("🗑️ Toplu İşlem Silme"),
                content=ft.Column([
                    ft.Text("Aşağıdaki kriterlere uyan kayıtları topluca silebilirsiniz:"),
                    ft.Container(height=4),
                    kapsam_secimi,
                    tur_secimi,
                    sayac_metni,
                    ft.Divider(height=10),
                    uyari_metni,
                    onay_kutusu
                ], tight=True, spacing=8),
                actions=[
                    make_button("Vazgeç", outlined=True, on_click=lambda _: picker_kapat(toplu_dialog)),
                    make_button("Evet, Kalıcı Olarak Sil", bgcolor="red", color="white", on_click=toplu_sil_onaylandi)
                ]
            )

            sayaci_guncelle()
            picker_ac(toplu_dialog)

        # ======================================================================
        # CSV YARDIMCI VE DÖNÜŞTÜRÜCÜ FONKSİYONLAR
        # ======================================================================
        def parse_turk_tutari(val_str):
            if not val_str:
                return 0.0
            s = str(val_str).strip().replace('"', '').replace("'", "")
            if not s:
                return 0.0
            if "." in s and "," in s:
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            try:
                return float(s)
            except ValueError:
                return 0.0

        def format_turk_para(val_float):
            """Sayıyı Türk Lirası CSV formatına çevirir (1586.4 -> '1.586,40')."""
            try:
                f = float(val_float or 0.0)
                tam = int(abs(f))
                ondalik = int(round((abs(f) - tam) * 100))
                tam_str = f"{tam:,}".replace(",", ".")
                isaret = "-" if f < 0 else ""
                return f"{isaret}{tam_str},{ondalik:02d}"
            except Exception:
                return "0,00"

        def parse_tarih_saat(val_str):
            s = str(val_str).strip()
            if " " in s:
                parcalar = s.split(" ", 1)
                return parcalar[0].strip(), parcalar[1].strip()
            return s, ""

        def miktar_birlestir(m1_str, m2_str):
            m1_str = str(m1_str or "").strip()
            m2_str = str(m2_str or "").strip()
            if not m1_str:
                return m2_str
            if not m2_str:
                return m1_str

            q1_m = re.match(r"^([0-9.,]+)\s*(.*)$", m1_str)
            q2_m = re.match(r"^([0-9.,]+)\s*(.*)$", m2_str)

            if q1_m and q2_m:
                u1 = q1_m.group(2).strip()
                u2 = q2_m.group(2).strip()
                if u1.lower() == u2.lower() or not u1 or not u2:
                    unit = u1 or u2
                    v1_str = q1_m.group(1).replace(",", ".")
                    v2_str = q2_m.group(1).replace(",", ".")
                    try:
                        total_val = float(v1_str) + float(v2_str)
                        if total_val == int(total_val):
                            formatted_val = str(int(total_val))
                        else:
                            formatted_val = f"{total_val:.3f}".rstrip("0").rstrip(".")
                        return f"{formatted_val} {unit}".strip()
                    except Exception:
                        pass

            return f"{m1_str} + {m2_str}".strip()

        def csv_icerigini_yukle(file_path):
            try:
                content = None
                for enc in ["utf-8-sig", "utf-8", "cp1254", "latin1"]:
                    try:
                        with open(file_path, "r", encoding=enc) as f:
                            content = f.read()
                        break
                    except Exception:
                        continue

                if not content:
                    bilgi_mesaji.value = "⚠️ CSV dosyası okunamadı."
                    bilgi_mesaji.color = "red"
                    page.update()
                    return

                lines_content = [line.strip() for line in content.splitlines() if line.strip()]
                if not lines_content:
                    return

                delim = ";" if ";" in lines_content[0] else ","
                reader = csv.reader(lines_content, delimiter=delim)
                header = [h.strip().lower() for h in next(reader, [])]

                en_son_tarih = None
                ham_kayitlar = []

                for row in reader:
                    if not row or len(row) < 2:
                        continue

                    tarih_ham = row[0].strip() if len(row) > 0 else ""
                    t_str, s_str = parse_tarih_saat(tarih_ham)

                    t_date = stringden_tarih_al(t_str)
                    if t_date:
                        en_son_tarih = t_date

                    if len(row) == 5:
                        firma_str = row[1].strip()
                        urun_str = row[2].strip()
                        kategori_str = row[3].strip()
                        miktar_str = ""
                        birim_fiyat_str = ""
                        tutar_str = row[4].strip()
                    else:
                        firma_str = row[1].strip() if len(row) > 1 else ""
                        urun_str = row[2].strip() if len(row) > 2 else ""
                        kategori_str = row[3].strip() if len(row) > 3 else "Diğer"
                        miktar_str = row[4].strip() if len(row) > 4 else ""
                        birim_fiyat_str = row[5].strip().replace("\"", "") if len(row) > 5 else ""
                        tutar_str = row[6].strip() if len(row) > 6 else (row[1].strip() if len(row) == 2 else "0")

                    tutar_float = parse_turk_tutari(tutar_str)

                    tur_turu = "Gider"
                    is_gelir_ipucu = any("kaynak" in h for h in header) or any(k in kategori_str.lower() for k in ["maaş", "ödenek", "ek ders", "gelir", "devir"])
                    if is_gelir_ipucu:
                        tur_turu = "Gelir"
                    elif "transfer" in kategori_str.lower() or "birikim" in kategori_str.lower():
                        tur_turu = "Para Aktarımı"

                    kayit = {
                        "kullanici": kullanici,
                        "tur": tur_turu,
                        "tarih": t_str or datetime.date.today().strftime("%d.%m.%Y"),
                        "saat": s_str or datetime.datetime.now().strftime("%H:%M"),
                        "kaynak": firma_str if tur_turu in ["Para Aktarımı", "Gelir"] else "",
                        "gelir_turu": kategori_str if tur_turu == "Gelir" else "",
                        "aciklama": urun_str,
                        "firma": firma_str if tur_turu == "Gider" else "",
                        "urun": urun_str if tur_turu == "Gider" else "",
                        "kategori": kategori_str if tur_turu == "Gider" else "",
                        "miktar": miktar_str,
                        "birim_fiyat": birim_fiyat_str,
                        "tutar": tutar_float
                    }
                    ham_kayitlar.append(kayit)

                # 1. Birebir Aynı Olan Mükerrer Kayıtları Birleştirme (Fiş İçi Toplama)
                birlestirilmis_kayitlar = []
                birlestirme_haritasi = {}
                birlestirilen_sayisi = 0

                for k in ham_kayitlar:
                    merge_key = (
                        k["tarih"].strip(),
                        k["saat"].strip(),
                        k["tur"].strip(),
                        k["firma"].strip().lower(),
                        k["urun"].strip().lower(),
                        k["kategori"].strip().lower(),
                        k["kaynak"].strip().lower(),
                        k["birim_fiyat"].strip()
                    )
                    if merge_key in birlestirme_haritasi:
                        mevcut = birlestirme_haritasi[merge_key]
                        mevcut["tutar"] += k["tutar"]
                        mevcut["miktar"] = miktar_birlestir(mevcut["miktar"], k["miktar"])
                        birlestirilen_sayisi += 1
                    else:
                        birlestirme_haritasi[merge_key] = k
                        birlestirilmis_kayitlar.append(k)

                # 2. Veritabanında Zaten Var Olan Kayıtları Ayıklama (Çift Yükleme Koruması)
                mevcut_kayitlar_seti = set()
                for it in islemler:
                    m_key = (
                        it.get("tarih", "").strip(),
                        it.get("saat", "").strip(),
                        it.get("tur", "").strip(),
                        (it.get("firma") or it.get("kaynak") or "").strip().lower(),
                        (it.get("urun") or it.get("aciklama") or "").strip().lower(),
                        round(float(it.get("tutar") or 0.0), 2)
                    )
                    mevcut_kayitlar_seti.add(m_key)

                yeni_eklenenler = []
                for k in birlestirilmis_kayitlar:
                    m_key = (
                        k["tarih"].strip(),
                        k["saat"].strip(),
                        k["tur"].strip(),
                        (k["firma"] or k["kaynak"]).strip().lower(),
                        (k["urun"] or k["aciklama"]).strip().lower(),
                        round(float(k["tutar"]), 2)
                    )
                    if m_key not in mevcut_kayitlar_seti:
                        yeni_eklenenler.append(k)
                        mevcut_kayitlar_seti.add(m_key)

                if not yeni_eklenenler:
                    bilgi_mesaji.value = f"ℹ️ Yüklenen dosyadaki tüm kayıtlar ({len(birlestirilmis_kayitlar)} adet) zaten sistemde kayıtlı."
                    bilgi_mesaji.color = "blue"
                    page.update()
                    return

                if supabase and yeni_eklenenler:
                    try:
                        chunk_size = 50
                        for i in range(0, len(yeni_eklenenler), chunk_size):
                            chunk = yeni_eklenenler[i:i + chunk_size]
                            res = supabase.table("islemler").insert(chunk).execute()
                            if res.data:
                                for idx, item_res in enumerate(res.data):
                                    chunk[idx]["id"] = item_res.get("id")
                    except Exception as ex:
                        print("CSV Supabase toplu kayıt hatası:", ex)

                for k in reversed(yeni_eklenenler):
                    islemler.insert(0, k)

                if en_son_tarih:
                    csv_bas, csv_bit = aktif_butce_donemini_bul(en_son_tarih)
                    secilen_donem_bas[0] = csv_bas
                    secilen_donem_bit[0] = csv_bit
                    tum_zamanlar_modu[0] = False

                ek_bilgi = f" ({birlestirilen_sayisi} mükerrer kayıt birleştirildi)" if birlestirilen_sayisi > 0 else ""
                bilgi_mesaji.value = f"✅ CSV\x27den {len(yeni_eklenenler)} işlem başarıyla yüklendi!{ek_bilgi}"
                bilgi_mesaji.color = "green"
                arayuzu_guncelle()

            except Exception as e:
                bilgi_mesaji.value = f"⚠️ CSV aktarım hatası: {str(e)[:45]}"
                bilgi_mesaji.color = "red"
                page.update()

        
        # --- AI FİŞ TARAMA İŞLEMCİSİ (Android + Masaüstü Tam Uyumlu) ---
        def fis_gorselini_tara_ve_goster(dosya_yolu):
            if not dosya_yolu:
                return

            iptal_edildi = [False]
            durum_metni = ft.Text("Görsel hazırlanıyor...", size=12, color="#475569")

            def yukleme_iptal(ev):
                iptal_edildi[0] = True
                close_app_dialog(page, yukleniyor_dialog)
                show_app_snackbar(page, "Fiş tarama işlemi iptal edildi.", color="#64748b")

            yukleniyor_dialog = ft.AlertDialog(
                content=ft.Container(
                    content=ft.Row([
                        ft.ProgressRing(width=28, height=28, stroke_width=3),
                        ft.Container(width=12),
                        ft.Column([
                            ft.Text("Fiş / Fatura Taranıyor...", weight=ft.FontWeight.BOLD, size=14),
                            durum_metni
                        ], spacing=2)
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=15,
                    width=320,
                    height=75
                ),
                actions=[
                    make_button("✕ İptal", outlined=True, height=32, on_click=yukleme_iptal)
                ],
                modal=False
            )
            show_app_dialog(page, yukleniyor_dialog)

            def status_guncelle(yeni_durum):
                if not iptal_edildi[0]:
                    durum_metni.value = yeni_durum
                    try:
                        page.update()
                    except Exception:
                        pass

            import threading

            def arka_plan_tara():
                try:
                    sonuc = gemini_fis_analiz_et(dosya_yolu, status_cb=status_guncelle)

                    if iptal_edildi[0]:
                        return

                    close_app_dialog(page, yukleniyor_dialog)

                    if not sonuc or "hata" in sonuc:
                        hata_msj = sonuc.get("hata", "Bilinmeyen hata") if sonuc else "Yanıt alınamadı"
                        hata_dialog = ft.AlertDialog(
                            title=ft.Text("⚠️ Fiş Okunamadı", size=15, weight=ft.FontWeight.BOLD, color="#b91c1c"),
                            content=ft.Container(
                                content=ft.Text(f"Hata Detayı:\n{hata_msj}", size=12),
                                width=320
                            ),
                            actions=[
                                make_button("Tamam", outlined=True, on_click=lambda _: close_app_dialog(page, hata_dialog))
                            ]
                        )
                        show_app_dialog(page, hata_dialog)
                        return

                    firma = sonuc.get("firma") or "Market"
                    tarih = sonuc.get("tarih") or datetime.date.today().strftime("%d.%m.%Y")
                    saat = sonuc.get("saat") or datetime.datetime.now().strftime("%H:%M")
                    urunler = sonuc.get("urunler") or []
                    toplam_tutar = float(sonuc.get("toplam_tutar") or 0.0)

                    if not urunler:
                        show_app_snackbar(page, "⚠️ Fişte herhangi bir ürün kalemi tespit edilemedi.", color="#f59e0b")
                        return

                    onay_listesi = []
                    secim_kontrolleri = []

                    for idx, u in enumerate(urunler):
                        u_adi = u.get("urun") or f"Ürün {idx+1}"
                        u_miktar = u.get("miktar") or "1 Adet"
                        u_fiyat = float(u.get("birim_fiyat") or u.get("tutar") or 0.0)
                        u_tutar = float(u.get("tutar") or u_fiyat)
                        u_kat = u.get("kategori") or "Market & Temel Gıda"
                        if u_kat not in GIDER_KATEGORILERI:
                            u_kat = "Market & Temel Gıda"

                        chk = ft.Checkbox(value=True, label=f"{u_adi} ({u_miktar}) - {u_tutar:,.2f} TL")
                        onay_listesi.append({
                            "chk": chk,
                            "urun": u_adi,
                            "miktar": u_miktar,
                            "birim_fiyat": u_fiyat,
                            "tutar": u_tutar,
                            "kategori": u_kat
                        })
                        secim_kontrolleri.append(chk)

                    def dialog_kapat(ev):
                        close_app_dialog(page, fis_dialog)

                    def secilenleri_ekle(ev):
                        eklenen_sayisi = 0
                        eklenen_tutar = 0.0
                        simdi_ts = int(datetime.datetime.now().timestamp() * 1000)

                        std_tarih = standart_tarih_yap(tarih)
                        fis_date_obj = stringden_tarih_al(std_tarih)

                        if fis_date_obj:
                            if not (secilen_donem_bas[0] <= fis_date_obj <= secilen_donem_bit[0]):
                                p_bas, p_bit = aktif_butce_donemini_bul(fis_date_obj)
                                secilen_donem_bas[0] = p_bas
                                secilen_donem_bit[0] = p_bit
                                tum_zamanlar_modu[0] = False

                        for item_idx, itm in enumerate(onay_listesi):
                            if itm["chk"].value:
                                yeni_id = str(simdi_ts + item_idx)
                                yeni_kayit = {
                                    "id": yeni_id,
                                    "kullanici": kullanici,
                                    "tur": "Gider",
                                    "tarih": std_tarih,
                                    "saat": saat,
                                    "kaynak": "",
                                    "gelir_turu": "",
                                    "aciklama": f"AI Fiş ({firma})",
                                    "firma": firma,
                                    "urun": itm["urun"],
                                    "kategori": itm["kategori"],
                                    "miktar": itm["miktar"],
                                    "birim_fiyat": itm["birim_fiyat"],
                                    "tutar": itm["tutar"]
                                }

                                if supabase:
                                    try:
                                        supabase.table("islemler").insert(yeni_kayit).execute()
                                    except Exception as db_err:
                                        print("Supabase kayıt hatası:", db_err)

                                islemler.append(yeni_kayit)
                                eklenen_sayisi += 1
                                eklenen_tutar += itm["tutar"]

                        dialog_kapat(None)

                        secilen_filtre[0] = "Tümü"
                        secilen_kategori[0] = "Tüm Kategoriler"
                        if hasattr(kategori_filtre_dropdown, "value"):
                            kategori_filtre_dropdown.value = "Tüm Kategoriler"

                        arayuzu_guncelle()

                        show_app_snackbar(
                            page,
                            f"✅ {firma} fişinden {eklenen_sayisi} kalem harcama ({eklenen_tutar:,.2f} TL) bütçeye eklendi!",
                            color="#16a34a"
                        )

                    fis_dialog = ft.AlertDialog(
                        title=ft.Text(f"📸 {firma} ({tarih})", size=16, weight=ft.FontWeight.BOLD),
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(f"Toplam: {toplam_tutar:,.2f} TL • {len(urunler)} Kalem Tespit Edildi", size=12, color="#475569", weight=ft.FontWeight.W_500),
                                ft.Text("Eklemek istediğiniz ürünleri seçin:", size=11, color="grey"),
                                ft.Container(
                                    content=ft.Column(secim_kontrolleri, scroll=ft.ScrollMode.AUTO, spacing=2),
                                    height=220,
                                    border=make_border_all(1, "#e2e8f0"),
                                    border_radius=8,
                                    padding=4
                                )
                            ], spacing=6),
                            width=330,
                            height=280
                        ),
                        actions=[
                            make_button("İptal", outlined=True, on_click=dialog_kapat),
                            make_button("✅ Bütçeye Ekle", bgcolor="#16a34a", color="white", on_click=secilenleri_ekle)
                        ],
                        actions_alignment=ft.MainAxisAlignment.END
                    )

                    show_app_dialog(page, fis_dialog)

                except Exception as th_err:
                    print("Arka plan tarama hatası:", th_err)
                    close_app_dialog(page, yukleniyor_dialog)
                    show_app_snackbar(page, f"Tarama sırasında beklenmeyen hata: {th_err}", color="#ef4444")

            threading.Thread(target=arka_plan_tara, daemon=True).start()

        # Android & Mobil için FilePicker Tanımı
        def mobil_dosya_secildi(e):
            if e.files and len(e.files) > 0:
                secilen_dosya = e.files[0].path
                if secilen_dosya:
                    fis_gorselini_tara_ve_goster(secilen_dosya)

        mobil_file_picker = ft.FilePicker(on_result=mobil_dosya_secildi)
        if hasattr(page, "overlay"):
            page.overlay.append(mobil_file_picker)
            try:
                page.update()
            except Exception:
                pass

        def fis_tara_tiklandi(e):
            # 1. Önce mobil / Android ortamı kontrol et (tkinter yoksa FilePicker aç)
            mobil_mi = False
            try:
                import tkinter as tk
                from tkinter import filedialog
            except Exception:
                mobil_mi = True

            if mobil_mi:
                try:
                    mobil_file_picker.pick_files(
                        dialog_title="Fiş / Fatura Fotoğrafı Seçin",
                        file_type=ft.FilePickerFileType.IMAGE,
                        allowed_extensions=["jpg", "jpeg", "png", "webp", "pdf", "heic"]
                    )
                    return
                except Exception as ex_mob:
                    print("Mobil dosya seçici hatası:", ex_mob)

            # 2. Masaüstü (Windows / Mac) ortamı için Tkinter dosya seçici
            dosya_yolu = None
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                dosya_yolu = filedialog.askopenfilename(
                    title="Fiş / Fatura Görseli veya PDF Seçin",
                    filetypes=[
                        ("Fiş ve Fatura Dosyaları", "*.jpg *.jpeg *.png *.webp *.bmp *.heic *.pdf"),
                        ("PDF Faturalar", "*.pdf"),
                        ("Resim Dosyaları", "*.jpg *.jpeg *.png *.webp *.bmp *.heic"),
                        ("Tüm Dosyalar", "*.*")
                    ]
                )
                root.destroy()
            except Exception as ex:
                # Masaüstünde tkinter başarısız olursa yine mobil filepicker dene
                try:
                    mobil_file_picker.pick_files(
                        dialog_title="Fiş / Fatura Fotoğrafı Seçin",
                        file_type=ft.FilePickerFileType.IMAGE
                    )
                    return
                except Exception:
                    show_app_snackbar(page, f"Dosya seçici açılamadı: {ex}", color="#ef4444")
                    return

            if dosya_yolu:
                fis_gorselini_tara_ve_goster(dosya_yolu)

        def csv_yukle_tiklandi(e):
            dosya_yolu = None
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                dosya_yolu = filedialog.askopenfilename(
                    title="Bütçe CSV Dosyasını Seçin",
                    filetypes=[("CSV Dosyaları", "*.csv"), ("Tüm Dosyalar", "*.*")]
                )
                root.destroy()
            except Exception as ex:
                print("Dosya seçici açılamadı:", ex)

            if dosya_yolu and os.path.exists(dosya_yolu):
                csv_icerigini_yukle(dosya_yolu)

        # CSV İndir / Dışa Aktar Butonu
        def csv_indir_tiklandi(e):
            dosya_yolu = None
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                t_bas = secilen_donem_bas[0].strftime("%d.%m.%Y")
                t_bit = secilen_donem_bit[0].strftime("%d.%m.%Y")
                varsayilan_isim = f"HaneButcesi_{t_bas}_{t_bit}.csv" if not tum_zamanlar_modu[0] else "HaneButcesi_TumKayitlar.csv"
                dosya_yolu = filedialog.asksaveasfilename(
                    title="Bütçe Verilerini CSV Olarak Kaydet",
                    defaultextension=".csv",
                    initialfile=varsayilan_isim,
                    filetypes=[("CSV Dosyası", "*.csv")]
                )
                root.destroy()
            except Exception as ex:
                print("Kaydetme penceresi hatası:", ex)

            if dosya_yolu:
                try:
                    with open(dosya_yolu, "w", encoding="utf-8-sig", newline="") as f:
                        writer = csv.writer(f, delimiter=",", quoting=csv.QUOTE_MINIMAL)
                        # Kullanıcının verdiği birebir aynı CSV başlığı
                        writer.writerow(["Tarih", "Firma/Kurum", "Ürün/Hizmet", "Kategori", "Miktar/Adet", "Birim Fiyat", "Toplam Tutar"])

                        # Aktif döneme göre filtrelenen veriler
                        for item in islemler:
                            t_date = stringden_tarih_al(item.get("tarih"))
                            if not tum_zamanlar_modu[0]:
                                if not t_date or not (secilen_donem_bas[0] <= t_date <= secilen_donem_bit[0]):
                                    continue

                            tarih_tam = f"{item.get('tarih', '')} {item.get('saat', '')}".strip()
                            firma = item.get("firma") or item.get("kaynak") or ""
                            urun = item.get("urun") or item.get("aciklama") or ""
                            kategori = item.get("kategori") or "Diğer"
                            miktar = item.get("miktar") or ""
                            birim_fiyat = item.get("birim_fiyat") or ""
                            toplam_tutar = format_turk_para(item.get("tutar") or 0.0)

                            writer.writerow([tarih_tam, firma, urun, kategori, miktar, birim_fiyat, toplam_tutar])

                    bilgi_mesaji.value = f"✅ Veriler CSV olarak kaydedildi:\n{os.path.basename(dosya_yolu)}"
                    bilgi_mesaji.color = "green"
                    page.update()
                except Exception as ex:
                    bilgi_mesaji.value = f"⚠️ CSV kaydetme hatası: {str(ex)[:45]}"
                    bilgi_mesaji.color = "red"
                    page.update()

        # --- DÖNEM DEĞİŞTİRME MANTIĞI ---
        def donem_kaydir(yon):
            y = secilen_donem_bas[0].year
            m = secilen_donem_bas[0].month
            if yon == "onceki":
                y_yeni, m_yeni = (y - 1, 12) if m == 1 else (y, m - 1)
            else:
                y_yeni, m_yeni = (y + 1, 1) if m == 12 else (y, m + 1)

            y_bit = y_yeni + 1 if m_yeni == 12 else y_yeni
            m_bit = 1 if m_yeni == 12 else m_yeni + 1

            secilen_donem_bas[0] = datetime.date(y_yeni, m_yeni, 15)
            secilen_donem_bit[0] = datetime.date(y_bit, m_bit, 14)
            tum_zamanlar_modu[0] = False
            arayuzu_guncelle()

        def tum_zamanlar_toggle(e):
            tum_zamanlar_modu[0] = not tum_zamanlar_modu[0]
            arayuzu_guncelle()

        # --- LİSTE HIZLI KAYDIRMA (EN BAŞA / EN SONA) ---
        def listeyi_basa_sar(e):
            try:
                liste_arayuzu.scroll_to(offset=0, duration=300)
            except Exception:
                pass

        def listeyi_sona_sar(e):
            try:
                liste_arayuzu.scroll_to(offset=-1, duration=300)
            except Exception:
                pass

        # --- KRONOLOJİK SIRALAMA YARDIMCISI ---
        def islem_siralama_anahtari(item):
            t_str = item.get("tarih") or "01.01.2000"
            s_str = item.get("saat") or "00:00"
            try:
                parts = t_str.split(".")
                y = int(parts[2])
                m = int(parts[1])
                d = int(parts[0])
            except Exception:
                y, m, d = 2000, 1, 1

            try:
                if ":" in s_str:
                    sh, sm = s_str.split(":")[:2]
                    hour = int(sh)
                    minute = int(sm)
                else:
                    hour, minute = 0, 0
            except Exception:
                hour, minute = 0, 0

            return datetime.datetime(y, m, d, hour, minute), item.get("id") or 0


        # --- İŞLEM DÜZENLEME MODALI ---
        def islem_duzenle_modal_ac(item):
            tur = item.get("tur", "Gider")

            mevcut_kat = item.get("kategori") or "Market & Temel Gıda"
            kat_secenekleri = list(GIDER_KATEGORILERI)
            if mevcut_kat and mevcut_kat not in kat_secenekleri:
                kat_secenekleri.insert(0, mevcut_kat)

            duzenle_tarih = ft.TextField(label="Tarih (GG.AA.YYYY)", value=item.get("tarih", ""), width=150, dense=True)
            duzenle_saat = ft.TextField(label="Saat (SS:DD)", value=item.get("saat", ""), width=150, dense=True)
            duzenle_tutar = ft.TextField(label="Tutar (TL)", value=str(item.get("tutar", 0.0)), width=310, dense=True, keyboard_type=ft.KeyboardType.NUMBER)

            if tur == "Gider":
                duzenle_firma = ft.TextField(label="Firma / Market", value=item.get("firma", ""), width=310, dense=True)
                duzenle_urun = ft.TextField(label="Ürün / Hizmet", value=item.get("urun", ""), width=310, dense=True)
                duzenle_kat = make_dropdown(options=kat_secenekleri, value=mevcut_kat, label="Kategori", width=310, dense=True)
                duzenle_miktar = ft.TextField(label="Miktar", value=item.get("miktar", ""), width=150, dense=True)
                duzenle_birim_fiyat = ft.TextField(label="Birim Fiyat (TL)", value=str(item.get("birim_fiyat", 0.0)), width=150, dense=True, keyboard_type=ft.KeyboardType.NUMBER)

                form_kontrolleri = [
                    duzenle_firma,
                    duzenle_urun,
                    duzenle_kat,
                    ft.Row([duzenle_miktar, duzenle_birim_fiyat], spacing=10),
                    duzenle_tutar,
                    ft.Row([duzenle_tarih, duzenle_saat], spacing=10)
                ]
            elif tur == "Gelir":
                duzenle_kaynak = ft.TextField(label="Kaynak / Kurum", value=item.get("kaynak", ""), width=310, dense=True)
                duzenle_gelir_turu = make_dropdown(
                    options=["Maaş", "Ek Gelir / Serbest", "Kira Geliri", "Yatırım / Faiz", "Diğer"],
                    value=item.get("gelir_turu") or "Maaş",
                    label="Gelir Türü",
                    width=310,
                    dense=True
                )
                duzenle_aciklama = ft.TextField(label="Açıklama", value=item.get("aciklama", ""), width=310, dense=True)
                form_kontrolleri = [
                    duzenle_kaynak,
                    duzenle_gelir_turu,
                    duzenle_aciklama,
                    duzenle_tutar,
                    ft.Row([duzenle_tarih, duzenle_saat], spacing=10)
                ]
            else:
                duzenle_alici = ft.TextField(label="Alıcı", value=item.get("kaynak", ""), width=310, dense=True)
                duzenle_aciklama = ft.TextField(label="Açıklama", value=item.get("aciklama", ""), width=310, dense=True)
                form_kontrolleri = [
                    duzenle_alici,
                    duzenle_aciklama,
                    duzenle_tutar,
                    ft.Row([duzenle_tarih, duzenle_saat], spacing=10)
                ]

            def duzenleme_kaydet(ev):
                try:
                    yeni_tutar = float(str(duzenle_tutar.value).replace(",", "."))
                except Exception:
                    yeni_tutar = float(item.get("tutar") or 0.0)

                yeni_tarih = standart_tarih_yap(duzenle_tarih.value)
                yeni_saat = duzenle_saat.value.strip() or "12:00"

                item["tutar"] = yeni_tutar
                item["tarih"] = yeni_tarih
                item["saat"] = yeni_saat

                if tur == "Gider":
                    item["firma"] = duzenle_firma.value.strip()
                    item["urun"] = duzenle_urun.value.strip()
                    item["kategori"] = duzenle_kat.value or "Diğer"
                    item["miktar"] = duzenle_miktar.value.strip()
                    try:
                        item["birim_fiyat"] = float(str(duzenle_birim_fiyat.value).replace(",", "."))
                    except Exception:
                        pass
                elif tur == "Gelir":
                    item["kaynak"] = duzenle_kaynak.value.strip()
                    item["gelir_turu"] = duzenle_gelir_turu.value or "Diğer"
                    item["aciklama"] = duzenle_aciklama.value.strip()
                else:
                    item["kaynak"] = duzenle_alici.value.strip()
                    item["aciklama"] = duzenle_aciklama.value.strip()

                if supabase and item.get("id"):
                    try:
                        supabase.table("islemler").update(item).eq("id", item["id"]).execute()
                    except Exception as db_err:
                        print("Supabase güncelleme hatası:", db_err)

                close_app_dialog(page, duzenle_dialog)
                arayuzu_guncelle()
                show_app_snackbar(page, "✅ İşlem başarıyla güncellendi!", color="#16a34a")

            duzenle_dialog = ft.AlertDialog(
                title=ft.Text(f"✏️ İşlemi Düzenle ({tur})", size=15, weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column(form_kontrolleri, spacing=8, scroll=ft.ScrollMode.AUTO),
                    width=330,
                    height=320
                ),
                actions=[
                    make_button("İptal", outlined=True, on_click=lambda _: close_app_dialog(page, duzenle_dialog)),
                    make_button("💾 Kaydet", bgcolor="#2563eb", color="white", on_click=duzenleme_kaydet)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, duzenle_dialog)

        # --- ARAYÜZ VE BAKİYE HESAPLAMA ---
        def arayuzu_guncelle():
            liste_arayuzu.controls.clear()

            # 1. TÜM ZAMANLAR KÜMÜLATİF BAKİYE (Eldeki Gerçek Toplam Nakit / Kasa)
            genel_gelir = 0.0
            genel_gider = 0.0
            genel_kullanici_harcamalari = {}
            genel_kullaniciya_aktarilan = {}

            for item in islemler:
                t = float(item.get("tutar") or 0.0)
                tur = item.get("tur")
                sahip = item.get("kullanici") or "Bilinmeyen"

                if tur == "Gelir":
                    genel_gelir += t
                elif tur == "Gider":
                    genel_gider += t
                    genel_kullanici_harcamalari[sahip] = genel_kullanici_harcamalari.get(sahip, 0.0) + t
                elif tur == "Para Aktarımı":
                    alici = item.get("kaynak") or "Aile Üyesi"
                    genel_kullaniciya_aktarilan[alici] = genel_kullaniciya_aktarilan.get(alici, 0.0) + t

            genel_kasa = genel_gelir - genel_gider

            # 2. SEÇİLİ DÖNEM HESAPLAMASI (O Ayın Gelir ve Gideri)
            donem_gelir = 0.0
            donem_gider = 0.0
            donem_kullanici_harcamalari = {}
            donem_kullaniciya_aktarilan = {}

            # Dönem başlığı güncellemesi
            bas_str = secilen_donem_bas[0].strftime("%d.%m.%Y")
            bit_str = secilen_donem_bit[0].strftime("%d.%m.%Y")
            if tum_zamanlar_modu[0]:
                donem_metni.value = "📅 Tüm Zamanlar (Tüm Kayıtlar)"
                donem_toggle_btn.text = "Döneme Dön"
            else:
                donem_metni.value = f"📅 {bas_str} - {bit_str}"
                donem_toggle_btn.text = "Tümünü Gör"

            # Döneme uyan kayıtları topla, istatistikleri ve filtreleri hesapla
            toplam_donem_gelir_sayisi = 0
            toplam_donem_gider_sayisi = 0
            kategori_toplam_tutar = 0.0
            kategori_islem_sayisi = 0
            donem_islemleri = []

            for item in islemler:
                t_date = stringden_tarih_al(item.get("tarih"))
                if not tum_zamanlar_modu[0]:
                    if not t_date or not (secilen_donem_bas[0] <= t_date <= secilen_donem_bit[0]):
                        continue

                tutar = float(item.get("tutar") or 0.0)
                islem_sahibi = item.get("kullanici") or "Bilinmeyen"
                islem_turu_val = item.get("tur")

                if islem_turu_val == "Gelir":
                    donem_gelir += tutar
                    toplam_donem_gelir_sayisi += 1
                elif islem_turu_val == "Gider":
                    donem_gider += tutar
                    toplam_donem_gider_sayisi += 1
                    donem_kullanici_harcamalari[islem_sahibi] = donem_kullanici_harcamalari.get(islem_sahibi, 0.0) + tutar
                elif islem_turu_val == "Para Aktarımı":
                    alici = item.get("kaynak") or "Aile Üyesi"
                    donem_kullaniciya_aktarilan[alici] = donem_kullaniciya_aktarilan.get(alici, 0.0) + tutar

                # 1. Tür Filtresi Kontrolü (Tümü / Gelir / Gider)
                if secilen_filtre[0] == "Gelir" and islem_turu_val != "Gelir":
                    continue
                if secilen_filtre[0] == "Gider" and islem_turu_val != "Gider":
                    continue

                # 2. Kategori Filtresi Kontrolü
                item_kat = (item.get("kategori") or item.get("gelir_turu") or "").strip()
                if secilen_kategori[0] != "Tüm Kategoriler":
                    kat_hedef = secilen_kategori[0].lower()
                    kat_mevcut = item_kat.lower()
                    if kat_hedef not in kat_mevcut and kat_mevcut not in kat_hedef:
                        continue
                    kategori_toplam_tutar += tutar
                    kategori_islem_sayisi += 1

                donem_islemleri.append(item)

            # Tarih ve Saate göre tam kronolojik sıralama (Gelir + Gider bir arada)
            donem_islemleri.sort(key=islem_siralama_anahtari, reverse=siralama_en_yeni[0])

            gosterilen_sayisi = 0
            for item in donem_islemleri:
                gosterilen_sayisi += 1
                tutar = float(item.get("tutar") or 0.0)
                islem_sahibi = item.get("kullanici") or "Bilinmeyen"
                islem_turu_val = item.get("tur")

                t_str = item.get("tarih", "")
                t_kisa = t_str[:5] if len(t_str) >= 5 else t_str
                s_str = item.get("saat", "").strip()
                zaman_metni = f"{t_kisa} {s_str}".strip()

                if islem_turu_val == "Gelir":
                    if not yonetici_mi:
                        continue
                    baslik = item.get("kaynak") or "Gelir"
                    ack = item.get("aciklama") or item.get("gelir_turu") or ""
                    alt_detay = f"{zaman_metni} • {ack}" if ack else zaman_metni
                    tutar_metni = f"+{tutar:,.2f} TL"
                    tutar_rengi = "#10b981"
                    ikon_adi = ft.Icons.ARROW_UPWARD
                    ikon_bg = "#d1fae5"
                    ikon_renk = "#047857"

                elif islem_turu_val == "Para Aktarımı":
                    alici = item.get("kaynak") or "Aile Üyesi"
                    if not (yonetici_mi or kullanici == alici):
                        continue
                    baslik = f"Aktarım: {alici}"
                    ack = item.get("aciklama") or "Nakit Aktarımı"
                    alt_detay = f"{zaman_metni} • {ack}"
                    tutar_metni = f"↕ {tutar:,.2f} TL"
                    tutar_rengi = "#2563eb"
                    ikon_adi = ft.Icons.SWAP_HORIZ
                    ikon_bg = "#dbeafe"
                    ikon_renk = "#1d4ed8"

                else:
                    # Gider
                    firma_adi = item.get("firma") or "Gider"
                    urun_adi = item.get("urun") or ""
                    baslik = f"{firma_adi} - {urun_adi}" if (urun_adi and urun_adi != firma_adi) else firma_adi
                    miktar_bilgisi = item.get("miktar") or ""
                    miktar_eki = f" • {miktar_bilgisi}" if (miktar_bilgisi and miktar_bilgisi != "-") else ""
                    kat_eki = f" • {item.get('kategori')}" if item.get('kategori') else ''
                    alt_detay = f"{zaman_metni}{kat_eki}{miktar_eki}"
                    tutar_metni = f"-{tutar:,.2f} TL"
                    tutar_rengi = "#ef4444"
                    ikon_adi = ft.Icons.ARROW_DOWNWARD
                    ikon_bg = "#fee2e2"
                    ikon_renk = "#b91c1c"

                duzenle_butonu = ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_color="#2563eb",
                    icon_size=15,
                    width=22,
                    height=22,
                    padding=0,
                    tooltip="Düzenle / Kategori Değiştir",
                    on_click=lambda e, it=item: islem_duzenle_modal_ac(it)
                ) if (yonetici_mi or item.get("kullanici") == kullanici) else ft.Container(width=0)

                sil_butonu = ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color="#94a3b8",
                    icon_size=15,
                    width=22,
                    height=22,
                    padding=0,
                    tooltip="Sil",
                    on_click=lambda e, it=item: silme_onayi_iste(it)
                ) if yonetici_mi else ft.Container(width=0)

                satir = ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ikon_adi, color=ikon_renk, size=14),
                                width=24,
                                height=24,
                                bgcolor=ikon_bg,
                                border_radius=12,
                                alignment=get_alignment_center()
                            ),
                            ft.Column([
                                ft.Text(baslik, size=12, weight=ft.FontWeight.W_600, no_wrap=True, max_lines=1),
                                ft.Text(alt_detay, size=10, color="#64748b", no_wrap=True, max_lines=1)
                            ], spacing=1, tight=True, expand=True)
                        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                        ft.Row([
                            ft.Text(tutar_metni, size=12, weight=ft.FontWeight.BOLD, color=tutar_rengi),
                            duzenle_butonu,
                            sil_butonu
                        ], spacing=1, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=make_padding(6, 4),
                    border=make_border_bottom(0.6, "#f1f5f9"),
                    border_radius=6,
                )
                liste_arayuzu.controls.append(satir)

            if gosterilen_sayisi == 0:
                liste_arayuzu.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=36, color="#94a3b8"),
                            ft.Text("Bu filtreye uygun işlem bulunamadı.", size=12, color="#94a3b8")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=20,
                        alignment=get_alignment_center()
                    )
                )

            # Bakiye Özeti ve Modern Kart Güncellemesi
            donem_fark = donem_gelir - donem_gider

            if yonetici_mi:
                uye_bakiye_metinleri = []
                for u in ["Aile Üyesi", "Ahmet", "Ayşe"]:
                    aktarilan = genel_kullaniciya_aktarilan.get(u, 0.0)
                    harcanan = genel_kullanici_harcamalari.get(u, 0.0)
                    kalan = aktarilan - harcanan
                    if aktarilan > 0 or harcanan > 0:
                        uye_bakiye_metinleri.append(f"{u}: {kalan:,.2f} TL")

                detay_str = " | ".join(uye_bakiye_metinleri) if uye_bakiye_metinleri else ""

                kasa_baslik_metni.value = "ELDEKİ TOPLAM PARA (KASA)"
                kasa_tutar_metni.value = f"{genel_kasa:,.2f} TL"
                kasa_tutar_metni.color = "white"

                bu_ay_gelir_txt.value = f"+{donem_gelir:,.2f} TL"
                bu_ay_gider_txt.value = f"-{donem_gider:,.2f} TL"
                bu_ay_fark_txt.value = f"{donem_fark:+,.2f} TL"
                bu_ay_fark_txt.color = "#10b981" if donem_fark >= 0 else "#f87171"

                uye_cuzdan_metni.value = f"💳 Üye Cüzdanları: {detay_str}" if detay_str else ""
                uye_cuzdan_metni.visible = bool(detay_str)
            else:
                benim_aktarilan = genel_kullaniciya_aktarilan.get(kullanici, 0.0)
                benim_harcanan = genel_kullanici_harcamalari.get(kullanici, 0.0)
                benim_kalan = benim_aktarilan - benim_harcanan
                bu_donem_harcanan = donem_kullanici_harcamalari.get(kullanici, 0.0)

                kasa_baslik_metni.value = "KİŞİSEL CÜZDANINIZ (KALAN)"
                kasa_tutar_metni.value = f"{benim_kalan:,.2f} TL"
                kasa_tutar_metni.color = "white"

                bu_ay_gelir_txt.value = f"+{benim_aktarilan:,.2f} TL"
                bu_ay_gider_txt.value = f"-{bu_donem_harcanan:,.2f} TL"
                bu_ay_fark_txt.value = f"-{benim_harcanan:,.2f} TL"

                uye_cuzdan_metni.value = f"Toplam Harcamanız: {benim_harcanan:,.2f} TL"
                uye_cuzdan_metni.visible = True

            # Kategori Özet Rozetini Güncelle
            if secilen_kategori[0] != "Tüm Kategoriler":
                donem_ek = " (Tüm Zamanlar)" if tum_zamanlar_modu[0] else ""
                kategori_ozet_metni.content.value = (
                    f"🏷️ {secilen_kategori[0]}{donem_ek} ➔ Toplam: {kategori_toplam_tutar:,.2f} TL ({kategori_islem_sayisi} işlem)"
                )
                kategori_ozet_metni.visible = True
            else:
                kategori_ozet_metni.visible = False
            try:
                kategori_ozet_metni.update()
            except Exception:
                pass

            # Filtre butonları üzerindeki sayaçları güncelle
            filtre_tumu_btn.content.value = f"Tümü ({toplam_donem_gelir_sayisi + toplam_donem_gider_sayisi})"
            filtre_gelir_btn.content.value = f"🟢 Gelir ({toplam_donem_gelir_sayisi})"
            filtre_gider_btn.content.value = f"🔴 Gider ({toplam_donem_gider_sayisi})"
            try:
                filtre_bari.update()
            except Exception:
                pass

            try:
                bakiye_karti.update()
            except Exception:
                pass
            try:
                donem_metni.update()
            except Exception:
                pass
            try:
                bilgi_mesaji.update()
            except Exception:
                pass
            page.update()

        # --- İŞLEM KAYDETME ---
        def islem_kaydet(e):
            tur = islem_turu.value

            if tur == "Gelir":
                tutar_val = 0.0
                try:
                    tutar_val = float(gelir_tutari.value.replace(",", ".")) if gelir_tutari.value else 0.0
                except ValueError:
                    tutar_val = 0.0

                kaynak_val = gelir_kaynagi.value.strip()
                aciklama_val = gelir_aciklamasi.value.strip()

                if tutar_val <= 0:
                    bilgi_mesaji.value = "⚠️ Lütfen 0'dan büyük geçerli bir gelir tutarı giriniz!"
                    bilgi_mesaji.color = "red"
                    page.update()
                    return

                if not kaynak_val and not aciklama_val:
                    bilgi_mesaji.value = "⚠️ Lütfen bir gelir kaynağı veya açıklama belirtiniz!"
                    bilgi_mesaji.color = "red"
                    page.update()
                    return

                yeni_kayit = {
                    "kullanici": kullanici,
                    "tur": "Gelir",
                    "tarih": secilen_gelir_tarih[0].strftime("%d.%m.%Y"),
                    "saat": secilen_gelir_saat[0],
                    "kaynak": kaynak_val or "Belirtilmedi",
                    "gelir_turu": gelir_turu.value,
                    "aciklama": aciklama_val or "-",
                    "firma": "",
                    "urun": "",
                    "kategori": "Gelir",
                    "miktar": "",
                    "birim_fiyat": "",
                    "tutar": tutar_val
                }

                if supabase:
                    try:
                        res = supabase.table("islemler").insert(yeni_kayit).execute()
                        if res.data:
                            yeni_kayit["id"] = res.data[0]["id"]
                    except Exception as ex:
                        print("Bulut kayıt hatası:", ex)

                islemler.insert(0, yeni_kayit)
                gelir_kaynagi.value = ""
                gelir_aciklamasi.value = ""
                gelir_tutari.value = ""

                su_an = datetime.datetime.now().strftime("%H:%M")
                secilen_gelir_saat[0] = su_an
                set_button_label(gelir_saat_btn, f"🕒 {su_an}")

            elif tur == "Para Aktarımı":
                tutar_val = 0.0
                try:
                    tutar_val = float(aktarim_tutari.value.replace(",", ".")) if aktarim_tutari.value else 0.0
                except ValueError:
                    tutar_val = 0.0

                if tutar_val <= 0:
                    bilgi_mesaji.value = "⚠️ Lütfen aktarılacak tutarı giriniz (0'dan büyük olmalı)!"
                    bilgi_mesaji.color = "red"
                    page.update()
                    return

                yeni_kayit = {
                    "kullanici": kullanici,
                    "tur": "Para Aktarımı",
                    "tarih": secilen_aktarim_tarih[0].strftime("%d.%m.%Y"),
                    "saat": datetime.datetime.now().strftime("%H:%M"),
                    "kaynak": aktarim_alici.value,
                    "gelir_turu": "Harçlık / Aktarım",
                    "aciklama": aktarim_aciklamasi.value.strip() or "Para Transferi",
                    "firma": "",
                    "urun": "",
                    "kategori": "Para Aktarımı",
                    "miktar": "",
                    "birim_fiyat": "",
                    "tutar": tutar_val
                }

                if supabase:
                    try:
                        res = supabase.table("islemler").insert(yeni_kayit).execute()
                        if res.data:
                            yeni_kayit["id"] = res.data[0]["id"]
                    except Exception as ex:
                        print("Bulut kayıt hatası:", ex)

                islemler.insert(0, yeni_kayit)
                aktarim_tutari.value = ""
                aktarim_aciklamasi.value = ""

            else:
                firma_val = gider_firma.value.strip()
                urun_val = gider_urun.value.strip()
                miktar_str = gider_miktar.value.strip()
                birim_val = gider_birim_secimi.value

                toplam_tutar_val = 0.0
                if gider_toplam_tutar.value:
                    try:
                        toplam_tutar_val = float(gider_toplam_tutar.value.replace(",", "."))
                    except ValueError:
                        toplam_tutar_val = 0.0
                elif gider_birim_fiyat.value:
                    try:
                        bf = float(gider_birim_fiyat.value.replace(",", "."))
                        m = float(miktar_str.replace(",", ".")) if miktar_str else 1.0
                        toplam_tutar_val = bf * m
                    except ValueError:
                        toplam_tutar_val = 0.0

                if toplam_tutar_val <= 0 and not firma_val and not urun_val:
                    bilgi_mesaji.value = "⚠️ Hiçbir veri girmediniz! Lütfen harcama tutarı ve ürün/firma giriniz."
                    bilgi_mesaji.color = "red"
                    page.update()
                    return

                if toplam_tutar_val <= 0:
                    bilgi_mesaji.value = "⚠️ Lütfen geçerli bir harcama tutarı giriniz (0'dan büyük olmalı)!"
                    bilgi_mesaji.color = "red"
                    page.update()
                    return

                if miktar_str and not birim_val:
                    bilgi_mesaji.value = f"⚠️ Miktar ({miktar_str}) belirlendiği için lütfen birim seçiniz!"
                    bilgi_mesaji.color = "red"
                    page.update()
                    return

                miktar_tam_metin = f"{miktar_str} {birim_val}".strip() if miktar_str else ""

                yeni_kayit = {
                    "kullanici": kullanici,
                    "tur": "Gider",
                    "tarih": secilen_gider_tarih[0].strftime("%d.%m.%Y"),
                    "saat": secilen_gider_saat[0],
                    "kaynak": "",
                    "gelir_turu": "",
                    "aciklama": "",
                    "firma": firma_val,
                    "urun": urun_val,
                    "kategori": gider_kategori.value,
                    "miktar": miktar_tam_metin,
                    "birim_fiyat": gider_birim_fiyat.value.strip(),
                    "tutar": toplam_tutar_val
                }

                if supabase:
                    try:
                        res = supabase.table("islemler").insert(yeni_kayit).execute()
                        if res.data:
                            yeni_kayit["id"] = res.data[0]["id"]
                    except Exception as ex:
                        print("Bulut kayıt hatası:", ex)

                islemler.insert(0, yeni_kayit)

                gider_firma.value = ""
                gider_urun.value = ""
                gider_miktar.value = ""
                gider_birim_secimi.value = None
                gider_birim_fiyat.value = ""
                gider_toplam_tutar.value = ""
                kullanici_girdileri.clear()

                su_an = datetime.datetime.now().strftime("%H:%M")
                secilen_gider_saat[0] = su_an
                set_button_label(gider_saat_btn, f"🕒 {su_an}")

            bilgi_mesaji.value = "✅ İşlem buluta kaydedildi!"
            bilgi_mesaji.color = "green"
            arayuzu_guncelle()

        yetki_metni = "👑 Ev Yöneticisi Paneli" if yonetici_mi else "👤 Aile Üyesi Paneli"

        def cikis_yap_aksiyon(e):
            oturum_sil()
            main(page)

        # Dönem Seçim Araç Çubuğu (Modern Kapsayıcı)
        onceki_btn = make_button("◀", width=36, height=32, outlined=True, on_click=lambda _: donem_kaydir("onceki"))
        sonraki_btn = make_button("▶", width=36, height=32, outlined=True, on_click=lambda _: donem_kaydir("sonraki"))
        donem_toggle_btn = make_button("Tümünü Gör", width=95, height=32, outlined=True, on_click=tum_zamanlar_toggle)

        donem_bar = ft.Container(
            content=ft.Row([
                onceki_btn,
                donem_metni,
                sonraki_btn,
                donem_toggle_btn
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#f8fafc",
            border=make_border_all(1, "#e2e8f0"),
            border_radius=12,
            padding=make_padding(8, 4),
            width=360
        )

        # Liste Araç Çubuğu (Kronolojik Sıralama, En Başa / En Sona Git ve Toplu Sil)
        def siralama_toggle(e):
            siralama_en_yeni[0] = not siralama_en_yeni[0]
            set_button_label(siralama_btn, "⏱️ Yeni ➔ Eski" if siralama_en_yeni[0] else "⏱️ Eski ➔ Yeni")
            bilgi_mesaji.value = "📅 Sıralama: Yeniden Eskiye (En Son İşlem Üstte)" if siralama_en_yeni[0] else "📅 Sıralama: Kronolojik (Eskiden Yeniye)"
            bilgi_mesaji.color = "blue"
            try:
                bilgi_mesaji.update()
            except Exception:
                pass
            arayuzu_guncelle()

        siralama_btn = make_button(
            "⏱️ Yeni ➔ Eski" if siralama_en_yeni[0] else "⏱️ Eski ➔ Yeni",
            height=32,
            outlined=True,
            on_click=siralama_toggle
        )
        toplu_sil_btn = make_button("🗑️ Toplu Sil", height=32, bgcolor="#d32f2f", color="white", on_click=toplu_silme_onayi_iste) if yonetici_mi else ft.Container()

        liste_ust_bar = ft.Container(
            content=ft.Row([
                ft.Text("İşlem Geçmişi", weight=ft.FontWeight.BOLD, size=14),
                ft.Row([
                    siralama_btn,
                    make_button("⬆", width=34, height=32, outlined=True, tooltip="En Başa Git", on_click=listeyi_basa_sar),
                    make_button("⬇", width=34, height=32, outlined=True, tooltip="En Sona Git", on_click=listeyi_sona_sar),
                    toplu_sil_btn
                ], spacing=3)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            width=380
        )


        # --- İSTATİSTİK VE KATEGORİ GRAFİKLERİ PENCERESİ ---
        def istatistik_ac(e=None):
            stat_tum_zamanlar = [tum_zamanlar_modu[0]]

            # İstatistik penceresi ana konteyneri
            stat_icerik_alani = ft.Column([], scroll=ft.ScrollMode.AUTO, spacing=10)

            def stat_hesapla_ve_ciz():
                stat_icerik_alani.controls.clear()

                toplam_gelir = 0.0
                toplam_gider = 0.0
                kat_harcamalari = {}

                for item in islemler:
                    t_date = stringden_tarih_al(item.get("tarih"))
                    if not stat_tum_zamanlar[0]:
                        if not t_date or not (secilen_donem_bas[0] <= t_date <= secilen_donem_bit[0]):
                            continue

                    tutar = float(item.get("tutar") or 0.0)
                    tur = item.get("tur")

                    if tur == "Gelir":
                        toplam_gelir += tutar
                    elif tur == "Gider":
                        toplam_gider += tutar
                        kat = (item.get("kategori") or "Diğer").strip()
                        if not kat:
                            kat = "Diğer"
                        kat_harcamalari[kat] = kat_harcamalari.get(kat, 0.0) + tutar

                net_fark = toplam_gelir - toplam_gider
                bas_str = secilen_donem_bas[0].strftime("%d.%m.%Y")
                bit_str = secilen_donem_bit[0].strftime("%d.%m.%Y")
                donem_etiketi = "Tüm Zamanlar" if stat_tum_zamanlar[0] else f"{bas_str} - {bit_str}"

                # 1. Dönem Seçim & Değiştirme Butonu
                def stat_toggle(ev):
                    stat_tum_zamanlar[0] = not stat_tum_zamanlar[0]
                    stat_hesapla_ve_ciz()
                    try:
                        stat_dialog.update()
                    except Exception:
                        page.update()

                donem_bar = ft.Container(
                    content=ft.Row([
                        ft.Text(f"📅 {donem_etiketi}", size=12, weight=ft.FontWeight.W_600, color="#1e293b"),
                        make_button(
                            "Döneme Dön" if stat_tum_zamanlar[0] else "Tüm Zamanlar",
                            width=110,
                            height=28,
                            outlined=True,
                            on_click=stat_toggle
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="#f8fafc",
                    border=make_border_all(1, "#e2e8f0"),
                    border_radius=8,
                    padding=make_padding(10, 4)
                )
                stat_icerik_alani.controls.append(donem_bar)

                # 2. Özet Mini Kartlar (Gelir, Gider, Net)
                ozet_satiri = ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Gelir", size=10, color="#166534"),
                            ft.Text(f"+{toplam_gelir:,.0f} TL", size=12, weight=ft.FontWeight.BOLD, color="#15803d")
                        ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#dcfce7",
                        border_radius=8,
                        padding=make_padding(8, 4),
                        expand=1
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Gider", size=10, color="#991b1b"),
                            ft.Text(f"-{toplam_gider:,.0f} TL", size=12, weight=ft.FontWeight.BOLD, color="#b91c1c")
                        ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#fee2e2",
                        border_radius=8,
                        padding=make_padding(8, 4),
                        expand=1
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Net Fark", size=10, color="#1e40af"),
                            ft.Text(f"{net_fark:+,.0f} TL", size=12, weight=ft.FontWeight.BOLD, color="#2563eb" if net_fark >= 0 else "#dc2626")
                        ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#eff6ff",
                        border_radius=8,
                        padding=make_padding(8, 4),
                        expand=1
                    ),
                ], spacing=6)
                stat_icerik_alani.controls.append(ozet_satiri)

                # 3. Kategori Dağılım Sıralaması
                sirali_kategoriler = sorted(kat_harcamalari.items(), key=lambda x: x[1], reverse=True)

                if sirali_kategoriler and toplam_gider > 0:
                    en_cok_kat, en_cok_tutar = sirali_kategoriler[0]
                    en_cok_oran = (en_cok_tutar / toplam_gider) * 100.0

                    # 1. Sıradaki Kategori Vurgu Rozeti
                    rozet = ft.Container(
                        content=ft.Row([
                            ft.Text("🏆 En Çok Harcanan:", size=11, color="#854d0e", weight=ft.FontWeight.BOLD),
                            ft.Text(f"{en_cok_kat} ({en_cok_tutar:,.2f} TL • %{en_cok_oran:.1f})", size=11, color="#713f12")
                        ], spacing=4),
                        bgcolor="#fef9c3",
                        border=make_border_all(1, "#fef08a"),
                        border_radius=8,
                        padding=make_padding(8, 4)
                    )
                    stat_icerik_alani.controls.append(rozet)

                    # Kategori Çubuk Grafikleri Başlığı
                    stat_icerik_alani.controls.append(
                        ft.Text("📊 Kategori Bazlı Harcama Dağılımı:", size=12, weight=ft.FontWeight.BOLD, color="#334155")
                    )

                    renk_haritasi = {
                        "Market & Temel Gıda": "#10b981",
                        "Ev & Faturalar": "#f59e0b",
                        "Ulaşım / Yakıt": "#3b82f6",
                        "Abur Cubur & Atıştırmalık": "#ec4899",
                        "Giyim & Kişisel": "#8b5cf6",
                        "Sağlık": "#ef4444",
                        "Eğlence & Restoran": "#f97316",
                        "Eğitim & Okul": "#06b6d4",
                        "Sigara/Tütün": "#64748b",
                        "Temizlik": "#14b8a6",
                        "Transfer / Birikim": "#6366f1",
                        "Diğer": "#94a3b8"
                    }

                    for kat_ad, kat_tut in sirali_kategoriler:
                        oran = (kat_tut / toplam_gider) * 100.0 if toplam_gider > 0 else 0.0
                        cubuk_orani = min(max(oran / 100.0, 0.01), 1.0)
                        bar_renk = renk_haritasi.get(kat_ad, "#3b82f6")

                        kat_karti = ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Row([
                                        ft.Container(width=10, height=10, border_radius=5, bgcolor=bar_renk),
                                        ft.Text(kat_ad, size=11.5, weight=ft.FontWeight.W_600, color="#1e293b")
                                    ], spacing=6),
                                    ft.Row([
                                        ft.Text(f"%{oran:.1f}", size=11, color="#64748b", weight=ft.FontWeight.BOLD),
                                        ft.Text(f"{kat_tut:,.2f} TL", size=11.5, weight=ft.FontWeight.BOLD, color="#b91c1c")
                                    ], spacing=6)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                # Modern doluluk çubuğu
                                ft.Container(
                                    content=ft.Row([
                                        ft.Container(bgcolor=bar_renk, border_radius=4, height=7, expand=int(cubuk_orani * 100)),
                                        ft.Container(bgcolor="#f1f5f9", border_radius=4, height=7, expand=max(1, int((1.0 - cubuk_orani) * 100)))
                                    ], spacing=0),
                                    border_radius=4,
                                    height=7
                                )
                            ], spacing=4),
                            bgcolor="white",
                            border=make_border_all(1, "#f1f5f9"),
                            border_radius=8,
                            padding=make_padding(8, 6)
                        )
                        stat_icerik_alani.controls.append(kat_karti)
                else:
                    stat_icerik_alani.controls.append(
                        ft.Container(
                            content=ft.Text("Seçilen dönemde henüz bir gider kaydı bulunmuyor.", size=12, color="grey"),
                            alignment=get_alignment_center(),
                            padding=20
                        )
                    )

            stat_hesapla_ve_ciz()

            def stat_kapat(ev):
                close_app_dialog(page, stat_dialog)

            stat_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Text("📊 Bütçe & Harcama Grafikleri", size=15, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.START),
                content=ft.Container(
                    content=stat_icerik_alani,
                    width=340,
                    height=380
                ),
                actions=[
                    make_button("Kapat", width=90, height=34, outlined=True, on_click=stat_kapat)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )

            show_app_dialog(page, stat_dialog)

        # Modern Üst Başlık Barı
        ust_baslik_bari = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Text("🏠 Hane Bütçesi", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(yetki_metni, size=10, color="white", weight=ft.FontWeight.BOLD),
                        bgcolor="#2563eb",
                        border_radius=10,
                        padding=make_padding(8, 2)
                    )
                ], spacing=8),
                ft.Row([
                    ft.IconButton(icon=ft.Icons.PIE_CHART_OUTLINE, icon_size=20, icon_color="#2563eb", tooltip="Kategori Grafikleri & İstatistik", on_click=istatistik_ac),
                    ft.IconButton(icon=ft.Icons.LOGOUT, icon_size=18, tooltip="Çıkış Yap", on_click=cikis_yap_aksiyon)
                ], spacing=2)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            width=360,
            padding=make_padding(0, 4)
        )

        # Hızlı Aksiyon Butonları (İşlem Ekle, Fiş Tara, CSV Yükle, CSV İndir)
        hizli_aksiyon_bari = ft.Row([
            form_ac_kapat_btn,
            make_button("📸 Fiş Tara", bgcolor="#8b5cf6", color="white", height=36, tooltip="Fiş Fotoğrafı Yükle & AI ile Oku", on_click=fis_tara_tiklandi),
            make_button("CSV", icon=ft.Icons.UPLOAD_FILE, height=36, outlined=True, tooltip="CSV Yükle", on_click=csv_yukle_tiklandi),
            make_button("İndir", icon=ft.Icons.DOWNLOAD, height=36, outlined=True, tooltip="CSV Olarak İndir", on_click=csv_indir_tiklandi)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=6)

        # Liste Konteyneri (Beyaz modern kart içine yerleştirilmiş temiz liste)
        liste_kapsayici = ft.Container(
            content=liste_arayuzu,
            bgcolor="white",
            border_radius=12,
            border=make_border_all(1, "#e2e8f0"),
            padding=4,
            width=380
        )

        page.add(
            ft.Column([
                ft.Container(height=2),
                ust_baslik_bari,
                donem_bar,
                bakiye_karti,
                ft.Container(height=2),
                hizli_aksiyon_bari,
                form_govdesi,
                ft.Container(height=2),
                filtre_bari,
                kategori_filtre_bari,
                kategori_ozet_metni,
                liste_ust_bar,
                liste_kapsayici,
                ft.Container(height=15)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6)
        )
        arayuzu_guncelle()

    # Oturum Kontrolü
    kayitli_oturum = oturum_oku()
    if kayitli_oturum and "kullanici" in kayitli_oturum and "yonetici_mi" in kayitli_oturum:
        ana_ekrana_git(kayitli_oturum["kullanici"], kayitli_oturum["yonetici_mi"])
        return

    # Giriş Ekranı
    kullanici_adi = ft.TextField(label="Kullanıcı Adı (yönetici / üye)", width=320)
    sifre = ft.TextField(label="Şifre", password=True, can_reveal_password=True, width=320)
    beni_hatirla = ft.Checkbox(label="Beni Hatırla", value=True)
    hata_mesaji = ft.Text("", color="red")

    def giris_yap(e):
        ad = kullanici_adi.value.strip().lower()
        pass_val = sifre.value.strip()

        if ad == "yönetici" and pass_val == "1234":
            if beni_hatirla.value:
                oturum_kaydet("Ev Yöneticisi", True)
            ana_ekrana_git("Ev Yöneticisi", yonetici_mi=True)
        elif ad == "üye" and pass_val == "5678":
            if beni_hatirla.value:
                oturum_kaydet("Aile Üyesi", False)
            ana_ekrana_git("Aile Üyesi", yonetici_mi=False)
        else:
            hata_mesaji.value = "Hatalı kullanıcı adı veya şifre!"
            page.update()

    page.add(
        ft.Column([
            ft.Container(height=60),
            ft.Text("🏠 Hane Bütçesi Giriş", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            kullanici_adi,
            sifre,
            ft.Container(content=ft.Row([beni_hatirla], alignment=ft.MainAxisAlignment.START), width=320),
            ft.Container(height=5),
            make_button("Giriş Yap", icon=ft.Icons.LOGIN, bgcolor="blue", color="white", width=320, height=45, on_click=giris_yap),
            hata_mesaji
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

    kullanici_adi.on_submit = giris_yap
    sifre.on_submit = giris_yap

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)