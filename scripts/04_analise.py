"""
04_analise.py - Passo analise do pipeline: análise dos dados do MovieLens.

Objetivo:
    Responder à pergunta "o que nos dizem os dados", em três partes:
      1. Análise exploratória (EDA): 
        (1.1) indicadores;
        (1.2) qualidade das tabelas
        (1.3) 10 figuras sobre a distribuição das notas, a atividade dos utilizadores, a popularidade dos filmes, o
         tempo, os géneros e as tags.
      2. Análises de sql/analise/ - 16 queries (qualidade, integridade, evolução no tempo, filmes, uso da escala e deteção de utilizadores suspeitos), com verificações.
      3. Coordenação entre contas (identificação de bots ou atividades suspetas na nos ratings): 
        (3.1) procura grupos de contas que dão a mesma nota extrema ao mesmo filme na mesma hora e compara-os com uma linha de base em que os timestamps são baralhados dentro de cada filme.
      4. Todas as agregações são feitas no DuckDB e só os resultados agregados passam para Python, por isso o mesmo script corre no small, no 1M e no 32M sem carregar os dados em memória.

    Verificações que fazem o script falhar (parte 2):
    - qualidade: 0 linhas com nulos e 0 valores fora da escala (no 1M, também só inteiros 1-5);
    - integridade: 0 ids de filmes repetidos e 0 avaliações sem filme;
    - linhas, utilizadores, filmes avaliados e média global iguais aos da parte 1;
    - a soma das avaliações por ano (anual) igual ao total de linhas;
    - no small, a classificação dos 5 utilizadores de referência da deteção de bots.

Entradas:
    data/<dataset>/parquet/<tabela>.parquet   Parquet sem partição (do 02_to_parquet.py)
    data/<dataset>/csv/<tabela>.csv           com --fonte csv
    sql/analise/*.sql                         queries da parte 2 (${ratings}, ${movies}, ${flag_bots})
    sql/athena/analise/*.sql                  versões Athena (só com --emular-athena)

Saídas:
    results/<dataset>/eda/
        01_...png a 10_...png       figuras (a 09, das tags, só existe se houver tags)
        eda_resumo_tabelas.csv      linhas, nulos e valores distintos de cada coluna
        eda_indicadores.csv         indicadores-chave do dataset
        eda_relatorio.md            relatório com indicadores, tabelas e figuras
    results/<dataset>/analises/
        <query>.csv                 resultado de cada query
        10_flag_bots_referencia.csv só no small: os 5 utilizadores de referência
        analises_resumo.csv         n.º de linhas e tempo de cada query
        analises_relatorio.md       fontes, verificações e resumo
        athena_emulado/             com --emular-athena: versões Athena emuladas e comparação
    results/<dataset>/bots_coordenacao/  (só com --coordenacao)
        rajadas.csv, rajadas_por_ano.csv, linha_base.csv, teste.csv,
        top10_rajadas.csv, top10_contas.csv, verificacao_permutacao.csv
        coordenacao_relatorio.md

Notas:
    - As ligações ao DuckDB ficam em UTC; os anos, as horas e os dias vêm de epoch_ms (sem fuso), por isso nenhum resultado depende da máquina;
    - ${flag_bots} é a tabela por utilizador de 10_flag_bots.sql. O script corre essa query primeiro e guarda-a numa tabela temporária; no Athena é um CTAS em Parquet;
    - A emulação do Athena valida a lógica e os resultados das versões Athena (com divisão inteira entre inteiros, como no Trino, e macros para from_unixtime, date_format, sequence e approx_percentile). Não valida a sintaxe do Trino: isso só na AWS;
    - Coordenação: a permutação ordena as avaliações de cada filme por hash(userId, movieId, semente), com uma semente por repetição (1..R), e dá-lhes os timestamps desse filme por ordem. É reprodutível com várias threads. Usa memory_limit (--memoria) e uma pasta temporária em data/<dataset>/duckdb_tmp/, apagada no fim.
"""
import argparse
import math
import re
import shutil
import time
from pathlib import Path
from string import Template

import duckdb
import matplotlib

# O backend "Agg" desenha as figuras diretamente em ficheiro, sem abrir janelas.
# Tem de ser escolhido antes de importar o pyplot.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from common import DATASETS, ROOT, SCHEMAS, duckdb_columns, load_config  # noqa: E402


# ===========================================================================
# Parte 1: análise exploratória (EDA)
# ===========================================================================

# ---------------------------------------------------------------------------
# PARTE 1.1 Identidade visual NOVA IMS - Slides utilizados noutros projetos de grupo
# ---------------------------------------------------------------------------
NOVA = {
    "verde": "#BED62F",         # verde-lima (destaque principal)
    "verde_escuro": "#8A9C1F",  # verde para linhas e texto sobre branco
    "verde_claro": "#E4EEA6",   # fundos e áreas
    "cinza": "#5B6062",         # cinzento dos cabeçalhos 
    "cinza_escuro": "#2E3133",  # texto principal
    "cinza_medio": "#9EA3A5",   # elementos secundários
    "cinza_claro": "#E3E5E6",   # grelhas e fundos
    "branco": "#FFFFFF",
}
# Ordem das cores quando um gráfico tem várias séries - bloco de código usado noutro projeto com EDA
PALETA_CATEGORICA = [NOVA["verde"], NOVA["cinza"], NOVA["verde_escuro"],
                     NOVA["cinza_medio"], NOVA["verde_claro"], NOVA["cinza_escuro"]]
# Escala de cor contínua (branco  a verde escuro) para o heatmap
CMAP_NOVA = LinearSegmentedColormap.from_list(
    "nova", [NOVA["branco"], NOVA["verde_claro"], NOVA["verde"], NOVA["verde_escuro"]])


def aplicar_estilo_nova():
    """Define o estilo de todas as figuras (fontes, cores, grelha), coerente com os slides NOVA IMS."""
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


def rodape(fig, dataset):
    """Escreve no canto inferior esquerdo da figura a identificação do projeto e do dataset."""
    fig.text(0.01, 0.005, f"BDF 2026 · NOVA IMS · MovieLens {dataset}",
             fontsize=8, color=NOVA["cinza_medio"], ha="left", va="bottom")


def fmt_milhares(x, _pos=None):
    """Formata valores dos eixos em português abreviado: 1,5 M, 25 mil, 300."""
    # NOTA 1:O matplotlib chama esta função para cada marca do eixo com (valor, posição);
    # NOTa 2: a posição não é usada, mas o parâmetro _pos tem de existir.
    if abs(x) >= 1e6:
        return f"{x/1e6:.1f} M".replace(".", ",")
    if abs(x) >= 1e3:
        return f"{x/1e3:.0f} mil"
    return f"{x:.0f}"


def num(x, casas=0):
    """Formato numérico português: espaço nos milhares, vírgula decimal (ex.: 100 836 ou 3,50)."""
    # O Python escreve 100,836.50; trocamos a vírgula por espaço e o ponto por vírgula
    s = f"{x:,.{casas}f}"
    return s.replace(",", " ").replace(".", ",")


# ---------------------------------------------------------------------------
# PARTE 1.2 Ligação aos dados
# ---------------------------------------------------------------------------
TABELAS = ["ratings", "movies", "tags", "links"]


def localizar(base, dataset, tabela, fonte):
    """Devolve (caminho, tipo) do ficheiro de uma tabela, ou None se não existir.

    Prefere o Parquet sem partição; usa o CSV se não houver Parquet (ou se fonte='csv').
    """
    pasta_pq = base / "data" / dataset / "parquet"
    pasta_csv = base / "data" / dataset / "csv"

    # Lista de candidatos por ordem de preferência; fica o primeiro que existir
    candidatos = []
    if fonte in ("auto", "parquet"):
        candidatos.append((pasta_pq / f"{tabela}.parquet", "parquet"))
        # Alternativa para nomes diferentes (ex.: ratings_v2.parquet). Só ficheiros - a pasta ratings_by_year/ (Parquet particionado) não é considerada.
        for p in sorted(pasta_pq.glob(f"{tabela}*.parquet")):
            if p.is_file():
                candidatos.append((p, "parquet"))
    if fonte in ("auto", "csv"):
        candidatos.append((pasta_csv / f"{tabela}.csv", "csv"))

    for caminho, tipo in candidatos:
        if caminho.exists() and caminho.is_file():
            return str(caminho), tipo
    return None


def ligar_eda(base, dataset, fonte):
    """Cria uma ligação DuckDB com uma view por tabela encontrada. Devolve (ligação, origem)."""
    con = duckdb.connect()
    # Fuso fixo em UTC: funções como to_timestamp devolvem TIMESTAMP WITH TIME ZONE e o anoou o mês dependeriam do fuso da máquina. Este script usa epoch_ms (sem fuso), mas assim nenhuma query futura fica dependente do sítio onde corre.
    con.execute("SET TimeZone = 'UTC'")
    origem = {}
    for t in TABELAS:
        loc = localizar(base, dataset, t, fonte)
        if loc is None:
            continue   # ex.: o 1M não tem tags nem links
        caminho, tipo = loc

        # Uma VIEW não copia dados: guarda só a query. Cada vez que se consulta "ratings",
        # o DuckDB lê o ficheiro e, no Parquet, só as colunas que a query usa.
        if tipo == "parquet":
            leitor = "read_parquet"
        else:
            leitor = "read_csv_auto"
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM {leitor}('{caminho}')")

        # Caminho relativo à raiz do projeto: o relatório é versionado e não deve expor pastas locais
        origem[t] = f"{tipo}: {Path(caminho).relative_to(base).as_posix()}"

    if "ratings" not in origem or "movies" not in origem:
        raise SystemExit(
            f"Não encontrei ratings e movies em data/{dataset}/parquet nem data/{dataset}/csv. "
            "Corre primeiro a ingestão e a conversão para Parquet.")
    return con, origem


def q(con, sql):
    """Corre uma query no DuckDB e devolve o resultado como DataFrame do pandas."""
    return con.execute(sql).df()


# ---------------------------------------------------------------------------
# PARTE 1.3 Estatística descritiva
# ---------------------------------------------------------------------------
def resumo_tabelas(con, origem):
    """Para cada coluna de cada tabela: n.º de linhas, nulos, % de nulos e valores distintos."""
    linhas = []
    for t in origem:
        cols = q(con, f"DESCRIBE {t}")["column_name"].tolist()
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        for c in cols:
            # COUNT(coluna) não conta nulos, por isso COUNT(*) - COUNT(coluna) = n.º de nulos.
            # approx_count_distinct é uma estimativa (HyperLogLog): muito mais rápida do que
            # COUNT(DISTINCT ...) no 32M, com erro de poucos por cento.
            nulos, distintos = con.execute(
                f'SELECT COUNT(*) - COUNT("{c}"), approx_count_distinct("{c}") FROM {t}'
            ).fetchone()
            if n:
                pct_nulos = round(100 * nulos / n, 3)
            else:
                pct_nulos = 0
            linhas.append({"tabela": t, "coluna": c, "linhas": n, "nulos": nulos,
                           "pct_nulos": pct_nulos, "distintos_aprox": distintos})
    return pd.DataFrame(linhas)


def gini(valores):
    """Coeficiente de Gini: 0 = atividade igual para todos, perto de 1 = concentrada em poucos."""
    v = np.sort(np.asarray(valores, dtype=float))
    n = v.size
    if n == 0 or v.sum() == 0:
        return float("nan")
    # Fórmula a partir das somas acumuladas dos valores ordenados (área sob a curva de Lorenz)
    cum = np.cumsum(v)
    return float((n + 1 - 2 * (cum.sum() / cum[-1])) / n)


