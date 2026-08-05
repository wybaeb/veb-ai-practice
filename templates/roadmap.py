#!/usr/bin/env python3
"""Дорожная карта инициативы (A10): диаграмма Ганта одной командой.

Единственный блок для правок — ИНИЦИАТИВА и ЭТАПЫ ниже. Всё остальное трогать
не нужно. Каждый этап — кортеж:
    (результат этапа, месяц начала 0–11, длительность в месяцах,
     точка решения после этапа)
Результат этапа — работающий результат, а не документ; точка решения — порог
числом, по которому продолжаем, меняем подход или останавливаемся.

Рендер:  python3 templates/roadmap.py -o roadmap_gantt.png
"""
import argparse

ИНИЦИАТИВА = "Предпроектная проработка инициатив регионов"

ЭТАПЫ = [
    ("Пилот: 20 заявок одного типа", 0, 3,
     "трудозатраты ≤ 34 ч/заявка — продолжаем"),
    ("Подключение реестров", 3, 3,
     "черновик за 3 дня ≥ 70 % заявок"),
    ("Раскатка на все типы заявок", 6, 3,
     "окупаемость идёт по базовому сценарию"),
    ("Эффект на годовой выборке", 9, 3,
     "NPV на фактических данных ≥ 0 — тиражируем"),
]

# ── дальше только рендер ─────────────────────────────────────────────────────

ФОН, ПАНЕЛЬ = "#1e2027", "#262933"
БРЕНД, СВЕТ, ПРИГЛУШЕНО = "#ff5533", "#ffffff", "#ffffffa0"


def диаграмма(путь):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyBboxPatch
    except ImportError:
        print("[matplotlib не установлен — диаграмма пропущена]")
        return

    n = len(ЭТАПЫ)
    fig, ax = plt.subplots(figsize=(11, 1.3 + 1.15 * n))
    fig.patch.set_facecolor(ФОН)
    ax.set_facecolor(ФОН)

    for i, (результат, старт, длит, порог) in enumerate(ЭТАПЫ):
        y = n - 1 - i
        ax.add_patch(FancyBboxPatch(
            (старт, y - .18), длит - .12, .36,
            boxstyle="round,pad=0.02,rounding_size=0.12",
            linewidth=0, facecolor=БРЕНД, alpha=.92))
        ax.text(старт + .08, y + .34, результат,
                fontsize=10.5, fontweight="bold", color=СВЕТ, va="bottom")
        кон = старт + длит - .06
        ax.plot(кон, y, marker="D", markersize=7, color=СВЕТ,
                markeredgecolor=БРЕНД, markeredgewidth=1.4, zorder=5)
        # подпись порога — справа от ромба; у этапов конца года справа нет
        # места, поэтому подпись уходит под бар и прижимается к правому краю
        if кон > 9:
            ax.text(кон, y - .34, "◆ " + порог, fontsize=8.6,
                    color=ПРИГЛУШЕНО, va="top", ha="right")
        else:
            ax.text(кон + .18, y, "◆ " + порог, fontsize=8.6,
                    color=ПРИГЛУШЕНО, va="center")

    for кв, м in (("I кв", 0), ("II кв", 3), ("III кв", 6), ("IV кв", 9)):
        ax.axvline(м, color="#ffffff22", linewidth=1, zorder=0)
        ax.text(м + 1.5, n - .28, кв, fontsize=9.5, color=ПРИГЛУШЕНО,
                ha="center", fontweight="bold")
    ax.axvline(12, color="#ffffff22", linewidth=1, zorder=0)

    ax.set_xlim(-.15, 12.15)
    ax.set_ylim(-.6, n)
    ax.axis("off")
    ax.set_title(f"Дорожная карта 12 месяцев · {ИНИЦИАТИВА}\n"
                 "каждый этап заканчивается работающим результатом, ◆ — точка решения",
                 fontsize=11.5, color=СВЕТ, pad=14)
    fig.tight_layout()
    fig.savefig(путь, dpi=150, facecolor=ФОН)
    print(f"Диаграмма Ганта сохранена: {путь}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Диаграмма Ганта дорожной карты (A10)")
    ap.add_argument("-o", "--out", default="roadmap_gantt.png",
                    metavar="PNG", help="куда сохранить диаграмму")
    args = ap.parse_args()
    диаграмма(args.out)
