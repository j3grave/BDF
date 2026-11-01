"""
04_eda.py - Análise exploratória (estatística e gráfica) dos datasets MovieLens.

Projeto BDF 2026 - NOVA IMS - case analysis MovieLens.

Todas as agregações são feitas no DuckDB e só os resultados agregados passam
para Python. Por isso o mesmo script corre no small, no 1M e no 32M sem
carregar os dados completos em memória.

Uso:
    python scripts/04_eda.py --dataset small
    python scripts/04_eda.py --dataset 32m --fonte parquet

Saídas em results/<dataset>/eda/:
    - figuras PNG numeradas (01_...png a 10_...png)
    - eda_resumo_tabelas.csv   (linhas, colunas, nulos, distintos por tabela)
    - eda_indicadores.csv      (indicadores-chave do dataset)
    - eda_relatorio.md         (relatório com indicadores e figuras)
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------------------
# Identidade visual NOVA IMS
# Cores retiradas dos slides oficiais da cadeira (template NOVA IMS).
# Para ajustar a paleta, basta alterar este bloco.
# ---------------------------------------------------------------------------
NOVA = {
    "verde": "#BED62F",         # verde-lima NOVA IMS (destaque principal)
    "verde_escuro": "#8A9C1F",  # verde para linhas e texto sobre branco
    "verde_claro": "#E4EEA6",   # fundos e áreas
    "cinza": "#5B6062",         # cinzento dos cabeçalhos NOVA IMS
    "cinza_escuro": "#2E3133",  # texto principal
    "cinza_medio": "#9EA3A5",   # elementos secundários
    "cinza_claro": "#E3E5E6",   # grelhas e fundos
    "branco": "#FFFFFF",
}
PALETA_CATEGORICA = [NOVA["verde"], NOVA["cinza"], NOVA["verde_escuro"],
                     NOVA["cinza_medio"], NOVA["verde_claro"], NOVA["cinza_escuro"]]
CMAP_NOVA = LinearSegmentedColormap.from_list(
    "nova", [NOVA["branco"], NOVA["verde_claro"], NOVA["verde"], NOVA["verde_escuro"]])


def aplicar_estilo_nova() -> None:
    """Estilo matplotlib coerente com os slides NOVA IMS."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.titlecolor": NOVA["cinza_escuro"],
        "axes.labelcolor": NOVA["cinza"],
        "axes.edgecolor": NOVA["cinza_medio"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": NOVA["cinza_claro"],
        "grid.linewidth": 0.7,
        "xtick.color": NOVA["cinza"],
        "ytick.color": NOVA["cinza"],
        "axes.prop_cycle": plt.cycler(color=PALETA_CATEGORICA),
        "figure.facecolor": NOVA["branco"],
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "legend.frameon": False,
    })


def rodape(fig, dataset: str) -> None:
    """Faixa de rodapé com a identificação do projeto (estilo slide NOVA IMS)."""
    fig.text(0.01, 0.005, f"BDF 2026 · NOVA IMS · MovieLens {dataset}",
             fontsize=8, color=NOVA["cinza_medio"], ha="left", va="bottom")


def fmt_milhares(x, _pos=None) -> str:
    if abs(x) >= 1e6:
        return f"{x/1e6:.1f} M".replace(".", ",")
    if abs(x) >= 1e3:
        return f"{x/1e3:.0f} mil"
    return f"{x:.0f}"


def num(x: float, casas: int = 0) -> str:
    """Formato numérico português: espaço nos milhares, vírgula decimal."""
    s = f"{x:,.{casas}f}"
    return s.replace(",", " ").replace(".", ",")


# ---------------------------------------------------------------------------
# Ligação aos dados
# ---------------------------------------------------------------------------
TABELAS = ["ratings", "movies", "tags", "links"]


