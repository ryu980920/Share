#!/usr/bin/env python3
"""
figures_presentation.py — 발표용 그림 생성 (contour.py 와 별개)

★ 왜 별도 스크립트인가
  contour.py 는 파이프라인 점검용(자동 실행, 영어 라벨, 부호 그대로)이고,
  이 스크립트는 발표 슬라이드에 그대로 넣을 수 있는 그림을 만든다.
  contour.py 가 만든 그림을 발표에 쓰면 안 되는 이유 3가지를 여기서 해결한다:

  (1) 지표: contour.py 는 stress_GPa(정규화 안 된 절대 응력)를 그린다.
      이 프로젝트의 헤드라인은 STE(Stress Transfer Efficiency)다.
  (2) 부호: 압축응력이라 값이 전부 음수 → 컬러바에서 "어두운 쪽 = 더 음수 =
      응력이 강함"인데, 보는 사람은 보통 "밝은 쪽 = 큰 값"으로 읽어 정반대로
      이해한다. 여기서는 절대값 |σ| 로 그려 "클수록 강함"이 직관과 일치하게 한다.
  (3) 라벨: 영어 축 라벨 → 한국어.

  추가로 SSSat(정전제어 품질) 지도와 트레이드오프 오버레이를 만든다 —
  STE 지도만 보면 "FR 은 영향이 작다"로 읽히는데, 실제로는 FR 이 SS·누설을
  크게 악화시키므로 그 축을 같이 보여줘야 결론이 왜곡되지 않는다.

사용법
    python analysis/figures_presentation.py
출력
    analysis/figures/pres_STE_map.png          ← 발표 메인 그림
    analysis/figures/pres_stress_map.png       ← 절대 응력 (보조)
    analysis/figures/pres_SSSat_map.png        ← 정전제어 품질
    analysis/figures/pres_tradeoff_overlay.png ← STE + SSSat 겹쳐보기
"""

from pathlib import Path

import matplotlib
import matplotlib.patheffects
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
#  ⚠ STE 계산에 쓰는 가정 — 팀 확정 전 잠정값
#
#  STE = |실제 채널 응력| / |Ge% 로 정해지는 명목 응력|
#  명목 응력 = M × f(x),  f(x)=0.042·x (Vegard, params.yaml),  x=Ge 몰분율
#
#  M(이축 탄성계수)은 baseline/params.yaml 에 아직 확정값이 없어 Si 의
#  일반적인 근사값 180 GPa 를 썼다. M 은 STE 전체에 곱해지는 상수라
#  "지도의 모양·경향"은 M 값과 무관하고, "절대 %값"만 M 에 비례해 바뀐다.
#  → 발표에서 절대 %를 인용하려면 M 출처를 먼저 확정할 것.
# ----------------------------------------------------------------------
M_BIAXIAL_MPA = 180000.0
VEGARD_COEF = 0.042

ROOT = Path(__file__).resolve().parent.parent
GRID = ROOT / "analysis" / "grid.csv"
FIGDIR = ROOT / "analysis" / "figures"

for cand in ["Noto Sans CJK KR", "Noto Sans CJK JP", "NanumGothic", "Malgun Gothic", "AppleGothic"]:
    try:
        matplotlib.font_manager.findfont(cand, fallback_to_default=False)
        plt.rcParams["font.family"] = cand
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False


def load():
    df = pd.read_csv(GRID)
    df["x"] = df["Ge_percent"] / 100.0
    df["sigma_nom_MPa"] = M_BIAXIAL_MPA * VEGARD_COEF * df["x"]
    df["STE_vol"] = df["SlFin_MPa"].abs() / df["sigma_nom_MPa"]
    df["STE_pt"] = df["SlFin_pt_MPa"].abs() / df["sigma_nom_MPa"]
    df["stress_abs_GPa"] = df["SlFin_MPa"].abs() / 1000.0
    return df


