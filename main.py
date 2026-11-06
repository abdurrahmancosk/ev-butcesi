import asyncio
import csv
import datetime
import io
import json
import os
import re
import ssl
import sys
import tempfile
import threading
import time
import types
import urllib.parse
import urllib.request
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

# ==============================================================================
# Haptic Feedback & Tıklama Sesi (Masaüstü Windows + Telefon Android / iOS)
# ==============================================================================
_haptic_instance = None
try:
    if hasattr(ft, "HapticFeedback"):
        _haptic_instance = ft.HapticFeedback()
except Exception:
    pass

# Doğal, zarif ve hafif tıklama sesi (25ms Soft Tap WAV)
_TIKLAMA_SESI_B64 = "UklGRsAIAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YZwIAAAAAFAEiAiZDHMQCBRMFzIasRzBHlkgdSETIjAizCHrIJEfwx2JG+wY9xW1EjMPfwumB7kDxf/Z+wP4U/TV8JbtouoD6MPl6uN94oDh+ODl4EbhGeJb4wblEud46S3sKO9c8r71P/nT/GwA/QN5B9IK/Q3tEJkT9hX9F6cZ7RrNG0IcThzvGykb/hl0GJIWXxTkESoPPQwnCfUFsgJt/y78BPn69RvzcvAH7uXrEeqT6G/nquZE5kDmm+ZW52vo1umR65bt3O9a8gb11/fB+rn9swCmA4YGSAniC0sOehBoEg0UZBVpFhcXbxduFxUXZxZmFRcUfxKlEJAOSQzYCUYHngTqATX/hvzq+Wn3DfXe8uTwJ++s7Xjsj+v16qrqsOoF66jrluzL7ULv9fDd8vL0LfeF+fH7Z/7eAE4DrQXzBxcKEAzaDWwPwRDVEaUSLRNtE2QTEhN5EpwRgBAnD5gN2gvyCegHxQWQA1IBFP/d/LX6pvi19uv0TvPj8bDwuO//7obuUO5d7qvuOu8G8A3xSfK381D1Dvfq+N364Pzr/vUA+QLuBM0GjwgtCqML6gz/Dd0Ogg/sDxoQCxDADzsPfg6MDWkMGgujCQsIWQaRBLwC4AAF/zD9afu3+R/4qPZW9S/0NvNu8tvxfvFY8WjxsPEs8tvyuvPF9Pn1UPfE+FH68fuc/U7//gCoAkUEzwVBB5QIxgnQCrALYwzmDDgNWA1FDQINjgzsCx4LKQoPCdUHgQYWBZsDFgKLAAL/f/0I/KL6U/kg+Az3HPZS9bL0PfT189vz7vMu9Jr0MPXu9c/20ffw+Cj6c/vM/C/+l//8AFwCsQP1BCQGOwc0CA0JwglSCrkK+AoOC/oKvQpYCs4JIAlQCGQHXQZBBRIE1wKUAUwACP/I/ZL8bPtZ+l35fPi59xb3lfY59gL28PUF9j72nPYc9733e/hU+UT6SPtc/Hv9ov7M//MAFgIvAzoEMwUXBuIGkgclCJgI6ggaCSgJFAndCIYIEAh8B80GBwYrBT0EQQM7Ai4BHwAT/wv+DP0a/Dj7avqy+RP5j/go+N/3tfer97/38/dE+LH4OfnZ+Y/6Wfsy/Bj9B/77/vL/5gDWAb4CmQNmBCAFxgVVBswGKAdpB40HlQeBB1EHBQegBiMGkAXpBDEEawOZAr8B4AAAACL/R/51/a789ftM+7b6NfrL+Xn5P/kf+Rn5Lvlb+aH5/vlx+vj6kfs6/O/8rv11/kD/DADWAJwBWwIQA7cDUATXBEwFqwX1BSgGQwZHBjQGCQbIBXIFCAWMBAAEZgPBAhICXQGkAOv/Mv9+/tH9Lf2W/Az8kfsp+9P6kfpk+kz6Svpd+oX6wfoQ+3L75Ptk/PH8iP0n/s3+df8dAMUAaQEGApoCJAOgAw8EbQS6BPUEHQUyBTMFIAX6BMMEeQQgBLcDQgPBAjcCpQEPAXUA3P9E/6/+If6a/R79rfxJ/PT7r/t6+1f7RftF+1f7e/uu+/L7RPyk/BD9hf0E/oj+Ev+d/ykAswA6AbwBNgKmAgwDZgOzA/EDIAQ/BE4ETQQ8BBsE6wOtA2EDCQOnAjsCyAFPAdEAUgDU/1b/2/5m/vf9kf01/eP8nvxn/D38IfwU/Bb8J/xG/HL8rPzx/EL9nP3+/Wj+1v5I/7z/LwCiABEBfAHgATwCkALZAhcDSQNvA4cDkgOPA38DYwM5AwQDxAJ7AigCzgFuAQkBoQA4AM//Z/8C/6H+Rv7y/af9Zf0t/QD93/zJ/MD8w/zS/O38E/1E/X/9w/0O/mH+uP4U/3P/0/8yAJEA7QBEAZcB4wEnAmIClQK9AtsC7QL1AvIC4wLKAqcCegJEAgYCwQF1ASUB0QB7ACQAzf93/yT/1P6K/kX+B/7S/aT9gP1m/VX9T/1S/WD9eP2Y/cL98/0s/mz+sP75/kb/lf/k/zMAgQDNABUBWQGXAc4B/wEoAkgCXwJuAnMCbwJiAk0CLgIIAtsBpgFtAS4B6wClAF0AFQDO/4b/Qv8A/8P+i/5Y/i3+CP7r/db9yf3F/cn91f3q/Qb+Kf5T/oL+t/7x/i7/bv+v//H/MgByALEA7AAkAVcBhAGrAcwB5gH5AQQCCAIEAvgB5QHLAasBhAFZASgB8wC8AIIARgAKAM//lf9c/yb/9P7G/p3+ef5b/kT+NP4q/if+K/42/kj+YP5+/qH+yf71/iX/WP+N/8P/+v8vAGUAmADJAPcAIAFFAWYBgAGVAaQBrAGuAaoBoAGPAXkBXgE+ARkB8ADEAJYAZgA0AAIA0v+h/3P/Rv8d//f+1v65/qH+j/6B/nr+eP59/ob+lv6q/sP+4f4D/yj/UP96/6b/0/8AAC0AWQCDAKsA0QDzABEBKwFAAVEBXQFjAWQBYAFXAUkBNgEfAQQB5QDDAJ4AdwBPACYA/v/V/63/h/9i/0D/Iv8G/+/+2/7N/sL+vf68/sD+yP7W/uf+/P4V/zL/Uf9y/5X/uv/f/wQAKQBNAHAAkQCwAMwA5QD6AAsBGQEiASYBJwEjARsBDwH/AOsA1AC6AJ4AfwBfAD4AHAD6/9n/uP+Y/3r/Xv9F/y//HP8M/wD/+P70/vT++P7//gr/Gf8r/0D/WP9y/47/q//K/+n/BwAmAEQAYAB8AJUAqwDAANEA3wDpAPAA9AD0APAA6QDfANEAwQCtAJcAgABmAEsAMAATAPj/3P/B/6f/jv93/2P/Uf9B/zX/K/8l/yL/Iv8m/yz/Nv9C/1L/Y/93/43/pP+9/9b/8P8JACIAOwBSAGkAfQCQAKAArgC6AMIAyADKAMoAxwDAALcArACeAI0AewBnAFIAPAAlAA0A9//g/8n/tP+g/43/fP9t/2H/V/9P/0r/SP9I/0z/Uf9a/2T/cf+A/5H/o/+3/8v/4P/1/woAHwAzAEYAWQBqAHkAhgCSAJsAoQCmAA=="
_ses_dosyasi_yolu = None

try:
    import base64
    _wav_raw = base64.b64decode(_TIKLAMA_SESI_B64)
    _temp_wav = os.path.join(tempfile.gettempdir(), "evbutcesi_click.wav")
    with open(_temp_wav, "wb") as _f_wav:
        _f_wav.write(_wav_raw)
    _ses_dosyasi_yolu = _temp_wav
except Exception:
    pass

# Flet Audio Servisi / Player referansı (Flet UI katmanı üzerinden garantili ses çalma)
_flet_audio_player = [None]

def _pc_tiklama_sesi_cal():
    """Bilgisayarda tıklandığında anında duyulur, doğal bir tıklama sesi çalar."""
    calindi = False

    # 1. Windows Ses Motoru (winsound - Windows'un doğal hoparlör sürücüsü)
    if sys.platform == "win32":
        try:
            import winsound
            # İlk olarak Windows sistem dokunma sesi (MessageBeep - her Windows bilgisayarda %100 açıktır)
            winsound.MessageBeep(winsound.MB_OK)
            calindi = True
        except Exception:
            pass

        if not calindi:
            try:
                import winsound
                # Standart frekanslı hafif bip tonu (1200 Hz, 35 milisaniye)
                winsound.Beep(1200, 35)
                calindi = True
            except Exception:
                pass

        if not calindi and _ses_dosyasi_yolu and os.path.exists(_ses_dosyasi_yolu):
            try:
                import winsound
                winsound.PlaySound(_ses_dosyasi_yolu, winsound.SND_FILENAME | winsound.SND_ASYNC)
                calindi = True
            except Exception:
                pass

    # 2. Flet Audio Player (Flutter / Web / masaüstü ses kanalı üzerinden)
    if not calindi and _flet_audio_player[0] is not None:
        try:
            player = _flet_audio_player[0]
            if hasattr(player, "play"):
                r = player.play()
                if asyncio.iscoroutine(r):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(r)
                    except Exception:
                        pass
                calindi = True
        except Exception:
            pass

    # 3. macOS / Linux Sistem Ses Komutları
    if not calindi:
        if sys.platform == "darwin":
            try:
                os.system("afplay /System/Library/Sounds/Tink.aiff &")
            except Exception:
                pass
        elif sys.platform.startswith("linux"):
            try:
                if _ses_dosyasi_yolu and os.path.exists(_ses_dosyasi_yolu):
                    os.system(f"aplay -q '{_ses_dosyasi_yolu}' 2>/dev/null &")
            except Exception:
                pass

def _android_ses_ve_titresim():
    """Android cihazlarda doğrudan donanım vibratörü ve sistem tıklama sesi çalar."""
    # Android Titreşim (pyjnius / Android Vibrator Service)
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        act = PythonActivity.mActivity
        vibrator = act.getSystemService(Context.VIBRATOR_SERVICE)
        if vibrator:
            vibrator.vibrate(30)
    except Exception:
        pass

    # Android Tıklama Sesi (AudioManager FX_KEY_CLICK)
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        act = PythonActivity.mActivity
        audio_mgr = act.getSystemService(Context.AUDIO_SERVICE)
        AudioManager = autoclass('android.media.AudioManager')
        audio_mgr.playSoundEffect(AudioManager.FX_KEY_CLICK, 0.8)
    except Exception:
        pass

def dokunma_geribildirimi():
    """Buton tıklamalarında hem masaüstünde hem de telefonda ses ve dokunma titreşimi üretir."""
    # 1. Bilgisayar Ses Motoru
    try:
        threading.Thread(target=_pc_tiklama_sesi_cal, daemon=True).start()
    except Exception:
        pass

    # 2. Android Donanım Ses & Titreşim Motoru
    try:
        threading.Thread(target=_android_ses_ve_titresim, daemon=True).start()
    except Exception:
        pass

    # 3. Flet Mobil Haptic Feedback Servisi (Android / iOS)
    if _haptic_instance:
        try:
            if hasattr(_haptic_instance, "selection_click"):
                res = _haptic_instance.selection_click()
                if asyncio.iscoroutine(res):
                    try:
                        asyncio.create_task(res)
                    except Exception:
                        pass
            elif hasattr(_haptic_instance, "light_impact"):
                res = _haptic_instance.light_impact()
                if asyncio.iscoroutine(res):
                    try:
                        asyncio.create_task(res)
                    except Exception:
                        pass
            elif hasattr(_haptic_instance, "vibrate"):
                res = _haptic_instance.vibrate()
                if asyncio.iscoroutine(res):
                    try:
                        asyncio.create_task(res)
                    except Exception:
                        pass
        except Exception:
            pass

def make_button(text, icon=None, bgcolor=None, color=None, width=None, height=None, on_click=None, outlined=False, tooltip=None, border_radius=12, **kwargs):
    """Hem Flet 1.0 hem eski sürümlerle %100 uyumlu, haptic titreşim destekli modern buton üretir."""
    if outlined:
        btn_cls = getattr(ft, "OutlinedButton", getattr(ft, "Button", None))
    else:
        btn_cls = getattr(ft, "ElevatedButton", getattr(ft, "Button", None))
    if btn_cls is None:
        btn_cls = getattr(ft, "Button", getattr(ft, "OutlinedButton", getattr(ft, "ElevatedButton", None)))

    # On_click sarmalayıcısı ile dokunma geri bildirimi (haptic) ve coroutine desteği
    wrapped_on_click = None
    if on_click is not None:
        def _tiklama_tetikle(e):
            dokunma_geribildirimi()
            res = None
            try:
                res = on_click(e)
            except TypeError:
                res = on_click()
            except Exception as ex_btn:
                print("Buton tıklama hatası:", ex_btn)
                return

            if res is not None and asyncio.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(res)
                except Exception:
                    try:
                        asyncio.create_task(res)
                    except Exception:
                        threading.Thread(target=lambda: asyncio.run(res), daemon=True).start()
        wrapped_on_click = _tiklama_tetikle

    style_obj = None
    if hasattr(ft, "ButtonStyle"):
        try:
            style_obj = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=border_radius)) if hasattr(ft, "RoundedRectangleBorder") else None
        except Exception:
            pass

    denemeler = [
        {"content": text, "icon": icon, "bgcolor": bgcolor, "color": color, "width": width, "height": height, "on_click": wrapped_on_click, "tooltip": tooltip, "style": style_obj},
        {"text": text, "icon": icon, "bgcolor": bgcolor, "color": color, "width": width, "height": height, "on_click": wrapped_on_click, "tooltip": tooltip},
        {"content": text, "icon": icon, "bgcolor": bgcolor, "color": color, "width": width, "height": height, "on_click": wrapped_on_click},
        {"text": text, "icon": icon, "bgcolor": bgcolor, "color": color, "width": width, "height": height, "on_click": wrapped_on_click},
        {"content": text, "width": width, "height": height, "on_click": wrapped_on_click},
        {"text": text, "width": width, "height": height, "on_click": wrapped_on_click},
        {"content": text},
        {"text": text},
    ]

    for p in denemeler:
        clean_p = {k: v for k, v in p.items() if v is not None}
        try:
            return btn_cls(**clean_p)
        except Exception:
            continue
    try:
        return ft.ElevatedButton(text=str(text), on_click=wrapped_on_click)
    except Exception:
        return ft.Container(content=ft.Text(str(text)), bgcolor=bgcolor, padding=8, on_click=wrapped_on_click)

def make_icon_btn(icon, on_click=None, icon_color=None, icon_size=20, tooltip=None, **kwargs):
    """Haptic dokunma titreşimli ve evrensel uyumlu simge buton üretir."""
    wrapped = None
    if on_click is not None:
        def _icon_tiklandi(e):
            dokunma_geribildirimi()
            res = None
            try:
                res = on_click(e)
            except TypeError:
                res = on_click()
            except Exception as ex_i:
                print("Simge tıklama hatası:", ex_i)
                return

            if res is not None and asyncio.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(res)
                except Exception:
                    try:
                        asyncio.create_task(res)
                    except Exception:
                        threading.Thread(target=lambda: asyncio.run(res), daemon=True).start()
        wrapped = _icon_tiklandi
    return ft.IconButton(
        icon=icon,
        icon_color=icon_color,
        icon_size=icon_size,
        tooltip=tooltip,
        on_click=wrapped,
        **kwargs
    )

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
HARCLIK_AYARLARI_DOSYASI = os.path.join(os.environ.get("FLET_APP_STORAGE_DATA") or BASE_DIR, "harclik_ayarlari.json")
TEMA_AYARI_DOSYASI = os.path.join(os.environ.get("FLET_APP_STORAGE_DATA") or BASE_DIR, "tema_ayari.json")