def localizar(base: Path, dataset: str, tabela: str, fonte: str) -> tuple[str, str] | None:
    """Devolve (caminho, tipo) da tabela. Prefere Parquet sem partição."""
    pasta_pq = base / "data" / dataset / "parquet"
    pasta_csv = base / "data" / dataset / "csv"
    candidatos = []
    if fonte in ("auto", "parquet"):
        candidatos += [(pasta_pq / f"{tabela}.parquet", "parquet")]
        candidatos += [(p, "parquet") for p in sorted(pasta_pq.glob(f"{tabela}*.parquet"))
                       if p.is_file()]
    if fonte in ("auto", "csv"):
        candidatos += [(pasta_csv / f"{tabela}.csv", "csv")]
    for caminho, tipo in candidatos:
        if caminho.exists() and caminho.is_file():
            return str(caminho), tipo
    return None


def ligar(base: Path, dataset: str, fonte: str) -> tuple[duckdb.DuckDBPyConnection, dict]:
    con = duckdb.connect()
    origem = {}
    for t in TABELAS:
        loc = localizar(base, dataset, t, fonte)
        if loc is None:
            continue
        caminho, tipo = loc
        leitor = "read_parquet" if tipo == "parquet" else "read_csv_auto"
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM {leitor}('{caminho}')")
        origem[t] = f"{tipo}: {caminho}"
    if "ratings" not in origem or "movies" not in origem:
        raise SystemExit(
            f"Não encontrei ratings e movies em data/{dataset}/parquet nem data/{dataset}/csv. "
            "Corre primeiro a ingestão e a conversão para Parquet.")
    return con, origem


def q(con, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


# ---------------------------------------------------------------------------
# Estatística descritiva
# ---------------------------------------------------------------------------
def resumo_tabelas(con, origem: dict) -> pd.DataFrame:
    linhas = []
    for t in origem:
        cols = q(con, f"DESCRIBE {t}")["column_name"].tolist()
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for c in cols:
            nulos, distintos = con.execute(
                f'SELECT COUNT(*) - COUNT("{c}"), approx_count_distinct("{c}") FROM {t}'
            ).fetchone()
            linhas.append({"tabela": t, "coluna": c, "linhas": n, "nulos": nulos,
                           "pct_nulos": round(100 * nulos / n, 3) if n else 0,
                           "distintos_aprox": distintos})
    return pd.DataFrame(linhas)


def gini(valores: np.ndarray) -> float:
    v = np.sort(np.asarray(valores, dtype=float))
    n = v.size
    if n == 0 or v.sum() == 0:
        return float("nan")
    cum = np.cumsum(v)
    return float((n + 1 - 2 * (cum.sum() / cum[-1])) / n)


# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------
def guardar(fig, pasta: Path, nome: str, dataset: str, figuras: list) -> None:
    rodape(fig, dataset)
    caminho = pasta / nome
    fig.savefig(caminho)
    plt.close(fig)
    figuras.append(nome)


def fig_distribuicao_ratings(con, pasta, ds, figuras, ind):
    df = q(con, "SELECT rating, COUNT(*) AS n FROM ratings GROUP BY rating ORDER BY rating")
    est = con.execute("""SELECT AVG(rating), MEDIAN(rating), STDDEV(rating),
                                MODE(rating) FROM ratings""").fetchone()
    ind.update({"rating_media": round(est[0], 3), "rating_mediana": est[1],
                "rating_desvio_padrao": round(est[2], 3), "rating_moda": est[3]})
    fig, ax = plt.subplots(figsize=(9, 4.5))
    cores = [NOVA["verde"] if r == est[3] else NOVA["cinza_medio"] for r in df["rating"]]
    ax.bar(df["rating"].astype(str), df["n"], color=cores, edgecolor=NOVA["cinza"], linewidth=0.4)
    total = df["n"].sum()
    for i, (r, n) in enumerate(zip(df["rating"], df["n"])):
        ax.text(i, n, f"{100*n/total:.1f}%".replace(".", ","), ha="center", va="bottom",
                fontsize=8, color=NOVA["cinza"])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))
    ax.set_title("Distribuição das avaliações")
    ax.set_xlabel("Avaliação (estrelas)")
    ax.set_ylabel("N.º de avaliações")
    ax.set_ylim(0, df["n"].max() * 1.18)
    ax.text(0.01, 0.97,
            f"média {est[0]:.2f}  ·  mediana {est[1]:.1f}  ·  desvio-padrão {est[2]:.2f}".replace(".", ","),
            transform=ax.transAxes, ha="left", va="top", fontsize=9, color=NOVA["cinza_escuro"])
    guardar(fig, pasta, "01_distribuicao_ratings.png", ds, figuras)