def pivot(df, col):
    pv = df.pivot_table(index="FR_nm", columns="Ge_percent", values=col).sort_index()
    return pv.columns.values.astype(float), pv.index.values.astype(float), pv.values


# ----------------------------------------------------------------------
#  등고선 부드럽게 만들기 (표시용 보간)
#
#  ⚠ 왜 필요한가: 격자가 5×5 뿐이라 matplotlib 기본 등고선은 격자점 사이를
#     직선으로 잇는다. 그래서 실제로는 완만한 곡선일 경계가 화면에서는
#     각진 다각형(꺾인 선)처럼 보인다.
#  ⚠ 주의: 이건 **표시용 보간일 뿐 새 데이터가 아니다.** 격자점의 실제 값은
#     그림 위에 숫자로 그대로 찍어두었으니, 해석은 항상 그 숫자를 기준으로 할 것.
#     scipy 를 못 쓰는 환경이라 numpy 만으로 (1) 세밀격자 이중선형 보간
#     → (2) 약한 가우시안 평활 순서로 구현했다. 평활 강도는 약하게 잡아
#     극값 위치가 격자점에서 벗어나지 않는 수준으로 유지한다.
# ----------------------------------------------------------------------
def _bilinear_upsample(X, Y, Z, n=160):
    xi = np.linspace(X.min(), X.max(), n)
    yi = np.linspace(Y.min(), Y.max(), n)
    ix = np.clip(np.searchsorted(X, xi) - 1, 0, len(X) - 2)
    iy = np.clip(np.searchsorted(Y, yi) - 1, 0, len(Y) - 2)
    tx = ((xi - X[ix]) / (X[ix + 1] - X[ix]))[None, :]
    ty = ((yi - Y[iy]) / (Y[iy + 1] - Y[iy]))[:, None]
    z00 = Z[np.ix_(iy, ix)]
    z01 = Z[np.ix_(iy, ix + 1)]
    z10 = Z[np.ix_(iy + 1, ix)]
    z11 = Z[np.ix_(iy + 1, ix + 1)]
    Zi = (z00 * (1 - tx) * (1 - ty) + z01 * tx * (1 - ty)
          + z10 * (1 - tx) * ty + z11 * tx * ty)
    return xi, yi, Zi


def _gaussian_blur(Z, sigma_px=3.0):
    r = int(3 * sigma_px)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma_px) ** 2)
    k /= k.sum()
    out = np.pad(Z, ((0, 0), (r, r)), mode="edge")
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 1, out)
    out = np.pad(out, ((r, r), (0, 0)), mode="edge")
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"), 0, out)
    return out


def smooth_grid(X, Y, Z, sigma_px=3.0, n=160):
    xi, yi, Zi = _bilinear_upsample(X, Y, Z, n=n)
    return xi, yi, _gaussian_blur(Zi, sigma_px=sigma_px)