# ---------------------------------------------------------------------------
# PARTE 1.4 Figuras
#
# Cada função faz uma query agregada, desenha uma figura e acrescenta o nome do ficheiro à lista "figuras". As que calculam indicadores guardam-nos em "ind".
# ---------------------------------------------------------------------------
def guardar(fig, pasta, nome, dataset, figuras):
    """Acrescenta o rodapé, grava a figura em PNG, fecha-a e regista o nome do ficheiro."""
    rodape(fig, dataset)
    caminho = pasta / nome
    fig.savefig(caminho)
    plt.close(fig)   # liberta a memória da figura
    figuras.append(nome)


def fig_distribuicao_ratings(con, pasta, ds, figuras, ind):
    """Figura 01: Quantas avaliações há de cada valor de avaliação(0,5 a 5 estrelas) e estatísticas do rating."""
    df = q(con, "SELECT rating, COUNT(*) AS n FROM ratings GROUP BY rating ORDER BY rating")
    est = con.execute("""SELECT AVG(rating), MEDIAN(rating), STDDEV(rating),
                                MODE(rating) FROM ratings""").fetchone()
    media, mediana, desvio, moda = est
    ind.update({"rating_media": round(media, 3), "rating_mediana": mediana,
                "rating_desvio_padrao": round(desvio, 3), "rating_moda": moda})

    fig, ax = plt.subplots(figsize=(9, 4.5))
    # A barra do valor mais frequente (moda) fica a verde; as restantes a cinzento
    cores = []
    for r in df["rating"]:
        if r == moda:
            cores.append(NOVA["verde"])
        else:
            cores.append(NOVA["cinza_medio"])
    ax.bar(df["rating"].astype(str), df["n"], color=cores, edgecolor=NOVA["cinza"], linewidth=0.4)

    # Percentagem por cima de cada barra
    total = df["n"].sum()
    for i, (r, n) in enumerate(zip(df["rating"], df["n"])):
        ax.text(i, n, f"{100*n/total:.1f}%".replace(".", ","), ha="center", va="bottom",
                fontsize=8, color=NOVA["cinza"])

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))
    ax.set_title("Distribuição das avaliações")
    ax.set_xlabel("Avaliação (estrelas)")
    ax.set_ylabel("N.º de avaliações")
    ax.set_ylim(0, df["n"].max() * 1.18)   # espaço livre por cima para as percentagens
    resumo = f"média {media:.2f}  ·  mediana {mediana:.1f}  ·  desvio-padrão {desvio:.2f}"
    ax.text(0.01, 0.97, resumo.replace(".", ","),
            transform=ax.transAxes, ha="left", va="top", fontsize=9, color=NOVA["cinza_escuro"])
    guardar(fig, pasta, "01_distribuicao_ratings.png", ds, figuras)


def fig_atividade(con, pasta, ds, figuras, ind, entidade):
    """Figuras 02 (entidade='utilizador') e 03 (entidade='filme'): histograma e curva de Lorenz."""
    # A mesma função serve para utilizadores e filmes; só mudam a coluna e os textos
    if entidade == "utilizador":
        col = "userId"
        sufixo = "user"
        rotulo_y = "N.º de utilizadores"
        rotulo_lorenz = "% acumulada de utilizadores (do menos ao mais ativo)"
        quem = "utilizadores mais ativos"
        nome = "02_atividade_utilizadores.png"
    else:
        col = "movieId"
        sufixo = "movie"
        rotulo_y = "N.º de filmes"
        rotulo_lorenz = "% acumulada de filmes (do menos ao mais avaliado)"
        quem = "filmes mais avaliados"
        nome = "03_popularidade_filmes.png"

    # Só o n.º de avaliações por utilizador/filme vem para Python (no 32M: ~200 mil valores)
    cont = q(con, f"SELECT {col}, COUNT(*) AS n FROM ratings GROUP BY {col}")["n"].to_numpy()
    g = gini(cont)
    qs = np.percentile(cont, [25, 50, 75, 90, 99])   # qs[1] = mediana, qs[3] = percentil 90
    ind.update({f"ratings_por_{sufixo}_min": int(cont.min()),
                f"ratings_por_{sufixo}_mediana": float(qs[1]),
                f"ratings_por_{sufixo}_media": round(float(cont.mean()), 1),
                f"ratings_por_{sufixo}_p90": float(qs[3]),
                f"ratings_por_{sufixo}_max": int(cont.max()),
                f"gini_{sufixo}": round(g, 3)})

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Esquerda: histograma com escala logarítmica, porque a distribuição tem cauda muito longa (muitos com poucas avaliações, poucos com milhares)
    bins = np.logspace(0, np.log10(cont.max() + 1), 40)
    a1.hist(cont, bins=bins, color=NOVA["verde"], edgecolor=NOVA["cinza"], linewidth=0.4)
    a1.set_xscale("log")
    a1.axvline(qs[1], color=NOVA["cinza_escuro"], linestyle="--", linewidth=1)
    a1.text(qs[1], a1.get_ylim()[1] * 0.95, f"  mediana = {qs[1]:.0f}",
            color=NOVA["cinza_escuro"], fontsize=9, va="top")
    a1.set_title(f"Avaliações por {entidade} (escala log)")
    a1.set_xlabel(f"N.º de avaliações por {entidade}")
    a1.set_ylabel(rotulo_y)

    # Direita: curva de Lorenz - representar a distribuição relativa de uma variável. Ordena do menos ao mais ativo e acumula a % de avaliações.
    # Quanto mais a curva se afasta da diagonal, mais concentrada é a atividade.
    v = np.sort(cont)
    x = np.linspace(0, 1, v.size + 1)
    y = np.concatenate([[0], np.cumsum(v) / v.sum()])
    a2.fill_between(x, y, x, color=NOVA["verde_claro"], alpha=0.8)
    a2.plot(x, y, color=NOVA["verde_escuro"], linewidth=2, label="Curva de Lorenz")
    a2.plot([0, 1], [0, 1], color=NOVA["cinza_medio"], linestyle="--", linewidth=1,
            label="Igualdade perfeita")
    # Parte das avaliações feita pelos 10% mais ativos = 1 - (valor da curva aos 90%)
    top10 = 1 - np.interp(0.9, x, y)
    a2.set_title(f"Concentração da atividade · Gini = {g:.2f}".replace(".", ","))
    a2.set_xlabel(rotulo_lorenz)
    a2.set_ylabel("% acumulada de avaliações")
    a2.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    a2.yaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    a2.text(0.04, 0.92, f"Os 10% {quem} concentram\n{100*top10:.0f}% das avaliações",
            transform=a2.transAxes, fontsize=9, color=NOVA["cinza_escuro"], va="top")
    a2.legend(loc="lower right", fontsize=8)
    ind[f"pct_ratings_top10pct_{sufixo}"] = round(100 * top10, 1)

    fig.tight_layout()
    guardar(fig, pasta, nome, ds, figuras)


def fig_cauda_longa(con, pasta, ds, figuras):
    """Figura 04: N.º de avaliações de cada filme - do mais ao menos popular (escala log-log)."""
    df = q(con, "SELECT COUNT(*) AS n FROM ratings GROUP BY movieId ORDER BY n DESC")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    rank = np.arange(1, len(df) + 1)   # posição de cada filme no ranking: 1, 2, 3, ...
    ax.loglog(rank, df["n"], color=NOVA["verde_escuro"], linewidth=2)
    ax.fill_between(rank, df["n"], 1, color=NOVA["verde_claro"], alpha=0.6)
    ax.set_title("Cauda longa: avaliações por filme ordenadas por popularidade")
    ax.set_xlabel("Posição do filme no ranking (escala log)")
    ax.set_ylabel("N.º de avaliações (escala log)")
    unicos = int((df["n"] == 1).sum())   # filmes com uma única avaliação
    ax.text(0.98, 0.95, f"{num(unicos)} filmes ({100*unicos/len(df):.0f}%) têm 1 só avaliação",
            transform=ax.transAxes, ha="right", va="top", fontsize=9, color=NOVA["cinza_escuro"])
    guardar(fig, pasta, "04_cauda_longa_filmes.png", ds, figuras)


# Nas figuras seguintes o ano é calculado em UTC (epoch_ms devolve TIMESTAMP sem fuso horário), como em 02_to_parquet.py, para coincidir com as partições year=AAAA.
def fig_temporal(con, pasta, ds, figuras, ind):
    """Figura 05: N.º de avaliações (barras) e avaliação média (linha) por ano"""
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

    # Segundo eixo vertical (à direita) para a média, que tem outra escala (2,5 a 4,5)
    ax2 = ax.twinx()
    ax2.plot(df["ano"], df["media"], color=NOVA["cinza_escuro"], marker="o", markersize=3.5,
             linewidth=1.5, label="Avaliação média")
    ax2.set_ylabel("Avaliação média", color=NOVA["cinza_escuro"])
    ax2.set_ylim(2.5, 4.5)
    ax2.grid(False)
    ax2.spines["right"].set_visible(True)
    ax.set_title("Evolução temporal: volume e avaliação média por ano")

    # Junta as legendas dos dois eixos numa só
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    guardar(fig, pasta, "05_evolucao_temporal.png", ds, figuras)


def fig_generos(con, pasta, ds, figuras, ind):
    """Figura 06: n.º de filmes e avaliação média de cada género."""
    # g: uma linha por par (filme, género), separando "Action|Comedy" com string_split + unnest. r: n.º de avaliações e média de cada filme.
    # A média do género é ponderada pelo n.º de avaliações de cada filme.
    df = q(con, """
        WITH g AS (SELECT movieId, unnest(string_split(genres, '|')) AS genero FROM movies),
             r AS (SELECT movieId, COUNT(*) AS n, AVG(rating) AS media FROM ratings GROUP BY movieId)
        SELECT genero, COUNT(DISTINCT g.movieId) AS filmes,
               SUM(r.n) AS avaliacoes, SUM(r.media * r.n) / SUM(r.n) AS media
        FROM g LEFT JOIN r USING (movieId)
        GROUP BY genero ORDER BY filmes""")
    # Sem os filmes sem género
    df = df[df["genero"] != "(no genres listed)"]
    ind["n_generos"] = len(df)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 6.5), sharey=True)
    a1.barh(df["genero"], df["filmes"], color=NOVA["verde"], edgecolor=NOVA["cinza"], linewidth=0.3)
    a1.set_title("Filmes por género")
    a1.set_xlabel("N.º de filmes (um filme pode ter vários géneros)")
    a1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))

    # Géneros acima da média global a verde escuro, abaixo a cinzento
    media_global = ind.get("rating_media", df["media"].mean())
    cores = []
    for m in df["media"]:
        if m >= media_global:
            cores.append(NOVA["verde_escuro"])
        else:
            cores.append(NOVA["cinza_medio"])
    a2.barh(df["genero"], df["media"], color=cores)
    a2.axvline(media_global, color=NOVA["cinza_escuro"], linestyle="--", linewidth=1)
    a2.set_xlim(df["media"].min() - 0.2, df["media"].max() + 0.1)
    a2.set_title("Avaliação média por género")
    a2.set_xlabel(f"Avaliação média (tracejado = média global {media_global:.2f})".replace(".", ","))
    fig.tight_layout()
    guardar(fig, pasta, "06_generos.png", ds, figuras)