def tema_oku():
    if os.path.exists(TEMA_AYARI_DOSYASI):
        try:
            with open(TEMA_AYARI_DOSYASI, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("tema", "system")
        except Exception:
            pass
    return "system"

def tema_kaydet(tema_val):
    try:
        with open(TEMA_AYARI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump({"tema": tema_val}, f)
    except Exception as ex:
        print("Tema kaydetme hatası:", ex)


def harclik_ayarlari_oku():
    varsayilan = {
        "aktif": True,
        "cocuk_sayisi": 2,
        "birim_harclik": 10.0,
        "saat": "08:30",
        "tatil_kontrol": True,
        "otomatik_ekle": True
    }
    if os.path.exists(HARCLIK_AYARLARI_DOSYASI):
        try:
            with open(HARCLIK_AYARLARI_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                varsayilan.update(data)
        except Exception:
            pass
    return varsayilan

def harclik_ayarlari_kaydet(ayarlar):
    try:
        with open(HARCLIK_AYARLARI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(ayarlar, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Harçlık ayarları kaydedilemedi:", e)

def son_csvleri_bul():
    """Telefonda veya bilgisayarda İndirilenler klasöründeki CSV bütçe dosyalarını bulur."""
    klasorler = [
        "/storage/emulated/0/Download",
        "/storage/emulated/0",
        "/sdcard/Download",
        "/sdcard",
        os.path.expanduser("~/Downloads"),
        "."
    ]
    bulunanlar = []
    for k in klasorler:
        if os.path.exists(k) and os.path.isdir(k):
            try:
                for f in os.listdir(k):
                    if f.lower().endswith(".csv"):
                        tam_yol = os.path.join(k, f)
                        try:
                            mtime = os.path.getmtime(tam_yol)
                            bulunanlar.append((mtime, tam_yol))
                        except Exception:
                            pass
            except Exception:
                pass
    bulunanlar.sort(key=lambda x: x[0], reverse=True)
    return [yol for _, yol in bulunanlar[:6]]

def son_gorselleri_bul(limit=4):
    """Telefonda veya bilgisayarda en son çekilen veya indirilen görselleri bulur."""
    klasorler = [
        "/storage/emulated/0/DCIM/Camera",
        "/storage/emulated/0/DCIM/Screenshots",
        "/storage/emulated/0/DCIM",
        "/storage/emulated/0/Pictures/Screenshots",
        "/storage/emulated/0/Pictures/Camera",
        "/storage/emulated/0/Pictures",
        "/storage/emulated/0/Pictures/Gallery",
        "/storage/emulated/0/MIUI/Gallery/cloud",
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Documents",
        "/sdcard/DCIM/Camera",
        "/sdcard/DCIM/Screenshots",
        "/sdcard/DCIM",
        "/sdcard/Pictures/Screenshots",
        "/sdcard/Pictures",
        "/sdcard/Download",
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Pictures"),
        "."
    ]
    bulunanlar = []
    uzantilar = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic", ".pdf")
    for k in klasorler:
        if os.path.exists(k) and os.path.isdir(k):
            try:
                for f in os.listdir(k):
                    if f.lower().endswith(uzantilar):
                        tam_yol = os.path.join(k, f)
                        try:
                            mtime = os.path.getmtime(tam_yol)
                            bulunanlar.append((mtime, tam_yol))
                        except Exception:
                            pass
            except Exception:
                pass
    bulunanlar.sort(key=lambda x: x[0], reverse=True)
    sonuc = []
    for mtime, yol in bulunanlar[:limit]:
        try:
            dt = datetime.datetime.fromtimestamp(mtime)
            zaman_str = dt.strftime("%d.%m %H:%M")
        except Exception:
            zaman_str = ""
        dosya_adi = os.path.basename(yol)
        sonuc.append({"yol": yol, "ad": dosya_adi, "zaman": zaman_str})
    return sonuc

def okul_gunu_mu(tarih, tatil_kontrol=True):
    """
    Tarihin MEB (Millî Eğitim Bakanlığı) Resmî Çalışma Takvimine göre 
    okulların açık olduğu bir ders günü olup olmadığını tespit eder.
    Hafta sonları, resmî tatiller, dinî bayramlar, ara tatiller ve yarıyıl/yaz tatillerinde False döner.
    """
    if isinstance(tarih, str):
        tarih = stringden_tarih_al(tarih)
    if not tarih:
        return False
        
    # Hafta sonu kontrolü (Cumartesi=5, Pazar=6)
    if tarih.weekday() >= 5:
        return False
        
    if not tatil_kontrol:
        return True

    yil = tarih.year
    ay = tarih.month
    gun = tarih.day
    d_obj = datetime.date(yil, ay, gun) if not isinstance(tarih, datetime.date) else tarih

    # Sabit Resmî Tatiller (Ulusal bayram ve genel tatiller)
    sabit_resmi_tatiller = [
        (1, 1),    # 1 Ocak Yılbaşı
        (4, 23),   # 23 Nisan Ulusal Egemenlik ve Çocuk Bayramı
        (5, 1),    # 1 Mayıs Emek ve Dayanışma Günü
        (5, 19),   # 19 Mayıs Atatürk'ü Anma, Gençlik ve Spor Bayramı
        (7, 15),   # 15 Temmuz Demokrasi ve Millî Birlik Günü
        (8, 30),   # 30 Ağustos Zafer Bayramı
        (10, 29),  # 29 Ekim Cumhuriyet Bayramı
    ]
    if (ay, gun) in sabit_resmi_tatiller:
        return False

    # -------------------------------------------------------------
    # 2026 - 2027 Eğitim ve Öğretim Yılı (MEB Resmî Çalışma Takvimi)
    # -------------------------------------------------------------
    # - Öğretmen Mesleki Çalışma: 1 Eylül 2026 Salı
    # - Uyum Haftası (Okul Öncesi & İlkokul 1): 7 - 11 Eylül 2026
    # - Tüm Kademelerde Ders Başlangıcı: 14 Eylül 2026 Pazartesi
    # - 1. Dönem Ara Tatili: 16 - 20 Kasım 2026 (Haftasonları ile 14-22 Kasım)
    # - 1. Dönem Sonu (Karne): 22 Ocak 2027 Cuma
    # - Yarıyıl Tatili (Sömestr): 25 Ocak - 5 Şubat 2027 (Haftasonları ile 23 Ocak - 7 Şubat)
    # - 2. Dönem Başlangıcı: 8 Şubat 2027 Pazartesi
    # - 2. Dönem Ara Tatili & Ramazan Bayramı: 8 - 12 Mart 2027 (Haftasonları ile 6-14 Mart)
    # - Kurban Bayramı: 17 - 20 Mayıs 2027 (19 Mayıs ile birleşik)
    # - Ders Yılı Sonu (Kapanış & Karneler): 25 Haziran 2027 Cuma
    # -------------------------------------------------------------
    if (yil == 2026 and ay >= 7) or (yil == 2027 and ay <= 8):
        # 2026 Yaz Tatili (7 Eylül 2026 Uyum / Başlangıç öncesi okul kapalı)
        if d_obj < datetime.date(2026, 9, 7):
            return False
        # 1. Dönem Ara Tatili: 16 - 20 Kasım 2026
        if datetime.date(2026, 11, 16) <= d_obj <= datetime.date(2026, 11, 20):
            return False
        # Yarıyıl Tatili (Sömestr): 25 Ocak - 5 Şubat 2027
        if datetime.date(2027, 1, 25) <= d_obj <= datetime.date(2027, 2, 5):
            return False
        # 2. Dönem Ara Tatili & Ramazan Bayramı: 8 - 12 Mart 2027
        if datetime.date(2027, 3, 8) <= d_obj <= datetime.date(2027, 3, 12):
            return False
        # Kurban Bayramı Tatili: 17 - 20 Mayıs 2027
        if datetime.date(2027, 5, 17) <= d_obj <= datetime.date(2027, 5, 20):
            return False
        # 2027 Yaz Tatili (25 Haziran 2027 sonrası ders yılı kapanışı)
        if d_obj > datetime.date(2027, 6, 25):
            return False
        return True

    # -------------------------------------------------------------
    # 2025 - 2026 Eğitim ve Öğretim Yılı (MEB Resmî Çalışma Takvimi)
    # -------------------------------------------------------------
    if (yil == 2025 and ay >= 7) or (yil == 2026 and ay <= 8):
        if d_obj < datetime.date(2025, 9, 8):
            return False
        # 1. Ara Tatil: 10 - 14 Kasım 2025
        if datetime.date(2025, 11, 10) <= d_obj <= datetime.date(2025, 11, 14):
            return False
        # Yarıyıl Tatili: 19 - 30 Ocak 2026
        if datetime.date(2026, 1, 19) <= d_obj <= datetime.date(2026, 1, 30):
            return False
        # Ramazan Bayramı: 20 Mart 2026
        if datetime.date(2026, 3, 20) <= d_obj <= datetime.date(2026, 3, 22):
            return False
        # 2. Ara Tatil: 6 - 10 Nisan 2026
        if datetime.date(2026, 4, 6) <= d_obj <= datetime.date(2026, 4, 10):
            return False
        # Kurban Bayramı: 27 - 30 Mayıs 2026
        if datetime.date(2026, 5, 27) <= d_obj <= datetime.date(2026, 5, 30):
            return False
        # Ders Yılı Sonu: 19 Haziran 2026
        if d_obj > datetime.date(2026, 6, 19):
            return False
        return True

    # -------------------------------------------------------------
    # 2024 - 2025 Eğitim ve Öğretim Yılı (MEB Resmî Çalışma Takvimi)
    # -------------------------------------------------------------
    if (yil == 2024 and ay >= 7) or (yil == 2025 and ay <= 8):
        if d_obj < datetime.date(2024, 9, 9):
            return False
        # 1. Ara Tatil: 11 - 15 Kasım 2024
        if datetime.date(2024, 11, 11) <= d_obj <= datetime.date(2024, 11, 15):
            return False
        # Yarıyıl Tatili: 20 - 31 Ocak 2025
        if datetime.date(2025, 1, 20) <= d_obj <= datetime.date(2025, 1, 31):
            return False
        # 2. Ara Tatil & Ramazan Bayramı: 31 Mart - 4 Nisan 2025
        if datetime.date(2025, 3, 31) <= d_obj <= datetime.date(2025, 4, 4):
            return False
        # Kurban Bayramı: 6 - 9 Haziran 2025
        if datetime.date(2025, 6, 6) <= d_obj <= datetime.date(2025, 6, 9):
            return False
        # Ders Yılı Sonu: 20 Haziran 2025
        if d_obj > datetime.date(2025, 6, 20):
            return False
        return True

    # Genel Şablon (Diğer yıllar için standart MEB tatil periyotları)
    if ay in [7, 8] or (ay == 6 and gun > 20) or (ay == 9 and gun < 8):
        return False
    if ay == 11 and 10 <= gun <= 16:
        return False
    if (ay == 1 and gun >= 20) or (ay == 2 and gun <= 5):
        return False
    if ay == 4 and 10 <= gun <= 16:
        return False

    return True

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
# Supabase Bulut Veritabanı Bağlantısı (Evrensel Sıfır-Bağımlılık REST İstemcisi)
# ==============================================================================
SUPABASE_URL = "https://ivngkowxxafkyvvzhdob.supabase.co"
SUPABASE_KEY = "sb_publishable_0pVRLE1ceJ0FlI32XGzbsw_Z_mldcXe"

class _SupabaseQueryBuilder:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.action = "select"
        self.params = {}
        self.filters = []
        self.data_payload = None

    def select(self, columns="*"):
        self.action = "select"
        self.params["select"] = columns
        return self

    def order(self, column, desc=False):
        direction = "desc" if desc else "asc"
        self.params["order"] = f"{column}.{direction}"
        return self

    def limit(self, count):
        self.params["limit"] = str(count)
        return self

    def eq(self, column, value):
        self.filters.append((column, f"eq.{value}"))
        return self

    def in_(self, column, values):
        val_str = "(" + ",".join([str(v) for v in values]) + ")"
        self.filters.append((column, f"in.{val_str}"))
        return self

    def insert(self, data):
        self.action = "insert"
        self.data_payload = data if isinstance(data, list) else [data]
        return self

    def update(self, data):
        self.action = "update"
        self.data_payload = data
        return self

    def delete(self):
        self.action = "delete"
        return self

    def execute(self):
        import urllib.request
        import urllib.parse
        import json
        import types
        import ssl

        res = types.SimpleNamespace(data=None)
        query_parts = [f"{k}={urllib.parse.quote(str(v))}" for k, v in self.params.items()]
        for col, flt in self.filters:
            query_parts.append(f"{urllib.parse.quote(col)}={urllib.parse.quote(flt)}")
        query_str = ("?" + "&".join(query_parts)) if query_parts else ""

        url = f"{self.client.base_url}/{self.table}{query_str}"
        method = "GET"
        body = None

        if self.action == "insert":
            method = "POST"
            body = json.dumps(self.data_payload).encode("utf-8")
        elif self.action == "update":
            method = "PATCH"
            body = json.dumps(self.data_payload).encode("utf-8")
        elif self.action == "delete":
            method = "DELETE"

        req = urllib.request.Request(url, data=body, headers=self.client.headers, method=method)

        ssl_ctx = None
        try:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
        except Exception:
            pass

        try:
            kw = {"timeout": 15}
            if ssl_ctx:
                kw["context"] = ssl_ctx
            with urllib.request.urlopen(req, **kw) as resp:
                resp_bytes = resp.read()
                if resp_bytes:
                    res.data = json.loads(resp_bytes.decode("utf-8"))
                else:
                    res.data = []
        except Exception as e:
            print(f"Supabase REST hatası ({self.action} on {self.table}):", e)
            res.data = None
        return res

class SupabaseRestClient:
    def __init__(self, url, key):
        self.base_url = url.rstrip('/') + "/rest/v1"
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def table(self, table_name):
        return _SupabaseQueryBuilder(self, table_name)

supabase = None
try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase istemcisi başarıyla bağlandı.")
except Exception:
    # Android'de veya kütüphane eksikse saf REST istemcisini devreye sok
    supabase = SupabaseRestClient(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase REST bulut köprüsü başarıyla aktif edildi.")


# ==============================================================================
# Google Gemini AI Fiş Tarama Entegrasyonu
# ==============================================================================

# ==============================================================================
# Standart Harcama Kategorileri
# ==============================================================================
KATEGORILER_DOSYASI = os.path.join(os.environ.get("FLET_APP_STORAGE_DATA") or BASE_DIR, "kategoriler.json")
GELIR_TURLERI_DOSYASI = os.path.join(os.environ.get("FLET_APP_STORAGE_DATA") or BASE_DIR, "gelir_turleri.json")

# Kapsamlı Standart Harcama Kategorileri (Tüm ev, aile, araç, eğitim ve kişisel harcamaları kapsar)
VARSAYILAN_GIDER_KATEGORILERI = [
    "Market & Temel Gıda",
    "Kasap & Şarküteri & Manav",
    "Fırın & Unlu Mamuller",
    "Abur Cubur & Atıştırmalık",
    "Ev & Faturalar (Elektrik, Su, Doğalgaz)",
    "Kira & Aidat",
    "İnternet, Telefon & TV",
    "Temizlik & Hijyen",
    "Kişisel Bakım & Kozmetik",
    "Giyim, Ayakkabı & Aksesuar",
    "Sağlık, İlaç & Medikal",
    "Eğitim, Okul & Kırtasiye",
    "Çocuk & Bebek",
    "Ulaşım & Toplu Taşıma",
    "Akaryakıt & Yakıt",
    "Araç Bakım & Muayene & Servis",
    "Dışarıda Yemek & Kafe & Restoran",
    "Eğlence, Kültür & Etkinlik",
    "Elektronik & Teknoloji",
    "Ev Eşyası & Mobilya & Beyaz Eşya",
    "Tadilat, Tamirat & Yapı Market",
    "Evcil Hayvan (Pamuk)",
    "Sigara/Tütün",
    "Spor, Fitness & Hobi",
    "Tatil & Seyahat & Konaklama",
    "Hediye, Bağış & Yardımlaşma",
    "Kredi Kartı, Kredi Ödemesi & Borç",
    "Vergi, Harç & Resmi İşlemler",
    "Sigorta, Kasko & Bireysel Emeklilik",
    "Transfer / Birikim",
    "Yatırım & Altın & Döviz",
    "Diğer"
]

# Güncellenmiş Gelir Türleri (Ek Ders ve Hediye eklendi, Kira Geliri ve Yatırım/Faiz silindi)
VARSAYILAN_GELIR_TURLERI = [
    "Maaş",
    "Ek Ders",
    "Hediye",
    "Ek Gelir / Serbest",
    "Diğer"
]

def kategoriler_oku():
    if os.path.exists(KATEGORILER_DOSYASI):
        try:
            with open(KATEGORILER_DOSYASI, "r", encoding="utf-8") as f:
                veriler = json.load(f)
                if isinstance(veriler, list) and len(veriler) > 0:
                    return veriler
        except Exception:
            pass
    return list(VARSAYILAN_GIDER_KATEGORILERI)

def kategoriler_kaydet(kat_listesi):
    try:
        with open(KATEGORILER_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(kat_listesi, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def gelir_turleri_oku():
    if os.path.exists(GELIR_TURLERI_DOSYASI):
        try:
            with open(GELIR_TURLERI_DOSYASI, "r", encoding="utf-8") as f:
                veriler = json.load(f)
                if isinstance(veriler, list) and len(veriler) > 0:
                    return veriler
        except Exception:
            pass
    return list(VARSAYILAN_GELIR_TURLERI)

def gelir_turleri_kaydet(tur_listesi):
    try:
        with open(GELIR_TURLERI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(tur_listesi, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def kategori_ekle(yeni_kat):
    yeni = str(yeni_kat).strip()
    if not yeni:
        return False
    mevcut = kategoriler_oku()
    if yeni not in mevcut:
        if "Diğer" in mevcut:
            mevcut.remove("Diğer")
            mevcut.append(yeni)
            mevcut.append("Diğer")
        else:
            mevcut.append(yeni)
        kategoriler_kaydet(mevcut)
        GIDER_KATEGORILERI.clear()
        GIDER_KATEGORILERI.extend(mevcut)
        return True
    return False

def gelir_turu_ekle(yeni_tur):
    yeni = str(yeni_tur).strip()
    if not yeni:
        return False
    mevcut = gelir_turleri_oku()
    if yeni not in mevcut:
        if "Diğer" in mevcut:
            mevcut.remove("Diğer")
            mevcut.append(yeni)
            mevcut.append("Diğer")
        else:
            mevcut.append(yeni)
        gelir_turleri_kaydet(mevcut)
        GELIR_TURLERI.clear()
        GELIR_TURLERI.extend(mevcut)
        return True
    return False

GIDER_KATEGORILERI = kategoriler_oku()
GELIR_TURLERI = gelir_turleri_oku()
kategoriler = GIDER_KATEGORILERI

GEMINI_KEY_DOSYASI = os.path.join(os.environ.get("FLET_APP_STORAGE_DATA") or BASE_DIR, "gemini_key.json")

def gemini_api_key_al():
    """Kullanıcının yerel olarak saklanan veya ortamdaki Gemini API anahtarını güvenle çeker."""
    if os.path.exists(GEMINI_KEY_DOSYASI):
        try:
            with open(GEMINI_KEY_DOSYASI, "r", encoding="utf-8") as f:
                d = json.load(f)
                k = d.get("api_key", "").strip()
                if k:
                    return k
        except Exception:
            pass
    if "GEMINI_API_KEY" in os.environ and os.environ["GEMINI_API_KEY"].strip():
        return os.environ["GEMINI_API_KEY"].strip()
    return ""

def gemini_api_key_kaydet(key_val):
    """API anahtarını cihazın yerel güvenli deposuna kaydeder (GitHub'a asla yüklenmez)."""
    try:
        with open(GEMINI_KEY_DOSYASI, "w", encoding="utf-8") as f:
            json.dump({"api_key": key_val.strip()}, f, ensure_ascii=False)
        return True
    except Exception as e:
        print("Gemini API anahtarı kaydedilemedi:", e)
        return False

GEMINI_API_KEY = gemini_api_key_al()

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

    # Gerçek, en güncel ve hızlı Google Gemini Flash modelleri
    oncelik = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-8b",
        "gemini-flash-latest"
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
            ("v1beta", "gemini-2.0-flash"),
            ("v1beta", "gemini-1.5-flash"),
            ("v1beta", "gemini-1.5-flash-latest"),
            ("v1beta", "gemini-flash-latest"),
            ("v1", "gemini-1.5-flash")
        ]
    return sirali

def kategori_akilli_duzelt(urun_adi, firma="", mevcut_kat=""):
    """Ürün ve firma adından harcama kategorisini %100 doğrulukla tespit eder veya düzeltir."""
    u = str(urun_adi or "").lower().strip()
    f = str(firma or "").lower().strip()
    m = str(mevcut_kat or "").strip()

    # 1. Sigara & Tütün Ürünleri
    sigara_kelimeler = [
        "sigara", "tütün", "tutun", "rothmans", "winston", "marlboro", "parliament",
        "kent", "camel", "tekel", "heets", "terea", "iqos", "puro", "makaron",
        "çakmak", "cakmak", "sarılmış tütün"
    ]
    if any(w in u for w in sigara_kelimeler):
        return "Sigara/Tütün"

    # 2. Abur Cubur & Atıştırmalık (Çikolata, Gofret, Bisküvi, Kek, Cips, Dondurma, Şekerleme vb.)
    abur_cubur_kelimeler = [
        "çikolata", "cikolata", "çikolatalı", "cikolatali", "çikol", "cikol", "ciko", "çiko",
        "tadelle", "canga", "albeni", "metro", "karam", "damak", "snickers", "twix", "bounty",
        "toblerone", "nutella", "çokokrem", "cokokrem", "gofret", "hoşbeş", "hosbes", "çokonat",
        "dido", "çikotren", "bisküvi", "biskuvi", "burçak", "burcak", "biskrem", "ikram", "negro",
        "petibör", "petibor", "oreo", "eti puf", "probis", "hanımeller", "saklıköy", "saklikoy",
        "kraker", "crax", "çubuk kraker", "cubuk kraker", "balık kraker", "balik kraker",
        "kek", "topkek", "paykek", "browni", "dankek", "popkek", "tart", "kurabiye", "sufle",
        "puding", "cips", "doritos", "lays", "ruffles", "patito", "pringles", "çerezos", "cerezoz",
        "kuruyemiş", "kuruyemis", "fıstık", "fistik", "fındık", "findik", "kaju", "badem",
        "çekirdek", "cekirdek", "leblebi", "dondurma", "golf", "cornetto", "magnum", "roko",
        "lungo", "algida", "buzparmak", "twister", "şekerleme", "sekerleme", "jelibon", "haribo",
        "bonbon", "lolipop", "draje", "mentos", "sakız", "sakiz", "falım", "falim", "vivident",
        "first", "şıpsevdi", "kola", "cola", "fanta", "sprite", "gazoz", "meşrubat", "mesrubat",
        "enerji içeceği", "soğuk çay", "ice tea", "fuse tea", "cevizli sucuk", "pestil", "lokum", "helva"
    ]
    if any(w in u for w in abur_cubur_kelimeler):
        return "Abur Cubur & Atıştırmalık"

    # 3. Temizlik & Kişisel Hijyen
    temizlik_kelimeler = [
        "deterjan", "çamaşır suyu", "camasir suyu", "yumuşatıcı", "yumusatici", "bulaşık tableti",
        "bulasik tableti", "bulaşık deterjanı", "bulaşık sıvısı", "fairy", "finish", "calgon",
        "pril", "omo", "ariel", "bingo", "perwoll", "tursil", "cif", "domestos", "porçöz", "porcoz",
        "çöp torbası", "cop torbasi", "bulaşık süngeri", "temizlik bezi", "mop", "vileda",
        "şampuan", "sampuan", "duş jeli", "dus jeli", "sabun", "sıvı sabun", "sivi sabun",
        "diş macunu", "dis macunu", "diş fırçası", "dis fircasi", "tuvalet kağıdı", "tuvalet kagidi",
        "kağıt havlu", "kagit havlu", "peçete", "pecete", "ıslak mendil", "islak mendil",
        "ıslak havlu", "islak havlu", "ped", "hijyenik ped", "molped", "orkid", "kotex", "günlük ped",
        "bebek bezi", "kolay tarama spreyi"
    ]
    if any(w in u for w in temizlik_kelimeler):
        return "Temizlik"

    # 4. Ev & Faturalar
    fatura_kelimeler = [
        "doğalgaz", "dogalgaz", "palen", "elektrik", "aras elektrik", "enerjisa", "su faturası",
        "fatura", "faturası", "internet", "fiber", "vodafone", "türk telekom", "turkcell",
        "aidat", "apartman", "kira", "ev kirası", "süpürge torbası", "filtre seti", "ampul",
        "led panel", "duş hortumu", "silikonize mastik", "sürgü", "ütü", "pişirme kağıdı",
        "buzdolabı poşeti"
    ]
    if any(w in u for w in fatura_kelimeler) or any(w in f for w in ["palen", "vodafone", "elektrik", "aidat", "kira"]):
        return "Ev & Faturalar"

    # 5. Ulaşım & Yakıt
    ulasim_kelimeler = [
        "benzin", "motorin", "mazot", "lpg", "akaryakıt", "petrol", "opet", "shell", "bp",
        "otobüs", "dolmuş", "taksi", "otopark", "hgs", "ogs", "araç yıkama", "lastik"
    ]
    if any(w in u for w in ulasim_kelimeler) or any(w in f for w in ["shell", "opet", "bp", "petrol"]):
        return "Ulaşım / Yakıt"

    # 6. Sağlık
    saglik_kelimeler = [
        "eczane", "ilaç", "ilac", "vitamin", "pastil", "surup", "şurup", "aspirin", "parol",
        "merhem", "yara bandı", "medikal", "hastane"
    ]
    if any(w in u for w in saglik_kelimeler) or "eczane" in f:
        return "Sağlık"

    # 7. Evcil Hayvan
    if any(w in u for w in ["kedi mama", "köpek mama", "kedi kum", "pamuk"]):
        return "Evcil Hayvan (Pamuk)"

    # 8. Eğitim & Okul
    if any(w in u for w in ["okul harçlığı", "harçlık", "harclik", "kırtasiye", "kirtasiye", "defter", "kalem", "okul"]):
        return "Eğitim & Okul"

    # 9. Giyim
    if any(w in u for w in ["pantolon", "gömlek", "tişört", "mont", "ayakkabı", "çorap", "kazak"]):
        return "Giyim"

    # 10. Dışarıda Yemek
    if any(w in u for w in ["döner", "kebap", "pizza", "burger", "lahmacun", "pide", "kafe", "restoran"]):
        return "Dışarıda Yemek / Eğlence"

    # Eğer mevcut kategori GIDER_KATEGORILERI içindeyse ve "Diğer" değilse koru, aksi halde Market
    if m in GIDER_KATEGORILERI and m != "Diğer":
        return m

    return "Market & Temel Gıda"

def gemini_fis_analiz_et(gorsel_yolu, api_key=None, status_cb=None):
    if not api_key:
        api_key = gemini_api_key_al()
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
        status_cb("📄 İçerik hazırlanıyor..." if ext == ".txt" else "📸 Görsel hazırlanıyor...")

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

    b64_data = base64.b64encode(img_bytes).decode("utf-8") if ext != ".txt" else ""

    prompt = """Sen uzman bir market, mağaza ve alışveriş fişi/faturası analiz asistanısın. Bu fiş veya fatura belgesindeki bilgileri oku. Yalnızca geçerli bir JSON nesnesi döndür (markdown kod blokları ekleme, doğrudan saf json döndür).
JSON yapısı:
{
  "firma": "Market/Mağaza Adı (örn: BİM, Migros, A101, ŞOK, Eczane)",
  "tarih": "GG.AA.YYYY formatında fiş tarihi (örn: 03.11.2026, bulunamazsa bugünün tarihi)",
  "saat": "SS:DD formatında fiş saati (örn: 14:35, bulunamazsa 12:00)",
  "urunler": [
    {
      "urun": "Ürün/Hizmet Adı (kısaltmaları anlaşılır yap, örn: GOLF ROKO ÇİKOLATA, ETİ BURÇAK)",
      "miktar": "Miktar (örn: 1 Adet, 1.5 kg, 2 Paket)",
      "birim_fiyat": 25.50,
      "tutar": 51.00,
      "kategori": "Aşağıdaki kategorilerden en uygununu seç: 'Abur Cubur & Atıştırmalık', 'Market & Temel Gıda', 'Temizlik', 'Sigara/Tütün', 'Ev & Faturalar', 'Ulaşım / Yakıt', 'Dışarıda Yemek / Eğlence', 'Giyim', 'Sağlık', 'Eğitim & Okul', 'Evcil Hayvan (Pamuk)', 'Diğer'"
    }
  ],
  "toplam_tutar": 51.00
}

KATEGORİ KURALLARI (ÇOK ÖNEMLİ):
1. 'Abur Cubur & Atıştırmalık': Çikolata, gofret, bisküvi, kek, cips, kraker, dondurma (golf, magnum, roko, lungo), şekerleme, sakız, kuruyemiş, gazlı içecek, meşrubat, soğuk çay, puding. (Çikolata, bisküvi, dondurma vb. tatlıları KESİNLİKLE temel gıda yapma, 'Abur Cubur & Atıştırmalık' olarak etiketle).
2. 'Market & Temel Gıda': Ekmek, un, süt, yoğurt, peynir, yumurta, sıvı yağ, zeytin, salça, bakliyat, et, tavuk, balık, sebze, meyve, makarna, pirinç, çay, baharat.
3. 'Temizlik': Deterjan, yumuşatıcı, bulaşık tableti/sıvısı, çamaşır suyu, şampuan, sabun, duş jeli, diş macunu/fırçası, tuvalet kağıdı, peçete, ıslak mendil, hijyenik ped, çöp torbası.
4. 'Sigara/Tütün': Sigara ve tütün mamulleri.
5. 'Ev & Faturalar': Doğalgaz, elektrik, su, internet, telefon faturaları, kira, aidat, ev gereçleri.
6. 'Ulaşım / Yakıt': Benzin, motorin, lpg, otobüs, dolmuş, taksi, otopark.
7. 'Dışarıda Yemek / Eğlence': Restoran, kafe, döner, kebap, fast food.
8. 'Sağlık': Eczane, ilaç, vitamin, medikal."""

    if ext == ".txt":
        raw_txt = img_bytes.decode("utf-8", errors="replace")
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt + f"\n\nAnaliz Edilecek Fiş/Dekont Metni:\n{raw_txt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }
    else:
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
                        # Kategorileri akıllı kurallarla düzelt ve doğrula
                        firma_adi = parsed.get("firma") or "Market"
                        for u_item in parsed.get("urunler", []):
                            u_item["kategori"] = kategori_akilli_duzelt(u_item.get("urun"), firma=firma_adi, mevcut_kat=u_item.get("kategori"))
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
        return None
    t_clean = str(tarih_str).split(" ")[0].strip()
    for sep in ["-", "/", "."]:
        if sep in t_clean:
            parts = t_clean.split(sep)
            if len(parts) == 3:
                try:
                    p0 = int(parts[0])
                    p1 = int(parts[1])
                    p2 = int(parts[2])
                    if len(parts[0]) == 4:
                        return f"{p2:02d}.{p1:02d}.{p0:04d}"
                    else:
                        return f"{p0:02d}.{p1:02d}.{p2:04d}"
                except Exception:
                    pass
    return None

def stringden_tarih_al(tarih_str):
    """Metin halindeki tarihi her formattan datetime.date nesnesine güvenle çevirir."""
    if not tarih_str:
        return None
    try:
        std = standart_tarih_yap(tarih_str)
        if not std:
            return None
        d, m, y = map(int, std.split("."))
        return datetime.date(y, m, d)
    except Exception:
        return None


# ==============================================================================
# GEÇMİŞ FİYAT HAFIZALI DOĞAL DİL / SÖZEL İŞLEM MOTORU
# ==============================================================================
def hafiza_olustur(islemler_listesi):
    """Kullanıcının geçmiş işlemlerinden ürün ve birim fiyat hafızası oluşturur."""
    hafiza = {}
    for it in islemler_listesi:
        firma = (it.get("firma") or it.get("kaynak") or "").strip()
        urun = (it.get("urun") or it.get("aciklama") or "").strip()
        birim = str(it.get("birim_fiyat") or "").strip()
        kat = it.get("kategori") or "Diğer"
        if firma and urun and birim and birim != "-":
            key = f"{firma.lower()} - {urun.lower()}"
            hafiza[key] = {
                "firma": firma,
                "urun": urun,
                "birim_fiyat": birim,
                "kategori": kat
            }
    return hafiza

def parse_sozel_ifade_yerel(cumle, fiyat_hafizasi):
    """Gelişmiş çevrimdışı / anlık akıllı kural tabanlı sözel ifade ayrıştırıcı."""
    c = str(cumle or "").strip()
    c_lower = c.lower()
    
    # İşlem türü belirleme
    tur = "Gider"
    if any(k in c_lower for k in ["maaş", "maas", "ek ders", "yattı", "yatti", "gelir", "ödenek"]):
        tur = "Gelir"
    elif any(k in c_lower for k in ["aktar", "gönder", "gonder", "havale", "eft", "harçlık ver", "harclik ver"]):
        tur = "Para Aktarımı"

    # Saat tespiti
    saat_str = datetime.datetime.now().strftime("%H:%M")
    saat_match = re.search(r'\b([01]?\d|2[0-3])[:.]([0-5]\d)\b', c)
    if saat_match:
        saat_str = f"{int(saat_match.group(1)):02d}:{int(saat_match.group(2)):02d}"

    # Tarih tespiti (bugün / dün / gg.aa)
    bugun_dt = datetime.date.today()
    if "dün" in c_lower or "dun" in c_lower:
        tarih_str = (bugun_dt - datetime.timedelta(days=1)).strftime("%d.%m.%Y")
    else:
        t_match = re.search(r'\b(0?[1-9]|[12]\d|3[01])[./](0?[1-9]|1[0-2])([./](\d{4}))?\b', c)
        if t_match:
            d_val = int(t_match.group(1))
            m_val = int(t_match.group(2))
            y_val = int(t_match.group(4)) if t_match.group(4) else bugun_dt.year
            tarih_str = f"{d_val:02d}.{m_val:02d}.{y_val}"
        else:
            tarih_str = bugun_dt.strftime("%d.%m.%Y")

    # Firma tespiti
    firmalar = [
        ("bim", "BİM"), ("bi̇m", "BİM"), ("a101", "A101"), ("şok", "ŞOK"), ("sok", "ŞOK"),
        ("migros", "Migros"), ("carrefour", "Carrefour"), ("düzgün", "Düzgün Market"),
        ("tarım kredi", "Tarım Kredi"), ("tarim kredi", "Tarım Kredi"), ("pazar", "Pazar"),
        ("fırın", "Fırın"), ("firin", "Fırın"), ("eczane", "Eczane"), ("shell", "Shell"),
        ("opet", "Opet"), ("bp", "BP"), ("petrol", "Petrol"), ("palen", "Palen Doğalgaz"),
        ("türk telekom", "Türk Telekom"), ("vodafone", "Vodafone"), ("turkcell", "Turkcell"),
        ("nakit", "Nakit"), ("okul", "Okul")
    ]
    bulunan_firma = "Market"
    for k, f_ad in firmalar:
        if k in c_lower:
            bulunan_firma = f_ad
            break

    # Miktar tespiti
    miktar_sayi = 1.0
    miktar_str = "1 adet"
    m_match = re.search(r'\b(\d+([.,]\d+)?)\s*(adet|tane|koli|kilo|kg|paket|ekmek|litre|lt|porsiyon)\b', c_lower)
    if m_match:
        miktar_sayi = float(m_match.group(1).replace(",", "."))
        birim_ad = m_match.group(3)
        if birim_ad in ["ekmek"]:
            miktar_str = f"{int(miktar_sayi) if miktar_sayi==int(miktar_sayi) else miktar_sayi} adet"
        else:
            miktar_str = f"{int(miktar_sayi) if miktar_sayi==int(miktar_sayi) else miktar_sayi} {birim_ad}"
    else:
        # Sayı varsa doğrudan miktar olarak al
        sayi_match = re.search(r'\b(\d+)\s+([a-zA-ZçğıöşüÇĞİÖŞÜ]+)', c_lower)
        if sayi_match and sayi_match.group(2) not in ["tl", "lira", "liraya", "saat", "de", "da", "te", "ta"]:
            miktar_sayi = float(sayi_match.group(1))
            miktar_str = f"{int(miktar_sayi)} adet"

    # Fiyat / Tutar tespiti
    toplam_tutar = 0.0
    birim_fiyat = 0.0
    fiyat_match = re.search(r'\b(\d+([.,]\d{1,2})?)\s*(tl|lira|liraya|liralık|liralk)\b', c_lower)
    if fiyat_match:
        toplam_tutar = float(fiyat_match.group(1).replace(",", "."))
        birim_fiyat = toplam_tutar / miktar_sayi if miktar_sayi else toplam_tutar
    else:
        # Cümlenin sonundaki bağımsız sayı tutar olabilir (örn: 'bim süt 45')
        son_sayi = re.findall(r'\b(\d+([.,]\d{1,2})?)\b', c_lower)
        if son_sayi:
            for s_tuple in reversed(son_sayi):
                val_cand = float(s_tuple[0].replace(",", "."))
                if val_cand != miktar_sayi and ":" not in s_tuple[0] and "." not in s_tuple[0]:
                    toplam_tutar = val_cand
                    birim_fiyat = toplam_tutar / miktar_sayi if miktar_sayi else toplam_tutar
                    break

    # Ürün tespiti
    urun_adi = "Genel Harcama"
    bilinen_urunler = [
        "ekmek", "süt", "sut", "yumurta", "peynir", "yoğurt", "yogurt", "çay", "cay",
        "tost", "benzin", "mazot", "su", "kahve", "simit", "sigara", "deterjan", "yağ", "yag",
        "makarna", "pirinç", "pirinc", "un", "şeker", "seker", "tavuk", "et", "kıyma", "kiyma"
    ]
    for u_word in bilinen_urunler:
        if u_word in c_lower:
            urun_adi = u_word.title()
            break

    # Hafızadan fiyat tamamlama
    if toplam_tutar == 0.0 and urun_adi != "Genel Harcama":
        for k_key, d in fiyat_hafizasi.items():
            f_k = (d.get("firma") or "").lower()
            u_k = (d.get("urun") or "").lower()
            if (bulunan_firma.lower() in f_k or not bulunan_firma) and (urun_adi.lower() in u_k):
                try:
                    bf_hafiza = float(str(d.get("birim_fiyat") or 0.0).replace(",", "."))
                    if bf_hafiza > 0:
                        birim_fiyat = bf_hafiza
                        toplam_tutar = birim_fiyat * miktar_sayi
                        break
                except Exception:
                    pass

    kat = kategori_akilli_duzelt(urun_adi, bulunan_firma)

    return {
        "tur": tur,
        "firma": bulunan_firma,
        "urun": urun_adi,
        "miktar": miktar_str,
        "birim_fiyat": f"{birim_fiyat:.2f}" if birim_fiyat else "",
        "tutar": float(toplam_tutar),
        "tarih": tarih_str,
        "saat": saat_str,
        "kategori": kat
    }

def _eski_parse_sozel_ifade_yerel(cumle, fiyat_hafizasi):
    """Çevrimdışı / anlık akıllı kural tabanlı sözel ifade ayrıştırıcı."""
    c = cumle.strip()
    
    # Saat tespiti (örn: 14.21, 14:21)
    saat_str = datetime.datetime.now().strftime("%H:%M")
    saat_match = re.search(r'\b([01]?\d|2[0-3])[:.]([0-5]\d)\b', c)
    if saat_match:
        saat_str = f"{int(saat_match.group(1)):02d}:{int(saat_match.group(2)):02d}"
        c_temiz = c[:saat_match.start()] + " " + c[saat_match.end():]
    else:
        c_temiz = c

    c_lower = c_temiz.lower()

    # Firma tespiti
    firmalar = [
        ("bim", "BİM"), ("bi̇m", "BİM"), ("a101", "A101"), ("şok", "ŞOK"), ("sok", "ŞOK"),
        ("migros", "Migros"), ("carrefour", "Carrefour"), ("düzgün", "Düzgün Market"),
        ("tarım kredi", "Tarım Kredi"), ("pazar", "Pazar"), ("fırın", "Fırın"),
        ("eczane", "Eczane"), ("benzin", "Petrol"), ("petrol", "Petrol"),
        ("nakit", "Nakit"), ("okul", "Okul"), ("pansiyon", "Pansiyon")
    ]
    bulunan_firma = "Market"
    for k, f_ad in firmalar:
        if k in c_lower:
            bulunan_firma = f_ad
            break

    # Miktar ve ürün kelimesi tespiti
    miktar_sayi = 1.0
    miktar_birim = "adet"
    urun_kelimesi = ""

    m_match = re.search(r'\b(\d+([.,]\d+)?)\s*(adet|tane|koli|kilo|kg|paket|takım|porsiyon)?\s*([a-zA-ZçğıöşüÇĞİÖŞÜ]+)', c_lower)
    if m_match:
        miktar_sayi = float(m_match.group(1).replace(",", "."))
        if m_match.group(3):
            miktar_birim = m_match.group(3)
        kelime = m_match.group(4)
        if kelime not in ["tl", "lira", "kuruş", "de", "da", "te", "ta", "alındı", "aldım", "yattı", "harcandı", "ödedim"]:
            urun_kelimesi = kelime

    if not urun_kelimesi:
        for w in ["ekmek", "süt", "yumurta", "peynir", "çay", "tost", "benzin", "su", "kahve", "simit", "sigara"]:
            if w in c_lower:
                urun_kelimesi = w
                break

    # Fiyat tespiti (cümlede açıkça belirtilmiş mi, yoksa hafızadan mı çekilecek?)
    fiyat_match = re.search(r'\b(\d+([.,]\d{1,2})?)\s*(tl|lira|liraya|liralık)\b', c_lower)
    birim_fiyat = None
    tam_eslesen_urun = (urun_kelimesi or "Ürün").title()
    bulunan_kat = "Market & Temel Gıda"

    if fiyat_match:
        toplam_tutar = float(fiyat_match.group(1).replace(",", "."))
        birim_fiyat = toplam_tutar / miktar_sayi if miktar_sayi else toplam_tutar
    else:
        # Fiyat hafızasından hatırlama! (BİM'de ekmek 11 TL vb.)
        # 1. Aşama: Firma + Ürün eşleşmesi (Standart/Tekli ürünleri önceliklendir)
        adaylar = []
        for k_key, d in fiyat_hafizasi.items():
            f_k = (d.get("firma") or "").lower()
            u_k = (d.get("urun") or "").lower()
            if bulunan_firma.lower() in f_k and urun_kelimesi.lower() in u_k:
                adaylar.append(d)

        if adaylar:
            secilen_d = None
            for ad in adaylar:
                u_lower = (ad.get("urun") or "").lower()
                if "tekli" in u_lower or u_lower == urun_kelimesi.lower() or "standart" in u_lower:
                    secilen_d = ad
                    break
            if not secilen_d:
                secilen_d = adaylar[0]

            try:
                bf_str = str(secilen_d["birim_fiyat"]).replace("TL", "").replace("₺", "").replace(".", "").replace(",", ".").strip()
                birim_fiyat = float(bf_str)
                tam_eslesen_urun = secilen_d["urun"]
                bulunan_kat = secilen_d.get("kategori", "Market & Temel Gıda")
            except Exception:
                pass

        # 2. Aşama: Sadece Ürün adı eşleşmesi
        if not birim_fiyat:
            for k_key, d in fiyat_hafizasi.items():
                u_k = (d.get("urun") or "").lower()
                if urun_kelimesi.lower() in u_k:
                    try:
                        bf_str = str(d["birim_fiyat"]).replace("TL", "").replace("₺", "").replace(".", "").replace(",", ".").strip()
                        birim_fiyat = float(bf_str)
                        tam_eslesen_urun = d["urun"]
                        bulunan_kat = d.get("kategori", "Market & Temel Gıda")
                        break
                    except Exception:
                        pass

        # 3. Aşama: Bilinen genel varsayılan
        if not birim_fiyat:
            if "ekmek" in urun_kelimesi.lower():
                birim_fiyat = 11.0
                tam_eslesen_urun = "EKMEK TEKLİ"
            else:
                birim_fiyat = 25.0
                tam_eslesen_urun = (urun_kelimesi or "Ürün").title()

        toplam_tutar = birim_fiyat * miktar_sayi

    miktar_str = f"{int(miktar_sayi) if miktar_sayi.is_integer() else miktar_sayi} {miktar_birim}"
    
    return {
        "tur": "Gider",
        "firma": bulunan_firma,
        "urun": tam_eslesen_urun or "Ürün",
        "miktar": miktar_str,
        "birim_fiyat": f"{birim_fiyat:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "tutar": round(toplam_tutar, 2),
        "tarih": datetime.date.today().strftime("%d.%m.%Y"),
        "saat": saat_str,
        "kategori": bulunan_kat,
        "hafizadan": True
    }

def main(page: ft.Page):
    # Platform mobil mi tespiti (Android ve iOS tespiti)
    def platform_mobil_mi():
        if hasattr(page, "platform") and page.platform:
            p_str = str(page.platform).lower()
            if "android" in p_str or "ios" in p_str:
                return True
        import sys
        if sys.platform in ["android", "ios"] or "android" in sys.platform.lower():
            return True
        if any(k in os.environ for k in ["ANDROID_ROOT", "ANDROID_DATA", "FLET_APP_STORAGE_DATA"]):
            return True
        if os.path.exists("/storage/emulated/0") or os.path.exists("/sdcard"):
            return True
        return False

    # Fiş Analizi İşlemci Referansı ve Global Galeri Seçici Servisi
    fis_analiz_tetikleyici = [None]

    def on_galeri_secimi_tamamlandi(e):
        if hasattr(e, "files") and e.files and len(e.files) > 0:
            toplu_yollar = []
            for f in e.files:
                p = getattr(f, "path", None)
                if not p and hasattr(f, "bytes") and f.bytes:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
                        tf.write(f.bytes)
                        p = tf.name
                if p and os.path.exists(str(p)):
                    toplu_yollar.append(str(p))
            if toplu_yollar and fis_analiz_tetikleyici[0]:
                fis_analiz_tetikleyici[0](toplu_yollar)

    galeri_picker = ft.FilePicker(on_result=on_galeri_secimi_tamamlandi)
    if hasattr(page, "services"):
        try:
            page.services.append(galeri_picker)
        except Exception:
            pass

    # CSV Analizi İşlemci Referansı ve Global CSV Seçici Servisi
    csv_islemci_tetikleyici = [None]

    def on_csv_secimi_tamamlandi(e):
        if hasattr(e, "files") and e.files and len(e.files) > 0:
            f = e.files[0]
            secilen_yol = getattr(f, "path", None)
            ham_metin = None
            if hasattr(f, "bytes") and f.bytes:
                for enc in ["utf-8-sig", "utf-8", "cp1254", "latin1"]:
                    try:
                        ham_metin = f.bytes.decode(enc)
                        break
                    except Exception:
                        pass
                if not ham_metin and f.bytes:
                    ham_metin = f.bytes.decode("latin1", errors="ignore")
            if (secilen_yol and os.path.exists(str(secilen_yol))) or ham_metin:
                if csv_islemci_tetikleyici[0]:
                    csv_islemci_tetikleyici[0](dosya_yolu=secilen_yol, ham_metin=ham_metin)

    csv_picker = ft.FilePicker(on_result=on_csv_secimi_tamamlandi)
    if hasattr(page, "services"):
        try:
            page.services.append(csv_picker)
        except Exception:
            pass



    page.title = "Hane Bütçesi Takip Sistemi"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = "#f1f5f9"
    page.theme_mode = ft.ThemeMode.LIGHT

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

        # Masaüstü ve tarayıcı için Flet Audio player hazırlığı
        if _ses_dosyasi_yolu and os.path.exists(_ses_dosyasi_yolu) and hasattr(ft, "Audio"):
            try:
                audio_ctrl = ft.Audio(src=_ses_dosyasi_yolu, autoplay=False, volume=0.5)
                _flet_audio_player[0] = audio_ctrl
                if hasattr(page, "overlay"):
                    page.overlay.append(audio_ctrl)
                elif hasattr(page, "services"):
                    page.services.append(audio_ctrl)
            except Exception as ex_aud:
                print("Flet audio init uyarısı:", ex_aud)
        aktif_tema_modu = tema_oku()
        if aktif_tema_modu == "light":
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = "#f8fafc"
        elif aktif_tema_modu == "dark":
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = "#0b1329"
        else:
            page.theme_mode = ft.ThemeMode.SYSTEM
            page.bgcolor = None

        # Aktif Bütçe Dönemi Durumu
        varsayilan_bas, varsayilan_bit = aktif_butce_donemini_bul()
        secilen_donem_bas = [varsayilan_bas]
        secilen_donem_bit = [varsayilan_bit]
        tum_zamanlar_modu = [False]
        siralama_en_yeni = [True]  # Varsayılan: Yeniden Eskiye (En yeni harcama üstte)

        # Buluttan mevcut kayıtları çek (ve dönemi en güncel veriye otomatik ayarla)
        if supabase:
            try:
                res = supabase.table("islemler").select("*").order("id", desc=True).limit(2000).execute()
                if res.data is not None:
                    islemler.clear()
                    islemler.extend(res.data)
                    # Eğer veri geldiyse ve mevcut bütçe döneminde kayıt yoksa, dönemi en güncel verinin ayına taşı
                    en_yeni_tarih = None
                    for it in islemler:
                        dt = stringden_tarih_al(it.get("tarih"))
                        if dt:
                            if not en_yeni_tarih or dt > en_yeni_tarih:
                                en_yeni_tarih = dt
                    if en_yeni_tarih:
                        p_bas, p_bit = aktif_butce_donemini_bul(en_yeni_tarih)
                        secilen_donem_bas[0] = p_bas
                        secilen_donem_bit[0] = p_bit
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

        # --- YENİ KATEGORİ VE GELİR TÜRÜ EKLEME MODALLARI ---
        def yeni_kategori_dialog_ac(e=None):
            dokunma_geribildirimi()
            yeni_kat_input = ft.TextField(
                label="Yeni Kategori Adı (Örn: Bahçe & Çiçek)",
                autofocus=True,
                width=280,
                dense=True
            )
            kat_uyari = ft.Text("", color="red", size=12)

            def kat_kaydet_aksiyon(ev):
                val = yeni_kat_input.value.strip()
                if not val:
                    kat_uyari.value = "Lütfen bir kategori adı giriniz."
                    try:
                        page.update()
                    except Exception:
                        pass
                    return
                kategori_ekle(val)
                mevcut = kategoriler_oku()
                gider_kategori.options = [make_option(k) for k in mevcut]
                gider_kategori.value = val

                # Kategori filtre dropdown'ını da güncelle
                kategori_filtre_listesi = ["Tüm Kategoriler"] + mevcut + gelir_turleri_oku()
                kategori_filtre_dropdown.options = [make_option(k) for k in kategori_filtre_listesi]

                close_app_dialog(page, kat_dialog)
                dokunma_geribildirimi()
                show_app_snackbar(page, f"✅ Yeni kategori eklendi: {val}", color="#10b981")
                try:
                    page.update()
                except Exception:
                    pass

            kat_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.CATEGORY_ROUNDED, color="#2563eb", size=22),
                    ft.Text("Yeni Kategori Ekle", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Column([
                    ft.Text("Harcamalarınız için yeni bir kategori tanımlayın:", size=11, color="#64748b"),
                    yeni_kat_input,
                    kat_uyari
                ], tight=True, spacing=10),
                actions=[
                    make_button("İptal", outlined=True, height=32, on_click=lambda _: close_app_dialog(page, kat_dialog)),
                    make_button("Ekle", bgcolor="#2563eb", color="white", height=32, on_click=kat_kaydet_aksiyon)
                ]
            )
            show_app_dialog(page, kat_dialog)

        def yeni_gelir_turu_dialog_ac(e=None):
            dokunma_geribildirimi()
            yeni_tur_input = ft.TextField(
                label="Yeni Gelir Türü (Örn: Burs, Prim)",
                autofocus=True,
                width=280,
                dense=True
            )
            tur_uyari = ft.Text("", color="red", size=12)

            def tur_kaydet_aksiyon(ev):
                val = yeni_tur_input.value.strip()
                if not val:
                    tur_uyari.value = "Lütfen bir gelir türü giriniz."
                    try:
                        page.update()
                    except Exception:
                        pass
                    return
                gelir_turu_ekle(val)
                mevcut = gelir_turleri_oku()
                gelir_turu.options = [make_option(k) for k in mevcut]
                gelir_turu.value = val

                # Kategori filtre dropdown'ını da güncelle
                kategori_filtre_listesi = ["Tüm Kategoriler"] + kategoriler_oku() + mevcut
                kategori_filtre_dropdown.options = [make_option(k) for k in kategori_filtre_listesi]

                close_app_dialog(page, tur_dialog)
                dokunma_geribildirimi()
                show_app_snackbar(page, f"✅ Yeni gelir türü eklendi: {val}", color="#10b981")
                try:
                    page.update()
                except Exception:
                    pass

            tur_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.MONEY_ROUNDED, color="#059669", size=22),
                    ft.Text("Yeni Gelir Türü Ekle", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Column([
                    ft.Text("Gelirleriniz için yeni bir tür tanımlayın:", size=11, color="#64748b"),
                    yeni_tur_input,
                    tur_uyari
                ], tight=True, spacing=10),
                actions=[
                    make_button("İptal", outlined=True, height=32, on_click=lambda _: close_app_dialog(page, tur_dialog)),
                    make_button("Ekle", bgcolor="#059669", color="white", height=32, on_click=tur_kaydet_aksiyon)
                ]
            )
            show_app_dialog(page, tur_dialog)

        # --- GELİR ALANLARI ---
        gelir_kaynagi = ft.TextField(label="Gelir Kaynağı (Örn: Şirket, Okul)", width=320, dense=True)
        gelir_turu = make_dropdown(
            label="Gelir Türü",
            options=gelir_turleri_oku(),
            value="Maaş",
            width=275,
            dense=True
        )
        gelir_turu_ekle_btn = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            icon_color="#059669",
            tooltip="Yeni Gelir Türü Ekle",
            on_click=yeni_gelir_turu_dialog_ac
        )
        gelir_turu_satiri = ft.Row(
            [gelir_turu, gelir_turu_ekle_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        gelir_aciklamasi = ft.TextField(label="Açıklama (Örn: Kasım ayı ek ders ödemesi)", width=320, dense=True)
        gelir_tutari = ft.TextField(label="Tutar (TL)", width=320, dense=True, keyboard_type=ft.KeyboardType.NUMBER)

        gelir_form_kutusu = ft.Column([
            ft.Text("Tarih ve Saat Seçimi:", size=12, color="grey"),
            gelir_tarih_saat_satiri,
            gelir_kaynagi,
            gelir_turu_satiri,
            gelir_aciklamasi,
            gelir_tutari
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # --- GİDER ALANLARI ---
        gider_firma = ft.TextField(label="Firma / Market (Örn: BİM, Migros)", width=320, dense=True)
        gider_urun = ft.TextField(label="Ürün / Hizmet (Örn: Süt, Ekmek, Elektrik)", width=320, dense=True)
        gider_kategori = make_dropdown(
            label="Kategori",
            options=kategoriler_oku(),
            value="Market & Temel Gıda",
            width=275,
            dense=True
        )
        kategori_ekle_btn = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            icon_color="#2563eb",
            tooltip="Yeni Kategori Ekle",
            on_click=yeni_kategori_dialog_ac
        )
        kategori_satiri = ft.Row(
            [gider_kategori, kategori_ekle_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
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

        gider_hesap_secimi = make_dropdown(
            label="Harcayan Hesap (Nereden Düşsün?)",
            options=["👑 Abdurrahman (Ana Kasa)", "👤 Hatice (Üye Cüzdanı)"],
            value="👑 Abdurrahman (Ana Kasa)" if yonetici_mi else "👤 Hatice (Üye Cüzdanı)",
            width=320,
            dense=True
        )

        gider_form_kutusu = ft.Column([
            ft.Text("Tarih ve Saat:", size=12, color="grey"),
            gider_tarih_saat_satiri,
            gider_hesap_secimi,
            gider_firma,
            gider_urun,
            kategori_satiri,
            miktar_birim_satiri,
            fiyat_satiri
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        # --- PARA AKTARIMI ALANLARI ---
        aktarim_alici = make_dropdown(
            label="Kime Para Aktarılacak?",
            options=["Hatice", "Aile Üyesi", "Ahmet", "Ayşe", "Mehmet", "Diğer"],
            value="Hatice",
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

        # Kullanıcı İsteği: Gelir, Gider ve Aylık Net kutucuklarının yükseklikleri birebir eşit olsun
        # ve tutarlar kutucuk içine estetik şekilde, taşmadan ortalı otursun.
        bu_ay_gelir_txt = ft.Text("+0,00 TL", size=10.5, weight=ft.FontWeight.BOLD, color="#10b981", text_align=ft.TextAlign.CENTER)
        bu_ay_gider_txt = ft.Text("-0,00 TL", size=10.5, weight=ft.FontWeight.BOLD, color="#f87171", text_align=ft.TextAlign.CENTER)
        bu_ay_fark_txt = ft.Text("0,00 TL", size=10.5, weight=ft.FontWeight.BOLD, color="#38bdf8", text_align=ft.TextAlign.CENTER)

        uye_cuzdan_metni = ft.Text("", size=11, color="#cbd5e1")

        # Lüks Modern Fintech Bakiye Kartı (Gece Mavisi / Zümrüt & Safir Vurgulu)
        bakiye_karti = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Column([
                        kasa_baslik_metni,
                        kasa_tutar_metni
                    ], spacing=2),
                    ft.Container(
                        content=ft.Icon(ft.Icons.WALLET_ROUNDED, color="#38bdf8", size=24),
                        bgcolor="#1e293b",
                        border=make_border_all(1, "#334155"),
                        border_radius=12,
                        padding=10
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=6),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Bu Ay Gelir", size=10, color="#94a3b8", weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                                bu_ay_gelir_txt
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                            bgcolor="#132338",
                            border_radius=10,
                            padding=make_padding(4, 4),
                            expand=1,
                            height=54,
                            alignment=get_alignment_center()
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Bu Ay Gider", size=10, color="#94a3b8", weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                                bu_ay_gider_txt
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                            bgcolor="#271822",
                            border_radius=10,
                            padding=make_padding(4, 4),
                            expand=1,
                            height=54,
                            alignment=get_alignment_center()
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Aylık Net", size=10, color="#94a3b8", weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER),
                                bu_ay_fark_txt
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                            bgcolor="#162235",
                            border_radius=10,
                            padding=make_padding(4, 4),
                            expand=1,
                            height=54,
                            alignment=get_alignment_center()
                        ),
                    ], spacing=6),
                ),
                uye_cuzdan_metni
            ], spacing=4),
            bgcolor="#0f172a",
            border=make_border_all(1, "#1e293b"),
            border_radius=18,
            padding=16,
            width=355,
        )

        bakiye_metni = ft.Text("", visible=False)
        donem_metni = ft.Text(size=13, weight=ft.FontWeight.BOLD, color="#1e293b")
        liste_arayuzu = ft.ListView(height=420, spacing=2)
        bilgi_mesaji = ft.Text("", size=12)

        # --- FİLTRELEME BUTONLARI (Tümü / Gelirler / Giderler) ---
        secilen_filtre = ["Tümü"]

        def filtre_sec(f_adi):
            dokunma_geribildirimi()
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

        kategori_filtre_listesi = ["Tüm Kategoriler"] + kategoriler_oku() + gelir_turleri_oku()

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
            width=355
        )

        # --- AÇILIR / KAPANIR İŞLEM EKLEME FORMU ---
        form_acik = [False]

        def form_toggle(e):
            form_acik[0] = not form_acik[0]
            form_govdesi.visible = form_acik[0]
            set_button_label(form_ac_kapat_btn, "✕ Formu Kapat" if form_acik[0] else "➕ Yeni İşlem")
            form_ac_kapat_btn.bgcolor = "#64748b" if form_acik[0] else "#2563eb"
            liste_arayuzu.height = 240 if form_acik[0] else 420
            try:
                form_govdesi.update()
                form_ac_kapat_btn.update()
                liste_arayuzu.update()
            except Exception:
                page.update()

        form_ac_kapat_btn = make_button("➕ Yeni İşlem", bgcolor="#2563eb", color="white", height=40, expand=True, on_click=form_toggle)

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
            width=355
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
            s = str(val_str).strip().replace('"', '').replace("'", "").replace("“", "").replace("”", "")
            s = s.replace("TL", "").replace("₺", "").replace(" ", "")
            if not s:
                return 0.0
            if "." in s and "," in s:
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            try:
                return float(s)
            except Exception:
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

        def csv_icerigini_yukle(dosya_yolu=None, ham_metin=None, zorla_ekle=False):
            csv_islemci_tetikleyici[0] = csv_icerigini_yukle
            try:
                content = ham_metin
                if not content and dosya_yolu:
                    for enc in ["utf-8-sig", "utf-8", "cp1254", "latin1"]:
                        try:
                            with open(dosya_yolu, "r", encoding=enc) as f:
                                content = f.read()
                            break
                        except Exception:
                            continue

                if not content:
                    show_app_snackbar(page, "⚠️ CSV içeriği okunamadı veya boş.", color="#dc2626")
                    bilgi_mesaji.value = "⚠️ CSV içeriği okunamadı veya boş."
                    bilgi_mesaji.color = "red"
                    page.update()
                    return

                content = content.lstrip("\ufeff").strip()
                lines_content = [line.strip() for line in content.splitlines() if line.strip()]
                if not lines_content:
                    show_app_snackbar(page, "⚠️ CSV içeriğinde geçerli satır bulunamadı.", color="#dc2626")
                    return

                # Ayırıcıyı belirle (Sekme, Noktalı Virgül veya Virgül)
                first_line = lines_content[0]
                if "\t" in first_line:
                    delim = "\t"
                elif ";" in first_line:
                    delim = ";"
                else:
                    delim = ","

                reader = list(csv.reader(lines_content, delimiter=delim))
                if not reader:
                    show_app_snackbar(page, "⚠️ CSV ayrıştırılamadı.", color="#dc2626")
                    return

                # Satır başlık mı veri mi tespiti
                def satir_baslik_mi(row):
                    if not row:
                        return False
                    ilk = str(row[0]).strip().lower()
                    if stringden_tarih_al(ilk) is not None:
                        return False
                    if any(w in ilk for w in ["tarih", "date", "zaman", "gün"]):
                        return True
                    for cell in row:
                        c_val = str(cell).strip().lower()
                        if c_val in ["firma", "ürün", "kategori", "tutar", "miktar", "birim fiyat", "toplam tutar", "kaynak"]:
                            return True
                    return False

                header = []
                data_rows = []
                if satir_baslik_mi(reader[0]):
                    header = [str(h).strip().lower() for h in reader[0]]
                    data_rows = reader[1:]
                else:
                    data_rows = reader

                # Tırnaksız virgüllü kuruşları düzeltme fonksiyonu
                def satir_duzelt(row):
                    r = [str(x).strip() for x in row]
                    # Son iki eleman ayrılmış ondalık mı kontrol et (örn: '453' ve '00' -> '453,00')
                    if len(r) >= 3 and r[-1].isdigit() and len(r[-1]) <= 2 and r[-2].replace(".", "").replace(" ", "").isdigit():
                        r = r[:-2] + [f"{r[-2]},{r[-1]}"]
                    if len(r) >= 4 and r[-2].isdigit() and len(r[-2]) <= 2 and r[-3].replace(".", "").replace(" ", "").isdigit():
                        r = r[:-3] + [f"{r[-3]},{r[-2]}", r[-1]]
                    return r

                en_son_tarih = None
                ham_kayitlar = []

                for raw_r in data_rows:
                    if not raw_r:
                        continue
                    row = satir_duzelt(raw_r)
                    if len(row) < 2:
                        continue

                    tarih_ham = row[0].strip()
                    t_str, s_str = parse_tarih_saat(tarih_ham)

                    t_date = stringden_tarih_al(t_str)
                    if t_date:
                        if not en_son_tarih or t_date > en_son_tarih:
                            en_son_tarih = t_date

                    firma_str = ""
                    urun_str = ""
                    kategori_str = "Diğer"
                    miktar_str = ""
                    birim_fiyat_str = ""
                    tutar_str = "0"

                    if len(row) >= 7:
                        # [Tarih, Firma, Ürün, Kategori, Miktar, Birim Fiyat, Tutar]
                        firma_str = row[1].strip()
                        urun_str = row[2].strip()
                        kategori_str = row[3].strip() or "Diğer"
                        miktar_str = row[4].strip()
                        birim_fiyat_str = row[5].strip().replace('"', '')
                        tutar_str = row[6].strip()
                    elif len(row) == 6:
                        # [Tarih, Firma, Ürün, Kategori, Miktar, Tutar]
                        firma_str = row[1].strip()
                        urun_str = row[2].strip()
                        kategori_str = row[3].strip() or "Diğer"
                        miktar_str = row[4].strip()
                        tutar_str = row[5].strip()
                    elif len(row) == 5:
                        # [Tarih, Kaynak/Firma, Açıklama/Ürün, Kategori, Tutar]
                        firma_str = row[1].strip()
                        urun_str = row[2].strip()
                        kategori_str = row[3].strip() or "Diğer"
                        tutar_str = row[4].strip()
                    elif len(row) == 4:
                        # [Tarih, Firma, Ürün, Tutar]
                        firma_str = row[1].strip()
                        urun_str = row[2].strip()
                        tutar_str = row[3].strip()
                    elif len(row) == 3:
                        # [Tarih, Açıklama, Tutar]
                        firma_str = row[1].strip()
                        urun_str = row[1].strip()
                        tutar_str = row[2].strip()
                    elif len(row) == 2:
                        # [Tarih, Tutar]
                        firma_str = "Harcama"
                        urun_str = "Genel Gider"
                        tutar_str = row[1].strip()

                    tutar_float = parse_turk_tutari(tutar_str)

                    # İşlem türü tespiti
                    tur_turu = "Gider"
                    is_gelir_ipucu = any("kaynak" in h for h in header) or any(k in kategori_str.lower() for k in ["maaş", "ödenek", "ek ders", "gelir", "devir", "hediye"]) or any(k in urun_str.lower() for k in ["maaş", "ödenek", "ek ders", "gelir"])
                    if is_gelir_ipucu:
                        tur_turu = "Gelir"
                    elif "transfer" in kategori_str.lower() or "birikim" in kategori_str.lower():
                        tur_turu = "Para Aktarımı"

                    kayit = {
                        "kullanici": kullanici or "Ev Yöneticisi",
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

                if not ham_kayitlar:
                    show_app_snackbar(page, "⚠️ Dosyadan geçerli işlem satırı çıkarılamadı.", color="#dc2626")
                    return

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

                # 2. Veritabanında Zaten Var Olan Kayıtları Ayıklama
                if zorla_ekle:
                    yeni_eklenenler = list(birlestirilmis_kayitlar)
                else:
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

                # Filtreleri sıfırla ki yüklenen kayıtlar filtreye takılıp gizlenmesin!
                secilen_filtre[0] = "Tümü"
                secilen_kategori[0] = "Tüm Kategoriler"
                tum_zamanlar_modu[0] = True

                if not yeni_eklenenler:
                    arayuzu_guncelle()
                    try:
                        liste_arayuzu.update()
                    except Exception:
                        pass
                    page.update()

                    show_app_snackbar(
                        page,
                        f"ℹ️ Dosyadaki {len(birlestirilmis_kayitlar)} işlem zaten sistemde kayıtlı. Tüm Zamanlar görünümünde listelendi.",
                        color="#0284c7"
                    )

                    def tekrar_hepsini_ekle(ev):
                        close_app_dialog(page, zaten_kayitli_dlg)
                        csv_icerigini_yukle(dosya_yolu=dosya_yolu, ham_metin=content, zorla_ekle=True)

                    zaten_kayitli_dlg = ft.AlertDialog(
                        title=ft.Row([
                            ft.Icon(ft.Icons.INFO_OUTLINE, color="#0284c7", size=24),
                            ft.Text("İşlemler Zaten Mevcut", size=16, weight=ft.FontWeight.BOLD)
                        ], spacing=8),
                        content=ft.Text(
                            f"Yüklenen CSV dosyasındaki {len(birlestirilmis_kayitlar)} adet işlem sistemde zaten kayıtlı olduğu için mükerrer eklenmedi.\n\n"
                            f"Tüm Zamanlar görünümüne geçilerek mevcut işlemleriniz listelendi.\n\n"
                            f"Yine de bu kayıtları sıfırdan tekrar eklemek ister misiniz?",
                            size=12,
                            color="#334155"
                        ),
                        actions=[
                            make_button("✕ Hayır, Kapat", height=34, outlined=True, on_click=lambda _: close_app_dialog(page, zaten_kayitli_dlg)),
                            make_button("⚠️ Evet, Hepsini Tekrar Ekle", height=34, bgcolor="#e11d48", color="white", on_click=tekrar_hepsini_ekle)
                        ],
                        actions_alignment=ft.MainAxisAlignment.END
                    )
                    show_app_dialog(page, zaten_kayitli_dlg)
                    return

                # Yeni kayıtları hafızaya ekle (Hemen ekranda görünsün!)
                for k in reversed(yeni_eklenenler):
                    islemler.insert(0, k)

                arayuzu_guncelle()
                try:
                    liste_arayuzu.update()
                except Exception:
                    pass
                page.update()

                # Buluta senkronizasyonu arka planda yap (Ekran donmasın!)
                if supabase and yeni_eklenenler:
                    def bulut_senkronize_et():
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

                    threading.Thread(target=bulut_senkronize_et, daemon=True).start()

                ek_bilgi = f" ({birlestirilen_sayisi} mükerrer birleştirildi)" if birlestirilen_sayisi > 0 else ""
                basari_mesaji = f"✅ CSV'den {len(yeni_eklenenler)} işlem başarıyla yüklendi!{ek_bilgi}"
                bilgi_mesaji.value = basari_mesaji
                bilgi_mesaji.color = "green"
                show_app_snackbar(page, basari_mesaji, color="#16a34a")

            except Exception as e:
                hata_msg = f"⚠️ CSV aktarım hatası: {str(e)[:60]}"
                bilgi_mesaji.value = hata_msg
                bilgi_mesaji.color = "red"
                show_app_snackbar(page, hata_msg, color="#dc2626")
                page.update()

        # --- AI FİŞ TARAMA İŞLEMCİSİ (Android + Masaüstü Tam Uyumlu) ---
        def fis_gorselini_tara_ve_goster(dosya_yollari):
            fis_analiz_tetikleyici[0] = fis_gorselini_tara_ve_goster
            if not dosya_yollari:
                return

            # Tek yol geldiyse listeye çevir
            if isinstance(dosya_yollari, str):
                yollar_listesi = [dosya_yollari]
            else:
                yollar_listesi = list(dosya_yollari)

            if not yollar_listesi:
                return

            iptal_edildi = [False]
            toplam_adet = len(yollar_listesi)
            durum_metni = ft.Text(f"Fişler hazırlanıyor (0/{toplam_adet})...", size=12, color="#475569")
            ilerleme_cubugu = ft.ProgressBar(value=0.0, width=310, color="#2563eb", bgcolor="#e2e8f0")

            def yukleme_iptal(ev):
                iptal_edildi[0] = True
                close_app_dialog(page, yukleniyor_dialog)
                show_app_snackbar(page, "Fiş tarama işlemi iptal edildi.", color="#64748b")

            yukleniyor_dialog = ft.AlertDialog(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.ProgressRing(width=26, height=26, stroke_width=3, color="#2563eb"),
                            ft.Column([
                                ft.Text(f"📸 {toplam_adet} Adet Fiş Taranıyor..." if toplam_adet > 1 else "📸 Fiş Taranıyor...", weight=ft.FontWeight.BOLD, size=13),
                                durum_metni
                            ], spacing=2, expand=True)
                        ], alignment=ft.MainAxisAlignment.START),
                        ft.Container(height=4),
                        ilerleme_cubugu
                    ], spacing=6, tight=True),
                    padding=14,
                    width=330,
                    height=100
                ),
                actions=[
                    make_button("✕ İptal", outlined=True, height=32, on_click=yukleme_iptal)
                ],
                modal=False
            )
            show_app_dialog(page, yukleniyor_dialog)

            def status_guncelle(yeni_durum, ilerleme=None):
                if not iptal_edildi[0]:
                    durum_metni.value = yeni_durum
                    if ilerleme is not None:
                        ilerleme_cubugu.value = ilerleme
                    try:
                        page.update()
                    except Exception:
                        pass

            def arka_plan_toplu_tara():
                try:
                    tum_sonuclar = []
                    for idx, y in enumerate(yollar_listesi):
                        if iptal_edildi[0]:
                            return
                        dosya_adi = os.path.basename(y)
                        status_guncelle(f"Fiş {idx+1}/{toplam_adet}: {dosya_adi[:18]}...", (idx / toplam_adet))
                        try:
                            res = gemini_fis_analiz_et(y, status_cb=lambda s: status_guncelle(f"[{idx+1}/{toplam_adet}] {s}"))
                            if res and "hata" not in res and res.get("urunler"):
                                tum_sonuclar.append({"dosya": y, "veri": res})
                            elif res and "hata" in res:
                                print(f"Fiş {idx+1} hata:", res.get("hata"))
                        except Exception as ex_f:
                            print(f"Fiş okuma hatası ({dosya_adi}):", ex_f)

                    status_guncelle("Mükerrer harcama kontrolleri yapılıyor...", 1.0)

                    if iptal_edildi[0]:
                        return

                    close_app_dialog(page, yukleniyor_dialog)

                    if not tum_sonuclar:
                        show_app_snackbar(page, "⚠️ Taranan fişlerden geçerli harcama verisi çıkarılamadı.", color="#ef4444")
                        return

                    # --- MÜKERRER KONTROLÜ VE ÖZET DERLEME ---
                    # Her ürünün sistemde (islemler) birebir aynı tarih, saat, firma veya tutarda olup olmadığı kontrol edilir
                    toplu_urun_kartlari = []
                    toplu_onay_verileri = []
                    toplam_okunan_urun = 0
                    toplam_okunan_tutar = 0.0
                    toplam_mukerrer_sayisi = 0
                    tam_mukerrer_fis_sayisi = 0

                    for f_idx, f_item in enumerate(tum_sonuclar):
                        f_veri = f_item["veri"]
                        f_firma = f_veri.get("firma") or "Market"
                        f_tarih = standart_tarih_yap(f_veri.get("tarih"))
                        f_saat = str(f_veri.get("saat") or "12:00").strip()[:5]
                        f_urunler = f_veri.get("urunler") or []
                        f_toplam = float(f_veri.get("toplam_tutar") or 0.0)

                        f_mukerrer_sayisi = 0
                        fis_urun_kontrolleri = []

                        for u_idx, u in enumerate(f_urunler):
                            u_adi = u.get("urun") or f"Ürün {u_idx+1}"
                            u_miktar = u.get("miktar") or "1 Adet"
                            u_fiyat = float(u.get("birim_fiyat") or u.get("tutar") or 0.0)
                            u_tutar = float(u.get("tutar") or u_fiyat)
                            u_kat = kategori_akilli_duzelt(u_adi, firma=f_firma, mevcut_kat=u.get("kategori"))
                            if u_kat not in GIDER_KATEGORILERI:
                                u_kat = "Market & Temel Gıda"

                            toplam_okunan_urun += 1
                            toplam_okunan_tutar += u_tutar

                            # Sistemdeki mevcut kayıtlarla mükerrerlik testi
                            u_adi_norm = u_adi.lower().strip()
                            u_tut_round = round(u_tutar, 2)
                            zaten_kayitli = False

                            for it in islemler:
                                it_tar = standart_tarih_yap(it.get("tarih"))
                                it_st = str(it.get("saat", "")).strip()[:5]
                                it_fir = str(it.get("firma", "")).strip().lower()
                                it_urn = str(it.get("urun", "")).strip().lower()
                                it_tut = round(float(it.get("tutar") or 0.0), 2)

                                if it_tar == f_tarih and it_st == f_saat:
                                    if (u_adi_norm in it_urn or it_urn in u_adi_norm or f_firma.lower() in it_fir) and abs(it_tut - u_tut_round) < 0.05:
                                        zaten_kayitli = True
                                        break

                            if zaten_kayitli:
                                f_mukerrer_sayisi += 1
                                toplam_mukerrer_sayisi += 1
                                chk_val = False  # Zaten kayıtlı olan ürün varsayılan olarak seçilmez
                                rozet = "⚠️ [ZATEN KAYITLI] "
                                label_color = "#b91c1c"
                            else:
                                chk_val = True   # Yeni ürün otomatik seçili
                                rozet = "✨ [YENİ] "
                                label_color = "#1e293b"

                            chk = ft.Checkbox(
                                value=chk_val,
                                label=f"{rozet}{u_adi} ({u_miktar}) - {u_tutar:,.2f} TL • [{u_kat}]"
                            )

                            toplu_onay_verileri.append({
                                "chk": chk,
                                "firma": f_firma,
                                "tarih": f_tarih,
                                "saat": f_saat,
                                "urun": u_adi,
                                "miktar": u_miktar,
                                "birim_fiyat": u_fiyat,
                                "tutar": u_tutar,
                                "kategori": u_kat,
                                "mukerrer": zaten_kayitli
                            })
                            fis_urun_kontrolleri.append(chk)

                        bu_fis_tam_mukerrer = (f_mukerrer_sayisi == len(f_urunler) and len(f_urunler) > 0)
                        if bu_fis_tam_mukerrer:
                            tam_mukerrer_fis_sayisi += 1

                        # Fiş kartı başlığı ve ürünleri
                        fis_durum_rozet = "⚠️ TÜMÜ ZATEN KAYITLI" if bu_fis_tam_mukerrer else (f"⚠️ {f_mukerrer_sayisi} Mükerrer" if f_mukerrer_sayisi > 0 else "✨ Tüm Ürünler Yeni")
                        fis_rozet_bg = "#fef2f2" if bu_fis_tam_mukerrer else ("#fffbeb" if f_mukerrer_sayisi > 0 else "#ecfdf5")
                        fis_rozet_color = "#b91c1c" if bu_fis_tam_mukerrer else ("#b45309" if f_mukerrer_sayisi > 0 else "#047857")

                        kart = ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Column([
                                        ft.Text(f"🧾 {f_firma}", size=12, weight=ft.FontWeight.BOLD, color="#1e293b"),
                                        ft.Text(f"📅 {f_tarih} 🕒 {f_saat} • {f_toplam:,.2f} TL", size=10, color="#64748b")
                                    ], spacing=1, expand=True),
                                    ft.Container(
                                        content=ft.Text(fis_durum_rozet, size=9.5, weight=ft.FontWeight.BOLD, color=fis_rozet_color),
                                        bgcolor=fis_rozet_bg,
                                        padding=make_padding(6, 2),
                                        border_radius=6
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Divider(height=4, color="#e2e8f0"),
                                ft.Column(fis_urun_kontrolleri, spacing=2)
                            ], spacing=4),
                            bgcolor="#f8fafc",
                            border=make_border_all(1, "#cbd5e1" if not bu_fis_tam_mukerrer else "#fca5a5"),
                            border_radius=8,
                            padding=8
                        )
                        toplu_urun_kartlari.append(kart)

                    # Onay ve Ekleme Fonksiyonu
                    def toplu_secilenleri_ekle(ev):
                        eklenen_adet = 0
                        eklenen_toplam = 0.0
                        simdi_ts = int(datetime.datetime.now().timestamp() * 1000)

                        harcayan_hesap = "Hatice" if (not yonetici_mi or kullanici == "Hatice") else "Abdurrahman"

                        for itm_idx, itm in enumerate(toplu_onay_verileri):
                            if itm["chk"].value:
                                std_tar = itm["tarih"]
                                yeni_kayit = {
                                    "kullanici": harcayan_hesap,
                                    "tur": "Gider",
                                    "tarih": std_tar,
                                    "saat": itm["saat"],
                                    "kaynak": "",
                                    "gelir_turu": "",
                                    "aciklama": f"AI Toplu Fiş ({itm['firma']})",
                                    "firma": itm["firma"],
                                    "urun": itm["urun"],
                                    "kategori": itm["kategori"],
                                    "miktar": itm["miktar"],
                                    "birim_fiyat": itm["birim_fiyat"],
                                    "tutar": itm["tutar"]
                                }

                                if supabase:
                                    try:
                                        res = supabase.table("islemler").insert(yeni_kayit).execute()
                                        if res and res.data and len(res.data) > 0 and res.data[0].get("id"):
                                            yeni_kayit["id"] = int(res.data[0]["id"])
                                    except Exception as db_err:
                                        print("Supabase toplu fiş kayıt hatası:", db_err)

                                if "id" not in yeni_kayit:
                                    mevcut_idler = [int(it.get("id")) for it in islemler if str(it.get("id", "")).isdigit()]
                                    yeni_kayit["id"] = (max(mevcut_idler) + 1 + itm_idx) if mevcut_idler else (itm_idx + 1)

                                islemler.insert(0, yeni_kayit)
                                eklenen_adet += 1
                                eklenen_toplam += itm["tutar"]

                        close_app_dialog(page, toplu_fis_dialog)

                        # Otomatik tüm zamanlar ve tüm kategorilere al
                        secilen_filtre[0] = "Tümü"
                        secilen_kategori[0] = "Tüm Kategoriler"
                        tum_zamanlar_modu[0] = True
                        if hasattr(kategori_filtre_dropdown, "value"):
                            kategori_filtre_dropdown.value = "Tüm Kategoriler"

                        arayuzu_guncelle()
                        try:
                            liste_arayuzu.update()
                        except Exception:
                            pass

                        show_app_snackbar(
                            page,
                            f"✅ {len(tum_sonuclar)} fişten seçilen {eklenen_adet} harcama ({eklenen_toplam:,.2f} TL) bütçenize eklendi!",
                            color="#16a34a"
                        )

                    # Dialog İçeriği Oluşturma
                    yeni_urun_sayisi = toplam_okunan_urun - toplam_mukerrer_sayisi
                    ozet_bilgi_metni = (
                        f"📊 {len(tum_sonuclar)} fişte toplam {toplam_okunan_urun} ürün ({toplam_okunan_tutar:,.2f} TL) bulundu.\n"
                        f"✨ {yeni_urun_sayisi} yeni ürün seçili • ⚠️ {toplam_mukerrer_sayisi} mükerrer ürünün işareti kaldırıldı."
                    )

                    toplu_fis_dialog = ft.AlertDialog(
                        title=ft.Row([
                            ft.Icon(ft.Icons.RECEIPT_LONG, color="#2563eb", size=24),
                            ft.Text(f"Toplu Fiş İnceleme ({len(tum_sonuclar)} Fiş)", size=15, weight=ft.FontWeight.BOLD)
                        ], spacing=8),
                        content=ft.Container(
                            content=ft.Column([
                                ft.Container(
                                    content=ft.Text(ozet_bilgi_metni, size=11, color="#1e293b", weight=ft.FontWeight.W_500),
                                    bgcolor="#f1f5f9",
                                    border=make_border_all(1, "#cbd5e1"),
                                    border_radius=8,
                                    padding=8
                                ),
                                ft.Container(
                                    content=ft.Column(toplu_urun_kartlari, scroll=ft.ScrollMode.AUTO, spacing=8),
                                    height=300,
                                    padding=2
                                )
                            ], spacing=8),
                            width=345,
                            height=380
                        ),
                        actions=[
                            make_button("✕ İptal", height=34, outlined=True, on_click=lambda _: close_app_dialog(page, toplu_fis_dialog)),
                            make_button("✅ Seçilenleri Bütçeye Ekle", height=34, bgcolor="#16a34a", color="white", on_click=toplu_secilenleri_ekle)
                        ],
                        actions_alignment=ft.MainAxisAlignment.END
                    )
                    show_app_dialog(page, toplu_fis_dialog)

                except Exception as th_err:
                    print("Toplu arka plan tarama hatası:", th_err)
                    close_app_dialog(page, yukleniyor_dialog)
                    show_app_snackbar(page, f"Tarama sırasında hata oluştu: {th_err}", color="#ef4444")

            threading.Thread(target=arka_plan_toplu_tara, daemon=True).start()        # Fiş analiz motorunu global seçiciye hemen bağla
        fis_analiz_tetikleyici[0] = fis_gorselini_tara_ve_goster

        # --- %100 HATASIZ VE KESİN FİŞ TARAMA MERKEZİ ---
        def fis_tara_tiklandi(e=None):
            fis_analiz_tetikleyici[0] = fis_gorselini_tara_ve_goster
            son_fotolar = son_gorselleri_bul(limit=6)

            metin_alani = ft.TextField(
                label="Fiş / Dekont / SMS Metni Yapıştır",
                multiline=True,
                min_lines=3,
                max_lines=5,
                text_size=11,
                hint_text="Örn: BİM 04.11.2026 Süt 35 TL, Ekmek 10 TL"
            )

            manuel_yol_alani = ft.TextField(
                label="Manuel Dosya Yolu (Örn: /sdcard/Download/fis.jpg)",
                value=son_fotolar[0]["yol"] if son_fotolar else "",
                text_size=11,
                dense=True
            )

            def secilen_yolu_tara(dosya_yolu):
                close_app_dialog(page, fis_dialog)
                fis_gorselini_tara_ve_goster(dosya_yolu)

            # Galeri ve Dosya Seçici Tetikleme (Toplu Fiş Seçimi - Hem PC hem Mobil)
            def galeri_tiklandi_aksiyon(ev=None):
                close_app_dialog(page, fis_dialog)
                show_app_snackbar(page, "📂 Fiş seçici açılıyor (Birden fazla seçebilirsiniz)...", color="#2563eb")

                if not platform_mobil_mi():
                    try:
                        import tkinter as tk
                        from tkinter import filedialog
                        root = tk.Tk()
                        root.withdraw()
                        root.attributes("-topmost", True)
                        dy_list = filedialog.askopenfilenames(
                            title="Bir veya Birden Fazla Fiş Görseli Seçin",
                            filetypes=[("Resim ve PDF Dosyaları", "*.jpg *.jpeg *.png *.webp *.bmp *.heic *.pdf"), ("Tüm Dosyalar", "*.*")]
                        )
                        root.destroy()
                        if dy_list:
                            gecerli_yollar = [y for y in dy_list if os.path.exists(y)]
                            if gecerli_yollar:
                                fis_gorselini_tara_ve_goster(gecerli_yollar)
                                return
                    except Exception as ex_tk:
                        print("Tkinter çoklu seçici uyarısı:", ex_tk)

                # Mobilde hazır galeri_picker servisini çoklu seçimle tetikle
                try:
                    res = galeri_picker.pick_files(
                        dialog_title="Fişleri Seçin (Çoklu Seçim Destekli)",
                        allow_multiple=True,
                        with_data=True
                    )
                    if asyncio.iscoroutine(res):
                        async def _await_picker_coro():
                            try:
                                files = await res
                                if files and len(files) > 0:
                                    yollar = []
                                    for f in files:
                                        p = getattr(f, "path", None)
                                        if not p and hasattr(f, "bytes") and f.bytes:
                                            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
                                                tf.write(f.bytes)
                                                p = tf.name
                                        if p and os.path.exists(str(p)):
                                            yollar.append(str(p))
                                    if yollar:
                                        fis_gorselini_tara_ve_goster(yollar)
                            except Exception as ex_coro:
                                print("Await picker hatası:", ex_coro)

                        if hasattr(page, "run_task"):
                            page.run_task(_await_picker_coro)
                        else:
                            threading.Thread(target=lambda: asyncio.run(_await_picker_coro()), daemon=True).start()
                except Exception as ex_pick:
                    show_app_snackbar(page, f"Seçici hatası: {ex_pick}", color="#ef4444")

            def metin_coz_tetikle(ev):
                raw = metin_alani.value.strip()
                if not raw:
                    show_app_snackbar(page, "Lütfen fiş veya dekont metni yapıştırın.", color="#ef4444")
                    return
                close_app_dialog(page, fis_dialog)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tf:
                    tf.write(raw)
                    txt_p = tf.name
                fis_gorselini_tara_ve_goster(txt_p)

            def manuel_yol_tara(ev):
                yol = manuel_yol_alani.value.strip()
                if not yol or not os.path.exists(yol):
                    show_app_snackbar(page, "Belirtilen dosya yolu bulunamadı.", color="#ef4444")
                    return
                close_app_dialog(page, fis_dialog)
                fis_gorselini_tara_ve_goster(yol)

            aktif_key = gemini_api_key_al()
            api_key_tf = ft.TextField(
                label="🔑 Gemini AI API Anahtarı",
                value=aktif_key or "",
                password=True,
                can_reveal_password=True,
                text_size=11,
                dense=True,
                hint_text="Google AI Studio'dan aldığınız anahtarı yapıştırın"
            )

            def api_keyi_kaydet_aksiyon(ev):
                val = api_key_tf.value.strip()
                if val:
                    gemini_api_key_kaydet(val)
                    show_app_snackbar(page, "✅ Gemini API anahtarı cihaza kaydedildi!", color="#10b981")
                else:
                    show_app_snackbar(page, "Lütfen geçerli bir anahtar girin.", color="#ef4444")

            dialog_icerik = [
                make_button(
                    "📁 Fişleri Seç (Tekli veya Çoklu Toplu Seçim)",
                    icon=ft.Icons.PHOTO_LIBRARY,
                    bgcolor="#2563eb",
                    color="white",
                    height=44,
                    on_click=galeri_tiklandi_aksiyon
                )
            ]

            # Eğer anahtar kayıtlı değilse uyarı ve giriş kutusu göster
            if not aktif_key:
                dialog_icerik.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.KEY, color="#f59e0b", size=18),
                                ft.Text("Gemini API Anahtarı Gerekli", weight=ft.FontWeight.BOLD, size=12, color="#92400e")
                            ], spacing=6),
                            ft.Text("Google AI Studio'dan aldığınız ücretsiz anahtarı buraya yapıştırın:", size=10, color="#78350f"),
                            api_key_tf,
                            make_button("💾 Anahtarı Güvenle Kaydet", bgcolor="#f59e0b", color="white", height=30, on_click=api_keyi_kaydet_aksiyon)
                        ], spacing=6),
                        bgcolor="#fffbeb",
                        border=make_border_all(1, "#fde68a"),
                        border_radius=8,
                        padding=8
                    )
                )

            dialog_icerik.append(ft.Divider(height=10, color="#e2e8f0"))

            # Telefon Galerisindeki / Bilgisayardaki Son Fotoğraflar
            if son_fotolar:
                foto_kartlari = []
                for foto in son_fotolar:
                    yol = foto["yol"]
                    ad = foto["ad"]
                    zaman = foto["zaman"]
                    foto_kartlari.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.RECEIPT_LONG, color="#8b5cf6", size=18),
                                ft.Column([
                                    ft.Text(ad, size=11, weight=ft.FontWeight.W_600, no_wrap=True, max_lines=1),
                                    ft.Text(f"🕒 {zaman}", size=9, color="#64748b")
                                ], spacing=1, expand=True),
                                make_button("⚡ Oku", bgcolor="#8b5cf6", color="white", height=28, on_click=lambda _, y=yol: secilen_yolu_tara(y))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor="#f5f3ff",
                            border=make_border_all(1, "#ddd6fe"),
                            border_radius=8,
                            padding=make_padding(6, 4)
                        )
                    )
                dialog_icerik.append(
                    ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.AUTO_AWESOME, color="#f59e0b", size=16),
                            ft.Text("Algılanan Son Fiş Fotoğrafları:", weight=ft.FontWeight.BOLD, size=12, color="#1e293b")
                        ], spacing=4),
                        *foto_kartlari
                    ], spacing=4)
                )

            # Metin ve Manuel Yol Seçenekleri
            dialog_icerik.extend([
                ft.Divider(height=10, color="#e2e8f0"),
                metin_alani,
                make_button(
                    "📝 Yapıştırılan Metni AI ile Çöz",
                    icon=ft.Icons.TEXT_SNIPPET,
                    outlined=True,
                    height=34,
                    on_click=metin_coz_tetikle
                ),
                ft.Divider(height=10, color="#e2e8f0"),
                manuel_yol_alani,
                make_button(
                    "🔍 Dosya Yolunu Oku",
                    outlined=True,
                    height=32,
                    on_click=manuel_yol_tara
                ),
                ft.Divider(height=10, color="#e2e8f0"),
                api_key_tf,
                make_button("🔑 API Anahtarını Güncelle", outlined=True, height=32, on_click=api_keyi_kaydet_aksiyon)
            ])

            fis_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.DOCUMENT_SCANNER, color="#2563eb", size=24),
                    ft.Text("AI Fiş / Fatura Tara", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column(dialog_icerik, spacing=8, scroll=ft.ScrollMode.AUTO),
                    width=330,
                    height=360,
                    padding=2
                ),
                actions=[
                    make_button("✕ Kapat", height=32, outlined=True, on_click=lambda _: close_app_dialog(page, fis_dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )

            show_app_dialog(page, fis_dialog)

        # --- CSV YÜKLEME İŞLEMCİSİ (HEM DOSYA SEÇİCİ HEM YAPIŞTIRMA DESTEKLİ) ---
        def csv_yukle_tiklandi(e=None):
            csv_islemci_tetikleyici[0] = csv_icerigini_yukle

            # 1. Sistem Dosya Seçiciyi Açma Aksiyonu
            def sistem_dosya_secici_ac(ev=None):
                close_app_dialog(page, csv_dialog)
                show_app_snackbar(page, "📂 Dosya seçici açılıyor...", color="#2563eb")

                if not platform_mobil_mi():
                    try:
                        import tkinter as tk
                        from tkinter import filedialog
                        root = tk.Tk()
                        root.withdraw()
                        root.attributes("-topmost", True)
                        dy = filedialog.askopenfilename(
                            title="Bütçe CSV Dosyasını Seçin",
                            filetypes=[("CSV Dosyaları", "*.csv"), ("Metin Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")]
                        )
                        root.destroy()
                        if dy and os.path.exists(dy):
                            csv_icerigini_yukle(dosya_yolu=dy)
                            return
                    except Exception:
                        pass

                # Mobilde hazır csv_picker servisini tetikle
                try:
                    res = csv_picker.pick_files(
                        dialog_title="Bütçe CSV Dosyasını Seçin",
                        allowed_extensions=["csv", "txt"],
                        allow_multiple=False,
                        with_data=True
                    )
                    if asyncio.iscoroutine(res):
                        async def _await_csv_picker_coro():
                            try:
                                files = await res
                                if files and len(files) > 0:
                                    f = files[0]
                                    p = getattr(f, "path", None)
                                    raw = None
                                    if hasattr(f, "bytes") and f.bytes:
                                        for enc in ["utf-8-sig", "utf-8", "cp1254", "latin1"]:
                                            try:
                                                raw = f.bytes.decode(enc)
                                                break
                                            except Exception:
                                                pass
                                    if p or raw:
                                        csv_icerigini_yukle(dosya_yolu=p, ham_metin=raw)
                            except Exception as ex_coro:
                                print("Await CSV picker hatası:", ex_coro)

                        if hasattr(page, "run_task"):
                            page.run_task(_await_csv_picker_coro)
                        else:
                            import threading
                            threading.Thread(target=lambda: asyncio.run(_await_csv_picker_coro()), daemon=True).start()
                except Exception as ex_pick:
                    show_app_snackbar(page, f"Seçici hatası: {ex_pick}", color="#ef4444")

            # 2. Metin Olarak Yapıştırarak Yükleme Aksiyonu
            def metin_yapistir_dialogu_ac(ev=None):
                close_app_dialog(page, csv_dialog)
                yapistir_tf = ft.TextField(
                    label="CSV Verisini Buraya Yapıştırın",
                    hint_text="Tarih,Firma,Ürün,Kategori,Miktar,Birim Fiyat,Tutar...\n06.09.2026,Palen Doğalgaz,Doğalgaz,Ev & Faturalar,1 Fatura,453,00,453,00",
                    multiline=True,
                    min_lines=6,
                    max_lines=12,
                    text_size=11
                )

                def yapistirilan_yukle(ev2):
                    metin = yapistir_tf.value.strip()
                    if not metin:
                        show_app_snackbar(page, "⚠️ Lütfen yapıştırılacak CSV metnini giriniz.", color="#ef4444")
                        return
                    close_app_dialog(page, yapistir_dialog)
                    csv_icerigini_yukle(ham_metin=metin)

                yapistir_dialog = ft.AlertDialog(
                    title=ft.Row([
                        ft.Icon(ft.Icons.PASTE, color="#8b5cf6", size=24),
                        ft.Text("CSV Metnini Yapıştır", size=16, weight=ft.FontWeight.BOLD)
                    ], spacing=8),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text("Kopyaladığınız CSV satırlarını aşağıdaki alana yapıştırıp hemen yükleyebilirsiniz:", size=11, color="#64748b"),
                            yapistir_tf
                        ], spacing=8, tight=True),
                        width=340
                    ),
                    actions=[
                        make_button("✕ Vazgeç", height=34, outlined=True, on_click=lambda _: close_app_dialog(page, yapistir_dialog)),
                        make_button("📥 İçeriği Yükle", height=34, bgcolor="#8b5cf6", color="white", on_click=yapistirilan_yukle)
                    ],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                show_app_dialog(page, yapistir_dialog)

            # 3. Klasörde Otomatik Bulunan CSV Dosyaları
            bulunan_csvler = son_csvleri_bul()
            yol_tf = ft.TextField(
                label="Manuel CSV Dosya Yolu",
                value=bulunan_csvler[0] if bulunan_csvler else "/storage/emulated/0/Download/HaneButcesi.csv",
                text_size=11,
                dense=True
            )

            def secilen_csv_yukle(dosya_yolu):
                close_app_dialog(page, csv_dialog)
                csv_icerigini_yukle(dosya_yolu=dosya_yolu)

            dialog_icerik = [
                make_button(
                    "📁 Dosyalardan / İndirilenlerden Seç (.csv)",
                    icon=ft.Icons.FOLDER_OPEN,
                    bgcolor="#2563eb",
                    color="white",
                    height=44,
                    on_click=sistem_dosya_secici_ac
                ),
                make_button(
                    "📋 CSV Metnini Yapıştırarak Yükle",
                    icon=ft.Icons.CONTENT_PASTE,
                    bgcolor="#8b5cf6",
                    color="white",
                    height=38,
                    on_click=metin_yapistir_dialogu_ac
                ),
                ft.Divider(height=14, color="#e2e8f0"),
                ft.Text("İndirilenler klasöründe algılanan CSV dosyaları:", size=11, color="#64748b")
            ]

            if bulunan_csvler:
                for c_yol in bulunan_csvler:
                    c_ad = os.path.basename(c_yol)
                    dialog_icerik.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.DESCRIPTION, color="#2563eb", size=18),
                                ft.Text(c_ad, size=11, weight=ft.FontWeight.W_600, expand=True, no_wrap=True),
                                make_button("📥 Yükle", height=28, bgcolor="#2563eb", color="white", on_click=lambda _, y=c_yol: secilen_csv_yukle(y))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            bgcolor="#eff6ff",
                            border=make_border_all(1, "#bfdbfe"),
                            border_radius=8,
                            padding=make_padding(6, 4)
                        )
                    )
            else:
                dialog_icerik.append(
                    ft.Text("İndirilenler klasöründe otomatik CSV bulunamadı.", size=10, color="#94a3b8")
                )

            dialog_icerik.extend([
                ft.Divider(height=10, color="#e2e8f0"),
                yol_tf,
                make_button("Dosya Yolundan Yükle", height=32, outlined=True, on_click=lambda _: secilen_csv_yukle(yol_tf.value.strip()))
            ])

            csv_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.UPLOAD_FILE, color="#2563eb", size=24),
                    ft.Text("CSV Dosyası Yükle", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column(dialog_icerik, spacing=8, tight=True),
                    width=340,
                    padding=2
                ),
                actions=[
                    make_button("✕ Kapat", height=32, outlined=True, on_click=lambda _: close_app_dialog(page, csv_dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, csv_dialog)

        def csv_indir_tiklandi(e=None):
            dokunma_geribildirimi()
            try:
                t_bas = secilen_donem_bas[0].strftime("%d.%m.%Y")
                t_bit = secilen_donem_bit[0].strftime("%d.%m.%Y")
                varsayilan_isim = f"HaneButcesi_{t_bas}_{t_bit}.csv" if not tum_zamanlar_modu[0] else "HaneButcesi_TumKayitlar.csv"

                import io
                out_buf = io.StringIO()
                writer = csv.writer(out_buf, delimiter=",", quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["Tarih", "Firma/Kurum", "Ürün/Hizmet", "Kategori", "Miktar/Adet", "Birim Fiyat", "Toplam Tutar"])

                yazilan_adet = 0
                aktarilacak_kayitlar = []
                for item in islemler:
                    t_date = stringden_tarih_al(item.get("tarih"))
                    if not tum_zamanlar_modu[0]:
                        if not t_date or not (secilen_donem_bas[0] <= t_date <= secilen_donem_bit[0]):
                            continue
                    aktarilacak_kayitlar.append(item)

                # En yeni alışveriş en altta olacak şekilde kronolojik sırala (Eskiden yeniye)
                aktarilacak_kayitlar.sort(key=islem_siralama_anahtari, reverse=False)

                for item in aktarilacak_kayitlar:
                    tarih_tam = f"{item.get('tarih', '')} {item.get('saat', '')}".strip()
                    firma = item.get("firma") or item.get("kaynak") or ""
                    urun = item.get("urun") or item.get("aciklama") or ""
                    kategori = item.get("kategori") or "Diğer"
                    miktar = item.get("miktar") or ""
                    birim_fiyat = item.get("birim_fiyat") or ""
                    toplam_tutar = format_turk_para(item.get("tutar") or 0.0)

                    writer.writerow([tarih_tam, firma, urun, kategori, miktar, birim_fiyat, toplam_tutar])
                    yazilan_adet += 1

                csv_str = out_buf.getvalue()
                csv_bytes = csv_str.encode("utf-8-sig")

                # 1. Güvenli Depolama Konumları (Android + Masaüstü Tam Uyumlu)
                kaydedilen_dosyalar = []
                guvenli_dizinler = [
                    os.environ.get("FLET_APP_STORAGE_DATA"),
                    tempfile.gettempdir(),
                    BASE_DIR,
                    os.path.join(os.path.expanduser("~"), "Downloads"),
                    os.path.join(os.path.expanduser("~"), "İndirilenler"),
                    "/storage/emulated/0/Download",
                    "/sdcard/Download"
                ]

                ana_kayit_yolu = None
                for g_dizin in guvenli_dizinler:
                    if g_dizin and os.path.exists(g_dizin) and os.path.isdir(g_dizin):
                        hedef_p = os.path.join(g_dizin, varsayilan_isim)
                        try:
                            with open(hedef_p, "wb") as f_out:
                                f_out.write(csv_bytes)
                            if not ana_kayit_yolu:
                                ana_kayit_yolu = hedef_p
                            if hedef_p not in kaydedilen_dosyalar:
                                kaydedilen_dosyalar.append(hedef_p)
                        except Exception:
                            pass

                if not ana_kayit_yolu:
                    # En kötü durumda temp klasörüne yaz
                    ana_kayit_yolu = os.path.join(tempfile.gettempdir(), varsayilan_isim)
                    with open(ana_kayit_yolu, "wb") as f_fallback:
                        f_fallback.write(csv_bytes)
                    kaydedilen_dosyalar.append(ana_kayit_yolu)

                # 2. İndirilenler (Downloads) Klasörüne Kaydet
                indirilenler_yollari = [
                    os.path.join(os.path.expanduser("~"), "Downloads"),
                    os.path.join(os.path.expanduser("~"), "İndirilenler"),
                    "/storage/emulated/0/Download",
                    "/sdcard/Download"
                ]
                for dpath in indirilenler_yollari:
                    if os.path.exists(dpath) and os.path.isdir(dpath):
                        hedef_down = os.path.join(dpath, varsayilan_isim)
                        try:
                            with open(hedef_down, "wb") as f_down:
                                f_down.write(csv_bytes)
                            if hedef_down not in kaydedilen_dosyalar:
                                kaydedilen_dosyalar.append(hedef_down)
                        except Exception:
                            pass

                # 3. Masaüstü (Desktop) Klasörüne de Kaydet
                masaustu_yollari = [
                    os.path.join(os.path.expanduser("~"), "Desktop"),
                    os.path.join(os.path.expanduser("~"), "Masaüstü")
                ]
                for mpath in masaustu_yollari:
                    if os.path.exists(mpath) and os.path.isdir(mpath):
                        hedef_desk = os.path.join(mpath, varsayilan_isim)
                        try:
                            with open(hedef_desk, "wb") as f_desk:
                                f_desk.write(csv_bytes)
                            if hedef_desk not in kaydedilen_dosyalar:
                                kaydedilen_dosyalar.append(hedef_desk)
                        except Exception:
                            pass

                # Kayıt yerleri özet metni
                kayit_yerleri_metni = chr(10).join([f"• {p}" for p in kaydedilen_dosyalar[:3]]) if kaydedilen_dosyalar else f"• {ana_klasor_dosyasi}"

                                # Mobil Cihazda Doğrudan Android Paylaşım / Dosya Kaydetme Penceresini Açma
                def dosyayi_sistemde_paylas(dosya_yolu):
                    if not dosya_yolu or not os.path.exists(dosya_yolu):
                        return
                    # 1. Flet Share Servisi
                    if hasattr(ft, "Share"):
                        try:
                            sh = ft.Share()
                            if hasattr(sh, "share_files"):
                                r_sh = sh.share_files([dosya_yolu], text="Hane Bütçesi CSV Verisi")
                                if asyncio.iscoroutine(r_sh):
                                    if hasattr(page, "run_task"):
                                        page.run_task(lambda: r_sh)
                                    else:
                                        asyncio.create_task(r_sh)
                                return
                        except Exception as ex_sh:
                            print("Share servisi hatası:", ex_sh)

                    # 2. Android Intent ile doğrudan Paylaşım (pyjnius)
                    try:
                        from jnius import autoclass, cast
                        PythonActivity = autoclass('org.kivy.android.PythonActivity')
                        Intent = autoclass('android.content.Intent')
                        Uri = autoclass('android.net.Uri')
                        File = autoclass('java.io.File')
                        FileProvider = autoclass('androidx.core.content.FileProvider')

                        act = PythonActivity.mActivity
                        f_obj = File(dosya_yolu)
                        uri = FileProvider.getUriForFile(act, act.getPackageName() + ".fileprovider", f_obj)
                        
                        share_intent = Intent(Intent.ACTION_SEND)
                        share_intent.setType("text/csv")
                        share_intent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', uri))
                        share_intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                        act.startActivity(Intent.createChooser(share_intent, "CSV Dosyasını Kaydet veya Paylaş"))
                    except Exception as ex_intent:
                        print("Android Intent paylaşım hatası:", ex_intent)

                # Mobilde dosyayı hemen sistem paylaşımına da gönder
                if platform_mobil_mi():
                    dosyayi_sistemde_paylas(ana_kayit_yolu)

                def panoya_kopyala(ev):
                    try:
                        if hasattr(page, "set_clipboard"):
                            page.set_clipboard(csv_str)
                        show_app_snackbar(page, "📋 CSV içeriği panoya kopyalandı! Excel'e yapıştırabilirsiniz.", color="#10b981")
                    except Exception:
                        pass

                def farkli_kaydet_ac(ev):
                    close_app_dialog(page, sonuc_dialog)
                    try:
                        import tkinter as tk
                        from tkinter import filedialog
                        root = tk.Tk()
                        root.withdraw()
                        root.attributes("-topmost", True)
                        f_secilen = filedialog.asksaveasfilename(
                            title="CSV Dosyasını Kaydedilecek Yeri Seçin",
                            defaultextension=".csv",
                            initialfile=varsayilan_isim,
                            filetypes=[("CSV Dosyası", "*.csv"), ("Tüm Dosyalar", "*.*")]
                        )
                        root.destroy()
                        if f_secilen:
                            with open(f_secilen, "wb") as f_usr:
                                f_usr.write(csv_bytes)
                            show_app_snackbar(page, f"✅ Seçtiğiniz konuma kaydedildi: {os.path.basename(f_secilen)}", color="#10b981")
                    except Exception as ex_tk:
                        print("Farklı kaydet seçici uyarısı:", ex_tk)

                sonuc_dialog = ft.AlertDialog(
                    title=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color="#10b981", size=24),
                        ft.Text("CSV Dosyası Kaydedildi", size=16, weight=ft.FontWeight.BOLD)
                    ], spacing=8),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(f"📊 Toplam {yazilan_adet} adet bütçe işlemi CSV olarak başarıyla kaydedildi.", size=12, weight=ft.FontWeight.W_600),
                            ft.Container(height=4),
                            ft.Text("Kaydedilen Konumlar:", size=11, color="#64748b", weight=ft.FontWeight.BOLD),
                            ft.Container(
                                content=ft.Text(kayit_yerleri_metni, size=10.5, color="#1e293b", selectable=True),
                                bgcolor="#f8fafc",
                                border=make_border_all(1, "#cbd5e1"),
                                border_radius=8,
                                padding=8
                            ),
                            ft.Text("İpucu: Dosya EvButcesi çalışma klasörünüze ve İndirilenler klasörünüze yazılmıştır.", size=10, color="#64748b", italic=True)
                        ], spacing=6, tight=True),
                        width=340
                    ),
                    actions=[
                        make_button("📤 Telefonda Paylaş / Kaydet", height=34, bgcolor="#2563eb", color="white", on_click=lambda ev: (dosyayi_sistemde_paylas(ana_kayit_yolu), close_app_dialog(page, sonuc_dialog))),
                        make_button("📋 Panoya Kopyala", height=34, outlined=True, tooltip="Metni kopyala", on_click=panoya_kopyala),
                        make_button("Tamam", height=34, outlined=True, on_click=lambda _: close_app_dialog(page, sonuc_dialog))
                    ],
                    actions_alignment=ft.MainAxisAlignment.END
                )
                show_app_dialog(page, sonuc_dialog)
                show_app_snackbar(page, f"✅ {yazilan_adet} işlem CSV olarak kaydedildi! ({varsayilan_isim})", color="#10b981")

            except Exception as ex_indir:
                print("CSV indirme genel hatası:", ex_indir)
                show_app_snackbar(page, f"⚠️ CSV indirme hatası: {str(ex_indir)[:50]}", color="#ef4444")


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

        # --- ÖZEL TARİH ARALIĞI SEÇİM MODALI (ÖRN: 3 EKİM - 20 EKİM) ---
        def tarih_araligi_secim_modal_ac(e=None):
            dokunma_geribildirimi()

            vars_bas = secilen_donem_bas[0] or datetime.date.today()
            vars_bit = secilen_donem_bit[0] or datetime.date.today()

            bas_tf = ft.TextField(
                label="Başlangıç Tarihi",
                value=vars_bas.strftime("%d.%m.%Y"),
                width=140,
                dense=True,
                hint_text="03.10.2026"
            )
            bit_tf = ft.TextField(
                label="Bitiş Tarihi",
                value=vars_bit.strftime("%d.%m.%Y"),
                width=140,
                dense=True,
                hint_text="20.10.2026"
            )

            def bas_takvim_secildi(ev):
                if ev.control.value:
                    val = ev.control.value
                    d = val.date() if isinstance(val, datetime.datetime) else val
                    bas_tf.value = d.strftime("%d.%m.%Y")
                    try:
                        bas_tf.update()
                    except Exception:
                        pass

            def bit_takvim_secildi(ev):
                if ev.control.value:
                    val = ev.control.value
                    d = val.date() if isinstance(val, datetime.datetime) else val
                    bit_tf.value = d.strftime("%d.%m.%Y")
                    try:
                        bit_tf.update()
                    except Exception:
                        pass

            bas_picker = ft.DatePicker(
                on_change=bas_takvim_secildi,
                first_date=datetime.datetime(2020, 1, 1),
                last_date=datetime.datetime(2035, 12, 31)
            )
            bit_picker = ft.DatePicker(
                on_change=bit_takvim_secildi,
                first_date=datetime.datetime(2020, 1, 1),
                last_date=datetime.datetime(2035, 12, 31)
            )

            def onayar_uygula(bas_d, bit_d):
                bas_tf.value = bas_d.strftime("%d.%m.%Y")
                bit_tf.value = bit_d.strftime("%d.%m.%Y")
                try:
                    bas_tf.update()
                    bit_tf.update()
                except Exception:
                    pass

            bugun_d = datetime.date.today()
            btn_bu_ay = make_button("📅 Bütçe Dönemi", height=28, outlined=True, on_click=lambda _: onayar_uygula(*aktif_butce_donemini_bul()))
            btn_son_30 = make_button("Son 30 Gün", height=28, outlined=True, on_click=lambda _: onayar_uygula(bugun_d - datetime.timedelta(days=30), bugun_d))
            btn_son_7 = make_button("Son 7 Gün", height=28, outlined=True, on_click=lambda _: onayar_uygula(bugun_d - datetime.timedelta(days=7), bugun_d))

            def aralik_filtrele(ev):
                b_date = stringden_tarih_al(bas_tf.value)
                e_date = stringden_tarih_al(bit_tf.value)

                if not b_date or not e_date:
                    show_app_snackbar(page, "Lütfen geçerli başlangıç ve bitiş tarihleri giriniz (Örn: 03.10.2026).", color="#ef4444")
                    return

                if b_date > e_date:
                    b_date, e_date = e_date, b_date

                secilen_donem_bas[0] = b_date
                secilen_donem_bit[0] = e_date
                tum_zamanlar_modu[0] = False

                close_app_dialog(page, tarih_dialog)
                arayuzu_guncelle()
                show_app_snackbar(page, f"📅 {b_date.strftime('%d.%m.%Y')} - {e_date.strftime('%d.%m.%Y')} aralığı filtrelendi!", color="#10b981")

            tarih_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.DATE_RANGE_ROUNDED, color="#2563eb", size=22),
                    ft.Text("Özel Tarih Aralığı Seç", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Başlangıç ve bitiş tarihlerini belirleyin (Örn: 3 Ekim - 20 Ekim):", size=11, color="#64748b"),
                        ft.Row([
                            ft.Column([
                                bas_tf,
                                make_button("📅 Takvim", height=28, outlined=True, on_click=lambda _: picker_ac(bas_picker))
                            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            ft.Column([
                                bit_tf,
                                make_button("📅 Takvim", height=28, outlined=True, on_click=lambda _: picker_ac(bit_picker))
                            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                        ft.Divider(height=6, color="#e2e8f0"),
                        ft.Text("Hızlı Seçenekler:", size=10.5, color="#64748b", weight=ft.FontWeight.W_600),
                        ft.Row([btn_bu_ay, btn_son_30, btn_son_7], spacing=6, wrap=True)
                    ], spacing=10, tight=True),
                    width=330
                ),
                actions=[
                    make_button("✕ İptal", height=34, outlined=True, on_click=lambda _: close_app_dialog(page, tarih_dialog)),
                    make_button("🔍 Filtrele", height=34, bgcolor="#2563eb", color="white", on_click=aralik_filtrele)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, tarih_dialog)

        # --- LİSTE HIZLI KAYDIRMA (EN BAŞA / EN SONA - TELEFON VE PC GARANTİLİ) ---
        def listeyi_basa_sar(e=None):
            dokunma_geribildirimi()

            async def _basa_gorev():
                # 1. liste_arayuzu en başa
                if hasattr(liste_arayuzu, "scroll_to"):
                    try:
                        r = liste_arayuzu.scroll_to(offset=0, duration=200)
                        if asyncio.iscoroutine(r): await r
                    except Exception:
                        pass
                    try:
                        r = liste_arayuzu.scroll_to(scroll_key="liste_basi", duration=200)
                        if asyncio.iscoroutine(r): await r
                    except Exception:
                        pass
                # 2. sayfa genel kaydırması
                if hasattr(page, "scroll_to"):
                    try:
                        r = page.scroll_to(offset=0, duration=200)
                        if asyncio.iscoroutine(r): await r
                    except Exception:
                        pass
                try:
                    liste_arayuzu.update()
                except Exception:
                    pass
                try:
                    page.update()
                except Exception:
                    pass

            if hasattr(page, "run_task"):
                page.run_task(_basa_gorev)
            else:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_basa_gorev())
                except Exception:
                    try:
                        asyncio.create_task(_basa_gorev())
                    except Exception:
                        threading.Thread(target=lambda: asyncio.run(_basa_gorev()), daemon=True).start()

            show_app_snackbar(page, "⬆ Listenin en başına gidildi", color="#2563eb")

        def listeyi_sona_sar(e=None):
            dokunma_geribildirimi()

            async def _sona_gorev():
                # 1. liste_arayuzu en alta
                if hasattr(liste_arayuzu, "scroll_to"):
                    try:
                        r = liste_arayuzu.scroll_to(offset=-1, duration=200)
                        if asyncio.iscoroutine(r): await r
                    except Exception:
                        pass
                    try:
                        r = liste_arayuzu.scroll_to(delta=100000, duration=200)
                        if asyncio.iscoroutine(r): await r
                    except Exception:
                        pass
                    try:
                        r = liste_arayuzu.scroll_to(scroll_key="liste_sonu", duration=200)
                        if asyncio.iscoroutine(r): await r
                    except Exception:
                        pass
                # 2. sayfa genel kaydırması
                if hasattr(page, "scroll_to"):
                    try:
                        r = page.scroll_to(offset=-1, duration=200)
                        if asyncio.iscoroutine(r): await r
                    except Exception:
                        pass
                    try:
                        r = page.scroll_to(delta=100000, duration=200)
                        if asyncio.iscoroutine(r): await r
                    except Exception:
                        pass
                try:
                    liste_arayuzu.update()
                except Exception:
                    pass
                try:
                    page.update()
                except Exception:
                    pass

            if hasattr(page, "run_task"):
                page.run_task(_sona_gorev)
            else:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_sona_gorev())
                except Exception:
                    try:
                        asyncio.create_task(_sona_gorev())
                    except Exception:
                        threading.Thread(target=lambda: asyncio.run(_sona_gorev()), daemon=True).start()

            show_app_snackbar(page, "⬇ Listenin en sonuna gidildi", color="#2563eb")

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

            raw_id = item.get("id")
            try:
                safe_id = int(raw_id) if raw_id is not None else 0
            except Exception:
                safe_id = 0

            return datetime.datetime(y, m, d, hour, minute), safe_id


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
                mevcut_kullanici = item.get("kullanici") or "Abdurrahman"
                if mevcut_kullanici == "Ev Yöneticisi":
                    mevcut_kullanici = "Abdurrahman"
                elif mevcut_kullanici == "Aile Üyesi":
                    mevcut_kullanici = "Hatice"

                duzenle_hesap = make_dropdown(
                    options=["Abdurrahman", "Hatice"],
                    value=mevcut_kullanici,
                    label="Harcayan Hesap (Kasa / Üye)",
                    width=310,
                    dense=True
                )
                duzenle_firma = ft.TextField(label="Firma / Market", value=item.get("firma", ""), width=310, dense=True)
                duzenle_urun = ft.TextField(label="Ürün / Hizmet", value=item.get("urun", ""), width=310, dense=True)
                duzenle_kat = make_dropdown(options=kat_secenekleri, value=mevcut_kat, label="Kategori", width=310, dense=True)
                duzenle_miktar = ft.TextField(label="Miktar", value=item.get("miktar", ""), width=150, dense=True)
                duzenle_birim_fiyat = ft.TextField(label="Birim Fiyat (TL)", value=str(item.get("birim_fiyat", 0.0)), width=150, dense=True, keyboard_type=ft.KeyboardType.NUMBER)

                # 3'lü Dinamik Hesaplama (Miktar, Birim Fiyat, Toplam Tutar)
                duzenle_hesaplaniyor = [False]
                duzenle_kullanici_girdileri = []

                def duzenle_kayit_ekle(alan):
                    if alan in duzenle_kullanici_girdileri:
                        duzenle_kullanici_girdileri.remove(alan)
                    duzenle_kullanici_girdileri.append(alan)

                def duzenle_kayit_sil(alan):
                    if alan in duzenle_kullanici_girdileri:
                        duzenle_kullanici_girdileri.remove(alan)

                def duzenle_sayi_formatla(val):
                    if val == int(val):
                        return str(int(val))
                    formatted = f"{val:.2f}"
                    return formatted.rstrip("0").rstrip(".") if formatted.endswith("0") else formatted

                def duzenle_float_al(val_str):
                    if not val_str:
                        return None
                    try:
                        clean = str(val_str).strip().replace(",", ".")
                        match = re.search(r"[-+]?\d*\.?\d+", clean)
                        if match:
                            return float(match.group(0))
                        return float(clean)
                    except Exception:
                        return None

                # Mevcut kayıttaki değerlere göre başlangıç önceliği
                m_init = duzenle_float_al(duzenle_miktar.value)
                bf_init = duzenle_float_al(duzenle_birim_fiyat.value)
                t_init = duzenle_float_al(duzenle_tutar.value)

                if m_init is not None and bf_init is not None and bf_init > 0:
                    duzenle_kullanici_girdileri = ["BF", "M"]
                elif m_init is not None and t_init is not None and t_init > 0:
                    duzenle_kullanici_girdileri = ["M", "T"]
                elif bf_init is not None and t_init is not None and t_init > 0:
                    duzenle_kullanici_girdileri = ["BF", "T"]

                def duzenle_hesapla_ve_guncelle(tetikleyen_alan):
                    if duzenle_hesaplaniyor[0]:
                        return

                    m_val = duzenle_float_al(duzenle_miktar.value)
                    bf_val = duzenle_float_al(duzenle_birim_fiyat.value)
                    t_val = duzenle_float_al(duzenle_tutar.value)

                    if m_val is None:
                        duzenle_kayit_sil("M")
                    if bf_val is None:
                        duzenle_kayit_sil("BF")
                    if t_val is None:
                        duzenle_kayit_sil("T")

                    if tetikleyen_alan == "M" and m_val is not None:
                        duzenle_kayit_ekle("M")
                    elif tetikleyen_alan == "BF" and bf_val is not None:
                        duzenle_kayit_ekle("BF")
                    elif tetikleyen_alan == "T" and t_val is not None:
                        duzenle_kayit_ekle("T")

                    if len(duzenle_kullanici_girdileri) >= 2:
                        aktif_1 = duzenle_kullanici_girdileri[-1]
                        aktif_2 = duzenle_kullanici_girdileri[-2]

                        girdi_kumesi = {aktif_1, aktif_2}
                        kalan_hedef = list({"M", "BF", "T"} - girdi_kumesi)[0]

                        duzenle_hesaplaniyor[0] = True
                        try:
                            if kalan_hedef == "T":
                                if m_val is not None and bf_val is not None:
                                    duzenle_tutar.value = f"{m_val * bf_val:.2f}"
                            elif kalan_hedef == "M":
                                if t_val is not None and bf_val is not None and bf_val > 0:
                                    duzenle_miktar.value = duzenle_sayi_formatla(t_val / bf_val)
                            elif kalan_hedef == "BF":
                                if t_val is not None and m_val is not None and m_val > 0:
                                    duzenle_birim_fiyat.value = f"{t_val / m_val:.2f}"
                        finally:
                            duzenle_hesaplaniyor[0] = False
                        try:
                            duzenle_miktar.update()
                            duzenle_birim_fiyat.update()
                            duzenle_tutar.update()
                        except Exception:
                            try:
                                page.update()
                            except Exception:
                                pass

                duzenle_miktar.on_change = lambda e: duzenle_hesapla_ve_guncelle("M")
                duzenle_birim_fiyat.on_change = lambda e: duzenle_hesapla_ve_guncelle("BF")
                duzenle_tutar.on_change = lambda e: duzenle_hesapla_ve_guncelle("T")

                form_kontrolleri = [
                    duzenle_hesap,
                    duzenle_firma,
                    duzenle_urun,
                    duzenle_kat,
                    ft.Row([duzenle_miktar, duzenle_birim_fiyat], spacing=10),
                    duzenle_tutar,
                    ft.Text("💡 İkisini girince üçüncüsü (Miktar, Birim Fiyat, Tutar) otomatik hesaplanır.", size=10, color="#64748b"),
                    ft.Row([duzenle_tarih, duzenle_saat], spacing=10)
                ]
            elif tur == "Gelir":
                duzenle_kaynak = ft.TextField(label="Kaynak / Kurum", value=item.get("kaynak", ""), width=310, dense=True)
                mevcut_gelir_turu = item.get("gelir_turu") or "Maaş"
                gelir_secenekleri = list(gelir_turleri_oku())
                if mevcut_gelir_turu and mevcut_gelir_turu not in gelir_secenekleri:
                    gelir_secenekleri.insert(0, mevcut_gelir_turu)
                duzenle_gelir_turu = make_dropdown(
                    options=gelir_secenekleri,
                    value=mevcut_gelir_turu,
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
                    item["kullanici"] = duzenle_hesap.value
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
            liste_arayuzu.controls.append(ft.Container(key="liste_basi", height=0))

            # 1. TÜM ZAMANLAR KÜMÜLATİF BAKİYE (Eldeki Gerçek Toplam Nakit / Kasa)
            # Kural: Harcama Aile Üyesi hesabından kaydedilirse o üyenin hesabından düşer; aksi durumda (Ev Yöneticisi) toplam kasadan düşer.
            genel_gelir = 0.0
            kasa_harcamalari = 0.0
            genel_kullanici_harcamalari = {}
            genel_kullaniciya_aktarilan = {}

            for item in islemler:
                t = float(item.get("tutar") or 0.0)
                tur = item.get("tur")
                sahip = (item.get("kullanici") or "Abdurrahman").strip()
                if sahip == "Ev Yöneticisi":
                    sahip = "Abdurrahman"
                elif sahip == "Aile Üyesi":
                    sahip = "Hatice"

                if tur == "Gelir":
                    genel_gelir += t
                elif tur == "Para Aktarımı":
                    alici = (item.get("kaynak") or "Hatice").strip()
                    if alici == "Aile Üyesi":
                        alici = "Hatice"
                    genel_kullaniciya_aktarilan[alici] = genel_kullaniciya_aktarilan.get(alici, 0.0) + t
                elif tur == "Gider":
                    if sahip not in ["Abdurrahman", "Ev Yöneticisi"]:
                        genel_kullanici_harcamalari[sahip] = genel_kullanici_harcamalari.get(sahip, 0.0) + t
                    else:
                        kasa_harcamalari += t

            # Kasadan üyelere aktarılan toplam tutar
            toplam_uyelere_aktarilan = sum(genel_kullaniciya_aktarilan.values())

            # Toplam Kasada Kalan Net Para:
            genel_kasa = genel_gelir - kasa_harcamalari - toplam_uyelere_aktarilan

            # 2. SEÇİLİ DÖNEM HESAPLAMASI (O Ayın Gelir ve Gideri)
            donem_gelir = 0.0
            donem_gider = 0.0
            donem_kasa_harcamasi = 0.0
            donem_kullanici_harcamalari = {}
            donem_kullaniciya_aktarilan = {}
            donem_toplam_harcama = 0.0

            # Dönem başlığı güncellemesi (Kompakt ve Şık Format)
            bas_str = secilen_donem_bas[0].strftime("%d.%m.%Y")
            bit_str = secilen_donem_bit[0].strftime("%d.%m.%Y")
            if tum_zamanlar_modu[0]:
                donem_metni.value = "🌐 Tüm Zamanlar (Filtresiz)"
                set_button_label(donem_toggle_btn, f"📅 Döneme Dön ({bas_str[:5]} - {bit_str[:5]})")
            else:
                donem_metni.value = f"📅 {bas_str} - {bit_str}"
                set_button_label(donem_toggle_btn, "🌐 Tüm Zamanlar")

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
                islem_sahibi = (item.get("kullanici") or "Abdurrahman").strip()
                if islem_sahibi == "Ev Yöneticisi":
                    islem_sahibi = "Abdurrahman"
                elif islem_sahibi == "Aile Üyesi":
                    islem_sahibi = "Hatice"

                islem_turu_val = item.get("tur")

                if islem_turu_val == "Gelir":
                    donem_gelir += tutar
                    toplam_donem_gelir_sayisi += 1
                elif islem_turu_val == "Para Aktarımı":
                    alici = (item.get("kaynak") or "Hatice").strip()
                    if alici == "Aile Üyesi":
                        alici = "Hatice"
                    donem_kullaniciya_aktarilan[alici] = donem_kullaniciya_aktarilan.get(alici, 0.0) + tutar
                elif islem_turu_val == "Gider":
                    donem_gider += tutar
                    donem_toplam_harcama += tutar
                    toplam_donem_gider_sayisi += 1
                    if islem_sahibi not in ["Abdurrahman", "Ev Yöneticisi"]:
                        donem_kullanici_harcamalari[islem_sahibi] = donem_kullanici_harcamalari.get(islem_sahibi, 0.0) + tutar
                    else:
                        donem_kasa_harcamasi += tutar

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
                    kat_adi = item.get('kategori') or "Diğer"
                    alt_detay = f"{zaman_metni} • {kat_adi}"
                    tutar_metni = f"-{tutar:,.2f} TL"
                    tutar_rengi = "#ef4444"
                    ikon_adi = ft.Icons.ARROW_DOWNWARD
                    ikon_bg = "#fee2e2"
                    ikon_renk = "#b91c1c"

                can_modify = yonetici_mi or islem_turu_val == "Gider"
                duzenle_butonu = ft.IconButton(
                    icon=ft.Icons.EDIT_OUTLINED,
                    icon_color="#2563eb",
                    icon_size=18,
                    width=28,
                    height=28,
                    padding=0,
                    visible=can_modify,
                    tooltip="Düzenle / Kategori Değiştir",
                    on_click=lambda e, it=item: islem_duzenle_modal_ac(it)
                )

                sil_butonu = ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color="#ef4444",
                    icon_size=18,
                    width=28,
                    height=28,
                    padding=0,
                    visible=can_modify,
                    tooltip="Sil",
                    on_click=lambda e, it=item: silme_onayi_iste(it)
                )

                # Kimin işlem yaptığı ve miktar/birim fiyat etiketleri
                sahip_badge_metni = "👑 Abdurrahman" if islem_sahibi in ["Abdurrahman", "Ev Yöneticisi"] else "👤 Hatice"
                sahip_badge_bg = "#eff6ff" if islem_sahibi in ["Abdurrahman", "Ev Yöneticisi"] else "#f0fdf4"
                sahip_badge_color = "#2563eb" if islem_sahibi in ["Abdurrahman", "Ev Yöneticisi"] else "#16a34a"

                miktar_val_str = str(item.get("miktar") or "").strip()
                raw_bf = item.get("birim_fiyat")
                bf_float = parse_turk_tutari(raw_bf)

                # Birim fiyat sıfır veya tanımsız ise tutar ve miktardan otomatik hesapla
                if bf_float <= 0 and tutar > 0 and miktar_val_str:
                    m_match = re.search(r'[-+]?\d*\.?\d+', miktar_val_str.replace(",", "."))
                    if m_match:
                        try:
                            m_num = float(m_match.group(0))
                            if m_num > 0:
                                bf_float = tutar / m_num
                                item["birim_fiyat"] = f"{bf_float:.2f}"
                        except Exception:
                            pass

                birim_detay_str = ""
                if miktar_val_str and bf_float > 0:
                    birim_detay_str = f"{miktar_val_str} × {format_turk_para(bf_float)} TL"
                elif bf_float > 0:
                    birim_detay_str = f"Birim: {format_turk_para(bf_float)} TL"
                elif miktar_val_str and miktar_val_str != "-":
                    birim_detay_str = miktar_val_str

                alt_etiketler = [
                    ft.Container(
                        content=ft.Text(sahip_badge_metni, size=9.5, color=sahip_badge_color, weight=ft.FontWeight.W_600),
                        bgcolor=sahip_badge_bg,
                        border_radius=6,
                        padding=make_padding(4, 2)
                    )
                ]
                if birim_detay_str:
                    alt_etiketler.append(
                        ft.Container(
                            content=ft.Text(f"📦 {birim_detay_str}", size=9.5, color="#475569", weight=ft.FontWeight.W_500),
                            bgcolor="#f1f5f9",
                            border_radius=6,
                            padding=make_padding(4, 2)
                        )
                    )

                satir = ft.Container(
                    content=ft.Row([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(ikon_adi, color=ikon_renk, size=15),
                                width=30,
                                height=30,
                                bgcolor=ikon_bg,
                                border_radius=15,
                                alignment=get_alignment_center()
                            ),
                            ft.Column([
                                # Uzun ürün isimleri kesilmesin diye wrap=True ve max_lines=2
                                ft.Text(baslik, size=12.5, weight=ft.FontWeight.W_600, color="#0f172a", max_lines=2),
                                ft.Text(alt_detay, size=10, color="#64748b"),
                                ft.Row(alt_etiketler, spacing=4, wrap=True)
                            ], spacing=2, tight=True, expand=True)
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START, expand=True),
                        ft.Column([
                            ft.Text(tutar_metni, size=12.5, weight=ft.FontWeight.BOLD, color=tutar_rengi),
                            ft.Row([duzenle_butonu, sil_butonu], spacing=2)
                        ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.END)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START),
                    padding=make_padding(8, 6),
                    bgcolor="#f8fafc",
                    border=make_border_all(1, "#f1f5f9"),
                    border_radius=10,
                )
                liste_arayuzu.controls.append(satir)

            liste_arayuzu.controls.append(ft.Container(key="liste_sonu", height=0))
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
                # Aktarım yapılan veya harcama yapan tüm üyeleri topla
                tum_uyeler = set(list(genel_kullaniciya_aktarilan.keys()) + list(genel_kullanici_harcamalari.keys()))
                for u in sorted(tum_uyeler):
                    if u in ["Abdurrahman", "Ev Yöneticisi"]:
                        continue
                    aktarilan = genel_kullaniciya_aktarilan.get(u, 0.0)
                    harcanan = genel_kullanici_harcamalari.get(u, 0.0)
                    kalan = aktarilan - harcanan
                    uye_bakiye_metinleri.append(f"{u}: {kalan:,.2f} TL (Harcama: {harcanan:,.2f} TL)")

                detay_str = " | ".join(uye_bakiye_metinleri) if uye_bakiye_metinleri else ""

                kasa_baslik_metni.value = "ELDEKİ TOPLAM PARA (KASA)"
                kasa_tutar_metni.value = f"{genel_kasa:,.2f} TL"
                kasa_tutar_metni.color = "white"

                donem_kasa_cikisi = donem_kasa_harcamasi + sum(donem_kullaniciya_aktarilan.values())
                donem_fark = donem_gelir - donem_kasa_cikisi

                bu_ay_gelir_txt.value = f"+{donem_gelir:,.2f} TL"
                bu_ay_gider_txt.value = f"-{donem_kasa_harcamasi:,.2f} TL"
                bu_ay_fark_txt.value = f"{donem_fark:+,.2f} TL"
                bu_ay_fark_txt.color = "#10b981" if donem_fark >= 0 else "#f87171"

                uye_cuzdan_metni.value = f"💳 Üye Cüzdanları: {detay_str}" if detay_str else ""
                uye_cuzdan_metni.visible = bool(detay_str)
            else:
                benim_aktarilan = genel_kullaniciya_aktarilan.get(kullanici, 0.0)
                benim_harcanan = genel_kullanici_harcamalari.get(kullanici, 0.0)
                benim_kalan = benim_aktarilan - benim_harcanan
                bu_donem_harcanan = donem_kullanici_harcamalari.get(kullanici, 0.0)
                bu_donem_aktarilan = donem_kullaniciya_aktarilan.get(kullanici, 0.0)

                kasa_baslik_metni.value = f"{kullanici.upper()} CÜZDANI (KALAN)"
                kasa_tutar_metni.value = f"{benim_kalan:,.2f} TL"
                kasa_tutar_metni.color = "white"

                bu_ay_gelir_txt.value = f"+{bu_donem_aktarilan:,.2f} TL"
                bu_ay_gider_txt.value = f"-{bu_donem_harcanan:,.2f} TL"
                bu_ay_fark_txt.value = f"{benim_kalan:+,.2f} TL"

                uye_cuzdan_metni.value = f"Toplam Harcamanız: {benim_harcanan:,.2f} TL / Kalan: {benim_kalan:,.2f} TL"
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
            try:
                liste_arayuzu.update()
            except Exception:
                pass
            try:
                liste_kapsayici.update()
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

                secilen_hesap = "Hatice" if "Hatice" in (gider_hesap_secimi.value or "") or "Aile Üyesi" in (gider_hesap_secimi.value or "") else "Abdurrahman"

                yeni_kayit = {
                    "kullanici": secilen_hesap,
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

        yetki_metni = f"👑 {kullanici} (Yönetici Paneli)" if yonetici_mi else f"👤 {kullanici} (Aile Üyesi Paneli)"

        # --- HESAP DEĞİŞTİRME VE ÇIKIŞ MERKEZİ ---
        def cikis_yap_aksiyon(e=None):
            def yoneticiye_gec(ev):
                close_app_dialog(page, cikis_dialog)
                oturum_kaydet("Abdurrahman", True)
                ana_ekrana_git("Abdurrahman", yonetici_mi=True)

            def uyeye_gec(ev):
                close_app_dialog(page, cikis_dialog)
                oturum_kaydet("Hatice", False)
                ana_ekrana_git("Hatice", yonetici_mi=False)

            def oturumu_kapat(ev):
                close_app_dialog(page, cikis_dialog)
                oturum_sil()
                giris_ekranina_git()

            diger_rol_btn = make_button(
                "👑 Abdurrahman Hesabına Geç",
                icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                bgcolor="#2563eb",
                color="white",
                height=40,
                on_click=yoneticiye_gec
            ) if not yonetici_mi else make_button(
                "👤 Hatice Hesabına Geç",
                icon=ft.Icons.PERSON,
                bgcolor="#0284c7",
                color="white",
                height=40,
                on_click=uyeye_gec
            )

            cikis_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.MANAGE_ACCOUNTS, color="#2563eb", size=24),
                    ft.Text("Hesap Değiştir / Çıkış", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Aktif Hesap: {kullanici} ({'Ev Yöneticisi' if yonetici_mi else 'Aile Üyesi'})", size=11, color="#64748b"),
                        ft.Container(height=4),
                        diger_rol_btn,
                        make_button(
                            "🚪 Tamamen Çıkış Yap (Giriş Ekranı)",
                            icon=ft.Icons.LOGOUT,
                            outlined=True,
                            height=38,
                            on_click=oturumu_kapat
                        )
                    ], spacing=8, tight=True),
                    width=320,
                    padding=4
                ),
                actions=[
                    make_button("✕ İptal", height=32, outlined=True, on_click=lambda _: close_app_dialog(page, cikis_dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, cikis_dialog)

        # --- VERİLERİ BULUTTAN YENİLEME / SENKRONİZASYON MERKEZİ ---
        def verileri_buluttan_yenile(e=None):
            if not supabase:
                show_app_snackbar(page, "⚠️ Supabase bulut veritabanı bağlantısı yok.", color="#ef4444")
                return

            show_app_snackbar(page, "🔄 Buluttan güncel işlemler çekiliyor...", color="#2563eb")

            def _arkaplan_yenile():
                try:
                    res = supabase.table("islemler").select("*").order("id", desc=True).limit(2000).execute()
                    if res and res.data is not None:
                        onceki_adet = len(islemler)
                        islemler.clear()
                        islemler.extend(res.data)
                        yeni_adet = len(islemler)

                        arayuzu_guncelle()

                        fark = yeni_adet - onceki_adet
                        if fark > 0:
                            show_app_snackbar(page, f"✅ {fark} yeni işlem yüklendi! (Toplam {yeni_adet})", color="#10b981")
                        elif fark < 0:
                            show_app_snackbar(page, f"✅ Liste güncellendi. (Toplam {yeni_adet})", color="#10b981")
                        else:
                            show_app_snackbar(page, f"✅ Veriler güncel. (Toplam {yeni_adet} işlem)", color="#10b981")
                    else:
                        show_app_snackbar(page, "⚠️ Buluttan veri alınamadı.", color="#f59e0b")
                except Exception as ex:
                    print("Bulut senkronizasyon hatası:", ex)
                    show_app_snackbar(page, f"Senkronizasyon hatası: {ex}", color="#ef4444")

            threading.Thread(target=_arkaplan_yenile, daemon=True).start()

        # Modern Dönem ve Özel Tarih Aralığı Seçim Çubuğu
        onceki_btn = make_icon_btn(ft.Icons.CHEVRON_LEFT_ROUNDED, icon_size=24, icon_color="#475569", tooltip="Önceki Bütçe Dönemi", on_click=lambda _: donem_kaydir("onceki"))
        sonraki_btn = make_icon_btn(ft.Icons.CHEVRON_RIGHT_ROUNDED, icon_size=24, icon_color="#475569", tooltip="Sonraki Bütçe Dönemi", on_click=lambda _: donem_kaydir("sonraki"))
        
        tarih_araligi_btn = make_button("📅 Özel Tarih Aralığı", height=30, outlined=True, tooltip="3 Ekim - 20 Ekim gibi istediğiniz tarih aralığını seçin", on_click=tarih_araligi_secim_modal_ac)
        donem_toggle_btn = make_button("🌐 Tüm Zamanlar", height=30, outlined=True, tooltip="Filtresiz tüm geçmiş kayıtları göster", on_click=tum_zamanlar_toggle)

        donem_bar = ft.Container(
            content=ft.Column([
                ft.Row([
                    onceki_btn,
                    ft.Container(
                        content=donem_metni,
                        on_click=tarih_araligi_secim_modal_ac,
                        tooltip="Tarih Aralığını Değiştirmek İçin Dokunun"
                    ),
                    sonraki_btn,
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    tarih_araligi_btn,
                    donem_toggle_btn
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=6)
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="white",
            border=make_border_all(1, "#e2e8f0"),
            border_radius=16,
            padding=make_padding(8, 6),
            width=355
        )

        # Modern Sıralama Seçenekleri (Kullanıcı İsteği: Tıklayınca 'Yeniden Eskiye' ve 'Eskiden Yeniye' seçenekleri açılır)
        def siralama_secenekleri_ac(e=None):
            dokunma_geribildirimi()

            def siralama_sec(en_yeni_mi):
                siralama_en_yeni[0] = en_yeni_mi
                set_button_label(siralama_btn, "⏱️ Yeniden Eskiye" if en_yeni_mi else "⏳ Eskiden Yeniye")
                bilgi_mesaji.value = "📅 Sıralama: Yeniden Eskiye (En Son İşlem Üstte)" if en_yeni_mi else "📅 Sıralama: Kronolojik (Eskiden Yeniye)"
                bilgi_mesaji.color = "#2563eb"
                try:
                    bilgi_mesaji.update()
                except Exception:
                    pass
                close_app_dialog(page, siralama_dialog)
                dokunma_geribildirimi()
                arayuzu_guncelle()

            siralama_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.SORT_ROUNDED, color="#2563eb", size=22),
                    ft.Text("İşlem Sıralama Seçenekleri", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("İşlem geçmişi listeleme sırasını belirleyin:", size=11, color="#64748b"),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED if siralama_en_yeni[0] else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                        color="#2563eb" if siralama_en_yeni[0] else "#94a3b8", size=20),
                                ft.Column([
                                    ft.Text("Yeniden Eskiye (En Yeni Üstte)", size=13, weight=ft.FontWeight.BOLD if siralama_en_yeni[0] else ft.FontWeight.NORMAL),
                                    ft.Text("En son yapılan harcama veya gelir en başta listelenir", size=10, color="#64748b")
                                ], spacing=1)
                            ], spacing=10),
                            bgcolor="#eff6ff" if siralama_en_yeni[0] else None,
                            border=make_border_all(1, "#bfdbfe" if siralama_en_yeni[0] else "#e2e8f0"),
                            border_radius=10,
                            padding=make_padding(10, 8),
                            on_click=lambda _: siralama_sec(True)
                        ),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED if not siralama_en_yeni[0] else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                        color="#2563eb" if not siralama_en_yeni[0] else "#94a3b8", size=20),
                                ft.Column([
                                    ft.Text("Eskiden Yeniye (Kronolojik)", size=13, weight=ft.FontWeight.BOLD if not siralama_en_yeni[0] else ft.FontWeight.NORMAL),
                                    ft.Text("Ayın başından sonuna doğru tarih sırasıyla listelenir", size=10, color="#64748b")
                                ], spacing=1)
                            ], spacing=10),
                            bgcolor="#eff6ff" if not siralama_en_yeni[0] else None,
                            border=make_border_all(1, "#bfdbfe" if not siralama_en_yeni[0] else "#e2e8f0"),
                            border_radius=10,
                            padding=make_padding(10, 8),
                            on_click=lambda _: siralama_sec(False)
                        ),
                    ], spacing=10, tight=True),
                    width=310
                ),
                actions=[
                    make_button("✕ Kapat", height=32, outlined=True, on_click=lambda _: close_app_dialog(page, siralama_dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, siralama_dialog)

        siralama_btn = make_button(
            "⏱️ Yeniden Eskiye" if siralama_en_yeni[0] else "⏳ Eskiden Yeniye",
            height=32,
            outlined=True,
            tooltip="İşlem Sıralama Seçenekleri (Yeniden Eskiye / Eskiden Yeniye)",
            on_click=siralama_secenekleri_ac
        )
        toplu_sil_btn = make_button("🗑️ Toplu Sil", height=30, bgcolor="#ef4444", color="white", tooltip="Listelenen Kayıtları Kalıcı Olarak Sil", on_click=toplu_silme_onayi_iste)
        yenile_btn = make_button("🔄 Yenile", height=30, bgcolor="#10b981", color="white", tooltip="Buluttaki Yeni Kayıtları Getir", on_click=verileri_buluttan_yenile)

        # Kullanıcı İsteği: Yeni/Eski/Başa/Sona üstte ortalı, İşlem Geçmişi başlığı altında ortalı, Yenile ve Toplu Sil de altta ortalı
        liste_ust_bar = ft.Container(
            content=ft.Column([
                # 1. Sıralama ve Başa / Sona Kaydırma Butonları (Ortalanmış)
                ft.Row([
                    siralama_btn,
                    make_button("⬆ Başa", height=32, outlined=True, tooltip="Listenin En Başına Git", on_click=listeyi_basa_sar),
                    make_button("⬇ Sona", height=32, outlined=True, tooltip="Listenin En Sonuna Git", on_click=listeyi_sona_sar),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),

                # 2. İşlem Geçmişi Başlığı (Ortalanmış)
                ft.Row([
                    ft.Icon(ft.Icons.RECEIPT_LONG_ROUNDED, size=18, color="#0f172a"),
                    ft.Text("İşlem Geçmişi", weight=ft.FontWeight.BOLD, size=15, color="#0f172a"),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),

                # 3. Yenile ve Toplu Sil Butonları (Ortalanmış)
                ft.Row([
                    yenile_btn,
                    toplu_sil_btn
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
            ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=355,
            padding=make_padding(0, 4)
        )


        # --- OTOMATİK OKUL HARÇLIĞI MANTIĞI VE AYARLARI ---
        def otomatik_harclik_tara_ve_ekle(sessiz=True):
            ayarlar = harclik_ayarlari_oku()
            if not ayarlar.get("aktif", True) or not ayarlar.get("otomatik_ekle", True):
                if not sessiz:
                    show_app_snackbar(page, "Otomatik harçlık sistemi şu anda devre dışı.", color="#64748b")
                return 0

            cocuk_sayisi = int(ayarlar.get("cocuk_sayisi", 2))
            birim_harclik = float(ayarlar.get("birim_harclik", 10.0))
            toplam_tutar = cocuk_sayisi * birim_harclik
            tatil_kontrol = ayarlar.get("tatil_kontrol", True)
            saat_val = ayarlar.get("saat", "08:30")

            mevcut_harclik_tarihleri = set()
            for item in islemler:
                if item.get("tur") == "Gider" and "okul harçlığı" in (item.get("urun") or "").lower():
                    t = item.get("tarih")
                    if t:
                        mevcut_harclik_tarihleri.add(standart_tarih_yap(t))

            bugun = datetime.date.today()
            if secilen_donem_bas[0] and secilen_donem_bas[0] <= bugun:
                baslangic = secilen_donem_bas[0]
                if (bugun - baslangic).days > 180:
                    baslangic = bugun - datetime.timedelta(days=180)
            else:
                baslangic = bugun - datetime.timedelta(days=45)

            eklenen_adet = 0
            gecici_gun = baslangic
            while gecici_gun <= bugun:
                std_gun = gecici_gun.strftime("%d.%m.%Y")
                if std_gun not in mevcut_harclik_tarihleri:
                    if okul_gunu_mu(gecici_gun, tatil_kontrol=tatil_kontrol):
                        yeni_kayit = {
                            "kullanici": kullanici or "Ev Yöneticisi",
                            "tur": "Gider",
                            "tarih": std_gun,
                            "saat": saat_val,
                            "kaynak": "",
                            "gelir_turu": "",
                            "aciklama": "Otomatik Okul Harçlığı",
                            "firma": "Nakit",
                            "urun": f"Okul Harçlığı ({cocuk_sayisi} Çocuk)",
                            "kategori": "Eğitim & Okul",
                            "miktar": f"{cocuk_sayisi} çocuk",
                            "birim_fiyat": format_turk_para(birim_harclik),
                            "tutar": float(toplam_tutar)
                        }

                        if supabase:
                            try:
                                res = supabase.table("islemler").insert(yeni_kayit).execute()
                                if res and res.data and len(res.data) > 0 and res.data[0].get("id"):
                                    yeni_kayit["id"] = res.data[0]["id"]
                            except Exception as db_err:
                                print("Harçlık Supabase kayıt hatası:", db_err)

                        if "id" not in yeni_kayit:
                            mevcut_idler = [it.get("id") for it in islemler if isinstance(it.get("id"), int)]
                            yeni_kayit["id"] = (max(mevcut_idler) + 1) if mevcut_idler else 1

                        islemler.append(yeni_kayit)
                        mevcut_harclik_tarihleri.add(std_gun)
                        eklenen_adet += 1

                gecici_gun += datetime.timedelta(days=1)

            if eklenen_adet > 0:
                arayuzu_guncelle()
                toplam_eklenen_tl = format_turk_para(eklenen_adet * toplam_tutar)
                msg = f"🎒 {eklenen_adet} okul günü için toplam {toplam_eklenen_tl} TL harçlık eklendi!"
                show_app_snackbar(page, msg, color="#10b981")
            else:
                if not sessiz:
                    show_app_snackbar(page, "ℹ️ Eksik okul harçlığı bulunamadı, tüm günler kayıtlı.", color="#2563eb")

            return eklenen_adet

        def harclik_ayarlari_modal_ac(e=None):
            ayarlar = harclik_ayarlari_oku()

            aktif_switch = ft.Switch(
                label="Otomatik Harçlık Sistemi Aktif",
                value=ayarlar.get("aktif", True),
                active_color="#10b981"
            )

            cocuk_sayisi_tf = ft.TextField(
                label="Çocuk Sayısı",
                value=str(ayarlar.get("cocuk_sayisi", 2)),
                width=130,
                keyboard_type=ft.KeyboardType.NUMBER
            )

            birim_harclik_tf = ft.TextField(
                label="Çocuk Başı Tutar (TL)",
                value=format_turk_para(ayarlar.get("birim_harclik", 10.0)),
                width=150,
                keyboard_type=ft.KeyboardType.NUMBER
            )

            tatil_cb = ft.Checkbox(
                label="Haftasonu ve MEB Tatillerinde Duraklat",
                value=ayarlar.get("tatil_kontrol", True)
            )

            onizleme_txt = ft.Text(size=12, weight=ft.FontWeight.BOLD, color="#2563eb")

            def onizleme_guncelle(ev=None):
                try:
                    cs = int(cocuk_sayisi_tf.value.strip() or "1")
                    bh = parse_turk_tutari(birim_harclik_tf.value.strip() or "0")
                    toplam = cs * bh
                    onizleme_txt.value = f"💰 Günlük Toplam: {format_turk_para(toplam)} TL ({cs} Çocuk x {format_turk_para(bh)} TL)"
                except Exception:
                    onizleme_txt.value = "⚠️ Geçerli bir sayı giriniz."
                try:
                    onizleme_txt.update()
                except Exception:
                    pass

            cocuk_sayisi_tf.on_change = onizleme_guncelle
            birim_harclik_tf.on_change = onizleme_guncelle
            onizleme_guncelle()

            def ayar_kaydet_aksiyon(ev):
                try:
                    cs = int(cocuk_sayisi_tf.value.strip() or "2")
                    bh = parse_turk_tutari(birim_harclik_tf.value.strip() or "10")
                    yeni_ayarlar = {
                        "aktif": aktif_switch.value,
                        "cocuk_sayisi": cs,
                        "birim_harclik": bh,
                        "saat": "08:30",
                        "tatil_kontrol": tatil_cb.value,
                        "otomatik_ekle": aktif_switch.value
                    }
                    harclik_ayarlari_kaydet(yeni_ayarlar)
                    close_app_dialog(page, harclik_dialog)
                    show_app_snackbar(page, f"✅ Harçlık ayarları güncellendi (Çocuk Başı: {format_turk_para(bh)} TL)", color="#10b981")
                except Exception as ex:
                    show_app_snackbar(page, f"Hata: {ex}", color="#ef4444")

            def eksik_gunleri_ekle_aksiyon(ev):
                ayar_kaydet_aksiyon(ev)
                otomatik_harclik_tara_ve_ekle(sessiz=False)

            harclik_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.SCHOOL, color="#f59e0b", size=24),
                    ft.Text("Otomatik Okul Harçlığı", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Okulların açık olduğu haftaiçi günlerde çocuklara otomatik harçlık ekler.", size=11, color="#64748b"),
                        ft.Text("📅 MEB 2026-2027 Takvimi: 16-20 Kasım Ara Tatil, 25 Ocak-5 Şubat Sömestr, 8-12 Mart 2. Ara Tatil.", size=10, color="#059669", weight=ft.FontWeight.W_500),
                        aktif_switch,
                        ft.Row([cocuk_sayisi_tf, birim_harclik_tf], spacing=8),
                        tatil_cb,
                        ft.Container(
                            content=onizleme_txt,
                            bgcolor="#f0f9ff",
                            border=make_border_all(1, "#bae6fd"),
                            border_radius=8,
                            padding=make_padding(8, 8),
                            alignment=get_alignment_center()
                        ),
                        ft.Container(
                            content=ft.Text("CSV Formatı: GG.AA.YYYY 08:30, Nakit, Okul Harçlığı, Eğitim & Okul", size=10, color="#94a3b8"),
                            padding=make_padding(0, 2)
                        )
                    ], spacing=10, tight=True),
                    width=320,
                    padding=4
                ),
                actions=[
                    make_button("⚡ Eksik Günleri Ekle", height=34, bgcolor="#2563eb", color="white", on_click=eksik_gunleri_ekle_aksiyon),
                    make_button("💾 Kaydet", height=34, bgcolor="#10b981", color="white", on_click=ayar_kaydet_aksiyon),
                    make_button("✕ Kapat", height=34, outlined=True, on_click=lambda _: close_app_dialog(page, harclik_dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, harclik_dialog)

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

        # Kullanıcı İsteği: Ana ekranda hangi hesapta işlem yapıldığını görmek amacıyla sadece
        # kullanıcı ismi rozeti yer alsın; hesap değiştirme ve çıkış işlemleri ise tek bir yerden
        # (üç çizgi menüsünden) yapılsın.
        profil_cipi = ft.Container(
            content=ft.Row([
                ft.Text(f"👑 {kullanici}" if yonetici_mi else f"👤 {kullanici}", size=11, color="#1e40af", weight=ft.FontWeight.BOLD)
            ], spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="#eff6ff",
            border=make_border_all(1, "#bfdbfe"),
            border_radius=16,
            padding=make_padding(8, 4),
            tooltip=f"Aktif Hesap: {kullanici}"
        )

        # --- TEMA SEÇİM DİYALOĞU ---
        def tema_secim_dialogu_ac(e=None):
            dokunma_geribildirimi()
            secili_tema = [tema_oku()]

            def tema_uygula(t_kod):
                secili_tema[0] = t_kod
                tema_kaydet(t_kod)
                if t_kod == "light":
                    page.theme_mode = ft.ThemeMode.LIGHT
                    page.bgcolor = "#f8fafc"
                elif t_kod == "dark":
                    page.theme_mode = ft.ThemeMode.DARK
                    page.bgcolor = "#0b1329"
                else:
                    page.theme_mode = ft.ThemeMode.SYSTEM
                    page.bgcolor = None
                try:
                    page.update()
                except Exception:
                    pass
                close_app_dialog(page, tema_dialog)
                show_app_snackbar(page, f"🎨 Tema güncellendi: {t_kod.title()}", color="#10b981")

            tema_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.PALETTE_ROUNDED, color="#7c3aed", size=22),
                    ft.Text("Görünüm ve Tema", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Uygulama görünüm temasını seçin:", size=11, color="#64748b"),
                        make_button("📱 Cihaz Teması ile Aynı (Varsayılan)", height=38, outlined=True, on_click=lambda _: tema_uygula("system")),
                        make_button("☀️ Açık Tema", height=38, outlined=True, on_click=lambda _: tema_uygula("light")),
                        make_button("🌙 Koyu Tema", height=38, outlined=True, on_click=lambda _: tema_uygula("dark")),
                    ], spacing=8, tight=True),
                    width=300
                ),
                actions=[
                    make_button("✕ Kapat", height=32, outlined=True, on_click=lambda _: close_app_dialog(page, tema_dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, tema_dialog)

        # --- ÜÇ ÇİZGİ HAMBURGER MENÜ MERKEZİ ---
        def menu_ac(e=None):
            dokunma_geribildirimi()
            
            def menu_aksiyon_calistir(fn):
                close_app_dialog(page, menu_dialog)
                fn()

            menu_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.MENU_ROUNDED, color="#2563eb", size=22),
                    ft.Text("Hızlı Menü", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.UPLOAD_FILE_ROUNDED, color="#2563eb"),
                            title=ft.Text("CSV'den İşlem Yükle", size=13, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text("Excel / CSV dosyasından yükleme", size=10, color="#64748b"),
                            on_click=lambda _: menu_aksiyon_calistir(csv_yukle_tiklandi)
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.DOWNLOAD_ROUNDED, color="#059669"),
                            title=ft.Text("Kayıtları CSV Olarak İndir", size=13, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text("Tüm işlemleri CSV olarak kaydet", size=10, color="#64748b"),
                            on_click=lambda _: (close_app_dialog(page, menu_dialog), csv_indir_tiklandi())
                        ),
                        ft.Divider(height=6, color="#e2e8f0"),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.CATEGORY_ROUNDED, color="#2563eb"),
                            title=ft.Text("Yeni Kategori Ekle", size=13, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text("Harcamalar için yeni kategori tanımla", size=10, color="#64748b"),
                            on_click=lambda _: menu_aksiyon_calistir(yeni_kategori_dialog_ac)
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.SAVINGS_ROUNDED, color="#059669"),
                            title=ft.Text("Yeni Gelir Türü Ekle", size=13, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text("Gelirler için yeni tür tanımla", size=10, color="#64748b"),
                            on_click=lambda _: menu_aksiyon_calistir(yeni_gelir_turu_dialog_ac)
                        ),
                        ft.Divider(height=6, color="#e2e8f0"),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PALETTE_OUTLINED, color="#7c3aed"),
                            title=ft.Text("Tema Seçimi (Sistem / Açık / Koyu)", size=13, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text("Varsayılan: Cihaz teması", size=10, color="#64748b"),
                            on_click=lambda _: menu_aksiyon_calistir(tema_secim_dialogu_ac)
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.SCHOOL_ROUNDED, color="#f59e0b"),
                            title=ft.Text("Otomatik Okul Harçlığı", size=13, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text("MEB takvimi uyumlu ayarlar", size=10, color="#64748b"),
                            on_click=lambda _: menu_aksiyon_calistir(harclik_ayarlari_modal_ac)
                        ),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.PIE_CHART_ROUNDED, color="#6366f1"),
                            title=ft.Text("Kategori Grafikleri & İstatistik", size=13, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text("Harcama dağılımı ve analizler", size=10, color="#64748b"),
                            on_click=lambda _: menu_aksiyon_calistir(istatistik_ac)
                        ),
                        ft.Divider(height=6, color="#e2e8f0"),
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.MANAGE_ACCOUNTS_ROUNDED, color="#dc2626"),
                            title=ft.Text("Hesap Değiştir / Çıkış", size=13, weight=ft.FontWeight.W_600),
                            subtitle=ft.Text(f"Aktif: {kullanici}", size=10, color="#64748b"),
                            on_click=lambda _: menu_aksiyon_calistir(cikis_yap_aksiyon)
                        )
                    ], spacing=0, scroll=ft.ScrollMode.AUTO),
                    width=320,
                    height=360
                ),
                actions=[
                    make_button("✕ Kapat", height=32, outlined=True, on_click=lambda _: close_app_dialog(page, menu_dialog))
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, menu_dialog)

        # Üst Başlık Barı (Telefonda ve Masaüstünde Asla Taşmayan, %100 Görünür ve Ferah Tasarım)
        # Menü butonu canlı mavi renkle belirginleştirildi; sağdaki tekrar eden ikonlar menüde olduğu için sadeleştirildi.
        menu_btn = make_icon_btn(
            ft.Icons.MENU_ROUNDED, 
            icon_size=28, 
            icon_color="#2563eb", 
            tooltip="Uygulama Menüsü (CSV, Tema, Ayarlar)", 
            on_click=menu_ac
        )

        ust_baslik_bari = ft.Container(
            content=ft.Row([
                ft.Row([
                    menu_btn,
                    ft.Text("🏠 Hane Bütçesi", size=17.5, weight=ft.FontWeight.BOLD)
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                profil_cipi
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            width=355,
            padding=make_padding(0, 4)
        )


        # --- DOĞAL DİL / SÖZEL İŞLEM EKLEME ÇUBUĞU (GEMINI.COM KALİTESİNDE) ---
        def sozel_islem_calistir(ev=None):
            cumle = sozel_input.value.strip()
            if not cumle:
                show_app_snackbar(page, "Lütfen bir ifade yazın (Örn: bimden 14.21 de 3 ekmek alındı)", color="#ef4444")
                return

            bilgi_mesaji.value = "🤖 Gemini AI ifadeyi analiz ediyor..."
            bilgi_mesaji.color = "#8b5cf6"
            try:
                bilgi_mesaji.update()
            except Exception:
                pass

            def arka_plan_sozel():
                hafiza = hafiza_olustur(islemler)
                api_key = gemini_api_key_al()
                sonuc = None

                # 1. Gemini AI ile profesyonel doğal dil analizi
                if api_key:
                    hafiza_satirlari = [f"- {v['firma']} | {v['urun']} | Birim Fiyat: {v['birim_fiyat']} TL | Kategori: {v['kategori']}" for v in list(hafiza.values())[:45]]
                    hafiza_metni = "\n".join(hafiza_satirlari)
                    su_an = datetime.datetime.now()
                    bugun_str = su_an.strftime("%d.%m.%Y")
                    saat_str = su_an.strftime("%H:%M")

                    prompt = f"""Sen profesyonel bir kişisel finans ve bütçe asistanısın. Kullanıcının doğal Türkçe harcama, gelir veya para transferi cümlesini analiz et.

KULLANICI CÜMLESİ:
"{cumle}"

BAĞLAM:
- Bugünün Tarihi: {bugun_str}
- Şimdiki Saat: {saat_str}
- Kullanıcının Geçmiş Bütçe Fiyat Hafızası:
{hafiza_metni}

ANALİZ VE ÇIKARIM KURALLARI:
1. İŞLEM TÜRÜ (tur):
   - 'Gider': Alışveriş, harcama, market, fatura, benzin, ödeme vb.
   - 'Gelir': Maaş, ek ders, harçlık alma, hediye para vb.
   - 'Para Aktarımı': Bir aile üyesine nakit verme, IBAN'dan para gönderme vb.
2. FİRMA / KURUM (firma veya kaynak):
   - Harcamada satıcı/market adı (Örn: 'BİM', 'A101', 'Migros', 'Shell', 'Eczane', 'Nakit').
   - Belirtilmemişse 'Market' veya 'Diğer' yaz.
3. ÜRÜN / HİZMET (urun veya aciklama):
   - Kullanıcının aldığı ürün veya yapılan harcamanın net adı (Örn: 'EKMEK TEKLİ', 'Süt', 'Benzin', 'Öğretmen Maaşı').
   - ASLA kullanıcının cümlesinde bahsetmediği alakasız ürünler uydurma!
4. MİKTAR (miktar):
   - Cümlede miktar varsa (Örn: '3 adet', '1.5 kg', '2 paket', '40 litre') yaz, yoksa '1 adet'.
5. FİYAT VE TUTAR:
   - Eğer kullanıcı tutarı doğrudan söylediyse (Örn: '850 TL benzin', '50 liraya tost'): bu tutarı kullan.
   - Eğer kullanıcı sadece miktar söylediyse ve fiyat belirtmediyse (Örn: '3 ekmek alındı'): Geçmiş Fiyat Hafızasındaki o firmanın birim fiyatını kullan (Örn: BİM Ekmek = 11,00 TL). Tutarı = miktar x birim_fiyat olarak hesapla (3 x 11,00 = 33,00 TL).
6. KATEGORİ:
   - Standart bütçe kategorilerinden en uygununu seç: 'Market & Temel Gıda', 'Abur Cubur & Atıştırmalık', 'Ev & Faturalar', 'Dışarıda Yemek / Eğlence', 'Eğitim & Okul', 'Ulaşım & Yakıt', 'Sağlık & Bakım', 'Giyim', 'Sigara/Tütün', 'Aile / Harçlık', 'Maaş', 'Ödenek', 'Ek Ders', 'Devir / Nakit', 'Transfer / Birikim', 'Diğer'.

ÇIKTI FORMATI:
Yalnızca aşağıdaki şemaya uygun SAF JSON döndür (markdown kod bloğu ekleme, doğrudan json döndür):
{{
  "tur": "Gider",
  "firma": "BİM",
  "urun": "EKMEK TEKLİ",
  "miktar": "3 adet",
  "birim_fiyat": "11,00",
  "tutar": 33.00,
  "tarih": "{bugun_str}",
  "saat": "{saat_str}",
  "kategori": "Market & Temel Gıda"
}}"""

                    ssl_ctx = None
                    try:
                        ssl_ctx = ssl.create_default_context()
                        ssl_ctx.check_hostname = False
                        ssl_ctx.verify_mode = ssl.CERT_NONE
                    except Exception:
                        pass

                    # Google API'den aktif ve çalışan flash modellerini dinamik çek
                    aktif_list = gemini_aktif_modelleri_bul(api_key, ssl_ctx)
                    denenecek_modeller = aktif_list[:3] if aktif_list else [("v1beta", "gemini-1.5-flash")]

                    for api_ver, model_name in denenecek_modeller:
                        try:
                            url = f"https://generativelanguage.googleapis.com/{api_ver}/models/{model_name}:generateContent"
                            payload = {
                                "contents": [{"parts": [{"text": prompt}]}],
                                "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"}
                            }
                            req = urllib.request.Request(
                                url,
                                data=json.dumps(payload).encode("utf-8"),
                                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"}
                            )
                            kw = {"timeout": 4}
                            if ssl_ctx:
                                kw["context"] = ssl_ctx
                            with urllib.request.urlopen(req, **kw) as resp:
                                res_data = json.loads(resp.read().decode("utf-8"))
                                cands = res_data.get("candidates", [])
                                if cands:
                                    txt = cands[0]["content"]["parts"][0]["text"].strip()
                                    if txt.startswith("```json"): txt = txt[7:]
                                    if txt.startswith("```"): txt = txt[3:]
                                    if txt.endswith("```"): txt = txt[:-3]
                                    sonuc = json.loads(txt.strip())
                                    if sonuc and "tutar" in sonuc:
                                        print(f"✅ Gemini AI sözel analiz başarılı ({model_name}): {sonuc}")
                                        break
                        except Exception as ex_m:
                            print(f"Gemini sözel model denemesi ({model_name}) hatası:", ex_m)
                            continue

                # 2. Yedek / Çevrimdışı Akıllı Ayrıştırıcı
                if not sonuc:
                    sonuc = parse_sozel_ifade_yerel(cumle, hafiza)

                if sonuc:
                    yeni_islem = {
                        "kullanici": kullanici or "Ev Yöneticisi",
                        "tur": sonuc.get("tur", "Gider"),
                        "tarih": sonuc.get("tarih") or datetime.date.today().strftime("%d.%m.%Y"),
                        "saat": sonuc.get("saat") or datetime.datetime.now().strftime("%H:%M"),
                        "kaynak": sonuc.get("kaynak", "") if sonuc.get("tur") in ["Gelir", "Para Aktarımı"] else "",
                        "gelir_turu": sonuc.get("kategori", "") if sonuc.get("tur") == "Gelir" else "",
                        "aciklama": f"Sözel: {cumle}",
                        "firma": sonuc.get("firma", "Diğer") if sonuc.get("tur") == "Gider" else "",
                        "urun": sonuc.get("urun", "Genel Harcama") if sonuc.get("tur") == "Gider" else "",
                        "kategori": sonuc.get("kategori", "Diğer"),
                        "miktar": sonuc.get("miktar", "1 adet"),
                        "birim_fiyat": str(sonuc.get("birim_fiyat", "")),
                        "tutar": float(sonuc.get("tutar", 0.0))
                    }

                    if supabase:
                        try:
                            res = supabase.table("islemler").insert(yeni_islem).execute()
                            if res and res.data and len(res.data) > 0 and res.data[0].get("id"):
                                yeni_islem["id"] = res.data[0]["id"]
                        except Exception as db_err:
                            print("Supabase sözel kayıt hatası:", db_err)

                    if "id" not in yeni_islem:
                        mevcut_idler = [it.get("id") for it in islemler if isinstance(it.get("id"), int)]
                        yeni_islem["id"] = (max(mevcut_idler) + 1) if mevcut_idler else 1

                    islemler.insert(0, yeni_islem)
                    sozel_input.value = ""
                    arayuzu_guncelle()
                    try:
                        liste_arayuzu.update()
                    except Exception:
                        pass

                    tutar_str = format_turk_para(yeni_islem["tutar"])
                    birim_str = yeni_islem.get("birim_fiyat", "")
                    firma_gosterim = yeni_islem.get("firma") or yeni_islem.get("kaynak") or "İşlem"
                    urun_gosterim = yeni_islem.get("urun") or yeni_islem.get("gelir_turu") or ""

                    if birim_str and birim_str != "-":
                        msg = f"✨ Eklendi: {firma_gosterim} - {urun_gosterim} ({yeni_islem['miktar']} x {birim_str} TL = {tutar_str} TL)"
                    else:
                        msg = f"✨ Eklendi: {firma_gosterim} - {urun_gosterim} ({tutar_str} TL)"

                    show_app_snackbar(page, msg, color="#10b981")
                    bilgi_mesaji.value = msg
                    bilgi_mesaji.color = "green"
                    try:
                        page.update()
                    except Exception:
                        pass
                else:
                    show_app_snackbar(page, "İfade anlaşılamadı, lütfen tekrar deneyin.", color="#ef4444")

            threading.Thread(target=arka_plan_sozel, daemon=True).start()

        sozel_input = ft.TextField(
            hint_text="🗣️ Sözel işlem yazın (örn: bimden 14.21 de 3 ekmek alındı)",
            text_size=11,
            expand=True,
            dense=True,
            on_submit=sozel_islem_calistir
        )

        # --- SESLE VERİ GİRİŞİ DİYALOĞU ---
        def sesli_giris_dialogu_ac(e=None):
            dokunma_geribildirimi()
            ses_metni_tf = ft.TextField(
                label="Konuştuğunuz İfadeyi Buradan İnceleyin / Düzenleyin",
                hint_text="Örn: BİM'den 3 ekmek 33 lira aldım...",
                multiline=True,
                min_lines=2,
                max_lines=4,
                value=sozel_input.value or "",
                autofocus=True
            )

            def sesli_onayla(ev):
                metin = ses_metni_tf.value.strip()
                if metin:
                    sozel_input.value = metin
                    close_app_dialog(page, sesli_dialog)
                    sozel_islem_calistir()
                else:
                    show_app_snackbar(page, "Lütfen harcamanızı söyleyin veya yazın.", color="#ef4444")

            sesli_dialog = ft.AlertDialog(
                title=ft.Row([
                    ft.Icon(ft.Icons.MIC_ROUNDED, color="#ef4444", size=24),
                    ft.Text("🎙️ Sesle Veri Girişi", size=16, weight=ft.FontWeight.BOLD)
                ], spacing=8),
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Klavyenizin mikrofon tuşuna dokunarak konuşabilir veya sesli ifadenizi buraya söyleyebilirsiniz:", size=11, color="#64748b"),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.RECORD_VOICE_OVER_ROUNDED, color="#6366f1", size=20),
                                ft.Text("Örn: 'BİM 3 ekmek 33 lira' veya 'Shell 500 tl benzin'", size=11, color="#4338ca", italic=True)
                            ], spacing=6),
                            bgcolor="#eef2ff",
                            border_radius=8,
                            padding=make_padding(8, 6)
                        ),
                        ses_metni_tf
                    ], spacing=10, tight=True),
                    width=330
                ),
                actions=[
                    make_button("✕ İptal", height=34, outlined=True, on_click=lambda _: close_app_dialog(page, sesli_dialog)),
                    make_button("⚡ AI ile Ekle", height=34, bgcolor="#6366f1", color="white", on_click=sesli_onayla)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            show_app_dialog(page, sesli_dialog)

        mic_btn = make_icon_btn(ft.Icons.MIC_ROUNDED, icon_size=22, icon_color="#ef4444", tooltip="🎙️ Sesle Veri Girişi", on_click=sesli_giris_dialogu_ac)

        sozel_cubuk = ft.Container(
            content=ft.Row([
                sozel_input,
                mic_btn,
                make_button("✨ AI Ekle", height=36, bgcolor="#6366f1", color="white", on_click=sozel_islem_calistir)
            ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor="white",
            border=make_border_all(1, "#e2e8f0"),
            border_radius=14,
            padding=make_padding(6, 6),
            width=355
        )

        # Hızlı Aksiyon Butonları (CSV Menüye Taşındı; Ekranda 2 Büyük, Ferah ve Ortalı Ana Buton Kaldı)
        btn_yeni_islem = form_ac_kapat_btn
        btn_fis_tara = make_button("📸 Fiş Tara", bgcolor="#7c3aed", color="white", height=44, tooltip="Fiş Fotoğrafı Yükle & AI ile Oku", expand=True, on_click=fis_tara_tiklandi)

        hizli_aksiyon_bari = ft.Container(
            content=ft.Row([btn_yeni_islem, btn_fis_tara], spacing=10, alignment=ft.MainAxisAlignment.CENTER),
            width=355
        )

        # Liste Konteyneri (Beyaz modern kart içine yerleştirilmiş temiz liste)
        liste_kapsayici = ft.Container(
            content=liste_arayuzu,
            bgcolor="white",
            border_radius=16,
            border=make_border_all(1, "#e2e8f0"),
            padding=6,
            width=355
        )

        page.add(
            ft.Column([
                ft.Container(height=2),
                ust_baslik_bari,
                donem_bar,
                bakiye_karti,
                ft.Container(height=2),
                sozel_cubuk,
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

        # Uygulama açılışında okulların açık olduğu günleri otomatik kontrol et ve harçlık ekle
        try:
            otomatik_harclik_tara_ve_ekle(sessiz=True)
        except Exception as ex_h_start:
            print("Açılış otomatik harçlık kontrol hatası:", ex_h_start)

    def giris_ekranina_git():
        if hasattr(page, "scroll_to"):
            try:
                page.scroll_to(offset=0, duration=0)
            except Exception:
                pass
        page.dialog = None
        if hasattr(page, "clean"):
            try:
                page.clean()
            except Exception:
                page.controls.clear()
        else:
            page.controls.clear()

        # Giriş Ekranı Bileşenleri
        kullanici_adi = ft.TextField(label="Kullanıcı Adı (Abdurrahman / Hatice)", width=320)
        sifre = ft.TextField(label="Şifre", password=True, can_reveal_password=True, width=320)
        beni_hatirla = ft.Checkbox(label="Beni Hatırla", value=True)
        hata_mesaji = ft.Text("", color="red")

        def giris_yap(e):
            raw_ad = kullanici_adi.value.strip()
            ad_lower = raw_ad.lower()
            pass_val = sifre.value.strip()

            if (raw_ad == "Abdurrahman" or ad_lower in ["abdurrahman", "yönetici"]) and pass_val == "1234":
                if beni_hatirla.value:
                    oturum_kaydet("Abdurrahman", True)
                ana_ekrana_git("Abdurrahman", yonetici_mi=True)
            elif (raw_ad == "Hatice" or ad_lower in ["hatice", "üye"]) and pass_val == "5678":
                if beni_hatirla.value:
                    oturum_kaydet("Hatice", False)
                ana_ekrana_git("Hatice", yonetici_mi=False)
            else:
                hata_mesaji.value = "Hatalı kullanıcı adı veya şifre!"
                page.update()

        def hizli_yonetici_giris(ev):
            if beni_hatirla.value:
                oturum_kaydet("Abdurrahman", True)
            ana_ekrana_git("Abdurrahman", yonetici_mi=True)

        def hizli_uye_giris(ev):
            if beni_hatirla.value:
                oturum_kaydet("Hatice", False)
            ana_ekrana_git("Hatice", yonetici_mi=False)

        page.add(
            ft.Column([
                ft.Container(height=40),
                ft.Text("🏠 Hane Bütçesi Giriş", size=24, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                kullanici_adi,
                sifre,
                ft.Container(content=ft.Row([beni_hatirla], alignment=ft.MainAxisAlignment.START), width=320),
                ft.Container(height=5),
                make_button("Giriş Yap", icon=ft.Icons.LOGIN, bgcolor="blue", color="white", width=320, height=45, on_click=giris_yap),
                hata_mesaji,
                ft.Divider(height=24, color="#e2e8f0"),
                ft.Text("⚡ Tek Tıkla Hızlı Hesap Girişi:", size=11, color="#64748b", weight=ft.FontWeight.W_600),
                ft.Row([
                    make_button("👑 Abdurrahman (Yönetici)", bgcolor="#2563eb", color="white", height=36, on_click=hizli_yonetici_giris),
                    make_button("👤 Hatice (Aile Üyesi)", bgcolor="#0284c7", color="white", height=36, on_click=hizli_uye_giris),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        kullanici_adi.on_submit = giris_yap
        sifre.on_submit = giris_yap
        page.update()

    # Oturum Kontrolü
    kayitli_oturum = oturum_oku()
    if kayitli_oturum and "kullanici" in kayitli_oturum and "yonetici_mi" in kayitli_oturum:
        ana_ekrana_git(kayitli_oturum["kullanici"], kayitli_oturum["yonetici_mi"])
    else:
        giris_ekranina_git()

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)