def draw_map(df, col, title, cbar_label, fname, cmap="YlGnBu",
             fmt="%.3f", note=None, annotate=True, best="max", smooth=True):
    X, Y, Z = pivot(df, col)
    # 색·등고선은 평활 격자로, 값 라벨·격자점은 원본으로 그린다
    Xp, Yp, Zp = smooth_grid(X, Y, Z) if smooth else (X, Y, Z)

    fig, ax = plt.subplots(figsize=(9.0, 6.4))

    cf = ax.contourf(Xp, Yp, Zp, levels=20, cmap=cmap)
    cs = ax.contour(Xp, Yp, Zp, levels=9, colors="white", linewidths=1.0, alpha=0.8)
    ax.clabel(cs, inline=True, fontsize=9, fmt=fmt)

    # 격자점 표시 + 값 라벨 (★ 항상 원본 값)
    for j, yy in enumerate(Y):
        for i, xx in enumerate(X):
            ax.plot(xx, yy, "o", ms=4.5, mfc="white", mec="black", mew=0.9, zorder=5)
            if annotate:
                ax.annotate(fmt % Z[j, i], (xx, yy), textcoords="offset points",
                            xytext=(0, 8), ha="center", fontsize=7.5, color="white",
                            zorder=6,
                            path_effects=[matplotlib.patheffects.withStroke(
                                linewidth=2, foreground="black")])

    # 최적점 표시
    idx = np.unravel_index(np.nanargmax(Z) if best == "max" else np.nanargmin(Z), Z.shape)
    ax.plot(X[idx[1]], Y[idx[0]], "*", ms=22, mfc="gold", mec="black", mew=1.2, zorder=7)

    ax.set_xlabel("Ge 조성 [%]", fontsize=12)
    ax.set_ylabel("FR — 리세스 깊이 [nm]", fontsize=12)
    ax.set_title(title, fontsize=14, pad=14)
    ax.set_xticks(X)
    ax.set_yticks(Y)
    # 모서리 격자점의 ★/값 라벨이 잘리지 않도록 여백을 준다
    ax.set_xlim(X.min() - 1.6, X.max() + 1.6)
    ax.set_ylim(Y.min() - 1.6, Y.max() + 2.4)
    cb = fig.colorbar(cf, ax=ax)
    cb.set_label(cbar_label, fontsize=11)

    if note:
        fig.text(0.01, 0.015, note, fontsize=8.5, color="#444")
        fig.subplots_adjust(bottom=0.17)

    fig.tight_layout(rect=(0, 0.06 if note else 0, 1, 1))
    out = FIGDIR / fname
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"저장: {out.relative_to(ROOT)}")


def draw_overlay(df):
    X, Y, Z_ste = pivot(df, "STE_vol")
    _, _, Z_ss = pivot(df, "SSlin")
    Xp, Yp, Zp_ste = smooth_grid(X, Y, Z_ste)
    _, _, Zp_ss = smooth_grid(X, Y, Z_ss)

    fig, ax = plt.subplots(figsize=(9.4, 6.6))
    cf = ax.contourf(Xp, Yp, Zp_ste, levels=20, cmap="YlGnBu")
    cb = fig.colorbar(cf, ax=ax)
    cb.set_label("STE — 응력 전달 효율 [-]  (색이 진할수록 높음 = 좋음)", fontsize=10.5)

    cs = ax.contour(Xp, Yp, Zp_ss, levels=[80, 85, 90, 100, 110, 120],
                    colors="crimson", linewidths=1.8, linestyles="--")
    ax.clabel(cs, inline=True, fontsize=9.5, fmt="SS %.0f")

    for j, yy in enumerate(Y):
        for i, xx in enumerate(X):
            ax.plot(xx, yy, "o", ms=4.5, mfc="white", mec="black", mew=0.9, zorder=5)

    # 실용 최적 띠 — STE 는 이미 포화(≈0.667)했는데 SS 는 아직 최저 구간
    # ★ 2026-08-23: FR=15/22nm 실측 추가 후 상한을 22 → 20nm 로 정정.
    #   근거: nm당 STE 이득 ÷ nm당 SSlin 손실 비율이 FR15→20 구간 2.91 에서
    #   FR20→22 구간 0.38 로 7.6배 급락(= 이득/대가 역전). gmSat 도 FR=20 에서
    #   최댓값(1.149e-4) 후 22nm 에서 감소. Ioff 도 22nm 에서 1e-9 를 넘어선다.
    ax.axhline(15, color="white", lw=2.2, ls="-", alpha=0.85, zorder=4)
    ax.axhline(20, color="white", lw=2.2, ls="-", alpha=0.85, zorder=4)
    ax.axhspan(15, 20, color="white", alpha=0.22, zorder=1)
    ax.annotate("실용 최적 구간  FR ≈ 15~20nm\nSTE 거의 최대 + SS 아직 최저",
                xy=(50, 17.5), fontsize=11, ha="center", va="center",
                color="white", weight="bold", zorder=8,
                path_effects=[matplotlib.patheffects.withStroke(
                    linewidth=3.2, foreground="black")])

    ax.set_xlabel("Ge 조성 [%]", fontsize=12)
    ax.set_ylabel("FR — 리세스 깊이 [nm]", fontsize=12)
    ax.set_title("STE(색) vs 게이트 제어 열화 SSlin(붉은 점선) — 트레이드오프",
                 fontsize=14, pad=14)
    ax.set_xticks(X)
    ax.set_yticks(Y)
    ax.set_xlim(X.min() - 1.6, X.max() + 1.6)
    ax.set_ylim(Y.min() - 1.0, Y.max() + 1.0)

    fig.text(0.01, 0.030,
             "붉은 점선(SSlin, mV/dec)은 낮을수록 좋다. FR 20nm 까지는 77~87 로 완만하지만 그 위로 100~124 까지 급격히 나빠진다 "
             "— STE 이득은 이미 포화했는데 게이트 제어만 잃는 구간.",
             fontsize=8.5, color="#444")
    fig.text(0.01, 0.008,
             "상한 20nm 근거: nm당 STE 이득 ÷ nm당 SSlin 손실 비율이 FR 15→20 구간 2.91 에서 FR 20→22 구간 0.38 로 역전 (FR=15/22nm 실측 확인).",
             fontsize=8.5, color="#444")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    out = FIGDIR / "pres_tradeoff_overlay.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"저장: {out.relative_to(ROOT)}")


