import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium", app_title="Lab01 · Интерактивный генератор")


@app.cell(hide_code=True)
def _():
    import io

    import marimo as mo
    import numpy as np
    import pandas as pd
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from scipy import stats

    # Та же палитра и стиль, что в Jupyter-ноутбуке (блок КТвД)
    STYLE = {
        "surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "grid": "#e6e5e0",
        # данные – цветом величины (как в ноутбуке), выборка генератора – графитовой линией
        "ls": {"polar": "-", "inverse": "--", "quantile": ":"},
    }
    mpl.rcParams.update({
        "figure.facecolor": STYLE["surface"], "axes.facecolor": STYLE["surface"],
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.titlesize": 11.5, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 10,
        "axes.labelcolor": STYLE["ink2"], "axes.edgecolor": STYLE["grid"],
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": STYLE["grid"], "grid.linewidth": 0.8, "axes.axisbelow": True,
        "xtick.color": STYLE["ink2"], "ytick.color": STYLE["ink2"],
        "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.frameon": False, "legend.fontsize": 9,
    })
    return io, mo, np, pd, plt, stats, STYLE


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Интерактивный генератор случайных чисел

    **Lab01 · блок КТвД.** Генератор из второго спринта (`InfoChemRandomGenerator`) с панелью управления.
    Базовый датчик – вихрь Мерсенна MT19937, $U \sim \mathcal{U}(0, 1)$. Поверх него три метода:
    полярный метод Марсальи, метод обратной функции и эмпирическое квантильное преобразование.
    Меняйте параметры, графики и метрики пересчитываются сами.

    **Лабораторная работа №1 · Прикладная статистика · команда ic22.**
    Генератор: Мамедгасанов Гашам, Дрожжина Анна, Михайлова Мария (Инфохимия).
    Интерактивное приложение: Караева Станислава, Котикова Елизавета (Дизайн, КТвД).
    """)
    return


@app.cell(hide_code=True)
def _(io, pd):
    def _read(urls, **kw):
        for url in urls:
            try:
                return pd.read_csv(url, **kw)
            except Exception:
                try:  # macOS + Python 3.14: ошибка сертификатов, как в основной части
                    import requests, urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    r = requests.get(url, verify=False, timeout=20)
                    r.raise_for_status()
                    return pd.read_csv(io.StringIO(r.text), **kw)
                except Exception:
                    continue
        raise RuntimeError(f"Не удалось загрузить: {urls[-1]}")

    esol = _read([
        "https://raw.githubusercontent.com/deepchem/deepchem/master/datasets/delaney-processed.csv",
        "delaney-processed.csv",
    ])
    wine = _read([
        "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
        "https://raw.githubusercontent.com/zygmuntz/wine-quality/master/winequality/winequality-red.csv",
        "winequality-red.csv",
    ], sep=";").drop_duplicates().reset_index(drop=True)

    DATA = {
        "lg S – растворимость (ESOL, основная часть)": dict(
            x=esol["measured log solubility in mols per litre"].to_numpy(float),
            axis="LogS = lg S  (S в моль/л; безразмерная)", step=0.01, color="#2a78d6"),
        "pH – вино (блок КТвД, K1)": dict(
            x=wine["pH"].to_numpy(float), axis="pH (безразмерная)", step=0.01, color="#e34948"),
        "Фикс. кислотность – вино (блок КТвД, K2)": dict(
            x=wine["fixed acidity"].to_numpy(float), axis="Фикс. кислотность, г/дм³", step=0.1, color="#eb6834"),
    }
    return DATA, wine


@app.cell(hide_code=True)
def _(DATA, mo):
    var_select = mo.ui.dropdown(options=list(DATA), value=list(DATA)[0], label="Величина")
    method_select = mo.ui.radio(
        options={
            "Полярный метод Марсальи → нормальное": "polar",
            "Обратная функция → логистическое": "inverse",
            "Эмпирическое квантильное преобразование": "quantile",
        },
        value="Полярный метод Марсальи → нормальное",
        label="Метод",
    )
    n_slider = mo.ui.slider(100, 20000, step=100, value=1100, label="Объём выборки n", show_value=True)
    seed_input = mo.ui.text(value="2026", label="seed (MT19937)", full_width=False)
    bins_slider = mo.ui.slider(10, 80, step=1, value=35, label="Число бинов", show_value=True)
    from_data = mo.ui.switch(value=True, label="μ и σ брать из данных")
    return bins_slider, from_data, method_select, n_slider, seed_input, var_select


@app.cell(hide_code=True)
def _(DATA, mo, np, var_select):
    _x = DATA[var_select.value]["x"]
    _m, _s = float(_x.mean()), float(_x.std(ddof=1))
    mu_slider = mo.ui.slider(round(_m - 2 * _s, 2), round(_m + 2 * _s, 2), step=round(_s / 50, 3),
                             value=round(_m, 2), label="μ вручную", show_value=True)
    sigma_slider = mo.ui.slider(round(_s * 0.25, 3), round(_s * 2.5, 3), step=round(_s / 50, 3),
                                value=round(_s, 3), label="σ вручную", show_value=True)
    return mu_slider, sigma_slider


@app.cell(hide_code=True)
def _(bins_slider, from_data, method_select, mo, mu_slider, n_slider, seed_input, sigma_slider, var_select):
    _manual = mo.hstack([mu_slider, sigma_slider], justify="start", gap=2) if not from_data.value else mo.md(
        "<span style='color:#52514e'>Включите ручной режим, чтобы сдвинуть μ и σ и посмотреть, как модель расходится с данными.</span>")
    controls = mo.vstack([
        mo.hstack([var_select, seed_input], justify="start", gap=2, wrap=True),
        method_select,
        mo.hstack([n_slider, bins_slider], justify="start", gap=2, wrap=True),
        from_data,
        _manual,
    ], gap=1)
    mo.callout(controls, kind="neutral")
    return


@app.cell(hide_code=True)
def _(np):
    class InfoChemRandomGenerator:
        """Генератор из спринта 2 + третий метод. Базовый датчик – только U(0, 1) от MT19937."""

        def __init__(self, seed=42):
            self.rng = np.random.Generator(np.random.MT19937(seed))
            self.acceptance = None

        def polar_marsaglia(self, n, mu, sigma):
            """Алгоритм P (Кнут, т. 2, 3.4.1), векторизованный: пары точек отбираются пачками."""
            out, tried, kept = [], 0, 0
            while kept < n:
                m = int((n - kept) / 2 / 0.785) + 16
                v = 2.0 * self.rng.random((m, 2)) - 1.0
                s = (v ** 2).sum(axis=1)
                ok = (s > 0) & (s < 1)
                tried += m
                v, s = v[ok], s[ok]
                z = (v * np.sqrt(-2.0 * np.log(s) / s)[:, None]).ravel()
                out.append(z)
                kept += z.size
            self.acceptance = (kept / 2) / tried
            return mu + sigma * np.concatenate(out)[:n]

        def inverse_logistic(self, n, mu, sigma):
            """Метод обратной функции: X = μ + s·ln(U / (1 − U)), s = σ√3 / π."""
            s = sigma * np.sqrt(3.0) / np.pi
            u = self.rng.uniform(1e-7, 1.0 - 1e-7, size=n)
            self.acceptance = 1.0
            return mu + s * np.log(u / (1.0 - u))

        def empirical_quantile(self, n, data):
            """Квантильное преобразование по эмпирической ФР с линейной интерполяцией."""
            xs = np.sort(data)
            p = (np.arange(1, xs.size + 1) - 0.5) / xs.size
            self.acceptance = 1.0
            return np.interp(self.rng.random(n), p, xs)

    return (InfoChemRandomGenerator,)


@app.cell(hide_code=True)
def _(DATA, InfoChemRandomGenerator, from_data, method_select, mu_slider, n_slider, np, seed_input, sigma_slider, var_select):
    real = DATA[var_select.value]["x"]
    method = method_select.value
    mu = float(real.mean()) if from_data.value else float(mu_slider.value)
    sigma = float(real.std(ddof=1)) if from_data.value else float(sigma_slider.value)

    _digits = "".join(ch for ch in seed_input.value if ch.isdigit())
    gen = InfoChemRandomGenerator(seed=int(_digits) if _digits else 0)
    if method == "polar":
        synth = gen.polar_marsaglia(n_slider.value, mu, sigma)
    elif method == "inverse":
        synth = gen.inverse_logistic(n_slider.value, mu, sigma)
    else:
        synth = gen.empirical_quantile(n_slider.value, real)
        if not from_data.value:  # ручной режим: тот же сдвиг и масштаб
            synth = mu + sigma * (synth - real.mean()) / real.std(ddof=1)
    acceptance = gen.acceptance
    return acceptance, method, mu, real, sigma, synth


@app.cell(hide_code=True)
def _(method, mo, mu, sigma):
    _f = {
        "polar": r"""