def fig_atividade(con, pasta, ds, figuras, ind, entidade: str):
    col = "userId" if entidade == "utilizador" else "movieId"
    cont = q(con, f"SELECT {col}, COUNT(*) AS n FROM ratings GROUP BY {col}")["n"].to_numpy()
    g = gini(cont)
    qs = np.percentile(cont, [25, 50, 75, 90, 99])
    sufixo = "user" if entidade == "utilizador" else "movie"
    ind.update({f"ratings_por_{sufixo}_min": int(cont.min()),
                f"ratings_por_{sufixo}_mediana": float(qs[1]),
                f"ratings_por_{sufixo}_media": round(float(cont.mean()), 1),
                f"ratings_por_{sufixo}_p90": float(qs[3]),
                f"ratings_por_{sufixo}_max": int(cont.max()),
                f"gini_{sufixo}": round(g, 3)})

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5))
    bins = np.logspace(0, np.log10(cont.max() + 1), 40)
    a1.hist(cont, bins=bins, color=NOVA["verde"], edgecolor=NOVA["cinza"], linewidth=0.4)
    a1.set_xscale("log")
    a1.axvline(qs[1], color=NOVA["cinza_escuro"], linestyle="--", linewidth=1)
    a1.text(qs[1], a1.get_ylim()[1] * 0.95, f"  mediana = {qs[1]:.0f}",
            color=NOVA["cinza_escuro"], fontsize=9, va="top")
    a1.set_title(f"Avaliações por {entidade} (escala log)")
    a1.set_xlabel(f"N.º de avaliações por {entidade}")
    a1.set_ylabel(f"N.º de {entidade}es" if entidade == "utilizador" else "N.º de filmes")

    # Curva de Lorenz: concentração da atividade
    v = np.sort(cont)
    x = np.linspace(0, 1, v.size + 1)
    y = np.concatenate([[0], np.cumsum(v) / v.sum()])
    a2.fill_between(x, y, x, color=NOVA["verde_claro"], alpha=0.8)
    a2.plot(x, y, color=NOVA["verde_escuro"], linewidth=2, label="Curva de Lorenz")
    a2.plot([0, 1], [0, 1], color=NOVA["cinza_medio"], linestyle="--", linewidth=1,
            label="Igualdade perfeita")
    top10 = 1 - np.interp(0.9, x, y)
    a2.set_title(f"Concentração da atividade · Gini = {g:.2f}".replace(".", ","))
    a2.set_xlabel(f"% acumulada de {entidade}es (do menos ao mais ativo)"
                  if entidade == "utilizador" else "% acumulada de filmes (do menos ao mais avaliado)")
    a2.set_ylabel("% acumulada de avaliações")
    a2.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    a2.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    quem = "utilizadores mais ativos" if entidade == "utilizador" else "filmes mais avaliados"
    a2.text(0.04, 0.92, f"Os 10% {quem} concentram\n{100*top10:.0f}% das avaliações",
            transform=a2.transAxes, fontsize=9, color=NOVA["cinza_escuro"], va="top")
    a2.legend(loc="lower right", fontsize=8)
    ind[f"pct_ratings_top10pct_{sufixo}"] = round(100 * top10, 1)
    nome = "02_atividade_utilizadores.png" if entidade == "utilizador" else "03_popularidade_filmes.png"
    fig.tight_layout()
    guardar(fig, pasta, nome, ds, figuras)