def main():
    FIGDIR.mkdir(parents=True, exist_ok=True)
    df = load()

    SMOOTH_NOTE = "  색·등고선은 표시용 평활 보간, 숫자는 실제 격자점 값."

    note_ste = (f"STE = |채널 응력| / (M×0.042×x),  M={M_BIAXIAL_MPA/1000:.0f} GPa 가정(팀 확정 전 잠정) · "
                "응력은 ChFin 체적평균(SlFin) 기준 · ★ = 최댓값 지점" + SMOOTH_NOTE)
    draw_map(df, "STE_vol",
             "Stress Transfer Efficiency (STE) — Ge% × FR",
             "STE [-]  (색이 진할수록 높음 = 효율적으로 전달됨)",
             "pres_STE_map.png", cmap="YlGnBu", fmt="%.3f",
             note=note_ste, best="max")

    draw_map(df, "stress_abs_GPa",
             "채널 압축응력 크기 |σ| — Ge% × FR",
             "|압축응력| [GPa]  (색이 진할수록 강함)",
             "pres_stress_map.png", cmap="YlOrBr", fmt="%.2f",
             note="압축응력이라 원본 값은 음수 — 여기서는 절대값으로 그려 '진할수록 강함'이 되게 했다. "
                  "★ = 응력이 가장 강한 지점(G70_F30)." + SMOOTH_NOTE,
             best="max")

    # ★ 게이트 제어 품질의 지표는 SSlin — 이상적 60mV/dec 한계와 비교 가능한 쪽
    draw_map(df, "SSlin",
             "Subthreshold Swing SSlin (저 Vd) — Ge% × FR",
             "SSlin [mV/dec]  (색이 진할수록 높음 = 게이트 제어 나쁨)",
             "pres_SSlin_map.png", cmap="Reds", fmt="%.0f",
             note="게이트 제어 품질의 지표. 이상적 하한 60 mV/dec 와 비교 가능한 건 이 값이다"
                  "(SS 이상식은 드레인이 장벽에 영향을 안 준다는 가정에서 유도되므로). "
                  "★ = 가장 좋은 지점." + SMOOTH_NOTE,
             best="min")

    # 누설은 SS 에 섞지 말고 따로 — 고 Ge% 에서 SiGe 밴드갭 축소로 접합 누설이 커진다
    df = df.copy()
    df["log10_Ioff"] = np.log10(df["Ioff_norm"].astype(float))
    draw_map(df, "log10_Ioff",
             "누설전류 Ioff (log10) — Ge% × FR",
             "log10(Ioff_norm)  (색이 진할수록 누설 큼)",
             "pres_Ioff_map.png", cmap="Purples", fmt="%.1f",
             note="SSSat 대신 누설을 따로 본 지도. 고 Ge% 에서 SiGe 밴드갭 축소로 드레인 접합 누설이 커지고, "
                  "FR 30nm 이상에서는 채널 스토퍼(SiStop) 제거로 관통 누설이 더해져 자릿수 단위로 뛴다. "
                  "★ = 누설이 가장 적은 지점." + SMOOTH_NOTE,
             best="min")

    # 숏채널 효과는 SSSat 이 아니라 DIBL 로 정량화한다
    draw_map(df, "DIBL_mV_V",
             "DIBL (드레인 유도 장벽 저하) — Ge% × FR",
             "DIBL [mV/V]  (색이 진할수록 숏채널 효과 심함)",
             "pres_DIBL_map.png", cmap="Oranges", fmt="%.0f",
             note="DIBL = (|VtiLin|-|VtiSat|)/ΔVd, ΔVd=0.75V 가정. FR 이 깊어질수록 5개 Ge% 전부에서 "
                  "단조 증가 — 리세스가 채널 스토퍼를 제거해 숏채널 효과가 커진다는 직접 증거. "
                  "★ = 가장 좋은 지점." + SMOOTH_NOTE,
             best="min")

    # --- STE 정규화 방법 비교: 체적평균 vs 계면 단일점 -------------------
    #  두 방식이 결론까지 뒤집는다는 걸 그림으로 보이는 짝 그림.
    #  "정규화 방법을 어떻게 정했나"에 대한 답이 이 두 장이다.
    draw_map(df, "STE_pt",
             "[대조군] 계면 단일점 기준 STE — Ge% × FR",
             "STE_pt [-]  (색이 진할수록 높음)",
             "pres_STE_pt_map.png", cmap="YlGnBu", fmt="%.3f",
             note="분자를 SlFin_pt(게이트 상단 계면 2nm×2nm×1nm 슬래브)로 바꾼 것. 채택본(체적평균)과 비교하면 "
                  "FR 축 거동이 정반대 — 여기서는 FR 이 커질수록 STE 가 오히려 낮아진다." + SMOOTH_NOTE,
             best="max")
    draw_norm_maps_shared(df)
    draw_norm_compare(df)

    draw_overlay(df)