**Полярный метод Марсальи.** Точка $(V_1, V_2)$ равномерна в квадрате $[-1, 1]^2$; берём только точки внутри круга:

$$V_i = 2U_i - 1,\quad S = V_1^2 + V_2^2,\quad 0 < S < 1 \;\Rightarrow\; Z_i = V_i\sqrt{\frac{-2\ln S}{S}},\quad X_i = \mu + \sigma Z_i .$$

Доля принятых пар в теории $\pi/4 \approx 78.5\,\%$.""",
        "inverse": r"""
**Метод обратной функции.** Если $U \sim \mathcal{U}(0,1)$, то $F^{-1}(U)$ имеет функцию распределения $F$. Для логистического закона

$$F(x) = \frac{1}{1 + e^{-(x-\mu)/s}} \;\Rightarrow\; X = \mu + s\ln\frac{U}{1-U},\qquad s = \frac{\sigma\sqrt{3}}{\pi}.$$""",
        "quantile": r"""
**Эмпирическое квантильное преобразование.** Вместо формулы – сами данные: $x_{(1)} \le \dots \le x_{(n)}$ в точках $p_i = (i - \tfrac12)/n$,

$$X = \hat{F}_n^{-1}(U) \quad\text{(линейная интерполяция между соседними } x_{(i)}\text{)}.$$