def fig_ano_lancamento(con, pasta, ds, figuras, ind):
    """Figura 07: N.º de filmes por ano de lançamento, extraído do título'."""
    # A expressão regular apanha 4 dígitos entre parênteses no fim do título.
    # TRY_CAST devolve NULL (em vez de dar erro) quando o título não tem ano.
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
    """Figura 08: Heatmap da avaliação média por género (linhas) e ano da avaliação (colunas)."""
    df = q(con, """
        WITH g AS (SELECT movieId, unnest(string_split(genres, '|')) AS genero FROM movies)
        SELECT genero, year(epoch_ms(r.timestamp * 1000)) AS ano, AVG(r.rating) AS media
        FROM ratings r JOIN g USING (movieId)
        WHERE genero <> '(no genres listed)'
        GROUP BY genero, ano""")
    # pivot passa do formato longo (genero, ano, media) para uma tabela género x ano
    pv = df.pivot(index="genero", columns="ano", values="media").sort_index()

    fig, ax = plt.subplots(figsize=(13, 6.5))
    im = ax.imshow(pv.values, aspect="auto", cmap=CMAP_NOVA, vmin=2.8, vmax=4.3)
    ax.set_yticks(range(len(pv.index)), pv.index)
    # Mostra no máximo 15 anos no eixo horizontal, para os rótulos não se sobreporem
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
    """Figura 09: as 20 tags mais usadas e quantos utilizadores usaram cada uma."""
    # lower(trim(...)) junta variantes como "Funny" e "funny "
    df = q(con, """SELECT lower(trim(tag)) AS tag, COUNT(*) AS n, COUNT(DISTINCT userId) AS users
                   FROM tags GROUP BY 1 ORDER BY n DESC LIMIT 20""")
    tot = con.execute("SELECT COUNT(*), COUNT(DISTINCT userId), COUNT(DISTINCT movieId) FROM tags").fetchone()
    ind.update({"tags_total": tot[0], "tags_utilizadores": tot[1], "tags_filmes": tot[2]})

    # Inverte a ordem para a tag mais usada ficar no topo do gráfico de barras horizontais
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


def esconder_eixos(ax):
    """Tira marcas, grelha e contornos a um eixo, para o usar como caixa de texto ou fundo."""
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)


def fig_painel(con, pasta, ds, figuras, ind):
    """Figura 10: painel-resumo de uma página (indicadores + 3 gráficos), pensado para um slide."""
    fig = plt.figure(figsize=(13, 7.3))
    fig.patch.set_facecolor(NOVA["branco"])

    # Faixa de título no topo. add_axes([esquerda, baixo, largura, altura]) em fração da figura.
    faixa = fig.add_axes([0, 0.9, 1, 0.1])
    faixa.set_facecolor(NOVA["cinza"])
    esconder_eixos(faixa)
    faixa.text(0.015, 0.5, f"MovieLens {ds} · retrato do dataset", color=NOVA["branco"],
               fontsize=18, fontweight="bold", va="center")
    faixa.add_patch(plt.Rectangle((0, 0), 1, 0.08, color=NOVA["verde"], transform=faixa.transAxes))

    # Seis cartões com os indicadores principais, lado a lado
    cartoes = [("Avaliações", num(ind["n_ratings"])),
               ("Utilizadores", num(ind["n_utilizadores"])),
               ("Filmes avaliados", num(ind["n_filmes_avaliados"])),
               ("Esparsidade", f"{ind['esparsidade_pct']:.2f}%".replace(".", ",")),
               ("Avaliação média", f"{ind['rating_media']:.2f}".replace(".", ",")),
               ("Período", f"{ind['ano_primeiro_rating']}–{ind['ano_ultimo_rating']}")]
    for i, (rot, val) in enumerate(cartoes):
        ax = fig.add_axes([0.015 + i * 0.163, 0.72, 0.15, 0.14])
        ax.set_facecolor(NOVA["verde_claro"])
        esconder_eixos(ax)
        ax.axvline(0, color=NOVA["verde"], linewidth=8)
        ax.text(0.1, 0.62, val, fontsize=17, fontweight="bold", color=NOVA["cinza_escuro"],
                transform=ax.transAxes, va="center")
        ax.text(0.1, 0.25, rot, fontsize=9, color=NOVA["cinza"], transform=ax.transAxes, va="center")

    # Gráfico 1: distribuição das avaliações
    r = q(con, "SELECT rating, COUNT(*) AS n FROM ratings GROUP BY rating ORDER BY rating")
    a1 = fig.add_axes([0.05, 0.08, 0.27, 0.53])
    a1.bar(r["rating"].astype(str), r["n"], color=NOVA["verde"], edgecolor=NOVA["cinza"], linewidth=0.3)
    a1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))
    a1.set_title("Distribuição das avaliações", fontsize=11)
    a1.tick_params(axis="x", labelsize=7)

    # Gráfico 2: avaliações por utilizador (escala log)
    u = q(con, "SELECT COUNT(*) AS n FROM ratings GROUP BY userId")["n"].to_numpy()
    a2 = fig.add_axes([0.38, 0.08, 0.27, 0.53])
    a2.hist(u, bins=np.logspace(0, np.log10(u.max() + 1), 30), color=NOVA["cinza_medio"],
            edgecolor=NOVA["cinza"], linewidth=0.3)
    a2.set_xscale("log")
    a2.set_title(f"Avaliações por utilizador · Gini {ind['gini_user']:.2f}".replace(".", ","), fontsize=11)

    # Gráfico 3: avaliações por ano
    t = q(con, "SELECT year(epoch_ms(timestamp * 1000)) AS ano, COUNT(*) AS n FROM ratings GROUP BY ano ORDER BY ano")
    a3 = fig.add_axes([0.71, 0.08, 0.27, 0.53])
    a3.plot(t["ano"], t["n"], color=NOVA["verde_escuro"], linewidth=2)
    a3.fill_between(t["ano"], t["n"], color=NOVA["verde_claro"])
    a3.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_milhares))
    a3.set_title("Avaliações por ano", fontsize=11)
    guardar(fig, pasta, "10_painel_resumo.png", ds, figuras)


# ---------------------------------------------------------------------------
# 1.5 Relatório
# ---------------------------------------------------------------------------
def relatorio_eda(pasta, ds, origem, resumo, ind, figuras, segundos):
    """Escreve eda_relatorio.md com as fontes, os indicadores, a qualidade das tabelas e as figuras."""
    linhas = [f"# Análise exploratória · MovieLens {ds}", "",
              f"Gerado por `scripts/04_analise.py` em {segundos:.1f} s.", "",
              "## Fontes", ""]
    for t, o in origem.items():
        linhas.append(f"- **{t}** — `{o}`")

    linhas += ["", "## Indicadores-chave", "", "| Indicador | Valor |", "|---|---|"]
    for k, v in ind.items():
        linhas.append(f"| {k} | {v} |")

    linhas += ["", "## Estrutura e qualidade das tabelas", "",
               "| Tabela | Coluna | Linhas | Nulos | % nulos | Distintos (aprox.) |",
               "|---|---|---|---|---|---|"]
    # itertuples percorre o DataFrame linha a linha; cada linha tem as colunas como atributos
    for r in resumo.itertuples():
        linhas.append(f"| {r.tabela} | {r.coluna} | {r.linhas} | {r.nulos} | {r.pct_nulos} | {r.distintos_aprox} |")

    linhas += ["", "## Figuras", ""]
    for f in figuras:
        linhas.append(f"![{f}]({f})")

    (pasta / "eda_relatorio.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def correr_eda(ds, fonte, resultados):
    """Liga aos dados, calcula os indicadores, gera as figuras e o relatório da EDA."""
    t0 = time.perf_counter()
    pasta = resultados / ds / "eda"
    pasta.mkdir(parents=True, exist_ok=True)
    aplicar_estilo_nova()

    con, origem = ligar_eda(ROOT, ds, fonte)
    print(f"[eda] dataset={ds}")
    for t, o in origem.items():
        print(f"  {t:8s} {o}")

    # 1. Qualidade das tabelas (nulos e valores distintos por coluna)
    resumo = resumo_tabelas(con, origem)
    resumo.to_csv(pasta / "eda_resumo_tabelas.csv", index=False)

    # 2. Indicadores gerais. Esparsidade = % de pares (utilizador, filme) sem avaliação:
    #    mostra quão "vazia" é a matriz utilizadores x filmes usada em recomendação.
    n_r, n_u, n_m = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT userId), COUNT(DISTINCT movieId) FROM ratings").fetchone()
    n_cat = con.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    ind = {"n_ratings": n_r, "n_utilizadores": n_u, "n_filmes_avaliados": n_m,
           "n_filmes_catalogo": n_cat,
           "filmes_sem_avaliacoes": n_cat - n_m,
           "esparsidade_pct": round(100 * (1 - n_r / (n_u * n_m)), 3)}

    # 3. Figuras. A ordem importa: o painel (10) e os géneros (06) usam indicadores
    #    calculados pelas figuras anteriores (média, Gini, anos).
    figuras = []
    fig_distribuicao_ratings(con, pasta, ds, figuras, ind)
    fig_atividade(con, pasta, ds, figuras, ind, "utilizador")
    fig_atividade(con, pasta, ds, figuras, ind, "filme")
    fig_cauda_longa(con, pasta, ds, figuras)
    fig_temporal(con, pasta, ds, figuras, ind)
    fig_generos(con, pasta, ds, figuras, ind)
    fig_ano_lancamento(con, pasta, ds, figuras, ind)
    fig_matriz_genero_ano(con, pasta, ds, figuras)
    if "tags" in origem:
        fig_tags(con, pasta, ds, figuras, ind)
    fig_painel(con, pasta, ds, figuras, ind)

    # 4. Indicadores e relatório
    pd.DataFrame(list(ind.items()), columns=["indicador", "valor"]).to_csv(
        pasta / "eda_indicadores.csv", index=False)
    segundos = time.perf_counter() - t0
    relatorio_eda(pasta, ds, origem, resumo, ind, figuras, segundos)

    print(f"  {n_r:,} avaliações · {n_u:,} utilizadores · {n_m:,} filmes avaliados".replace(",", " "))
    print(f"  esparsidade {ind['esparsidade_pct']}% · média {ind['rating_media']} · Gini utilizadores {ind['gini_user']}")
    print(f"  {len(figuras)} figuras em {pasta}")
    # Sem o arranque do Python nem os imports; o run_pipeline.py mostra o tempo total
    print(f"[eda] tempo interno do script (sem arranque nem imports): {segundos:.2f} s")

# ===========================================================================
# Parte 2: análises de sql/analise/
# ===========================================================================

PASTA_SQL = ROOT / 'sql' / 'analise'
PASTA_SQL_ATHENA = ROOT / 'sql' / 'athena' / 'analise'

# Queries cujo resultado outras queries usam: nome do ficheiro -> nome da tabela temporária.
# 10_flag_bots corre primeiro (a ordem alfabética já o põe à frente, por começar por um dígito).
MATERIALIZAR = {'10_flag_bots': 'flag_bots'}
DEPENDENCIAS = {'eventos': ['10_flag_bots'], '10_flag_bots_calibracao': ['10_flag_bots']}