def draw_norm_maps_shared(df):
    """
    체적평균 vs 계면점 STE 를 **같은 색 스케일**로 나란히 그린다.

    ⚠ 왜 필요한가: 두 방식은 절대값 범위가 달라서(체적평균 0.59~0.68,
      계면점 0.89~0.94) 각자 자기 범위로 색을 칠하면 두 그림의 색을 직접
      비교할 수 없다. 여기서는 **각 방식의 최댓값 대비 %** 로 환산한 뒤
      하나의 컬러바를 공유해, 색 비교와 방향 비교를 동시에 가능하게 한다.
      부수적으로 "체적평균이 계면점보다 격자 안에서 더 크게 변한다"
      (동적 범위 12.4%p vs 5.6%p)는 것도 색의 폭으로 드러난다.
    """
    specs = [("STE_vol", "채택: 체적평균 SlFin 기준"),
             ("STE_pt", "대조: 계면 단일점 SlFin_pt 기준")]
    grids = []
    for col, ttl in specs:
        X, Y, Z = pivot(df, col)
        grids.append((X, Y, Z / np.nanmax(Z) * 100.0, ttl))

    vmin = min(np.nanmin(g[2]) for g in grids) - 0.5
    levels = np.linspace(vmin, 100.0, 22)

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 5.9), sharey=True)
    for ax, (X, Y, Z, ttl) in zip(axes, grids):
        Xp, Yp, Zp = smooth_grid(X, Y, Z)
        cf = ax.contourf(Xp, Yp, Zp, levels=levels, cmap="YlGnBu", extend="min")
        cs = ax.contour(Xp, Yp, Zp, levels=levels[::3], colors="white",
                        linewidths=0.9, alpha=0.8)
        ax.clabel(cs, inline=True, fontsize=8.5, fmt="%.0f%%")
        for j, yy in enumerate(Y):
            for i, xx in enumerate(X):
                ax.plot(xx, yy, "o", ms=4, mfc="white", mec="black", mew=0.9, zorder=5)
                ax.annotate(f"{Z[j, i]:.1f}", (xx, yy), textcoords="offset points",
                            xytext=(0, 7), ha="center", fontsize=7, color="white", zorder=6,
                            path_effects=[matplotlib.patheffects.withStroke(
                                linewidth=2, foreground="black")])
        # 각 방식의 피크가 있는 FR 행을 표시
        peak_fr = Y[np.unravel_index(np.nanargmax(Z), Z.shape)[0]]
        ax.axhline(peak_fr, color="crimson", lw=2.0, ls="--", zorder=7)
        ax.annotate(f"← 최댓값 행  FR={peak_fr:.0f}nm", xy=(X.max(), peak_fr),
                    xytext=(-6, 7), textcoords="offset points", ha="right",
                    fontsize=10, color="crimson", weight="bold", zorder=8,
                    path_effects=[matplotlib.patheffects.withStroke(
                        linewidth=2.5, foreground="white")])
        ax.set_xlabel("Ge 조성 [%]", fontsize=11.5)
        ax.set_title(ttl, fontsize=12.5)
        ax.set_xticks(X); ax.set_yticks(Y)
        ax.set_xlim(X.min() - 1.6, X.max() + 1.6)
        ax.set_ylim(Y.min() - 1.2, Y.max() + 1.2)
    axes[0].set_ylabel("FR — 리세스 깊이 [nm]", fontsize=11.5)

    fig.subplots_adjust(left=0.065, right=0.875, top=0.885, bottom=0.235, wspace=0.10)
    cax = fig.add_axes([0.895, 0.235, 0.018, 0.65])
    cb = fig.colorbar(cf, cax=cax)
    cb.set_label("각 방식의 최댓값 대비 [%]  (색이 진할수록 높음)", fontsize=10)

    fig.suptitle("STE 정규화 방법 — 같은 색 스케일로 직접 비교", fontsize=14.5, y=0.965)
    fig.text(0.012, 0.085,
             "두 방식은 절대값 범위가 달라(체적평균 0.59~0.68 / 계면점 0.89~0.94) 각자 스케일로 그리면 색 비교가 불가능하다. "
             "여기서는 각 방식의 최댓값 대비 %로 환산해 컬러바를 공유했다.",
             fontsize=9, color="#444")
    fig.text(0.012, 0.048,
             "왼쪽은 위로 갈수록 계속 진해지고(최댓값 행 FR=30nm), 오른쪽은 FR=10nm 에서 가장 진했다가 위로 갈수록 옅어진다 — FR 축 거동이 정반대.",
             fontsize=9, color="#444")
    fig.text(0.012, 0.013,
             "색이 변하는 폭도 체적평균 쪽이 더 넓다(격자 안 동적 범위 12.4%p vs 5.6%p) — 계면점 지도가 전반적으로 고르게 진해 보이는 이유다.",
             fontsize=9, color="#444")
    out = FIGDIR / "pres_STE_norm_maps_shared.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"저장: {out.relative_to(ROOT)}")