def fig_cauda_longa(con, pasta, ds, figuras):
    df = q(con, "SELECT COUNT(*) AS n FROM ratings GROUP BY movieId ORDER BY n DESC")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    rank = np.arange(1, len(df) + 1)
    ax.loglog(rank, df["n"], color=NOVA["verde_escuro"], linewidth=2)
    ax.fill_between(rank, df["n"], 1, color=NOVA["verde_claro"], alpha=0.6)
    ax.set_title("Cauda longa: avaliações por filme ordenadas por popularidade")
    ax.set_xlabel("Posição do filme no ranking (escala log)")
    ax.set_ylabel("N.º de avaliações (escala log)")
    unicos = int((df["n"] == 1).sum())
    ax.text(0.98, 0.95, f"{num(unicos)} filmes ({100*unicos/len(df):.0f}%) têm 1 só avaliação",
            transform=ax.transAxes, ha="right", va="top", fontsize=9, color=NOVA["cinza_escuro"])
    guardar(fig, pasta, "04_cauda_longa_filmes.png", ds, figuras)


# Ano em UTC (epoch_ms devolve TIMESTAMP sem fuso horário), como em 02_to_parquet.py
def fig_temporal(con, pasta, ds, figuras, ind):
    df = q(con, """SELECT year(epoch_ms(timestamp * 1000)) AS ano, COUNT(*) AS n,
                          AVG(rating) AS media, COUNT(DISTINCT userId) AS utilizadores
                   FROM ratings GROUP BY ano ORDER BY ano""")
    ind.update({"ano_primeiro_rating": int(df["ano"].min()),
                "ano_ultimo_rating": int(df["ano"].max())})
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.bar(df["ano"], df["n"], color=NOVA["verde"], edgecolor=NOVA["cinza"], linewidth=0.3,
           label="N.º de avaliações")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))
    ax.set_ylabel("N.º de avaliações")
    ax.set_xlabel("Ano da avaliação")
    ax2 = ax.twinx()
    ax2.plot(df["ano"], df["media"], color=NOVA["cinza_escuro"], marker="o", markersize=3.5,
             linewidth=1.5, label="Avaliação média")
    ax2.set_ylabel("Avaliação média", color=NOVA["cinza_escuro"])
    ax2.set_ylim(2.5, 4.5)
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax.set_title("Evolução temporal: volume e avaliação média por ano")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    guardar(fig, pasta, "05_evolucao_temporal.png", ds, figuras)


def fig_generos(con, pasta, ds, figuras, ind):
    df = q(con, """
        WITH g AS (SELECT movieId, unnest(string_split(genres, '|')) AS genero FROM movies),
             r AS (SELECT movieId, COUNT(*) AS n, AVG(rating) AS media FROM ratings GROUP BY movieId)
        SELECT genero, COUNT(DISTINCT g.movieId) AS filmes,
               SUM(r.n) AS avaliacoes, SUM(r.media * r.n) / SUM(r.n) AS media
        FROM g LEFT JOIN r USING (movieId)
        GROUP BY genero ORDER BY filmes""")
    df = df[df["genero"] != "(no genres listed)"]
    ind["n_generos"] = len(df)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 6.5), sharey=True)
    a1.barh(df["genero"], df["filmes"], color=NOVA["verde"], edgecolor=NOVA["cinza"], linewidth=0.3)
    a1.set_title("Filmes por género")
    a1.set_xlabel("N.º de filmes (um filme pode ter vários géneros)")
    a1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))
    media_global = ind.get("rating_media", df["media"].mean())
    cores = [NOVA["verde_escuro"] if m >= media_global else NOVA["cinza_medio"] for m in df["media"]]
    a2.barh(df["genero"], df["media"], color=cores)
    a2.axvline(media_global, color=NOVA["cinza_escuro"], linestyle="--", linewidth=1)
    a2.set_xlim(df["media"].min() - 0.2, df["media"].max() + 0.1)
    a2.set_title("Avaliação média por género")
    a2.set_xlabel(f"Avaliação média (tracejado = média global {media_global:.2f})".replace(".", ","))
    fig.tight_layout()
    guardar(fig, pasta, "06_generos.png", ds, figuras)