Сохраняет асимметрию и хвосты данных, но не выходит за $[x_{(1)}, x_{(n)}]$.""",
    }[method]
    mo.md(_f + f"\n\nСейчас: $\\mu = {mu:.4g}$, $\\sigma = {sigma:.4g}$.")
    return


@app.cell(hide_code=True)
def _(acceptance, method, mo, np, real, stats, synth):
    ks = stats.ks_2samp(real, synth)
    _err_m = abs(synth.mean() - real.mean()) / abs(real.mean()) * 100
    _err_s = abs(synth.std(ddof=1) - real.std(ddof=1)) / real.std(ddof=1) * 100
    _verdict = "H₀ не отвергается: распределения неразличимы" if ks.pvalue > 0.05 else "H₀ отвергается: распределения различаются"
    mo.hstack([
        mo.stat(f"{ks.pvalue:.3f}", label="КС-тест, p", caption=_verdict, bordered=True),
        mo.stat(f"{_err_m:.2f} %", label="Ошибка x̄", caption="относительно x̄ данных", bordered=True),
        mo.stat(f"{_err_s:.2f} %", label="Ошибка s", caption="относительно s данных", bordered=True),
        mo.stat(f"{stats.skew(synth):+.2f}", label="γ₁", caption=f"у данных {stats.skew(real):+.2f}", bordered=True),
        mo.stat(f"{acceptance * 100:.1f} %" if method == "polar" else "100 %", label="Принято",
                caption="теория: π/4 = 78.5 %" if method == "polar" else "без отбраковки", bordered=True),
    ], widths=[1.6, 1, 1, 1, 1], gap=1)
    return (ks,)


@app.cell(hide_code=True)
def _(DATA, STYLE, bins_slider, method, mu, np, plt, real, sigma, stats, synth, var_select):
    _cfg = DATA[var_select.value]
    _c, _ls = _cfg["color"], STYLE["ls"][method]
    _name = {"polar": "полярный метод", "inverse": "обратная функция", "quantile": "квантильный метод"}[method]
    _lo, _hi = min(real.min(), synth.min()), max(real.max(), synth.max())
    _w = max(_cfg["step"], round((_hi - _lo) / bins_slider.value / _cfg["step"]) * _cfg["step"])
    _start = np.floor(_lo / _cfg["step"] + 1e-9) * _cfg["step"] - _cfg["step"] / 2   # границы между значениями сетки прибора
    _bins = np.arange(_start, _hi + _w, _w)

    fig, _ax = plt.subplots(1, 3, figsize=(13, 3.9), gridspec_kw={"width_ratios": [1.3, 1, 1]})
    _ax[0].hist(real, bins=_bins, density=True, color=_c, alpha=0.45, edgecolor=STYLE["surface"], linewidth=1)
    _ax[0].hist(synth, bins=_bins, density=True, histtype="step", color=STYLE["ink"], linestyle=_ls, linewidth=1.6)
    if method != "quantile":
        _g = np.linspace(_lo, _hi, 400)
        _pdf = stats.norm.pdf(_g, mu, sigma) if method == "polar" else stats.logistic.pdf(_g, mu, sigma * np.sqrt(3) / np.pi)
        _ax[0].plot(_g, _pdf, color=STYLE["ink2"], linewidth=1, alpha=0.8)
    _ax[0].set_title("Плотность"); _ax[0].set_xlabel(_cfg["axis"]); _ax[0].set_ylabel("Плотность вероятности")

    for _d, _col, _st in [(real, _c, "-"), (synth, STYLE["ink"], _ls)]:
        _s = np.sort(_d)
        _ax[1].step(_s, np.arange(1, _s.size + 1) / _s.size, where="post", color=_col, linestyle=_st, linewidth=1.8)
    _ax[1].set_title("Функции распределения (ECDF)")
    _ax[1].set_xlabel(_cfg["axis"]); _ax[1].set_ylabel("$\\hat{F}(x) = P(X \\leq x)$")

    _p = np.linspace(0.005, 0.995, 120)
    _qr, _qs = np.quantile(real, _p), np.quantile(synth, _p)
    _ax[2].scatter(_qr, _qs, s=14, color=_c, edgecolor=STYLE["surface"], linewidth=0.5)
    _ax[2].plot([_qr.min(), _qr.max()], [_qr.min(), _qr.max()], color=STYLE["ink2"], linewidth=1.2, linestyle="--")
    _ax[2].set_title("Q-Q: генератор против данных")
    _ax[2].set_xlabel("Квантили данных"); _ax[2].set_ylabel("Квантили генератора")

    # Одна общая легенда под графиками – не перекрывает данные ни на одной панели
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    _handles = [Patch(facecolor=_c, alpha=0.45, label="Данные (гистограмма)"),
                Line2D([], [], color=_c, lw=1.8, label="Данные (ECDF)"),
                Line2D([], [], color=STYLE["ink"], lw=1.6, ls=_ls, label=f"Генератор: {_name}")]
    if method != "quantile":
        _handles.append(Line2D([], [], color=STYLE["ink2"], lw=1, alpha=0.8, label="Теоретическая плотность"))
    _handles.append(Line2D([], [], color=STYLE["ink2"], lw=1.2, ls="--", label="Q-Q: полное совпадение y = x"))
    fig.legend(handles=_handles, loc="lower center", ncol=len(_handles), frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig
    return


@app.cell(hide_code=True)
def _(mo, np, real, stats, synth):
    def _m(a):
        return [a.size, a.mean(), np.median(a), a.std(ddof=1), np.quantile(a, 0.25), np.quantile(a, 0.75),
                a.min(), a.max(), stats.skew(a), stats.kurtosis(a)]

    _names = ["n", "Среднее x̄", "Медиана", "СКО s", "Q₁", "Q₃", "Минимум", "Максимум", "Асимметрия γ₁", "Эксцесс γ₂"]
    _r, _s = _m(real), _m(synth)
    _rows = ["| Метрика | Данные | Генератор | Разница |", "|:---|---:|---:|---:|"]
    for _i, (_nm, _a, _b) in enumerate(zip(_names, _r, _s)):
        _rows.append(f"| {_nm} | {_a:.4g} | {_b:.4g} | {'–' if _i == 0 else f'{_b - _a:+.3g}'} |")
    mo.md("### Сравнение метрик\n\n" + "\n".join(_rows))
    return


@app.cell(hide_code=True)
def _(mo, wine):
    _cols = {"pH": "pH", "Фикс. кислотность, г/дм³": "fixed acidity", "Лимонная кислота, г/дм³": "citric acid",
             "Летучая кислотность, г/дм³": "volatile acidity", "Плотность, г/см³": "density", "Алкоголь, % об.": "alcohol"}
    dep_x = mo.ui.dropdown(options=_cols, value="Фикс. кислотность, г/дм³", label="Ось X")
    dep_y = mo.ui.dropdown(options=_cols, value="pH", label="Ось Y")
    dep_log = mo.ui.switch(value=True, label="логарифмическая шкала X")
    mo.vstack([
        mo.md("---\n## Связь величин в датасете вина\n\nДве величины одной природы зависимы. "
              "Здесь можно посмотреть на любую пару показателей и сразу увидеть коэффициенты корреляции."),
        mo.callout(mo.hstack([dep_x, dep_y, dep_log], justify="start", gap=2, wrap=True), kind="neutral"),
    ])
    return dep_log, dep_x, dep_y


@app.cell(hide_code=True)
def _(STYLE, dep_log, dep_x, dep_y, mo, np, plt, stats, wine):
    _x, _y = wine[dep_x.value].to_numpy(float), wine[dep_y.value].to_numpy(float)
    _use_log = dep_log.value and (_x > 0).all()
    _xt = np.log(_x) if _use_log else _x
    _r = stats.pearsonr(_xt, _y); _rho = stats.spearmanr(_x, _y); _tau = stats.kendalltau(_x, _y)

    dep_fig, _ax = plt.subplots(figsize=(8, 4.2))
    _ax.scatter(_x, _y, s=12, color=STYLE["ink2"], alpha=0.35, edgecolor="none", label=f"вина (n = {_x.size})")
    _b, _a = np.polyfit(_xt, _y, 1)
    _g = np.linspace(_x.min(), _x.max(), 200)
    _ax.plot(_g, _a + _b * (np.log(_g) if _use_log else _g), color=STYLE["ink"], linewidth=2,
             label="МНК-прямая" + (" по ln x" if _use_log else ""))
    if _use_log:
        _ax.set_xscale("log")
        _nice = np.array([0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 30, 50, 100])
        _ticks = _nice[(_nice >= _x.min() * 0.95) & (_nice <= _x.max() * 1.05)]
        _ax.xaxis.set_major_locator(plt.FixedLocator(_ticks))
        _ax.xaxis.set_minor_locator(plt.NullLocator())
        _ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    _lab = {"pH": "pH", "fixed acidity": "Фикс. кислотность, г/дм³", "citric acid": "Лимонная кислота, г/дм³",
            "volatile acidity": "Летучая кислотность, г/дм³", "density": "Плотность, г/см³", "alcohol": "Алкоголь, % об."}
    _ax.set_xlabel(_lab[dep_x.value].replace("pH", "pH (безразмерная)") + (" (лог. шкала)" if _use_log else ""))
    _ax.set_ylabel(_lab[dep_y.value].replace("pH", "pH (безразмерная)"))
    _ax.set_title("Диаграмма рассеяния")
    _ax.legend(loc="best")
    dep_fig.tight_layout()
    mo.hstack([
        dep_fig,
        mo.vstack([
            mo.stat(f"{_r.statistic:+.3f}", label="Пирсон r" + (" (ln x)" if _use_log else ""), caption=f"p = {_r.pvalue:.1e}", bordered=True),
            mo.stat(f"{_rho.statistic:+.3f}", label="Спирмен ρₛ", caption=f"p = {_rho.pvalue:.1e}", bordered=True),
            mo.stat(f"{_tau.statistic:+.3f}", label="Кендалл τ", caption=f"p = {_tau.pvalue:.1e}", bordered=True),
        ], gap=1),
    ], widths=[3, 1], align="center")
    return


if __name__ == "__main__":
    app.run()