def draw_norm_compare(df):
    """체적평균 vs 계면점 — FR 축 거동과 이동도 예측력을 한 장에 비교."""
    ge_list = sorted(df["Ge_percent"].unique())
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.9))

    # (1) FR 축 거동 — 두 방식이 반대로 움직인다
    for ax, col, ttl in ((axes[0], "STE_vol", "채택: 체적평균 SlFin 기준"),
                         (axes[1], "STE_pt", "대조: 계면 단일점 SlFin_pt 기준")):
        for ge in ge_list:
            s = df[df.Ge_percent == ge].sort_values("FR_nm")
            ax.plot(s["FR_nm"], s[col], "o-", lw=1.8, ms=6, label=f"Ge {ge:.0f}%")
        ax.set_xlabel("FR — 리세스 깊이 [nm]", fontsize=11)
        ax.set_ylabel("STE [-]", fontsize=11)
        ax.set_title(ttl, fontsize=12)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8.5)
        # 피크 위치 표시
        for ge in ge_list:
            s = df[df.Ge_percent == ge].sort_values("FR_nm")
            i = s[col].values.argmax()
            ax.axvline(s["FR_nm"].values[i], color="gray", ls=":", lw=0.8, alpha=0.5)

    # (2) 이동도(gmSat) 예측력 — 판정 근거
    r_vol, r_pt = [], []
    for ge in ge_list:
        s = df[df.Ge_percent == ge]
        r_vol.append(np.corrcoef(s["SlFin_MPa"].abs(), s["gmSat"])[0, 1])
        r_pt.append(np.corrcoef(s["SlFin_pt_MPa"].abs(), s["gmSat"])[0, 1])
    ax = axes[2]
    x = np.arange(len(ge_list))
    ax.bar(x - 0.19, r_vol, 0.38, label="체적평균 SlFin", color="#2c7fb8")
    ax.bar(x + 0.19, r_pt, 0.38, label="계면점 SlFin_pt", color="#d95f0e")
    ax.axhline(0, color="black", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Ge {g:.0f}%" for g in ge_list], fontsize=9)
    ax.set_ylabel("응력 vs gmSat 상관계수  (FR 축 내)", fontsize=10.5)
    ax.set_title("판정 근거 — 이동도를 잘 예측하는 쪽", fontsize=12)
    ax.set_ylim(-0.6, 1.15)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=9, loc="lower right")
    for xi, v in zip(x - 0.19, r_vol):
        ax.annotate(f"{v:+.2f}", (xi, v), ha="center", va="bottom", fontsize=8.5)
    for xi, v in zip(x + 0.19, r_pt):
        ax.annotate(f"{v:+.2f}", (xi, v), ha="center", va="top", fontsize=8.5)

    fig.suptitle("STE 정규화 방법 비교 — 왜 체적평균을 채택했는가", fontsize=14)
    fig.text(0.012, 0.055,
             "왼쪽/가운데: 같은 데이터인데 FR 축 거동이 정반대다 — 체적평균은 FR=30nm 에서 피크, 계면점은 FR=10nm 에서 피크 후 계속 하락(점선 = 피크 위치).",
             fontsize=9, color="#444")
    fig.text(0.012, 0.028,
             "오른쪽: 이동도(gmSat)와의 상관 — 계면점은 5개 Ge% 전부에서 음의 상관이라, '응력이 세지는데 이동도는 약해진다'는 물리적으로 성립하지 않는 결과가 된다.",
             fontsize=9, color="#444")
    fig.text(0.012, 0.001,
             "단, 계면점 방식이 개념적으로 틀린 건 아니다 — 현재 창이 tri-gate 의 상단 계면만 잡고 있어 전류가 흐르는 측벽을 놓친 게 원인일 수 있다(측벽 포함 재추출은 향후과제).",
             fontsize=9, color="#444")
    fig.tight_layout(rect=(0, 0.10, 1, 0.95))
    out = FIGDIR / "pres_STE_normalization_compare.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    print(f"저장: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    import matplotlib.patheffects  # noqa: F401  (draw_map 에서 사용)
    main()