def fig_ano_lancamento(con, pasta, ds, figuras, ind):
    df = q(con, r"""
        SELECT TRY_CAST(regexp_extract(trim(title), '\((\d{4})\)\s*$', 1) AS INTEGER) AS ano,
               COUNT(*) AS n
        FROM movies GROUP BY ano ORDER BY ano""")
    sem_ano = int(df.loc[df["ano"].isna(), "n"].sum())
    df = df.dropna()
    ind["filmes_sem_ano_no_titulo"] = sem_ano
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.fill_between(df["ano"], df["n"], color=NOVA["verde_claro"])
    ax.plot(df["ano"], df["n"], color=NOVA["verde_escuro"], linewidth=1.5)
    ax.set_title("Filmes por ano de lançamento (extraído do título)")
    ax.set_xlabel("Ano de lançamento")
    ax.set_ylabel("N.º de filmes")
    ax.text(0.01, 0.95, f"{num(sem_ano)} filmes sem ano identificável no título",
            transform=ax.transAxes, fontsize=9, color=NOVA["cinza"], va="top")
    guardar(fig, pasta, "07_ano_lancamento.png", ds, figuras)


def fig_matriz_genero_ano(con, pasta, ds, figuras):
    df = q(con, """
        WITH g AS (SELECT movieId, unnest(string_split(genres, '|')) AS genero FROM movies)
        SELECT genero, year(epoch_ms(r.timestamp * 1000)) AS ano, AVG(r.rating) AS media
        FROM ratings r JOIN g USING (movieId)
        WHERE genero <> '(no genres listed)'
        GROUP BY genero, ano""")
    pv = df.pivot(index="genero", columns="ano", values="media").sort_index()
    fig, ax = plt.subplots(figsize=(13, 6.5))
    im = ax.imshow(pv.values, aspect="auto", cmap=CMAP_NOVA, vmin=2.8, vmax=4.3)
    ax.set_yticks(range(len(pv.index)), pv.index)
    passo = max(1, len(pv.columns) // 15)
    ax.set_xticks(range(0, len(pv.columns), passo), pv.columns[::passo])
    ax.grid(False)
    ax.set_title("Avaliação média por género e ano da avaliação")
    ax.set_xlabel("Ano da avaliação")
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01)
    cb.set_label("Avaliação média", color=NOVA["cinza"])
    cb.outline.set_visible(False)
    guardar(fig, pasta, "08_heatmap_genero_ano.png", ds, figuras)


def fig_tags(con, pasta, ds, figuras, ind):
    df = q(con, """SELECT lower(trim(tag)) AS tag, COUNT(*) AS n, COUNT(DISTINCT userId) AS users
                   FROM tags GROUP BY 1 ORDER BY n DESC LIMIT 20""")
    tot = con.execute("SELECT COUNT(*), COUNT(DISTINCT userId), COUNT(DISTINCT movieId) FROM tags").fetchone()
    ind.update({"tags_total": tot[0], "tags_utilizadores": tot[1], "tags_filmes": tot[2]})
    df = df.iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["tag"], df["n"], color=NOVA["verde"], edgecolor=NOVA["cinza"], linewidth=0.3)
    for y, (n, u) in enumerate(zip(df["n"], df["users"])):
        ax.text(n, y, f"  {num(u)} utiliz.", va="center", fontsize=8, color=NOVA["cinza"])
    ax.set_title("As 20 tags mais usadas")
    ax.set_xlabel("N.º de utilizações")
    ax.text(0.99, 0.02, f"Apenas {num(tot[1])} utilizadores escreveram tags",
            transform=ax.transAxes, ha="right", fontsize=9, color=NOVA["cinza_escuro"])
    guardar(fig, pasta, "09_top_tags.png", ds, figuras)


