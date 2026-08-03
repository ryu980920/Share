#!/usr/bin/env python3
"""
contour.py — grid.csv 로부터 2차원 등고선을 그리고 상호작용을 판정한다.

이 프로젝트의 결론이 나오는 스크립트다.
  (1) GIDL 등고선  ← 발표의 하이라이트 그림
  (2) 교호작용 회귀 → 등고선이 "직선/평행"인지 "휘었는지"를 눈이 아니라 숫자로 판정
  (3) 시너지 정량화 → 개별 최적화 대비 결합 최적화의 추가 개선분

사용법
    python analysis/contour.py
    python analysis/contour.py --metric Ion_A_um --no-log
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
    b12 ~ 0 이면 → 등고선이 직선·평행. 두 변수는 독립.
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
    """상호작용 유무 판정 → 기획서 4-4절의 (a)/(b)/(c) 패턴."""
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
        note = ("등고선이 직선·평행. 두 변수를 따로 최적화해도 결과가 같다.\n"
                "  → 기획서 5-4절 시나리오 A. '설계 자유도 확보'가 결론이 된다.\n"
                "    헤드라인은 '결합 최적화로 GIDL X% 저감'으로 두고,\n"
                "    독립성 확인은 부가 결론으로 배치할 것.")
    # 개선 방향: z(=GIDL)를 낮추려면 x 는 -sign(b1), y 는 -sign(b2) 방향으로 움직인다.
    # 그 방향으로 함께 움직였을 때 교호작용항이 z 를 더 낮추면(음의 기여) 시너지다.
    elif -b12 * np.sign(b1) * np.sign(b2) > 0:
        pat = "(b) 시너지"
        note = ("두 변수를 함께 줄일 때의 개선이 각각의 개선을 더한 것보다 크다.\n"
                "  → 가장 강한 결론. 등고선이 한쪽 구석으로 휘어 모인다.")
    else:
        pat = "(c) 트레이드오프 — 최적점 이동"
        note = ("DBCAT 을 바꾸면 최적 도핑 농도도 함께 이동한다.\n"
                "  → 한 변수만 최적화하면 다른 변수의 최적점을 놓친다.\n"
                "    '2차원 설계 맵'의 필요성을 직접 증명하는 결과.")

    return pat, note, crit, rel


# ======================================================================
#  시너지 정량화
# ======================================================================
def synergy(df, x_nom, y_nom, metric, lower_is_better=True):
    """
    개별 최적화 vs 결합 최적화. log10 단위(dex)로 계산한다.
      dX  : y 를 기준값에 고정하고 x 만 최적화했을 때의 개선
      dY  : x 를 기준값에 고정하고 y 만 최적화했을 때의 개선
      dJ  : 둘 다 자유롭게 최적화했을 때의 개선
      시너지 = dJ - (dX + dY)
    """
    def val(sub):
        v = sub[metric].to_numpy(dtype=float)
        v = v[np.isfinite(v) & (v > 0)]
        return v

    base_row = df[(np.isclose(df.D_BCAT_nm, x_nom)) &
                  (np.isclose(df.doping_multiplier, y_nom))]
    if base_row.empty:
        return None
    z_base = np.log10(float(base_row[metric].iloc[0]))

    row_x = df[np.isclose(df.doping_multiplier, y_nom)]
    row_y = df[np.isclose(df.D_BCAT_nm, x_nom)]
    f = np.min if lower_is_better else np.max

    vx, vy, vj = val(row_x), val(row_y), val(df)
    if len(vx) == 0 or len(vy) == 0 or len(vj) == 0:
        return None

    dX = z_base - np.log10(f(vx))
    dY = z_base - np.log10(f(vy))
    dJ = z_base - np.log10(f(vj))

    best = df.loc[df[metric].idxmin() if lower_is_better else df[metric].idxmax()]
    return dict(z_base=z_base, dX=dX, dY=dY, dJ=dJ, syn=dJ - (dX + dY), best=best)


# ======================================================================
#  그림
# ======================================================================
def draw(df, metric, log_scale, label, fname, cmap="viridis"):
    piv = df.pivot_table(index="doping_multiplier", columns="D_BCAT_nm", values=metric)
    if piv.isna().all().all():
        return None
    X, Y = np.meshgrid(piv.columns.to_numpy(float), piv.index.to_numpy(float))
    Z = piv.to_numpy(float)
    Zp = np.log10(np.where(Z > 0, Z, np.nan)) if log_scale else Z

    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    cf = ax.contourf(X, Y, Zp, levels=18, cmap=cmap)
    cs = ax.contour(X, Y, Zp, levels=9, colors="white", linewidths=0.8, alpha=0.75)
    ax.clabel(cs, inline=True, fontsize=7, fmt="%.2f")
    ax.scatter(X, Y, s=14, c="white", edgecolors="k", linewidths=0.5, zorder=3)

    cb = fig.colorbar(cf, ax=ax)
    cb.set_label(("log10 " if log_scale else "") + label)
    ax.set_xlabel("DBCAT — nitride thickness [nm]")
    ax.set_ylabel("S/D doping multiplier [-]")
    ax.set_title(f"{label}  vs  (DBCAT, doping)")
    fig.tight_layout()
    FIGDIR.mkdir(exist_ok=True)
    out = FIGDIR / fname
    fig.savefig(out, dpi=200)
    plt.close(fig)
    return out


# ======================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", default="I_GIDL_A_um")
    ap.add_argument("--no-log", action="store_true")
    ap.add_argument("--all-figures", action="store_true",
                    help="GIDL 외 Ion/DIBL/SS 등고선도 함께 생성")
    args = ap.parse_args()

    if not GRID.exists():
        print("grid.csv 없음. 먼저 merge.py 를 돌릴 것.", file=sys.stderr)
        return 1
    df = pd.read_csv(GRID)
    with open(PARAMS, encoding="utf-8") as f:
        params = yaml.safe_load(f)

    x_nom = float(params["geometry"]["D_BCAT_nm"])
    y_nom = 1.00
    metric = args.metric
    log_scale = not args.no_log

    sub = df[np.isfinite(df[metric])]
    if len(sub) < 4:
        print(f"유효 데이터 {len(sub)}개. 회귀에는 최소 4개 필요.", file=sys.stderr)
        return 1

    x = sub["D_BCAT_nm"].to_numpy(float)
    y = sub["doping_multiplier"].to_numpy(float)
    z = np.log10(sub[metric].to_numpy(float)) if log_scale else sub[metric].to_numpy(float)

    beta, se, tvals, pvals, r2 = interaction_regression(x, y, z)

    print("=" * 70)
    print(f" 교호작용 회귀 — {'log10(' + metric + ')' if log_scale else metric}")
    print(f" 데이터 {len(sub)}점 / 격자 {len(df)}점")
    print("=" * 70)
    names = ["절편", "DBCAT (주효과)", "도핑 (주효과)", "DBCAT x 도핑 (교호작용)"]
    print(f"  {'항':26s}{'계수':>12s}{'표준오차':>12s}{'t':>9s}{'p':>10s}")
    for i, nm in enumerate(names):
        p = f"{pvals[i]:.4f}" if pvals is not None else "   -  "
        print(f"  {nm:26s}{beta[i]:12.4f}{se[i]:12.4f}{tvals[i]:9.2f}{p:>10s}")
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

    s = synergy(df, x_nom, y_nom, metric, lower_is_better=True)
    if s:
        print()
        print("=" * 70)
        print(f" 시너지 정량화 (기준점 D{int(x_nom)}_N100)")
        print("=" * 70)
        def pct(dex):
            return (1 - 10 ** (-dex)) * 100
        print(f"  DBCAT 만 최적화        : {s['dX']:+.3f} dex  ({pct(s['dX']):+.1f}%)")
        print(f"  도핑 만 최적화         : {s['dY']:+.3f} dex  ({pct(s['dY']):+.1f}%)")
        print(f"  개별 최적화의 단순 합  : {s['dX']+s['dY']:+.3f} dex  "
              f"({pct(s['dX']+s['dY']):+.1f}%)")
        print(f"  결합 최적화 (실제)     : {s['dJ']:+.3f} dex  ({pct(s['dJ']):+.1f}%)")
        print(f"  ---------------------------------------------")
        print(f"  ★ 시너지 (추가 개선분) : {s['syn']:+.3f} dex")
        print(f"\n  최적 조합: {s['best']['run_id']}  "
              f"(DBCAT={s['best']['D_BCAT_nm']:.0f} nm, "
              f"도핑x{s['best']['doping_multiplier']:.2f})")
        if "Ion_A_um" in df.columns:
            base = df[(np.isclose(df.D_BCAT_nm, x_nom)) &
                      (np.isclose(df.doping_multiplier, y_nom))]
            if not base.empty and np.isfinite(base["Ion_A_um"].iloc[0]):
                i0 = float(base["Ion_A_um"].iloc[0])
                i1 = float(s["best"]["Ion_A_um"])
                print(f"  그때의 Ion 변화: {i0:.3e} -> {i1:.3e} A/um "
                      f"({(i1/i0-1)*100:+.1f}%)   ← 대가")
        print("\n  ※ 이 표의 숫자가 발표 결론 문장(기획서 6-1절)에 그대로 들어간다.")

    out = draw(df, metric, log_scale, metric, f"contour_{metric}.png")
    if out:
        print(f"\n그림 저장: {out.relative_to(ROOT)}")

    if args.all_figures:
        for m, lg, cm in [("Ion_A_um", True, "plasma"),
                          ("DIBL_mV_V", False, "coolwarm"),
                          ("SS_mV_dec", False, "cividis"),
                          ("Ion_Ioff_ratio", True, "magma")]:
            if m in df.columns:
                o = draw(df, m, lg, m, f"contour_{m}.png", cm)
                if o:
                    print(f"그림 저장: {o.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
