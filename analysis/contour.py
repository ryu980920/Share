#!/usr/bin/env python3
"""
contour.py — grid.csv 로부터 2차원 등고선을 그리고 상호작용 + 임계두께 경계선을 판정한다.

이 프로젝트의 결론이 나오는 스크립트다.
  (1) 응력/이동도 등고선          ← 발표의 하이라이트 그림
  (2) People-Bean / Luryi-Suhir 경계선 오버레이 ← "어디부터 결함으로 무효화되는가"
  (3) 교호작용 회귀 → 등고선이 "직선/평행"인지 "휘었는지"를 눈이 아니라 숫자로 판정
  (4) 시너지 정량화 → 개별 최적화 대비 결합 최적화의 추가 개선분

★ 등고선(색 채워진 면) 자체는 Sentaurus 의 완전정합(pseudomorphic) 가정 결과라
  결함을 반영하지 않는다. 경계선 안쪽에서 최댓값을 찾는 것이지 등고선 전체
  최댓값이 우리 결론이 아니다 (docs/technical-notes.md 2-2절).

사용법
    python analysis/contour.py
    python analysis/contour.py --metric mobility_gain_pct
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
GRID = ROOT / "analysis" / "grid.csv"
PARAMS = ROOT / "baseline" / "params.yaml"
FIGDIR = ROOT / "analysis" / "figures"

try:
    from scipy import stats as _st
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


# ======================================================================
#  임계두께 경계선 (docs/technical-notes.md 3절, baseline/params.yaml#critical_thickness)
# ======================================================================
def people_bean_tc_nm(ge_percent):
    """Tc(nm) = 1.23 * x^-3.08,  x = Ge 몰분율(0~1). 근사식 — 원 논문과 대조 권장."""
    x = np.asarray(ge_percent, dtype=float) / 100.0
    with np.errstate(divide="ignore", invalid="ignore"):
        return 1.23 * np.power(x, -3.08)


def luryi_suhir_safe_ge_threshold(fin_width_nm, x_grid_percent):
    """
    fin 폭 W < 15*Tc(x) 이면 리세스 깊이와 무관하게(탄성 완화만으로) 안전.
    이 조건이 성립하는 가장 높은 Ge% 를 반환한다 (그 왼쪽은 전부 안전).

    ★ 주의: 이건 tech note 에 적힌 W<15*Tc 조건을 그대로 문턱값으로 옮긴 것이지,
      Luryi-Suhir(1986) 원 논문에서 2차원(두께 방향까지) 보정 곡선을 직접
      유도한 게 아니다. 팀이 원 논문을 직접 대조해 이 해석이 맞는지 확인할 것
      (docs/technical-notes.md 4절 항목 4). fin_width_nm 이 아직 미확정
      (baseline/params.yaml PLACEHOLDER)이면 None 을 반환한다.
    """
    if fin_width_nm is None or not np.isfinite(fin_width_nm):
        return None
    tc = people_bean_tc_nm(x_grid_percent)
    safe = fin_width_nm < 15 * tc
    if not np.any(safe):
        return None
    # 안전한 구간 중 가장 높은 Ge%
    return float(np.max(np.asarray(x_grid_percent)[safe]))


# ======================================================================
#  교호작용 회귀
# ======================================================================
def interaction_regression(x, y, z):
    """
    z = b0 + b1*xc + b2*yc + b12*xc*yc  (xc, yc 는 [-1,+1] 로 코딩)

    b12 가 통계적으로 0과 다르면 → 두 변수가 상호작용한다.
    """
    xc = 2 * (x - x.min()) / (x.max() - x.min()) - 1
    yc = 2 * (y - y.min()) / (y.max() - y.min()) - 1
    X = np.column_stack([np.ones_like(xc), xc, yc, xc * yc])

    beta, *_ = np.linalg.lstsq(X, z, rcond=None)
    resid = z - X @ beta
    n, p = X.shape
    dof = n - p
    if dof <= 0:
        return beta, None, None, None, np.nan

    mse = float(resid @ resid) / dof
    cov = mse * np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    tvals = beta / se

    if HAVE_SCIPY:
        pvals = 2 * (1 - _st.t.cdf(np.abs(tvals), dof))
    else:
        pvals = None

    ss_tot = float(((z - z.mean()) ** 2).sum())
    r2 = 1 - float((resid ** 2).sum()) / ss_tot if ss_tot > 0 else np.nan
    return beta, se, tvals, pvals, r2


def verdict(beta, tvals, pvals):
    """상호작용 유무 판정 → (a)/(b)/(c) 패턴. 응력/이동도는 '높을수록 좋음' 기준."""
    b1, b2, b12 = beta[1], beta[2], beta[3]
    t12 = tvals[3] if tvals is not None else np.nan

    if pvals is not None:
        signif = pvals[3] < 0.05
        crit = f"p = {pvals[3]:.4f} (< 0.05 이면 유의)"
    else:
        signif = abs(t12) > 2.0
        crit = f"|t| = {abs(t12):.2f} (> 2 이면 유의)  ※scipy 없어 근사 기준 사용"

    main_scale = max(abs(b1), abs(b2))
    rel = abs(b12) / main_scale if main_scale > 0 else np.nan

    if not signif:
        pat = "(a) 상호작용 없음 — 독립"
        note = ("등고선이 직선·평행. Ge%·리세스 깊이를 따로 최적화해도 결과가 같다.\n"
                "  → '설계 자유도 확보'가 결론이 된다. 단, 결함 경계선(People-Bean/\n"
                "    Luryi-Suhir)은 Sentaurus 결과와 무관하게 여전히 별도로 적용된다.")
    elif b12 * np.sign(b1) * np.sign(b2) > 0:
        pat = "(b) 시너지"
        note = ("두 변수를 함께 늘릴 때의 개선이 각각의 개선을 더한 것보다 크다.\n"
                "  → 가장 강한 결론. 단, 경계선 밖(결함 예상 영역)에서의 시너지는\n"
                "    무의미하니 반드시 경계선 안쪽 값으로만 판단할 것.")
    else:
        pat = "(c) 트레이드오프 — 최적점 이동"
        note = ("Ge% 를 바꾸면 최적 리세스 깊이도 함께 이동한다.\n"
                "  → 한 변수만 최적화하면 다른 변수의 최적점을 놓친다.\n"
                "    '2차원 설계 맵'의 필요성을 직접 증명하는 결과.")

    return pat, note, crit, rel


# ======================================================================
#  시너지 정량화 (응력/이동도는 높을수록 좋음 — lower_is_better=False)
# ======================================================================
def synergy(df, x_nom, y_nom, metric, lower_is_better=False):
    def val(sub):
        v = sub[metric].to_numpy(dtype=float)
        return v[np.isfinite(v)]

    base_row = df[(np.isclose(df.Ge_percent, x_nom)) &
                  (np.isclose(df.Recess_nm, y_nom))]
    if base_row.empty:
        return None
    z_base = float(base_row[metric].iloc[0])

    row_x = df[np.isclose(df.Recess_nm, y_nom)]
    row_y = df[np.isclose(df.Ge_percent, x_nom)]
    f = np.min if lower_is_better else np.max

    vx, vy, vj = val(row_x), val(row_y), val(df)
    if len(vx) == 0 or len(vy) == 0 or len(vj) == 0:
        return None

    dX = f(vx) - z_base
    dY = f(vy) - z_base
    dJ = f(vj) - z_base

    best = df.loc[df[metric].idxmin() if lower_is_better else df[metric].idxmax()]
    return dict(z_base=z_base, dX=dX, dY=dY, dJ=dJ, syn=dJ - (dX + dY), best=best)


# ======================================================================
#  그림
# ======================================================================
def draw(df, metric, label, fname, cmap="viridis", crit_params=None):
    piv = df.pivot_table(index="Recess_nm", columns="Ge_percent", values=metric)
    if piv.isna().all().all():
        return None
    X, Y = np.meshgrid(piv.columns.to_numpy(float), piv.index.to_numpy(float))
    Z = piv.to_numpy(float)

    fig, ax = plt.subplots(figsize=(7.4, 5.8))
    cf = ax.contourf(X, Y, Z, levels=18, cmap=cmap)
    cs = ax.contour(X, Y, Z, levels=9, colors="white", linewidths=0.8, alpha=0.75)
    ax.clabel(cs, inline=True, fontsize=7, fmt="%.2f")
    ax.scatter(X, Y, s=14, c="white", edgecolors="k", linewidths=0.5, zorder=3)

    # --- 임계두께 경계선 오버레이 ---
    if crit_params is not None:
        xg = np.linspace(max(1, X.min()), X.max(), 200)
        tc = people_bean_tc_nm(xg)
        m = tc <= Y.max() * 1.3
        if np.any(m):
            ax.plot(xg[m], tc[m], "r--", lw=1.8,
                    label="People-Bean (1985) critical thickness (blanket)")

        fw = crit_params.get("fin_width_nm")
        ge_thr = luryi_suhir_safe_ge_threshold(fw, xg)
        if ge_thr is not None:
            ax.axvline(ge_thr, color="orange", ls=":", lw=1.8,
                       label=f"Luryi-Suhir safe boundary (Ge%<{ge_thr:.0f}, depth-independent)")
        ax.legend(loc="upper right", fontsize=8, framealpha=0.85)

    cb = fig.colorbar(cf, ax=ax)
    cb.set_label(label)
    ax.set_xlabel("Ge composition [%]")
    ax.set_ylabel("Recess depth [nm]")
    ax.set_title(f"{label}  vs  (Ge%, recess depth)")
    fig.tight_layout()
    FIGDIR.mkdir(exist_ok=True)
    out = FIGDIR / fname
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


# ======================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="stress_GPa")
    ap.add_argument("--all-figures", action="store_true",
                    help="응력 외 이동도/Vth/Ion 등고선도 함께 생성")
    args = ap.parse_args()

    if not GRID.exists():
        print("grid.csv 없음. 먼저 build.py 를 돌릴 것.", file=sys.stderr)
        return 1
    df = pd.read_csv(GRID)
    with open(PARAMS, encoding="utf-8") as f:
        params = yaml.safe_load(f)

    doe = params["doe"]
    if not doe.get("values_confirmed", False):
        print("=" * 70)
        print(" ⚠ baseline/params.yaml 의 doe.values_confirmed 가 false 다.")
        print("   아래 결과는 참고용이다 — Ge%/리세스 깊이 스윕 값이 확정되면 다시 돌릴 것.")
        print("=" * 70)
        print()

    x_nom = float(doe.get("x_levels", [np.nan])[len(doe.get("x_levels", [])) // 2])
    y_nom = float(doe.get("y_levels", [np.nan])[len(doe.get("y_levels", [])) // 2])
    metric = args.metric

    sub = df[np.isfinite(df[metric])] if metric in df.columns else df.iloc[0:0]
    if len(sub) < 4:
        print(f"유효 데이터 {len(sub)}개 ({metric}). 회귀에는 최소 4개 필요.", file=sys.stderr)
        return 1

    x = sub["Ge_percent"].to_numpy(float)
    y = sub["Recess_nm"].to_numpy(float)
    z = sub[metric].to_numpy(float)

    beta, se, tvals, pvals, r2 = interaction_regression(x, y, z)

    print("=" * 70)
    print(f" 교호작용 회귀 — {metric}")
    print(f" 데이터 {len(sub)}점 / 격자 {len(df)}점")
    print("=" * 70)
    names = ["절편", "Ge% (주효과)", "리세스 깊이 (주효과)", "Ge% x 리세스 깊이 (교호작용)"]
    print(f"  {'항':30s}{'계수':>12s}{'표준오차':>12s}{'t':>9s}{'p':>10s}")
    for i, nm in enumerate(names):
        p = f"{pvals[i]:.4f}" if pvals is not None else "   -  "
        print(f"  {nm:30s}{beta[i]:12.4f}{se[i]:12.4f}{tvals[i]:9.2f}{p:>10s}")
    print(f"\n  R^2 = {r2:.4f}")

    pat, note, crit, rel = verdict(beta, tvals, pvals)
    print()
    print("-" * 70)
    print(f"  판정: {pat}")
    print(f"  근거: {crit}")
    if np.isfinite(rel):
        print(f"  교호작용/주효과 비 = {rel:.2f}")
    print(f"\n  {note}")
    print("-" * 70)

    # --- 임계두께 경계선 요약 ---
    ct = params.get("critical_thickness", {})
    fin_w = params.get("geometry", {}).get("fin_width_nm")
    print()
    print("=" * 70)
    print(" 임계두께 경계선 (docs/technical-notes.md 3절)")
    print("=" * 70)
    tc_at_nom = people_bean_tc_nm(x_nom) if np.isfinite(x_nom) else np.nan
    if np.isfinite(tc_at_nom):
        print(f"  People-Bean: Ge {x_nom:.0f}% 에서 임계두께 Tc ≈ {tc_at_nom:.1f} nm")
        if np.isfinite(y_nom):
            state = "임계두께 초과 — 결함 예상" if y_nom > tc_at_nom else "임계두께 이내 — 안전 예상"
            print(f"    공칭 리세스 깊이 {y_nom:.0f} nm → {state}")
    if fin_w is None:
        print("  Luryi-Suhir: fin_width_nm 이 아직 PLACEHOLDER — 보정 경계 계산 불가.")
        print("    baseline/params.yaml 확정 후(docs/ROLES.md #4 과제) 다시 돌릴 것.")
    else:
        thr = luryi_suhir_safe_ge_threshold(fin_w, np.linspace(1, max(x, default=50).max() if len(x) else 50, 400))
        if thr is not None:
            print(f"  Luryi-Suhir: Ge% < {thr:.0f} 이면 리세스 깊이와 무관하게 안전 (fin 폭 {fin_w}nm 기준)")
        else:
            print("  Luryi-Suhir: 스윕 범위 내에서 안전 조건을 만족하는 Ge% 가 없다.")

    s = synergy(df, x_nom, y_nom, metric, lower_is_better=False)
    if s:
        print()
        print("=" * 70)
        print(f" 시너지 정량화 (기준점 G{x_nom:.0f}_R{y_nom:.0f})")
        print("=" * 70)
        print(f"  Ge% 만 최적화          : {s['dX']:+.3f}")
        print(f"  리세스 깊이만 최적화   : {s['dY']:+.3f}")
        print(f"  개별 최적화의 단순 합  : {s['dX']+s['dY']:+.3f}")
        print(f"  결합 최적화 (실제)     : {s['dJ']:+.3f}")
        print(f"  ---------------------------------------------")
        print(f"  ★ 시너지 (추가 개선분) : {s['syn']:+.3f}")
        print(f"\n  최댓값 지점: {s['best']['run_id']}  "
              f"(Ge%={s['best']['Ge_percent']:.0f}, 리세스={s['best']['Recess_nm']:.0f}nm)")
        print("  ⚠ 이 최댓값이 임계두께 경계선 안쪽인지 반드시 위 표와 대조할 것 —")
        print("    경계선 밖이면 '최댓값'이 아니라 '결함으로 무효한 값'이다.")
        print("\n  ※ 이 표의 숫자가 발표 결론 문장에 그대로 들어간다.")

    crit_params = {"fin_width_nm": fin_w}
    out = draw(df, metric, metric, f"contour_{metric}.png", crit_params=crit_params)
    if out:
        print(f"\n그림 저장: {out.relative_to(ROOT)}")

    if args.all_figures:
        for m, cm in [("mobility_gain_pct", "plasma"),
                      ("Vth_V", "coolwarm"),
                      ("Ion_A_um", "magma")]:
            if m in df.columns:
                o = draw(df, m, m, f"contour_{m}.png", cm, crit_params=crit_params)
                if o:
                    print(f"그림 저장: {o.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