def fig_painel(con, pasta, ds, figuras, ind):
    """Painel-resumo de uma página, pensado para um slide."""
    fig = plt.figure(figsize=(13, 7.3))
    fig.patch.set_facecolor(NOVA["branco"])
    faixa = fig.add_axes([0, 0.9, 1, 0.1])
    faixa.set_facecolor(NOVA["cinza"])
    faixa.set_xticks([]); faixa.set_yticks([]); faixa.grid(False)
    for s in faixa.spines.values():
        s.set_visible(False)
    faixa.text(0.015, 0.5, f"MovieLens {ds} · retrato do dataset", color=NOVA["branco"],
               fontsize=18, fontweight="bold", va="center")
    faixa.add_patch(plt.Rectangle((0, 0), 1, 0.08, color=NOVA["verde"], transform=faixa.transAxes))

    cartoes = [("Avaliações", num(ind["n_ratings"])),
               ("Utilizadores", num(ind["n_utilizadores"])),
               ("Filmes avaliados", num(ind["n_filmes_avaliados"])),
               ("Esparsidade", f"{ind['esparsidade_pct']:.2f}%".replace(".", ",")),
               ("Avaliação média", f"{ind['rating_media']:.2f}".replace(".", ",")),
               ("Período", f"{ind['ano_primeiro_rating']}–{ind['ano_ultimo_rating']}")]
    for i, (rot, val) in enumerate(cartoes):
        ax = fig.add_axes([0.015 + i * 0.163, 0.72, 0.15, 0.14])
        ax.set_facecolor(NOVA["verde_claro"]); ax.grid(False)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.axvline(0, color=NOVA["verde"], linewidth=8)
        ax.text(0.1, 0.62, val, fontsize=17, fontweight="bold", color=NOVA["cinza_escuro"],
                transform=ax.transAxes, va="center")
        ax.text(0.1, 0.25, rot, fontsize=9, color=NOVA["cinza"], transform=ax.transAxes, va="center")

    r = q(con, "SELECT rating, COUNT(*) AS n FROM ratings GROUP BY rating ORDER BY rating")
    a1 = fig.add_axes([0.05, 0.08, 0.27, 0.53])
    a1.bar(r["rating"].astype(str), r["n"], color=NOVA["verde"], edgecolor=NOVA["cinza"], linewidth=0.3)
    a1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))
    a1.set_title("Distribuição das avaliações", fontsize=11)
    a1.tick_params(axis="x", labelsize=7)

    u = q(con, "SELECT COUNT(*) AS n FROM ratings GROUP BY userId")["n"].to_numpy()
    a2 = fig.add_axes([0.38, 0.08, 0.27, 0.53])
    a2.hist(u, bins=np.logspace(0, np.log10(u.max() + 1), 30), color=NOVA["cinza_medio"],
            edgecolor=NOVA["cinza"], linewidth=0.3)
    a2.set_xscale("log")
    a2.set_title(f"Avaliações por utilizador · Gini {ind['gini_user']:.2f}".replace(".", ","), fontsize=11)

    t = q(con, "SELECT year(epoch_ms(timestamp * 1000)) AS ano, COUNT(*) AS n FROM ratings GROUP BY ano ORDER BY ano")
    a3 = fig.add_axes([0.71, 0.08, 0.27, 0.53])
    a3.plot(t["ano"], t["n"], color=NOVA["verde_escuro"], linewidth=2)
    a3.fill_between(t["ano"], t["n"], color=NOVA["verde_claro"])
    a3.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))
    a3.set_title("Avaliações por ano", fontsize=11)
    guardar(fig, pasta, "10_painel_resumo.png", ds, figuras)


