#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — сборка зашифрованной страницы практики для GitHub Pages.

Берёт src/app.html, шифрует паролем (PBKDF2-HMAC-SHA256 + AES-256-GCM,
совместимо с WebCrypto в браузере) и собирает index.html с парольным гейтом.
После ввода пароля страница расшифровывается на клиенте, пароль кладётся
в localStorage — при следующем заходе не запрашивается.

Ссылка на AGENTS.md лежит ВНУТРИ зашифрованной части: чтобы её получить,
нужно открыть страницу паролем. Сам файл AGENTS.md в репозитории остаётся
читаемым — иначе агент не сможет его загрузить (пароль он ввести не может).

Использование:
    python3 build.py --password 'ПАРОЛЬ'
    VEB_PRACTICE_PASSWORD='ПАРОЛЬ' python3 build.py
"""
import argparse
import base64
import os
import sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER = 200_000
ROOT = os.path.dirname(os.path.abspath(__file__))


def b64(b):
    return base64.b64encode(b).decode()


def encrypt(plaintext: bytes, password: str):
    salt = os.urandom(16)
    iv = os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER)
    key = kdf.derive(password.encode())
    ct = AESGCM(key).encrypt(iv, plaintext, None)  # ct||tag — как ждёт WebCrypto
    return b64(salt), b64(iv), b64(ct)


GATE = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Практика с ИИ-агентом · Государство на скорости ИИ</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;800&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box}}
body{{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;
 font-family:'Manrope',system-ui,-apple-system,'Segoe UI',sans-serif;color:#fff;
 background:radial-gradient(1100px 620px at 82% -14%,rgba(255,85,51,.26),transparent 62%),
            linear-gradient(180deg,#23262e,#1e2027)}}
.card{{background:#23262e;border:1px solid rgba(255,255,255,.11);border-radius:22px;
 box-shadow:0 30px 80px rgba(0,0,0,.45);padding:40px 36px;width:min(440px,94vw)}}
.mark{{width:46px;height:46px;border-radius:13px;margin-bottom:22px;
 background:linear-gradient(135deg,#ff5533,#ff8a6b);box-shadow:0 8px 22px rgba(255,85,51,.36)}}
.eyebrow{{color:#ff5533;font-weight:800;font-size:11.5px;letter-spacing:.14em;
 text-transform:uppercase;margin-bottom:10px}}
h1{{font-size:25px;font-weight:800;margin:0 0 10px;line-height:1.2}}
p{{color:rgba(255,255,255,.62);font-size:14.5px;margin:0 0 24px;line-height:1.55}}
input{{width:100%;padding:14px 16px;font-size:16px;font-family:inherit;color:#fff;
 background:#1a1d24;border:1.5px solid rgba(255,255,255,.13);border-radius:12px;outline:none}}
input:focus{{border-color:#ff5533}}
input::placeholder{{color:rgba(255,255,255,.3)}}
button{{margin-top:12px;width:100%;padding:14px;font-size:15px;font-weight:800;font-family:inherit;
 border:0;border-radius:12px;cursor:pointer;background:#ff5533;color:#fff;transition:.15s}}
button:hover{{filter:brightness(1.08)}}
.err{{color:#ff8a6b;font-size:13px;height:18px;margin-top:11px;font-weight:700}}
.foot{{margin-top:22px;padding-top:18px;border-top:1px solid rgba(255,255,255,.1);
 font-size:12.5px;color:rgba(255,255,255,.4);line-height:1.55}}
</style></head>
<body>
<div class="card">
 <div class="mark"></div>
 <div class="eyebrow">karpov.courses × ВЭБ.РФ</div>
 <h1>Практика с персональным ИИ-агентом</h1>
 <p>Страница закрыта паролем. Внутри — пошаговое описание практики, промпты,
    шаблоны артефактов и ссылка, которую вы даёте своему агенту.</p>
 <input id="pw" type="password" placeholder="Пароль" autocomplete="current-password" autofocus>
 <button id="go">Открыть</button>
 <div class="err" id="err"></div>
 <div class="foot">Интенсив «Государство на скорости ИИ» · 6–7 августа 2026.
   Пароль сохраняется в браузере — при следующем заходе вводить не нужно.</div>
</div>
<script>
const DATA={{salt:"{salt}",iv:"{iv}",ct:"{ct}",iter:{iter}}};
const KEY="veb_practice_pw";
const dec=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function unlock(pw){{
  const enc=new TextEncoder();
  const km=await crypto.subtle.importKey("raw",enc.encode(pw),"PBKDF2",false,["deriveKey"]);
  const key=await crypto.subtle.deriveKey(
    {{name:"PBKDF2",salt:dec(DATA.salt),iterations:DATA.iter,hash:"SHA-256"}},
    km,{{name:"AES-GCM",length:256}},false,["decrypt"]);
  const pt=await crypto.subtle.decrypt({{name:"AES-GCM",iv:dec(DATA.iv)}},key,dec(DATA.ct));
  return new TextDecoder().decode(pt);
}}
async function render(html){{document.open();document.write(html);document.close();}}
async function attempt(pw,fromCache){{
  try{{const html=await unlock(pw);localStorage.setItem(KEY,pw);await render(html);}}
  catch(e){{
    if(fromCache){{localStorage.removeItem(KEY);}}
    else{{document.getElementById("err").textContent="Неверный пароль";
      document.getElementById("pw").value="";document.getElementById("pw").focus();}}
  }}
}}
document.getElementById("go").onclick=()=>attempt(document.getElementById("pw").value,false);
document.getElementById("pw").addEventListener("keydown",e=>{{if(e.key==="Enter")attempt(e.target.value,false);}});
const cached=localStorage.getItem(KEY);
if(cached) attempt(cached,true);
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description="Сборка зашифрованной страницы практики")
    ap.add_argument("--password", default=os.environ.get("VEB_PRACTICE_PASSWORD"))
    ap.add_argument("--src", default=os.path.join(ROOT, "src", "app.html"))
    ap.add_argument("--out", default=os.path.join(ROOT, "index.html"))
    a = ap.parse_args()
    if not a.password:
        sys.exit("Нужен пароль: --password '...' или VEB_PRACTICE_PASSWORD=...")
    with open(a.src, "rb") as f:
        plaintext = f.read()
    salt, iv, ct = encrypt(plaintext, a.password)
    html = GATE.format(salt=salt, iv=iv, ct=ct, iter=ITER)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"OK · {a.out} · payload {len(ct)} b64-символов · PBKDF2 {ITER} итераций")


if __name__ == "__main__":
    main()
