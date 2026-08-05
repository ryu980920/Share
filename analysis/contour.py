#!/usr/bin/env python3
"""
contour.py — grid.csv 로부터 2차원 지도를 그리고 상호작용을 판정한다.

이 프로젝트의 결론이 나오는 스크립트다.
  (1) Stress Transfer Efficiency(STE) 2차원 지도    ← 발표의 하이라이트 그림
  (2) 교호작용 회귀 → 지도가 "직선/평행"인지 "휘었는지"를 눈이 아니라 숫자로 판정
  (3) 시너지 정량화 → 개별 최적화 대비 결합 최적화의 추가 개선분

★ 2026-08-05: 결함 경계(People-Bean/Luryi-Suhir) 프레이밍을 폐기하고
  Stress Transfer Efficiency(STE) 프레이밍으로 전환하며, 이 스크립트의
  people_bean_tc_nm()/luryi_suhir_safe_ge_threshold() 및 경계선 오버레이
  로직을 전부 제거했다 — README.md 참고. Y축 변수명도 리세스 깊이
  (Recess_nm) → FR(FR_nm)로 바뀌었다.

★ ste 지표는 정규화 방법(baseline/params.yaml#stress_transfer_efficiency.
  normalization)이 아직 팀 확정 전이라 build.py 가 계산해 넣지 않는다.
  grid.csv 에 ste 컬럼이 없으면 이 스크립트는 stress_GPa 로만 지도를 그린다.

사용법
    python analysis/contour.py
    python analysis/contour.py --metric ste
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
    """상호작용 유무 판정 → (a)/(b)/(c) 패턴. STE/응력은 '높을수록 좋음' 기준."""
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
        note = ("지도가 직선·평행. Ge%·FR 을 따로 최적화해도 결과가 같다.\n"
                "  → '설계 자유도 확보'가 결론이 된다.")
    elif b12 * np.sign(b1) * np.sign(b2) > 0:
        pat = "(b) 시너지"
        note = ("두 변수를 함께 늘릴 때의 개선이 각각의 개선을 더한 것보다 크다.\n"
                "  → 가장 강한 결론.")
    else:
        pat = "(c) 트레이드오프 — 최적점 이동"
        note = ("Ge% 를 바꾸면 최적 FR 도 함께 이동한다.\n"
                "  → 한 변수만 최적화하면 다른 변수의 최적점을 놓친다.\n"
                "    '2차원 설계 맵'의 필요성을 직접 증명하는 결과.")

    return pat, note, crit, rel


# ======================================================================
#  시너지 정량화 (STE/응력은 높을수록 좋음 — lower_is_better=False)
# ======================================================================
def synergy(df, x_nom, y_nom, metric, lower_is_better=False):
    def val(sub):
        v = sub[metric].to_numpy(dtype=float)
        return v[np.isfinite(v)]

    base_row = df[(np.isclose(df.Ge_percent, x_nom)) &
                  (np.isclose(df.FR_nm, y_nom))]
    if base_row.empty:
        return None
    z_base = float(base_row[metric].iloc[0])

    row_x = df[np.isclose(df.FR_nm, y_nom)]
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
def draw(df, metric, label, fname, cmap="viridis"):
    piv = df.pivot_table(index="FR_nm", columns="Ge_percent", values=metric)
    if piv.isna().all().all():
        return None
    X, Y = np.meshgrid(piv.columns.to_numpy(float), piv.index.to_numpy(float))
    Z = piv.to_numpy(float)

    fig, ax = plt.subplots(figsize=(7.4, 5.8))
    cf = ax.contourf(X, Y, Z, levels=18, cmap=cmap)
    cs = ax.contour(X, Y, Z, levels=9, colors="white", linewidths=0.8, alpha=0.75)
    ax.clabel(cs, inline=True, fontsize=7, fmt="%.2f")
    ax.scatter(X, Y, s=14, c="white", edgecolors="k", linewidths=0.5, zorder=3)

    cb = fig.colorbar(cf, ax=ax)
    cb.set_label(label)
    ax.set_xlabel("Ge composition [%]")
    ax.set_ylabel("FR — recess depth [nm]")
    ax.set_title(f"{label}  vs  (Ge%, FR)")
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
                    help="ste/Vth/Ion 지도도 함께 생성 (컬럼이 있는 경우만)")
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
        print("   아래 결과는 참고용이다 — Ge%/FR 스윕 값이 확정되면 다시 돌릴 것.")
        print("=" * 70)
        print()

    norm = params.get("stress_transfer_efficiency", {}).get("normalization", {})
    if "ste" not in df.columns and args.metric == "ste":
        print("⚠ grid.csv 에 ste 컬럼이 없다. STE 정규화 방법이 아직 확정되지 않았기 때문이다")
        print("  (baseline/params.yaml#stress_transfer_efficiency.normalization 확인).")
        print("  --metric stress_GPa 로 다시 실행할 것.")
        return 1
    if not norm.get("channel_adjacent_point") or not norm.get("stress_to_GPa_method"):
        print("=" * 70)
        print(" ⚠ STE 정규화 방법(채널 인접 지점, GPa 환산)이 아직 팀 확정 전이다.")
        print("   지금 나오는 ste 값(있다면)은 참고용이며 결론이 아니다.")
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
    y = sub["FR_nm"].to_numpy(float)
    z = sub[metric].to_numpy(float)

    beta, se, tvals, pvals, r2 = interaction_regression(x, y, z)

    print("=" * 70)
    print(f" 교호작용 회귀 — {metric}")
    print(f" 데이터 {len(sub)}점 / 격자 {len(df)}점")
    print("=" * 70)
    names = ["절편", "Ge% (주효과)", "FR (주효과)", "Ge% x FR (교호작용)"]
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

    s = synergy(df, x_nom, y_nom, metric, lower_is_better=False)
    if s:
        print()
        print("=" * 70)
        print(f" 시너지 정량화 (기준점 G{x_nom:.0f}_F{y_nom:.0f})")
        print("=" * 70)
        print(f"  Ge% 만 최적화          : {s['dX']:+.3f}")
        print(f"  FR 만 최적화           : {s['dY']:+.3f}")
        print(f"  개별 최적화의 단순 합  : {s['dX']+s['dY']:+.3f}")
        print(f"  결합 최적화 (실제)     : {s['dJ']:+.3f}")
        print(f"  ---------------------------------------------")
        print(f"  ★ 시너지 (추가 개선분) : {s['syn']:+.3f}")
        print(f"\n  최댓값 지점: {s['best']['run_id']}  "
              f"(Ge%={s['best']['Ge_percent']:.0f}, FR={s['best']['FR_nm']:.0f}nm)")
        print("\n  ※ 이 표의 숫자가 발표 결론 문장에 그대로 들어간다.")
        print("  ⚠ metric 이 ste 가 아니라 stress_GPa 라면, 이 최댓값은 'STE 관점의 최적'이")
        print("    아니라 '절대 응력 관점의 최적'이라는 것을 발표에서 구분해서 말할 것.")

    out = draw(df, metric, metric, f"contour_{metric}.png")
    if out:
        print(f"\n그림 저장: {out.relative_to(ROOT)}")

    if args.all_figures:
        for m, cm in [("ste", "plasma"),
                      ("Vth_V", "coolwarm"),
                      ("Ion_A_um", "magma")]:
            if m in df.columns:
                o = draw(df, m, m, f"contour_{m}.png", cm)
                if o:
                    print(f"그림 저장: {o.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
