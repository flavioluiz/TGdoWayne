"""Figuras da dissertação v2.

Uso (na raiz do repositório):  .venv/bin/python dissertacao_v2/scripts/figuras.py

1. supressao.pdf   -- razão (f_g/f)^2 entre marés não tensoriais e tensoriais,
                      para amplitudes métricas comparáveis, nas bandas dos detectores.
2. orf_terra.pdf   -- ORFs apenas-Terra tensorial e de helicidade zero (Fierz--Pauli)
                      para várias razões de velocidade beta; integração direta
                      independente, conferida contra fórmulas fechadas e limites.
3. informacao.pdf  -- informação média sobre a massa (KL posterior||priori) nas
                      campanhas sintéticas já executadas (valores lidos de
                      figures/academicas/plot_values.npz).
4. falsos_positivos.pdf -- declarações espúrias de modo escalar (BF>10) em
                      500 injeções puramente tensoriais, com IC de Clopper--Pearson.
"""
import pathlib, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.special import roots_legendre
from scipy.stats import beta as beta_dist

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "dissertacao_v2" / "figuras"
sys.path.insert(0, str(ROOT / "src"))
from pta.orf import earth_analytic, hellings_downs  # só para conferência

plt.rcParams.update({"font.size": 10, "axes.grid": True, "grid.alpha": .3,
                     "savefig.bbox": "tight", "figure.dpi": 150})
H_EV_S = 4.135667696e-15


# ---------------------------------------------------------------- 1
def fig_supressao():
    f = np.logspace(-10, 4, 800)
    casos = [(4.4e-22, r"$4{,}4\times10^{-22}$ eV (limite adotado em 2004)", "C3", ":"),
             (1.92e-23, r"$1{,}92\times10^{-23}$ eV (GWTC-4, 90%)", "C0", "-"),
             (8.2e-24, r"$8{,}2\times10^{-24}$ eV (NANOGrav 15 anos + espectro)", "C2", "--")]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for m, lab, c, ls in casos:
        fg = m / H_EV_S
        viaj = f > fg
        ax.loglog(f[viaj], (fg / f[viaj])**2, color=c, ls=ls, label=lab)
    for (a, b, nome) in [(1e-9, 1e-7, "PTA"), (1e-4, 1e-1, "LISA"), (10, 2e3, "LIGO/Virgo")]:
        ax.axvspan(a, b, color="0.85", alpha=.6, lw=0)
        ax.text(np.sqrt(a * b), 1.6, nome, ha="center", va="bottom", fontsize=9)
    ax.axhline(1, color="k", lw=.8)
    ax.set_ylim(1e-24, 1e2); ax.set_xlim(1e-10, 1e4)
    ax.set_xlabel("frequência da onda $f$ (Hz)")
    ax.set_ylabel(r"$(f_g/f)^2$")
    ax.legend(fontsize=8, loc="lower left", framealpha=1)
    fig.savefig(OUT / "supressao.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- 2
def _orfs_terra(beta, zeta, n=600):
    """Integração direta sobre a esfera: devolve (Gamma_T, Gamma_0) apenas-Terra."""
    x, wx = roots_legendre(n)
    phi = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False); wphi = 2 * np.pi / (2 * n)
    X, P = np.meshgrid(x, phi, indexing="ij")
    W = wx[:, None] * wphi
    d = np.cos(zeta)
    mua = X
    mub = d * X + np.sqrt(1 - d * d) * np.sqrt(1 - X * X) * np.cos(P)
    Da, Db = 1 + beta * mua, 1 + beta * mub
    T = 2 * (d - mua * mub)**2 - (1 - mua**2) * (1 - mub**2)
    gT = 3 / (32 * np.pi) * np.sum(W * T / (Da * Db))
    Aa = 1 + (2 * beta**2 - 3) * mua**2
    Ab = 1 + (2 * beta**2 - 3) * mub**2
    g0 = 1 / (32 * np.pi) * np.sum(W * Aa * Ab / (Da * Db))
    return gT, g0