# ---------------------------------------------------------------------------
# PARTE 2.1Ligação aos dados
# ---------------------------------------------------------------------------
def leitor(cfg, tabela, fonte):
    """Texto SQL que lê uma tabela do dataset no formato pedido (Parquet ou CSV)."""
    if fonte == 'parquet':
        caminho = cfg['paths']['parquet'] / f'{tabela}.parquet'
        texto = f"read_parquet('{caminho.as_posix()}')"
    else:
        caminho = cfg['paths']['csv'] / f'{tabela}.csv'
        # Tipos fixos (common.SCHEMAS) e as mesmas opções do 02_to_parquet.py: os títulos podem
        # ter aspas escritas como "" (ex.: "11'09""01 - September 11 (2002)")
        texto = (f"read_csv('{caminho.as_posix()}', header = true, delim = ',', quote = '\"', "
                 f"escape = '\"', columns = {duckdb_columns(SCHEMAS[tabela])})")
    if not caminho.exists():
        raise SystemExit(f'Não encontrei {caminho.relative_to(ROOT)}. Corre primeiro a ingestão '
                         'e a conversão para Parquet (run_pipeline.py --steps ingest parquet).')
    return texto, f'{fonte}: {caminho.relative_to(ROOT).as_posix()}'


def ligar_analises(cfg, fonte):
    """Ligação DuckDB em UTC com as views ratings_base (sem year) e movies. Devolve (ligação, origem)."""
    con = duckdb.connect()
    # Fuso fixo: to_timestamp e afins devolvem TIMESTAMP WITH TIME ZONE, e o ano ou o mês
    # dependeriam do fuso da máquina. As queries usam epoch_ms/year, mas assim fica garantido.
    con.execute("SET TimeZone = 'UTC'")
    origem = {}
    for tabela, view in (('ratings', 'ratings_base'), ('movies', 'movies')):
        texto, origem[tabela] = leitor(cfg, tabela, fonte)
        con.execute(f'CREATE VIEW {view} AS SELECT * FROM {texto}')
    return con, origem


# ${ratings} tem sempre a coluna year (em UTC), como no 03_benchmark.py.
FONTES_DUCKDB = {
    'ratings': '(SELECT *, year(epoch_ms(timestamp * 1000)) AS year FROM ratings_base)',
    'movies': 'movies',
    'flag_bots': 'flag_bots',
}

# Na emulação do Athena, ${ratings} é escrito como no 08_athena_benchmark.py para as tabelas sem
# partição: year a partir de from_unixtime (UTC no Trino; aqui, a macro abaixo).
FONTES_ATHENA = {
    'ratings': '(SELECT x.*, year(from_unixtime(x."timestamp")) AS year FROM ratings_base AS x)',
    'movies': 'movies',
    'flag_bots': 'flag_bots',
}

MACROS_ATHENA = [
    # Trino: from_unixtime(bigint) devolve timestamp em UTC. make_timestamp (microssegundos)
    # devolve TIMESTAMP sem fuso, por isso também não depende do fuso da sessão.
    'CREATE OR REPLACE MACRO from_unixtime(x) AS make_timestamp(CAST(x AS BIGINT) * 1000000)',
    'CREATE OR REPLACE MACRO date_format(t, f) AS strftime(t, f)',
    'CREATE OR REPLACE MACRO sequence(a, b) AS range(a, b + 1)',
    # approx_percentile do Trino é aproximado; aqui usa-se o quantil exato (diferenças pequenas)
    'CREATE OR REPLACE MACRO approx_percentile(x, p) AS quantile_cont(x, p)',
]


# Padrões que a emulação não reproduz: no Trino, uma divisão com um literal decimal
# (100.0 * x / y, x * 1.0 / y) fica com a escala do literal (1 casa decimal), enquanto no DuckDB
# dá um número real. Nas versões Athena usa-se CAST(... AS double); esta verificação apanha
# esquecimentos. Apanha "100.0 *" (literal antes da conta) e "* 1.0" (literal depois).
DECIMAL_EM_CONTA = re.compile(r'(\d+\.\d+\s*[*/])|([*/]\s*\d+\.\d+)')


def avisos_trino(texto):
    """Linhas (sem comentários) de uma query Athena com um literal decimal numa multiplicação ou divisão."""
    avisos = []
    for linha in texto.splitlines():
        codigo = linha.split('--')[0]
        if DECIMAL_EM_CONTA.search(codigo):
            avisos.append(codigo.strip())
    return avisos


def preparar_emulacao(con):
    """Põe a ligação a comportar-se como o Trino onde isso muda resultados."""
    # No Trino, bigint / bigint é divisão inteira; no DuckDB é real. Com esta opção o DuckDB
    # faz como o Trino, e um erro desses nas versões Athena aparece na comparação.
    con.execute('SET integer_division = true')
    for m in MACROS_ATHENA:
        con.execute(m)


# ---------------------------------------------------------------------------
# PARTE 2.2 Execução das queries
# ---------------------------------------------------------------------------
def listar_queries(pasta, pedidas):
    """Ficheiros .sql de uma pasta (ordem alfabética), filtrados por --queries com as dependências."""
    # Dicionário nome -> ficheiro, ex.: {'anual': Path('sql/analise/anual.sql'), ...}
    ficheiros = {}
    for f in sorted(pasta.glob('*.sql')):
        ficheiros[f.stem] = f
    if not pedidas:
        return ficheiros   # sem --queries: corre todas

    desconhecidas = [q for q in pedidas if q not in ficheiros]
    if desconhecidas:
        raise SystemExit(f'Queries desconhecidas: {desconhecidas}. Existem: {list(ficheiros)}')
    # Juntamos às queries pedidas aquelas de que dependem (ex.: eventos precisa de 10_flag_bots)
    nomes = set(pedidas)
    for q in pedidas:
        nomes.update(DEPENDENCIAS.get(q, []))
    # Mantemos só as escolhidas, pela ordem alfabética original
    escolhidas = {}
    for nome, ficheiro in ficheiros.items():
        if nome in nomes:
            escolhidas[nome] = ficheiro
    return escolhidas


def correr(con, nome, ficheiro, fontes, destino):
    """Corre uma query, grava o resultado em CSV (COPY) e devolve (n.º de linhas, segundos)."""
    sql = Template(ficheiro.read_text(encoding='utf-8')).substitute(fontes).strip().rstrip(';')
    t0 = time.perf_counter()
    if nome in MATERIALIZAR:
        # Tabela temporária para as queries que dependem desta (ex.: ${flag_bots} em eventos)
        tabela = MATERIALIZAR[nome]
        con.execute(f'CREATE OR REPLACE TEMP TABLE {tabela} AS {sql}')
        sql = f'SELECT * FROM {tabela}'
    # COPY escreve diretamente do DuckDB para o ficheiro, sem passar o resultado pelo Python
    # (o COPY devolve o n.º de linhas escritas)
    linhas = con.execute(f"COPY ({sql}) TO '{destino.as_posix()}' (HEADER, DELIMITER ',')").fetchone()[0]
    return linhas, time.perf_counter() - t0


# ---------------------------------------------------------------------------
# PARTE 2.3 - Verificações
# ---------------------------------------------------------------------------
def ler(pasta, nome):
    """Lê o CSV de uma query, ou None se essa query não correu."""
    f = pasta / f'{nome}.csv'
    return pd.read_csv(f) if f.exists() else None


def verificar(pasta, ds):
    """Asserções sobre os resultados. Devolve uma lista de (verificação, resultado, ok)."""
    res = []
    qual = ler(pasta, 'qualidade')
    if qual is not None:
        q = qual.iloc[0]
        res.append(('qualidade: linhas com nulos = 0', int(q.linhas_com_nulos), q.linhas_com_nulos == 0))
        res.append(('qualidade: fora da escala comum = 0', int(q.fora_dominio_comum), q.fora_dominio_comum == 0))
        res.append(('qualidade: pares (utilizador, filme) repetidos = 0', int(q.pares_repetidos), q.pares_repetidos == 0))
        if ds == '1m':   # o 1M só tem estrelas inteiras de 1 a 5
            ok = q.nao_inteiros == 0 and q.inferior_a_um == 0
            res.append(('qualidade (1M): só inteiros de 1 a 5', f'{int(q.nao_inteiros)} / {int(q.inferior_a_um)}', ok))
    integ = ler(pasta, 'integridade')
    if integ is not None:
        i = integ.iloc[0]
        res.append(('integridade: ids de filmes repetidos = 0', int(i.ids_filmes_repetidos), i.ids_filmes_repetidos == 0))
        res.append(('integridade: avaliações sem filme = 0', int(i.ratings_sem_filme), i.ratings_sem_filme == 0))

    # Comparação com a parte 1 (EDA)
    f_ind = pasta.parent / 'eda' / 'eda_indicadores.csv'
    if f_ind.exists() and qual is not None:
        ind = pd.read_csv(f_ind).set_index('indicador')['valor']
        q = qual.iloc[0]
        for col, chave in (('linhas', 'n_ratings'), ('utilizadores', 'n_utilizadores'), ('filmes', 'n_filmes_avaliados')):
            res.append((f'{col} = {chave} da EDA', f'{int(q[col])} / {int(ind[chave])}', int(q[col]) == int(ind[chave])))
    pond = ler(pasta, 'ponderado')
    if f_ind.exists() and pond is not None:
        media = pond.media_global.iloc[0]
        ref = float(pd.read_csv(f_ind).set_index('indicador')['valor']['rating_media'])
        res.append(('média global = rating_media da EDA', f'{media:.3f} / {ref:.3f}', round(media, 3) == ref))
    anual = ler(pasta, 'anual')
    if anual is not None and qual is not None:
        soma = int(anual.num_ratings.sum())
        res.append(('soma de anual.num_ratings = linhas', f'{soma} / {int(qual.linhas.iloc[0])}', soma == int(qual.linhas.iloc[0])))
    return res


# Utilizadores de referência da deteção de bots no small: (classificação esperada, porquê).
REFERENCIA_BOTS = {
    'small': {
        257: ('sem sinais', '20 avaliações em 11 min no registo: não pode ser sinalizado'),
        7: ('sem sinais', 'uso normal: não pode ser sinalizado'),
        89: ('suspeito (regra B)', '518 avaliações em 23 min no registo, ~2 s cada: candidato'),
        610: ('suspeito (regra A)', '566 avaliações numa hora, ~4 s cada, ~6 meses depois do registo'),
        534: ('submissão em lote', 'muitas avaliações no mesmo segundo (2016): não é bot'),
    },
}


def inteiro(x):
    """Número sem casas decimais, ou '-' se o valor estiver em falta (NaN)."""
    if pd.isna(x):
        return '-'
    return f'{x:.0f}'