# ---------------------------------------------------------------------------
# Relatório
# ---------------------------------------------------------------------------
def escrever_relatorio(pasta: Path, ds: str, origem: dict, resumo: pd.DataFrame,
                       ind: dict, figuras: list, segundos: float) -> None:
    linhas = [f"# Análise exploratória · MovieLens {ds}", "",
              f"Gerado por `scripts/04_eda.py` em {segundos:.1f} s.", "",
              "## Fontes", ""]
    linhas += [f"- **{t}** — `{o}`" for t, o in origem.items()]
    linhas += ["", "## Indicadores-chave", "", "| Indicador | Valor |", "|---|---|"]
    linhas += [f"| {k} | {v} |" for k, v in ind.items()]
    linhas += ["", "## Estrutura e qualidade das tabelas", "",
               "| Tabela | Coluna | Linhas | Nulos | % nulos | Distintos (aprox.) |",
               "|---|---|---|---|---|---|"]
    linhas += [f"| {r.tabela} | {r.coluna} | {r.linhas} | {r.nulos} | {r.pct_nulos} | {r.distintos_aprox} |"
               for r in resumo.itertuples()]
    linhas += ["", "## Figuras", ""]
    linhas += [f"![{f}]({f})" for f in figuras]
    (pasta / "eda_relatorio.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="EDA estatística e gráfica do MovieLens (paleta NOVA IMS)")
    ap.add_argument("--dataset", default="small", help="small | 1m | 32m")
    ap.add_argument("--fonte", default="auto", choices=["auto", "parquet", "csv"],
                    help="auto: usa Parquet se existir, senão CSV")
    ap.add_argument("--base", default=str(Path(__file__).resolve().parent.parent),
                    help="raiz do projeto (onde está a pasta data/)")
    args = ap.parse_args()

    t0 = time.perf_counter()
    base = Path(args.base).resolve()
    pasta = base / "results" / args.dataset / "eda"
    pasta.mkdir(parents=True, exist_ok=True)
    aplicar_estilo_nova()

    con, origem = ligar(base, args.dataset, args.fonte)
    print(f"[eda] dataset={args.dataset}")
    for t, o in origem.items():
        print(f"  {t:8s} {o}")

    resumo = resumo_tabelas(con, origem)
    resumo.to_csv(pasta / "eda_resumo_tabelas.csv", index=False)

    n_r, n_u, n_m = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT userId), COUNT(DISTINCT movieId) FROM ratings").fetchone()
    n_cat = con.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    ind = {"n_ratings": n_r, "n_utilizadores": n_u, "n_filmes_avaliados": n_m,
           "n_filmes_catalogo": n_cat,
           "filmes_sem_avaliacoes": n_cat - n_m,
           "esparsidade_pct": round(100 * (1 - n_r / (n_u * n_m)), 3)}

    figuras: list[str] = []
    fig_distribuicao_ratings(con, pasta, args.dataset, figuras, ind)
    fig_atividade(con, pasta, args.dataset, figuras, ind, "utilizador")
    fig_atividade(con, pasta, args.dataset, figuras, ind, "filme")
    fig_cauda_longa(con, pasta, args.dataset, figuras)
    fig_temporal(con, pasta, args.dataset, figuras, ind)
    fig_generos(con, pasta, args.dataset, figuras, ind)
    fig_ano_lancamento(con, pasta, args.dataset, figuras, ind)
    fig_matriz_genero_ano(con, pasta, args.dataset, figuras)
    if "tags" in origem:
        fig_tags(con, pasta, args.dataset, figuras, ind)
    fig_painel(con, pasta, args.dataset, figuras, ind)

    pd.DataFrame(list(ind.items()), columns=["indicador", "valor"]).to_csv(
        pasta / "eda_indicadores.csv", index=False)
    segundos = time.perf_counter() - t0
    escrever_relatorio(pasta, args.dataset, origem, resumo, ind, figuras, segundos)

    print(f"  {n_r:,} avaliações · {n_u:,} utilizadores · {n_m:,} filmes avaliados".replace(",", " "))
    print(f"  esparsidade {ind['esparsidade_pct']}% · média {ind['rating_media']} · Gini utilizadores {ind['gini_user']}")
    print(f"  {len(figuras)} figuras em {pasta}")
    print(f"[eda] {segundos:.1f} s")


if __name__ == "__main__":
    main()