def fig_orf():
    zetas = np.linspace(0, np.pi, 61)
    betas = [0.0, 0.5, 0.9]
    res = {b: np.array([_orfs_terra(b, z) for z in zetas]) for b in betas}
    d = np.cos(zetas)
    p2 = (3 * d**2 - 1) / 2
    # conferências independentes
    for b in betas:
        ref = np.array([earth_analytic(b, c) for c in d])
        err = np.max(np.abs(res[b][:, 0] - ref))
        assert err < 1e-6, (b, err)
    assert np.max(np.abs(res[0.0][:, 1] - p2 / 10)) < 1e-10
    assert np.max(np.abs(res[0.0][:, 0] - p2 / 5)) < 1e-10
    # limite formal beta->1 do escalar: A/D -> 1-mu, logo Gamma_0 = (3+d)/24
    x, wx = roots_legendre(400); phi = np.linspace(0, 2*np.pi, 800, endpoint=False)
    X, P = np.meshgrid(x, phi, indexing="ij"); W = wx[:, None] * (2*np.pi/800)
    g0_1 = []
    for z in zetas:
        c = np.cos(z); mub = c*X + np.sqrt(1-c*c)*np.sqrt(1-X*X)*np.cos(P)
        g0_1.append(np.sum(W*(1-X)*(1-mub))/(32*np.pi))
    g0_1 = np.array(g0_1)
    assert np.max(np.abs(g0_1 - (3 + d) / 24)) < 1e-10
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.3), sharey=True)
    cores = {1.0: "k", 0.9: "C0", 0.5: "C1", 0.0: "C3"}
    axs[0].plot(np.degrees(zetas), hellings_downs(d), color="k", label=r"$\beta=1$ (Hellings–Downs)")
    axs[1].plot(np.degrees(zetas), g0_1, color="k", ls="--", label=r"$\beta\to1$ (limite formal)")
    for b in [0.9, 0.5, 0.0]:
        axs[0].plot(np.degrees(zetas), res[b][:, 0], color=cores[b], label=rf"$\beta={b:g}$")
        axs[1].plot(np.degrees(zetas), res[b][:, 1], color=cores[b], label=rf"$\beta={b:g}$")
    axs[0].set_title("tensorial ($+$, $\\times$)", fontsize=10)
    axs[1].set_title("helicidade zero de Fierz–Pauli", fontsize=10)
    for ax in axs:
        ax.axhline(0, color="0.5", lw=.6); ax.set_xlim(0, 180); ax.set_xticks(range(0, 181, 30))
        ax.set_xlabel(r"separação angular $\zeta$ (graus)"); ax.legend(fontsize=7.5)
    axs[0].set_ylabel(r"$\Gamma^{\rm Terra}(\zeta)$")
    fig.savefig(OUT / "orf_terra.pdf"); plt.close(fig)
    return {b: (res[b][0], res[b][30]) for b in betas}


# ---------------------------------------------------------------- 3
def fig_informacao():
    d = np.load(ROOT / "figures/academicas/plot_values.npz", allow_pickle=True)
    # ordem das nove análises no arquivo original
    idx = {"dados completos\n(verossimilhança exata)": 0,
           "correlações por frequência\n(controle gaussiano)": 5,
           "correlações comprimidas\n(controle gaussiano)": 6}
    fig, ax = plt.subplots(figsize=(7, 3.2))
    width = .36
    for j, (pop, lab, c) in enumerate([("P12K4", "12 pulsares, 4 frequências", "C0"),
                                       ("P16K8", "16 pulsares, 8 frequências", "C1")]):
        v = d[f"population_information_{pop}"]
        y = [v[i, 0] for i in idx.values()]; e = [v[i, 1] for i in idx.values()]
        ax.bar(np.arange(3) + (j - .5) * width, y, width, yerr=e, capsize=3, color=c, label=lab)
    ax.axhline(np.log(1 / 0.9), color="k", ls="--", lw=.9)
    ax.text(2.45, np.log(1/0.9) - .012, "referência: priori reduzida\na 90% do intervalo", ha="right", fontsize=8)
    ax.set_xticks(range(3)); ax.set_xticklabels(list(idx.keys()), fontsize=8.5)
    ax.set_ylabel("KL média posterior‖priori (nat)")
    ax.legend(fontsize=8, loc="upper right")
    ax.set_ylim(0, .15)
    fig.savefig(OUT / "informacao.pdf"); plt.close(fig)
    return {pop: d[f"population_information_{pop}"][:, :2] for pop in ("P12K4", "P16K8")}


# ---------------------------------------------------------------- 4
def fig_falsos_positivos():
    # contagens nominais das 500 injeções tensoriais (figures/escalar/tabela_falsos_positivos.tex)
    casos = [("dados completos,\nverossimilhança exata", 2),
             ("correlações por frequência,\naproximação normal", 22),
             ("correlações comprimidas,\naproximação normal", 10)]
    n = 500
    fig, ax = plt.subplots(figsize=(6.4, 3))
    for i, (lab, k) in enumerate(casos):
        lo = beta_dist.ppf(.025, k, n - k + 1) if k else 0
        hi = beta_dist.ppf(.975, k + 1, n - k)
        ax.errorbar(i, 100 * k / n, yerr=[[100 * (k / n - lo)], [100 * (hi - k / n)]],
                    fmt="o", color="C0", capsize=4)
    ax.set_xticks(range(3)); ax.set_xticklabels([c[0] for c in casos], fontsize=8.5)
    ax.set_xlim(-.5, 2.5)
    ax.set_ylabel("declarações espúrias (%)")
    fig.savefig(OUT / "falsos_positivos.pdf"); plt.close(fig)


if __name__ == "__main__":
    fig_supressao()
    ext = fig_orf()
    for b, (z0, z90) in ext.items():
        print(f"beta={b}: zeta=0 GT={z0[0]:.6f} G0={z0[1]:.6f} | zeta=90 GT={z90[0]:.6f} G0={z90[1]:.6f}")
    info = fig_informacao()
    for pop, v in info.items():
        print(pop, np.round(v, 5).tolist())
    fig_falsos_positivos()
    print("figuras em", OUT)