def justificar(r):
    """Texto com os números que levam à classificação de um utilizador (linha de 10_flag_bots.csv)."""
    # Uma frase por regra que o utilizador cumpre; se não cumprir nenhuma, explicamos porquê
    partes = []
    if r.regra_a:
        partes.append(f'regra A: {inteiro(r.max_eventos_10min_apos)} eventos em 10 min depois do registo '
                      f'(limiar p99,9 = {r.limiar_regra_a:.1f}), mediana de {inteiro(r.mediana_intervalo_apos_s)} s entre eventos')
    if r.regra_b:
        partes.append(f'regra B: {r.eventos_registo} eventos nas primeiras 24 h, mediana de '
                      f'{inteiro(r.mediana_intervalo_registo_s)} s entre eventos (>= 100 e <= 2 s)')
    if r.submissao_lote:
        partes.append(f'submissão em lote: até {r.max_avaliacoes_mesmo_segundo} avaliações no mesmo segundo '
                      f'({r.pct_eventos_lote:.0f}% dos eventos com 2 ou mais), primeiro dia {r.primeiro_dia}')
    if not partes:
        partes.append(f'depois do registo: máx. {inteiro(r.max_eventos_10min_apos)} eventos em 10 min (limiar '
                      f'{r.limiar_regra_a:.1f}); registo: {r.eventos_registo} eventos, mediana de '
                      f'{inteiro(r.mediana_intervalo_registo_s)} s (a regra B exige >= 100 eventos e <= 2 s); '
                      f'máx. {r.max_avaliacoes_mesmo_segundo} avaliações no mesmo segundo')
    partes.append(f'sinais complementares: {r.sinais_complementares}/3')
    return '; '.join(partes)


def referencia_bots(pasta, ds):
    """Grava 10_flag_bots_referencia.csv (só datasets com referência) e devolve as verificações."""
    flags = ler(pasta, '10_flag_bots')
    if flags is None or ds not in REFERENCIA_BOTS:
        return []
    linhas, verif = [], []
    for uid, (esperado, porque) in REFERENCIA_BOTS[ds].items():
        r = flags[flags.userId == uid].iloc[0]
        ok = r.classificacao == esperado
        linhas.append({'userId': uid, 'caso': porque, 'esperado': esperado, 'obtido': r.classificacao,
                       'ok': 'sim' if ok else 'NÃO', 'justificacao': justificar(r)})
        verif.append((f'bots: utilizador {uid} = {esperado}', r.classificacao, ok))
    pd.DataFrame(linhas).to_csv(pasta / '10_flag_bots_referencia.csv', index=False)
    return verif


def iguais(a, b, tol=1e-6):
    """Compara dois resultados pela posição das colunas (no Athena os nomes saem em minúsculas)."""
    if a.shape != b.shape:
        return False, f'formas diferentes: {a.shape} vs {b.shape}'
    for j in range(a.shape[1]):
        x, y = a.iloc[:, j], b.iloc[:, j]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            # Números: iguais a menos de uma tolerância (as somas em vírgula flutuante podem
            # diferir no último dígito). Dois valores em falta contam como iguais.
            for u, v in zip(x, y):
                if pd.isna(u) and pd.isna(v):
                    continue
                if pd.isna(u) or pd.isna(v) or not math.isclose(u, v, rel_tol=tol, abs_tol=tol):
                    return False, f'coluna {a.columns[j]}: {u} vs {v}'
        # Texto (ou tipos diferentes): compara-se o texto de cada valor
        elif not (x.astype(str).values == y.astype(str).values).all():
            return False, f'coluna {a.columns[j]} difere'
    return True, ''


