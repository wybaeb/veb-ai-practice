#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка презентации защиты: не заезжает ли контент на колонтитул.

Зачем. Тема удерживает большинство дизайнерских проблем генерации (прозрачные
таблицы, ограничение картинок, безопасная зона), но CSS не может ужать слайд,
на который навалили больше текста, чем помещается. Этот скрипт — измеримый
гейт: рендерит презентацию в картинки и смотрит, есть ли контент в защитной полосе
над нижним краем кадра (там живут подпись и номер страницы).

Правило починки — СОКРАЩАЙ ТЕКСТ, а не кегль: убери строку, ужми формулировку,
разбей слайд на два. Уменьшение шрифта — последнее средство.

Запуск:
    python3 templates/check_slides.py deck.md
    python3 templates/check_slides.py deck.md --theme templates/theme.css

Код возврата: 0 — все слайды чистые; 1 — есть заезды (список в выводе).
Зависимости: npx @marp-team/marp-cli + Chrome, Pillow. Если чего-то нет,
скрипт честно скажет и завершится кодом 2 (проверка недоступна — проверь глазами).
"""

import argparse
import os
import subprocess
import sys
import tempfile

# Защитная полоса: нижние пиксели кадра 1280×720, где стоят колонтитул и номер.
# Рендер идёт со СКРЫТЫМ колонтитулом (см. ниже), поэтому в полосе не должно
# быть ни одного яркого пикселя — любой найденный означает заезд контента.
BAND_TOP, BAND_BOTTOM = 662, 712     # y-диапазон полосы (из 720)
X_FROM_FRAC, X_TO_FRAC = 0.03, 0.97  # почти вся ширина
BRIGHT = 96                          # порог «на тёмном фоне что-то нарисовано»
MIN_PIXELS = 40                      # меньше — списываем на антиалиасинг

# Колонтитул и номер скрываются на время проверки, чтобы их собственные пиксели
# не путались с заездом контента. Титульный и секционный слайды центрируют
# контент и проверяются на общих основаниях.
HIDE_CHROME_CSS = "\nfooter, section::after { visibility: hidden !important; }\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("deck")
    ap.add_argument("--theme", default=os.path.join(os.path.dirname(__file__), "theme.css"))
    args = ap.parse_args()

    try:
        from PIL import Image
    except ImportError:
        print("check_slides: нет Pillow (pip install pillow) — проверь слайды глазами")
        sys.exit(2)

    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "s.png")
        # копия темы с выключенным колонтитулом; @theme-имя сохраняется
        check_theme = os.path.join(td, "theme_check.css")
        with open(check_theme, "w", encoding="utf-8") as f:
            f.write(open(args.theme, encoding="utf-8").read() + HIDE_CHROME_CSS)
        env = dict(os.environ, CHROME_NO_SANDBOX="true")
        res = subprocess.run(
            ["npx", "@marp-team/marp-cli", args.deck, "--theme", check_theme,
             "--allow-local-files", "--images", "png", "-o", out],
            capture_output=True, text=True, env=env, timeout=420)
        pngs = sorted(f for f in os.listdir(td) if f.endswith(".png"))
        if res.returncode != 0 or not pngs:
            print("check_slides: рендер не удался — проверь слайды глазами\n"
                  + (res.stderr or "")[-400:])
            sys.exit(2)

        bad = []
        for i, name in enumerate(pngs, 1):
            im = Image.open(os.path.join(td, name)).convert("L")
            w, h = im.size
            ky, kx = h / 720.0, w / 1280.0
            band = im.crop((int(w * X_FROM_FRAC), int(BAND_TOP * ky),
                            int(w * X_TO_FRAC), int(BAND_BOTTOM * ky)))
            n = sum(1 for p in band.getdata() if p > BRIGHT)
            if n >= MIN_PIXELS * kx * ky:
                bad.append((i, n))

        if bad:
            print("Контент заезжает в зону колонтитула:")
            for i, n in bad:
                print(f"  слайд {i}: сократи текст (убери строку или разбей слайд) "
                      f"[{n} px в защитной полосе]")
            print("Правило: сокращай ФОРМУЛИРОВКИ, а не кегль.")
            sys.exit(1)
        print(f"OK: все {len(pngs)} слайдов в кадре, колонтитул чистый")


if __name__ == "__main__":
    main()