# ---------------------------------------------------------------------------
def relatorio_analises(pasta, ds, origem, resumo, verif, comparacao, segundos):
    """Escreve analises_relatorio.md com as fontes, as verificações e o resumo das queries."""
    L = [f'# Análises · MovieLens {ds}', '',
         f'Gerado por `scripts/04_analise.py` em {segundos:.1f} s (sessão DuckDB em UTC).', '',
         '## Fontes', '']
    for t, o in origem.items():
        L.append(f'- **{t}** — `{o}`')
    L += ['', '## Verificações', '', '| Verificação | Valor | OK |', '|---|---|---|']
    for nome, valor, ok in verif:
        L.append(f"| {nome} | {valor} | {'sim' if ok else '**NÃO**'} |")
    L += ['', '## Queries', '', '| Query | Linhas | Segundos | CSV |', '|---|---:|---:|---|']
    for r in resumo:
        L.append(f"| {r['query']} | {r['linhas']} | {r['segundos']:.3f} | `{r['query']}.csv` |")
    flags, calib = ler(pasta, '10_flag_bots'), ler(pasta, '10_flag_bots_calibracao')
    if flags is not None and calib is not None:
        c = calib.iloc[0]
        L += ['', '## Deteção de bots (10_flag_bots)', '',
              f"- Utilizadores: {int(c.utilizadores)}; suspeitos: {int(c.suspeitos)} ({c.pct_suspeitos:.2f}%) "
              f"= regra A {int(c.regra_a)} + regra B {int(c.regra_b)} (sem repetir quem tem as duas).",
              f"- Submissão em lote (reportada à parte, não é bot): {int(c.submissao_lote)} utilizadores, "
              f"dos quais {int(c.so_submissao_lote)} sem outra classificação.",
              f"- Ritmo sustentado depois do registo (máx. de eventos em 10 min), "
              f"{int(c.utilizadores_com_atividade_apos_registo)} utilizadores: p50 {c.p50:.1f}, p90 {c.p90:.1f}, "
              f"p99 {c.p99:.1f}, p99,5 {c.p99_5:.1f}, p99,9 {c.p99_9:.1f}, máximo {c.maximo:.0f}.",
              f"- Sinalizados pela regra A com o limiar no p99 / p99,5 / p99,9: {int(c.sinalizados_a_p99)} / "
              f"{int(c.sinalizados_a_p99_5)} / {int(c.sinalizados_a_p99_9)} (a query usa o p99,9).", '']
        lote = flags[flags.submissao_lote]
        if len(lote):
            # Década do primeiro rating: '2016-03-01'[:3] = '201' -> '2010s'
            decadas =(lote.primeiro_dia.str[:3] + '0s').value_counts().sort_index()
            L.append('Submissão em lote por década do primeiro rating: '
                     + ', '.join(f'{d}: {n}' for d, n in decadas.items()) + '.')
            L.append('')
        susp = flags[flags.regra_a | flags.regra_b]
        if len(susp):
            L += ['| userId | Classificação | Justificação |', '|---|---|---|']
            for r in susp.itertuples():
                L.append(f'| {r.userId} | {r.classificacao} | {justificar(r)} |')
        ref = ler(pasta, '10_flag_bots_referencia')
        if ref is not None:
            L += ['', '### Utilizadores de referência', '',
                  '| userId | Caso | Esperado | Obtido | OK | Justificação |', '|---|---|---|---|---|---|']
            for r in ref.itertuples():
                L.append(f'| {r.userId} | {r.caso} | {r.esperado} | {r.obtido} | {r.ok} | {r.justificacao} |')
    if comparacao:
        L += ['', '## Versões Athena emuladas no DuckDB', '',
              'Emulação: divisão inteira entre inteiros e macros para `from_unixtime`, `date_format`, '
              '`sequence` e `approx_percentile`. Valida a lógica, não a sintaxe do Trino.', '',
              '| Query | Linhas DuckDB | Linhas Athena (emul.) | Iguais | Nota |', '|---|---:|---:|---|---|']
        for c in comparacao:
            L.append(f"| {c['query']} | {c['linhas_duckdb']} | {c['linhas_athena']} | {c['iguais']} | {c['nota']} |")
    (pasta / 'analises_relatorio.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


def correr_analises(cfg, args):
    """Corre as queries de sql/analise/, verifica os resultados e escreve o relatório."""
    ds = cfg['dataset']
    pasta = cfg['paths']['results'] / ds / 'analises'
    pasta.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    # 1. Queries DuckDB: cada uma grava o seu CSV
    con, origem = ligar_analises(cfg, args.fonte)
    print(f'[analises] dataset={ds} fonte={args.fonte}')
    resumo = []
    for nome, ficheiro in listar_queries(PASTA_SQL, args.queries).items():
        linhas, seg = correr(con, nome, ficheiro, FONTES_DUCKDB, pasta / f'{nome}.csv')
        resumo.append({'query': nome, 'linhas': linhas, 'segundos': round(seg, 4), 'fonte': args.fonte})
        print(f'  {nome:24} {seg * 1000:9.1f} ms  {linhas:>9,} linhas'.replace(',', ' '))
    con.close()
    pd.DataFrame(resumo).to_csv(pasta / 'analises_resumo.csv', index=False)

    # 2. (Opcional) Versões Athena emuladas: correm numa ligação nova "à Trino" e cada
    #    resultado é comparado com o da versão DuckDB da mesma query
    comparacao = []
    if args.emular_athena:
        destino = pasta / 'athena_emulado'
        destino.mkdir(exist_ok=True)
        con, _ = ligar_analises(cfg, args.fonte)
        preparar_emulacao(con)
        print('[analises] versões Athena emuladas no DuckDB')
        for nome, ficheiro in listar_queries(PASTA_SQL_ATHENA, args.queries).items():
            linhas, seg = correr(con, nome, ficheiro, FONTES_ATHENA, destino / f'{nome}.csv')
            a = ler(pasta, nome)
            b = ler(destino, nome)
            if a is None:
                ok, nota = False, 'sem versão DuckDB'
            else:
                ok, nota = iguais(a, b)
            avisos = avisos_trino(ficheiro.read_text(encoding='utf-8'))
            if avisos:
                ok, nota = False, f'literal decimal numa conta (escala no Trino): {avisos[0]}'

            comparacao.append({'query': nome, 'linhas_duckdb': None if a is None else len(a),
                               'linhas_athena': linhas, 'iguais': 'sim' if ok else 'NÃO', 'nota': nota})
            print(f"  {nome:24} {linhas:>9,} linhas  iguais: {'sim' if ok else 'NÃO ' + nota}".replace(',', ' '))
        con.close()
        pd.DataFrame(comparacao).to_csv(destino / 'comparacao.csv', index=False)

    # 3. Verificações, relatório e, se alguma falhar, erro (o pipeline pára)
    verif = verificar(pasta, ds) + referencia_bots(pasta, ds)
    segundos = time.perf_counter() - t0
    relatorio_analises(pasta, ds, origem, resumo, verif, comparacao, segundos)
    for nome, valor, ok in verif:
        print(f"  [{'ok' if ok else 'FALHA'}] {nome}: {valor}")
    print(f'[analises] {len(resumo)} queries em {pasta.relative_to(ROOT)} ({segundos:.1f} s)')

    falhas = [v for v in verif if not v[2]]
    diferentes = [c for c in comparacao if c['iguais'] != 'sim']
    if falhas or diferentes:
        raise SystemExit(f'[analises] {len(falhas)} verificações falharam e {len(diferentes)} versões '
                         'Athena emuladas diferem (ver analises_relatorio.md)')

# ===========================================================================
# Parte 3: coordenação entre contas - Identificação de BOTS
#
# Deverá identificar poucos porque quando o movilens foi criado um utilizador ao registar-se tinha de avaliar pelnos 20 filmes e o carregamento era feito por bacth, quando submetia as avaliações, o que pode parecer "rajadas", s\ao na realidade ações normais.
# ===========================================================================

# ---------------------------------------------------------------------------
# PARTE 3.1 - Parâmetros do teste
# ---------------------------------------------------------------------------

# Lados: para cada dataset, o nome de cada grupo de notas extremas e a condição SQL que o define.
# O 1M só tem notas inteiras (1 a 5); o small e o 32M têm meias estrelas (0,5 a 5,0).
LADOS = {
    '1m':    {'1': 'rating = 1', '5': 'rating = 5'},
    'small': {'0.5': 'rating = 0.5', '<=1.0': 'rating <= 1.0', '5.0': 'rating = 5.0'},
    '32m':   {'0.5': 'rating = 0.5', '<=1.0': 'rating <= 1.0', '5.0': 'rating = 5.0'},
}

# Comparações: (análise, rótulo das notas, lados que entram). Cada lado conta uma vez.
# A análise "principal" usa os lados mais extremos; a de "sensibilidade" junta 0,5 e 1,0.
COMPARACOES = {
    '1m': [('principal', '1', ['1']), ('principal', '5', ['5']), ('principal', '1 e 5', ['1', '5'])],
    '32m': [('principal', '0.5', ['0.5']), ('principal', '5.0', ['5.0']),
            ('principal', '0.5 e 5.0', ['0.5', '5.0']),
            ('sensibilidade', '<=1.0', ['<=1.0']), ('sensibilidade', '<=1.0 e 5.0', ['<=1.0', '5.0'])],
}
COMPARACOES['small'] = COMPARACOES['32m']   # o small tem a mesma escala do 32M

LIMIARES_UTILIZADORES = (3, 5, 10, 20)   # U: n.º mínimo de utilizadores distintos numa rajada
LIMIARES_DESVIO = (1.5, 2.0)             # D: distância mínima entre a nota e a média do filme
ALFA = 0.05                              # nível de significância, antes da correção de Bonferroni
TOP = 10                                 # n.º de rajadas reais que são analisadas conta a conta
AMOSTRA_JACCARD = 1000                   # contas ao acaso para o Jaccard de referência entre pares quaisquer

# Colunas que identificam uma comparação (usadas para juntar o real com a linha de base)
CHAVE = ['analise', 'notas', 'min_utilizadores', 'min_desvio']


# ---------------------------------------------------------------------------
# PARTE 3.2 - Dados e consultas no DuckDB
# ---------------------------------------------------------------------------

def ligar_coordenacao(cfg, memoria):
    """Ligação DuckDB em UTC com a tabela r (userId, movieId, rating, ts), a view movies e filme."""
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    # Limite de memória e pasta temporária: se a memória não chegar (32M), o DuckDB escreve
    # resultados intermédios em disco em vez de falhar.
    con.execute(f"SET memory_limit = '{memoria}'")
    tmp = cfg['paths']['base'] / 'duckdb_tmp'
    con.execute(f"SET temp_directory = '{tmp.as_posix()}'")

    pasta = cfg['paths']['parquet']
    for t in ('ratings', 'movies'):
        if not (pasta / f'{t}.parquet').exists():
            raise SystemExit(f'Não encontrei {(pasta / f"{t}.parquet").relative_to(ROOT)}. '
                             'Corre primeiro run_pipeline.py --steps ingest parquet.')

    # Carregamos os ratings para uma tabela em memória (r), porque vão ser lidos muitas vezes
    # (uma por permutação). Só as 4 colunas de que precisamos; timestamp passa a chamar-se ts.
    con.execute(f"""CREATE TABLE r AS
                    SELECT userId, movieId, rating, timestamp AS ts
                    FROM read_parquet('{(pasta / 'ratings.parquet').as_posix()}')""")
    con.execute(f"CREATE VIEW movies AS SELECT * FROM read_parquet('{(pasta / 'movies.parquet').as_posix()}')")

    # Média e "estreia" (primeira avaliação no dataset) de cada filme: não mudam com a permutação,
    # por isso calculam-se uma só vez.
    con.execute("""CREATE TABLE filme AS
                   SELECT movieId, AVG(rating) AS media_filme, COUNT(*) AS avaliacoes_filme,
                          MIN(ts) AS estreia_ts
                   FROM r GROUP BY movieId""")
    return con, tmp


def sql_rajadas(tabela, lados):
    """SQL das rajadas: grupos (filme, lado, hora) com >= 3 utilizadores a >= 1,5 da média.

    Usa os limiares mínimos (U = 3 e D = 1,5); os mais exigentes filtram-se depois em Python.
    u_15 e u_2: n.º de utilizadores distintos do grupo a >= 1,5 e a >= 2 da média do filme.
    """
    # Uma subquery por lado (ex.: nota 0,5 e nota 5,0), juntas com UNION ALL
    partes = []
    for nome, cond in lados.items():
        partes.append(f"""SELECT t.userId, t.movieId, t.rating, t.ts, '{nome}' AS lado,
                                 abs(t.rating - f.media_filme) AS desvio, f.media_filme
                          FROM {tabela} t JOIN filme f USING (movieId)
                          WHERE t.{cond} AND abs(t.rating - f.media_filme) >= {min(LIMIARES_DESVIO)}""")
    extremas = ' UNION ALL '.join(partes)

    # ts // 3600 é a hora de relógio (divisão inteira dos segundos por 3600)
    return f"""
        WITH ext AS ({extremas})
        SELECT movieId, lado, ts // 3600 AS hora,
               COUNT(DISTINCT userId)                                AS u_15,
               COUNT(DISTINCT userId) FILTER (WHERE desvio >= 2)     AS u_2,
               MIN(rating) AS nota_min, MAX(rating) AS nota_max,
               MAX(desvio) AS desvio_max, MAX(media_filme) AS media_filme
        FROM ext
        GROUP BY movieId, lado, ts // 3600
        HAVING COUNT(DISTINCT userId) >= {min(LIMIARES_UTILIZADORES)}"""


def contar(df, comparacoes):
    """N.º de rajadas por comparação (análise, notas, U, D), a partir do resultado de sql_rajadas."""
    linhas = []
    for analise, notas, lados in comparacoes:
        sub = df[df.lado.isin(lados)]          # só as rajadas dos lados desta comparação
        for u in LIMIARES_UTILIZADORES:
            for d in LIMIARES_DESVIO:
                # Com D = 1,5 conta-se u_15; com D = 2 conta-se u_2
                if d == 1.5:
                    col = sub.u_15
                else:
                    col = sub.u_2
                linhas.append({'analise': analise, 'notas': notas, 'min_utilizadores': u,
                               'min_desvio': d, 'rajadas': int((col >= u).sum())})
    return pd.DataFrame(linhas)


def por_ano(df, lados):
    """Rajadas por ano (U >= 3, D >= 1,5) nos lados indicados. Devolve uma Series ano -> n.º."""
    sub = df[df.lado.isin(lados)]
    # hora * 3600 volta a dar segundos; pd.to_datetime(..., unit='s') converte em data (UTC)
    return pd.to_datetime(sub.hora * 3600, unit='s').dt.year.value_counts()


def permutar(con, semente):
    """Cria a tabela p: cada avaliação do filme recebe um dos timestamps desse filme, baralhados.

    a: avaliações do filme por ordem de hash(userId, movieId, semente) -> posição rn;
    b: timestamps do filme por ordem cronológica -> posição rn;
    a avaliação na posição k recebe o k-ésimo timestamp. O conjunto de timestamps do filme
    fica igual; muda qual o utilizador (e a nota) que fica em cada momento.
    """
    con.execute(f"""
        CREATE OR REPLACE TABLE p AS
        WITH a AS (SELECT userId, movieId, rating,
                          row_number() OVER (PARTITION BY movieId
                                             ORDER BY hash(userId, movieId, {semente}), userId) AS rn
                   FROM r),
             b AS (SELECT movieId, ts,
                          row_number() OVER (PARTITION BY movieId ORDER BY ts, userId) AS rn
                   FROM r)
        SELECT a.userId, a.movieId, a.rating, b.ts
        FROM a JOIN b USING (movieId, rn)""")


def verificar_permutacao(con):
    """Verifica que a permutação está correta e devolve (resumo, exemplo).

    Em todos os filmes, p tem de ter as mesmas avaliações (utilizador, nota) e o mesmo conjunto
    de timestamps que r, e os timestamps têm de ter mudado de avaliação.
    """
    # Compara r e p filme a filme. Somar o hash de cada valor é uma forma rápida de comparar
    # dois conjuntos: se tiverem os mesmos elementos, a soma é igual (seja qual for a ordem).
    v = con.execute("""
        WITH a AS (SELECT movieId, COUNT(*) AS n, SUM(hash(ts)) AS h_ts, MIN(ts) AS mn, MAX(ts) AS mx,
                          SUM(hash(userId, rating)) AS h_av FROM r GROUP BY movieId),
             b AS (SELECT movieId, COUNT(*) AS n, SUM(hash(ts)) AS h_ts, MIN(ts) AS mn, MAX(ts) AS mx,
                          SUM(hash(userId, rating)) AS h_av FROM p GROUP BY movieId)
        SELECT COUNT(*) AS filmes,
               count_if(a.n <> b.n OR a.h_ts <> b.h_ts OR a.mn <> b.mn OR a.mx <> b.mx) AS filmes_ts_diferentes,
               count_if(a.h_av <> b.h_av) AS filmes_avaliacoes_diferentes
        FROM a FULL JOIN b USING (movieId)""").fetchone()

    # Quantas avaliações mudaram de timestamp e de hora com a permutação
    mudou = con.execute("""
        SELECT COUNT(*), count_if(r.ts <> p.ts),
               count_if(r.ts // 3600 <> p.ts // 3600)
        FROM r JOIN p USING (userId, movieId)""").fetchone()
    n_r = con.execute('SELECT COUNT(*) FROM r').fetchone()[0]

    resumo = {'filmes': v[0], 'filmes_ts_diferentes': v[1], 'filmes_avaliacoes_diferentes': v[2],
              'avaliacoes': n_r, 'pares_juntos': mudou[0], 'ts_mudou': mudou[1], 'hora_mudou': mudou[2]}
    if v[1] or v[2] or mudou[0] != n_r:
        raise SystemExit(f'Permutação inválida: {resumo}')

    # Exemplo para o relatório: o filme com 6 avaliações e menor movieId, antes e depois
    exemplo = con.execute("""
        WITH f AS (SELECT MIN(movieId) AS movieId FROM filme WHERE avaliacoes_filme = 6)
        SELECT r.movieId, r.userId, r.rating,
               strftime(epoch_ms(r.ts * 1000), '%Y-%m-%d %H:%M:%S') AS ts_original,
               strftime(epoch_ms(p.ts * 1000), '%Y-%m-%d %H:%M:%S') AS ts_permutado
        FROM r JOIN f USING (movieId) JOIN p USING (userId, movieId)
        ORDER BY r.ts, r.userId""").df()
    return resumo, exemplo


def caracterizar(con, top):
    """Uma linha por conta de cada rajada do top, e o Jaccard entre as contas de cada rajada."""
    con.register('top_df', top[['rajada', 'movieId', 'lado_cond', 'hora']])

    # Membros de cada rajada: as contas que deram a nota extrema ao filme naquela hora.
    # "baixo" é a nota mínima da escala (0,5 ou 1) e "alto" a máxima (5).
    membros_sql = """SELECT DISTINCT t.rajada, r.userId, r.ts
                     FROM top_df t JOIN r ON r.movieId = t.movieId AND r.ts // 3600 = t.hora
                     JOIN filme f ON f.movieId = r.movieId
                     WHERE ((t.lado_cond = 'baixo' AND r.rating = (SELECT MIN(rating) FROM r))
                         OR (t.lado_cond = 'alto' AND r.rating = (SELECT MAX(rating) FROM r)))
                       AND abs(r.rating - f.media_filme) >= 1.5"""

    # Para cada conta: antiguidade no momento da rajada, se estava no registo (primeiras 24 h),
    # quantas avaliações fez depois e se voltou a avaliar mais de 24 h depois.
    contas = con.execute(f"""
        WITH membros AS ({membros_sql}),
             u AS (SELECT userId, COUNT(*) AS avaliacoes_conta, MIN(ts) AS primeiro_ts, MAX(ts) AS ultimo_ts
                   FROM r WHERE userId IN (SELECT userId FROM membros) GROUP BY userId),
             depois AS (SELECT m.rajada, m.userId, COUNT(x.ts) AS avaliacoes_depois
                        FROM membros m LEFT JOIN r x ON x.userId = m.userId AND x.ts > m.ts
                        GROUP BY m.rajada, m.userId)
        SELECT m.rajada, m.userId,
               strftime(epoch_ms(m.ts * 1000), '%Y-%m-%d %H:%M:%S')     AS momento,
               u.avaliacoes_conta,
               strftime(epoch_ms(u.primeiro_ts * 1000), '%Y-%m-%d')     AS primeiro_dia,
               ROUND((m.ts - u.primeiro_ts) / 86400.0, 2)               AS antiguidade_dias,
               m.ts - u.primeiro_ts < 86400                             AS no_registo,
               d.avaliacoes_depois,
               ROUND((u.ultimo_ts - m.ts) / 86400.0, 2)                 AS dias_ate_ultima,
               u.ultimo_ts - m.ts > 86400                               AS voltou_depois_24h
        FROM membros m JOIN u USING (userId) JOIN depois d USING (rajada, userId)
        ORDER BY m.rajada, m.ts, m.userId""").df()

    # Jaccard entre duas contas = filmes em comum / filmes avaliados por pelo menos uma das duas.
    # Perto de 1: as contas avaliaram quase os mesmos filmes (sinal de coordenação).
    jac = con.execute(f"""
        WITH membros AS (SELECT DISTINCT rajada, userId FROM ({membros_sql})),
             ru AS (SELECT userId, movieId FROM r WHERE userId IN (SELECT userId FROM membros)),
             n AS (SELECT userId, COUNT(*) AS n FROM ru GROUP BY userId),
             pares AS (SELECT a.rajada, a.userId AS u1, b.userId AS u2
                       FROM membros a JOIN membros b ON a.rajada = b.rajada AND a.userId < b.userId),
             comuns AS (SELECT p.rajada, p.u1, p.u2, COUNT(*) AS comuns
                        FROM pares p JOIN ru x ON x.userId = p.u1 JOIN ru y ON y.userId = p.u2 AND y.movieId = x.movieId
                        GROUP BY p.rajada, p.u1, p.u2)
        SELECT p.rajada,
               AVG(COALESCE(c.comuns, 0) / (n1.n + n2.n - COALESCE(c.comuns, 0)))  AS jaccard_medio,
               MAX(COALESCE(c.comuns, 0) / (n1.n + n2.n - COALESCE(c.comuns, 0)))  AS jaccard_max
        FROM pares p
        LEFT JOIN comuns c USING (rajada, u1, u2)
        JOIN n n1 ON n1.userId = p.u1 JOIN n n2 ON n2.userId = p.u2
        GROUP BY p.rajada""").df()
    return contas, jac


def jaccard_referencia(con):
    """Jaccard médio e p95 entre pares de contas quaisquer (amostra fixa de contas), para comparação."""
    # A amostra é "ao acaso" mas reprodutível: ordenar por hash(userId, 42) dá sempre as mesmas contas.
    return con.execute(f"""
        WITH amostra AS (SELECT userId FROM (SELECT DISTINCT userId FROM r)
                         ORDER BY hash(userId, 42) LIMIT {AMOSTRA_JACCARD}),
             ra AS (SELECT r.userId, r.movieId FROM r JOIN amostra USING (userId)),
             n AS (SELECT userId, COUNT(*) AS n FROM ra GROUP BY userId),
             comuns AS (SELECT x.userId AS u1, y.userId AS u2, COUNT(*) AS comuns
                        FROM ra x JOIN ra y ON x.movieId = y.movieId AND x.userId < y.userId
                        GROUP BY 1, 2),
             pares AS (SELECT a.userId AS u1, b.userId AS u2, a.n + b.n AS soma
                       FROM n a JOIN n b ON a.userId < b.userId)
        SELECT AVG(COALESCE(c.comuns, 0) / (p.soma - COALESCE(c.comuns, 0))),
               quantile_cont(COALESCE(c.comuns, 0) / (p.soma - COALESCE(c.comuns, 0)), 0.95)
        FROM pares p LEFT JOIN comuns c USING (u1, u2)""").fetchone()


# ---------------------------------------------------------------------------
# PARTE 3.3 - Passos do main
# ---------------------------------------------------------------------------

def lados_principais(comparacoes):
    """Lista dos lados usados na análise principal, sem repetições e pela ordem em que aparecem."""
    lados = []
    for analise, notas, lados_comparacao in comparacoes:
        if analise != 'principal':
            continue
        for lado in lados_comparacao:
            if lado not in lados:
                lados.append(lado)
    return lados


def linha_de_base(con, lados, comparacoes, principal, repeticoes):
    """Corre as permutações e conta as rajadas em cada uma.

    Devolve (base, anos_base, tempos, verificacao, exemplo):
    base       DataFrame com o n.º de rajadas por permutação e por comparação
    anos_base  lista de Series (uma por permutação) com as rajadas por ano
    tempos     segundos de cada permutação
    """
    base, anos_base, tempos = [], [], []
    verif = exemplo = None
    for semente in range(1, repeticoes + 1):
        tp = time.perf_counter()
        permutar(con, semente)
        # A verificação é cara, por isso só se faz na primeira permutação
        if semente == 1:
            verif, exemplo = verificar_permutacao(con)
        pdf = con.execute(sql_rajadas('p', lados)).df()
        c = contar(pdf, comparacoes)
        c.insert(0, 'repeticao', semente)
        base.append(c)
        anos_base.append(por_ano(pdf, principal).rename(semente))
        tempos.append(time.perf_counter() - tp)
        if semente == 1 or semente % 10 == 0:
            print(f'  permutação {semente}/{repeticoes} ({tempos[-1]:.1f} s)', flush=True)
    base = pd.concat(base, ignore_index=True)
    return base, anos_base, tempos, verif, exemplo


def teste_permutacao(real, base, repeticoes):
    """Compara o n.º real de rajadas com a linha de base. Devolve (teste, n.º de comparações, limiar)."""
    # Estatísticas da linha de base por comparação: média, desvio-padrão, p95 e máximo
    grupos = base.groupby(CHAVE, sort=False)['rajadas']
    agg = pd.DataFrame({'media': grupos.mean(),
                        'desvio_padrao': grupos.std(),
                        'p95': grupos.quantile(0.95),
                        'maximo': grupos.max()}).reset_index()
    real_renomeado = real.rename(columns={'rajadas': 'real'})
    teste = real_renomeado.merge(agg, on=CHAVE)

    # Quantas permutações tiveram pelo menos tantas rajadas como o real (para o valor-p)
    juntas = base.merge(real_renomeado, on=CHAVE)
    juntas['ge'] = juntas['rajadas'] >= juntas['real']
    ge = juntas.groupby(CHAVE, sort=False)['ge'].sum().rename('perm_ge_real').reset_index()
    teste = teste.merge(ge, on=CHAVE)

    # Valor-p empírico com a correção "+1" (nunca dá 0) e limiar de Bonferroni
    m = len(teste)
    alfa_bonf = ALFA / m
    teste['valor_p'] = ((1 + teste.perm_ge_real) / (1 + repeticoes)).round(4)
    # z = quantos desvios-padrão o real está acima da média das permutações.
    # .where(... > 0) deixa vazio (NaN) quando o desvio-padrão ou a média são 0, para não dividir por 0.
    teste['z'] = ((teste.real - teste.media) / teste.desvio_padrao.where(teste.desvio_padrao > 0)).round(2)
    teste['sinal_bonferroni'] = teste.valor_p < alfa_bonf
    teste['razao_real_media'] = (teste.real / teste.media.where(teste.media > 0)).round(2)
    for col in ('media', 'desvio_padrao', 'p95'):
        teste[col] = teste[col].round(2)
    return teste, m, alfa_bonf


def rajadas_por_ano(con, real_df, anos_base, principal):
    """Rajadas reais por ano, média e p95 nas permutações, e contas novas por ano."""
    anos = pd.DataFrame({'rajadas_reais': por_ano(real_df, principal)})
    # Uma coluna por permutação; anos sem rajadas nessa permutação ficam a 0
    anos_b = pd.concat(anos_base, axis=1).fillna(0)
    anos = anos.join(pd.DataFrame({'media_permutacoes': anos_b.mean(axis=1).round(2),
                                   'p95_permutacoes': anos_b.quantile(0.95, axis=1).round(2)}), how='outer')

    # Contas novas: ano da primeira avaliação de cada utilizador
    primeiras = con.execute("""SELECT year(epoch_ms(MIN(ts) * 1000)) AS ano, COUNT(*) AS n
                               FROM r GROUP BY userId""").df()
    novas = primeiras.groupby('ano').size().rename('contas_novas')

    anos = anos.join(novas, how='outer').fillna(0).sort_index()
    anos.index.name = 'ano'
    anos = anos.astype({'rajadas_reais': int, 'contas_novas': int}).reset_index()
    return anos


def detalhe_rajadas(con, real_df):
    """Junta a cada rajada real o título, a estreia do filme e o total de avaliações dessa hora.

    Devolve as rajadas ordenadas da mais forte para a mais fraca (mais utilizadores; desempate
    pelo desvio) e a lista de colunas que vão para o CSV.
    """
    con.register('real_df', real_df)
    # SEMI JOIN: fica só com as avaliações das (filme, hora) que são rajadas, sem as duplicar
    rajadas = con.execute("""
        SELECT d.*, fm.title, fm.avaliacoes_filme, fm.estreia_ts, h.avaliacoes_filme_hora
        FROM real_df d
        JOIN (SELECT f.*, m.title FROM filme f JOIN movies m USING (movieId)) fm USING (movieId)
        JOIN (SELECT r.movieId, r.ts // 3600 AS hora, COUNT(*) AS avaliacoes_filme_hora
              FROM r SEMI JOIN (SELECT DISTINCT movieId, hora FROM real_df) k
                   ON r.movieId = k.movieId AND r.ts // 3600 = k.hora
              GROUP BY 1, 2) h USING (movieId, hora)""").df()
    rajadas = rajadas.sort_values(['u_15', 'desvio_max', 'movieId', 'hora'],
                                  ascending=[False, False, True, True]).reset_index(drop=True)

    # Colunas legíveis para o relatório
    rajadas['inicio_hora_utc'] = pd.to_datetime(rajadas.hora * 3600, unit='s').dt.strftime('%Y-%m-%d %H:00')
    rajadas['pct_da_hora'] = (100 * rajadas.u_15 / rajadas.avaliacoes_filme_hora).round(1)
    rajadas['dias_desde_estreia_dataset'] = ((rajadas.hora * 3600 - rajadas.estreia_ts) / 86400).round(2)
    # Ano no fim do título, ex.: "Toy Story (1995)" -> 1995
    rajadas['ano_titulo'] = rajadas.title.str.extract(r'\((\d{4})\)\s*$')[0]
    rajadas['desvio_max'] = rajadas.desvio_max.round(3)
    rajadas['media_filme'] = rajadas.media_filme.round(3)
    cols = ['movieId', 'title', 'ano_titulo', 'lado', 'inicio_hora_utc', 'u_15', 'u_2',
            'avaliacoes_filme_hora', 'pct_da_hora', 'media_filme', 'desvio_max', 'avaliacoes_filme',
            'dias_desde_estreia_dataset']
    return rajadas, cols


def resumo_por_rajada(contas):
    """Resumo das contas de cada rajada: antiguidade, registo, atividade e (se houver) suspeitos."""
    grupos = contas.groupby('rajada')
    resumo = pd.DataFrame({
        'antiguidade_mediana_dias': grupos['antiguidade_dias'].median(),
        'pct_no_registo': (100 * grupos['no_registo'].mean()).round(1),
        'avaliacoes_conta_mediana': grupos['avaliacoes_conta'].median(),
        'pct_voltaram_24h': (100 * grupos['voltou_depois_24h'].mean()).round(1),
    })
    # Contas classificadas como suspeitas na parte 2 (10_flag_bots.csv)
    if 'classificacao' in contas:
        suspeito = contas['classificacao'].fillna('').str.startswith('suspeito')
        resumo['contas_suspeitas'] = suspeito.groupby(contas['rajada']).sum().astype(int)
    return resumo.reset_index()


def top_rajadas(con, cfg, ds, rajadas, cols, principal, saida):
    """Caracteriza as TOP rajadas mais fortes da análise principal e grava os CSV do top 10."""
    top = rajadas[rajadas.lado.isin(principal)].head(TOP).copy()
    top.insert(0, 'rajada', range(1, len(top) + 1))
    # lado baixo = nota mínima da escala (0,5 ou 1); alto = 5
    lado_cond = []
    for lado in top.lado:
        if lado in ('5', '5.0'):
            lado_cond.append('alto')
        else:
            lado_cond.append('baixo')
    top['lado_cond'] = lado_cond

    contas, jac = caracterizar(con, top)
    # Classificação da deteção de bots (parte 2), se existir
    bots_csv = cfg['paths']['results'] / ds / 'analises' / '10_flag_bots.csv'
    if bots_csv.exists():
        bots = pd.read_csv(bots_csv, usecols=['userId', 'classificacao'])
        contas = contas.merge(bots, on='userId', how='left')
    contas.to_csv(saida / 'top10_contas.csv', index=False)

    resumo = resumo_por_rajada(contas)
    top = top.merge(resumo, on='rajada').merge(jac, on='rajada')
    top['jaccard_medio'] = top.jaccard_medio.round(3)
    top['jaccard_max'] = top.jaccard_max.round(3)
    # A rajada calhou na primeira semana do filme no dataset?
    top['coincide_estreia_7d'] = top.dias_desde_estreia_dataset.abs() <= 7
    cols_top = ['rajada'] + cols + list(resumo.columns[1:]) + ['jaccard_medio', 'jaccard_max', 'coincide_estreia_7d']
    top = top[cols_top]
    top.to_csv(saida / 'top10_rajadas.csv', index=False)
    return top


def tabela_md(df):
    """Converte um DataFrame numa tabela em Markdown (valores em falta ficam vazios)."""
    cols = list(df.columns)
    linhas = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, row in df.iterrows():
        valores = []
        for v in row:
            if pd.isna(v):
                valores.append('')
            else:
                valores.append(str(v))
        linhas.append('| ' + ' | '.join(valores) + ' |')
    return '\n'.join(linhas)


def relatorio_coordenacao(saida, ds, args, lados, tempos, t_carga, segundos, verif, exemplo,
                       teste, m, alfa_bonf, anos, top, jac_ref):
    """Escreve coordenacao_relatorio.md com os tempos, a verificação, o teste e o top 10."""
    R = args.repeticoes
    p_min = 1 / (1 + R)   # menor valor-p possível com R permutações

    # Textos auxiliares da secção "Definição"
    lados_txt = []
    for nome, cond in lados.items():
        lados_txt.append(f'`{nome}` ({cond})')
    u_txt = ', '.join(str(u) for u in LIMIARES_UTILIZADORES)
    d_txt = ', '.join(f'{d:g}' for d in LIMIARES_DESVIO)

    # Aviso quando o n.º de permutações não permite passar Bonferroni
    aviso_bonferroni = ''
    if p_min >= alfa_bonf:
        aviso_bonferroni = (' **Com este n.º de permutações nenhuma comparação pode passar o limiar corrigido**; '
                            f'seriam precisas pelo menos {int(m / ALFA)} permutações. '
                            'O z é dado como informação complementar.')

    colunas_top = ['rajada', 'title', 'lado', 'inicio_hora_utc', 'u_15', 'avaliacoes_filme_hora',
                   'pct_da_hora', 'desvio_max', 'dias_desde_estreia_dataset', 'antiguidade_mediana_dias',
                   'pct_no_registo', 'avaliacoes_conta_mediana', 'pct_voltaram_24h', 'jaccard_medio',
                   'jaccard_max']
    if 'contas_suspeitas' in top:
        colunas_top.append('contas_suspeitas')

    md = [f'# Coordenação entre contas · MovieLens {ds}', '',
          f'Gerado por `scripts/04_analise.py` (sessão DuckDB em UTC, memory_limit {args.memoria}, '
          'fonte Parquet).', '',
          '## Tempos', '',
          f'- Total: {segundos:.1f} s ({segundos / 60:.1f} min).',
          f'- Carga dos dados: {t_carga:.1f} s.',
          f'- Permutações: {R}, {sum(tempos):.1f} s no total, {sum(tempos) / R:.2f} s em média '
          f'(a primeira inclui a verificação: {tempos[0]:.1f} s).', '',
          '## Definição', '',
          f'Rajada: (filme, lado, hora UTC) com >= U utilizadores distintos cuja nota está no lado e a >= D da '
          f'média do filme. Lados: {", ".join(lados_txt)}. '
          f'U em {{{u_txt}}}, D em {{{d_txt}}}.', '',
          f'Linha de base: {R} permutações dos timestamps dentro de cada filme (sementes 1..{R}).', '',
          '## Verificação da permutação (semente 1)', '',
          f'- Filmes: {verif["filmes"]}; com conjunto de timestamps diferente: {verif["filmes_ts_diferentes"]}; '
          f'com avaliações (utilizador, nota) diferentes: {verif["filmes_avaliacoes_diferentes"]}.',
          f'- Avaliações: {verif["avaliacoes"]}; com timestamp diferente do original: {verif["ts_mudou"]} '
          f'({100 * verif["ts_mudou"] / verif["avaliacoes"]:.1f}%); com hora diferente: {verif["hora_mudou"]} '
          f'({100 * verif["hora_mudou"] / verif["avaliacoes"]:.1f}%).', '',
          f'Exemplo (filme {exemplo.movieId.iloc[0]}, 6 avaliações):', '',
          tabela_md(exemplo), '',
          '## Real vs linha de base', '',
          f'Comparações: {m}. Bonferroni: limiar {ALFA} / {m} = {alfa_bonf:.5f}. '
          f'Menor valor-p empírico possível com {R} permutações: 1 / {R + 1} = {p_min:.5f}.'
          + aviso_bonferroni, '',
          tabela_md(teste[CHAVE + ['real', 'media', 'desvio_padrao', 'p95', 'maximo', 'razao_real_media',
                                   'z', 'valor_p', 'sinal_bonferroni']]), '',
          '## Rajadas por ano (análise principal, U >= 3, D >= 1,5)', '',
          tabela_md(anos), '',
          f'## As {TOP} rajadas reais mais fortes (análise principal)', '',
          tabela_md(top[colunas_top]), '',
          f'Jaccard de referência entre pares de contas quaisquer ({AMOSTRA_JACCARD} contas ao acaso): '
          f'média {jac_ref[0]:.3f}, p95 {jac_ref[1]:.3f}.', '']
    (saida / 'coordenacao_relatorio.md').write_text('\n'.join(md), encoding='utf-8')


def correr_coordenacao(cfg, args):
    """Rajadas reais, linha de base por permutação, teste, top 10 e relatório."""
    ds = cfg['dataset']
    lados, comparacoes = LADOS[ds], COMPARACOES[ds]
    principal = lados_principais(comparacoes)
    R = args.repeticoes
    saida = cfg['paths']['results'] / ds / 'bots_coordenacao'
    saida.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    con, tmp = ligar_coordenacao(cfg, args.memoria)
    t_carga = time.perf_counter() - t0

    # 1. Rajadas reais
    real_df = con.execute(sql_rajadas('r', lados)).df()
    real = contar(real_df, comparacoes)
    print(f'[{ds}] rajadas reais (U>=3, D>=1,5, todos os lados): {len(real_df)}')

    # 2. Linha de base: R permutações dos timestamps dentro de cada filme, e o teste
    base, anos_base, tempos, verif, exemplo = linha_de_base(con, lados, comparacoes, principal, R)
    teste, m, alfa_bonf = teste_permutacao(real, base, R)

    # 3. Rajadas por ano (análise principal, U >= 3, D >= 1,5) e contas novas por ano
    anos = rajadas_por_ano(con, real_df, anos_base, principal)
    anos.to_csv(saida / 'rajadas_por_ano.csv', index=False)

    # 4. Rajadas reais: detalhe e top 10 da análise principal
    rajadas, cols = detalhe_rajadas(con, real_df)
    rajadas[cols].to_csv(saida / 'rajadas.csv', index=False)
    top = top_rajadas(con, cfg, ds, rajadas, cols, principal, saida)
    jac_ref = jaccard_referencia(con)

    base.to_csv(saida / 'linha_base.csv', index=False)
    teste.to_csv(saida / 'teste.csv', index=False)
    exemplo.to_csv(saida / 'verificacao_permutacao.csv', index=False)
    con.close()
    shutil.rmtree(tmp, ignore_errors=True)   # apaga a pasta temporária do DuckDB

    # 5. Relatório
    segundos = time.perf_counter() - t0
    relatorio_coordenacao(saida, ds, args, lados, tempos, t_carga, segundos, verif, exemplo,
                       teste, m, alfa_bonf, anos, top, jac_ref)
    print(f'Gravado em {saida.relative_to(ROOT)} ({segundos:.1f} s)')


# ===========================================================================
# PARTE 4 - Execução
# ===========================================================================

def parse_args():
    """Lê as opções da linha de comandos."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    ap.add_argument('--fonte', default='parquet', choices=['parquet', 'csv'],
                    help='ler o Parquet (por omissão) ou os CSV normalizados')
    ap.add_argument('--queries', nargs='+', metavar='NOME',
                    help='parte 2: correr só estas queries de sql/analise/ (e as de que dependem)')
    ap.add_argument('--emular-athena', action='store_true',
                    help='parte 2: corre também as versões de sql/athena/analise/ emuladas no DuckDB e compara')
    ap.add_argument('--coordenacao', action='store_true',
                    help='parte 3: corre o teste de coordenação entre contas (cerca de 3 s por permutação no 32M)')
    ap.add_argument('--repeticoes', type=int, default=20,
                    help='parte 3: n.º de permutações da linha de base (20 por omissão; 800 para passar Bonferroni)')
    ap.add_argument('--memoria', default='12GB', help='parte 3: memory_limit do DuckDB (12GB por omissão)')
    return ap.parse_args()


def main():
    """Corre a EDA, as análises e, com --coordenacao, o teste de coordenação."""
    args = parse_args()
    cfg = load_config(args.dataset)
    correr_eda(cfg['dataset'], args.fonte, cfg['paths']['results'])
    correr_analises(cfg, args)
    if args.coordenacao:
        correr_coordenacao(cfg, args)


if __name__ == '__main__':
    main()
