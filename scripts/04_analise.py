"""
04_analise.py - Passo analise do pipeline: análise dos dados do MovieLens.

Objetivo:
    Responder à pergunta "o que nos dizem os dados", em duas partes:
      1. Análise exploratória (EDA): 
        (1.1) indicadores;
        (1.2) qualidade das tabelas
        (1.3) 10 figuras sobre a distribuição das notas, a atividade dos utilizadores, a popularidade dos filmes, o
         tempo, os géneros e as tags.
      2. Análises de sql/analise/ - 17 queries (qualidade, integridade, evolução no tempo, filmes, uso da escala, registo e deteção de utilizadores suspeitos), com verificações.
      Todas as agregações são feitas no DuckDB e só os resultados agregados passam para Python, por isso o mesmo script corre no small, no 1M e no 32M sem carregar os dados em memória.

    Verificações que fazem o script falhar (parte 2):
    - qualidade: 0 linhas com nulos e 0 valores fora da escala (no 1M, também só inteiros 1-5);
    - integridade: 0 ids de filmes repetidos e 0 avaliações sem filme;
    - linhas, utilizadores, filmes avaliados e média global iguais aos da parte 1;
    - a soma das avaliações por ano (anual) igual ao total de linhas;
    - no small, a classificação dos 5 utilizadores de referência da deteção de bots.

Entradas:
    data/<dataset>/parquet/<tabela>.parquet   Parquet sem partição (do 02_to_parquet.py)
    sql/analise/*.sql                         queries da parte 2 (${ratings}, ${movies}, ${flag_bots})

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

Notas:
    - As ligações ao DuckDB ficam em UTC; os anos, as horas e os dias vêm de epoch_ms (sem fuso), por isso nenhum resultado depende da máquina;
    - ${flag_bots} é a tabela por utilizador de 10_flag_bots.sql. O script corre essa query primeiro e guarda-a numa tabela temporária.
"""
import time
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

from common import ROOT, load_config  # noqa: E402


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


def ligar_eda(base, dataset):
    """Cria uma ligação DuckDB com uma view por tabela encontrada. Devolve (ligação, origem)."""
    con = duckdb.connect()
    # Fuso fixo em UTC: funções como to_timestamp devolvem TIMESTAMP WITH TIME ZONE e o anoou o mês dependeriam do fuso da máquina. Este script usa epoch_ms (sem fuso), mas assim nenhuma query futura fica dependente do sítio onde corre.
    con.execute("SET TimeZone = 'UTC'")
    origem = {}
    for t in TABELAS:
        caminho = base / "data" / dataset / "parquet" / f"{t}.parquet"
        if not caminho.exists():
            continue   # ex.: o 1M não tem tags nem links

        # Uma VIEW não copia dados: guarda só a query. Cada vez que se consulta "ratings",
        # o DuckDB lê o ficheiro e só as colunas que a query usa.
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{caminho.as_posix()}')")

        # Caminho relativo à raiz do projeto: o relatório é versionado e não deve expor pastas locais
        origem[t] = f"parquet: {caminho.relative_to(base).as_posix()}"

    if "ratings" not in origem or "movies" not in origem:
        raise SystemExit(
            f"Não encontrei ratings e movies em data/{dataset}/parquet. "
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


def correr_eda(ds, resultados):
    """Liga aos dados, calcula os indicadores, gera as figuras e o relatório da EDA."""
    t0 = time.perf_counter()
    pasta = resultados / ds / "eda"
    pasta.mkdir(parents=True, exist_ok=True)
    aplicar_estilo_nova()

    con, origem = ligar_eda(ROOT, ds)
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

# Queries cujo resultado outras queries usam: nome do ficheiro -> nome da tabela temporária.
# 10_flag_bots corre primeiro (a ordem alfabética já o põe à frente, por começar por um dígito).
MATERIALIZAR = {'10_flag_bots': 'flag_bots'}


# ---------------------------------------------------------------------------
# PARTE 2.1Ligação aos dados
# ---------------------------------------------------------------------------
def leitor(cfg, tabela):
    """Texto SQL que lê o Parquet de uma tabela do dataset, e a origem para o relatório."""
    caminho = cfg['paths']['parquet'] / f'{tabela}.parquet'
    if not caminho.exists():
        raise SystemExit(f'Não encontrei {caminho.relative_to(ROOT)}. Corre primeiro a ingestão '
                         'e a conversão para Parquet.')
    return f"read_parquet('{caminho.as_posix()}')", f'parquet: {caminho.relative_to(ROOT).as_posix()}'


def ligar_analises(cfg):
    """Ligação DuckDB em UTC com as views ratings_base (sem year) e movies. Devolve (ligação, origem)."""
    con = duckdb.connect()
    # Fuso fixo: to_timestamp e afins devolvem TIMESTAMP WITH TIME ZONE, e o ano ou o mês
    # dependeriam do fuso da máquina. As queries usam epoch_ms/year, mas assim fica garantido.
    con.execute("SET TimeZone = 'UTC'")
    origem = {}
    for tabela, view in (('ratings', 'ratings_base'), ('movies', 'movies')):
        texto, origem[tabela] = leitor(cfg, tabela)
        con.execute(f'CREATE VIEW {view} AS SELECT * FROM {texto}')
    return con, origem


# ${ratings} tem sempre a coluna year (em UTC), como no 03_benchmark.py.
FONTES_DUCKDB = {
    'ratings': '(SELECT *, year(epoch_ms(timestamp * 1000)) AS year FROM ratings_base)',
    'movies': 'movies',
    'flag_bots': 'flag_bots',
}

# ---------------------------------------------------------------------------
# PARTE 2.2 Execução das queries
# ---------------------------------------------------------------------------
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
        89: ('sem sinais', '518 avaliações em 23 min, só no registo: as primeiras 24 h não contam'),
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
                      f'(limiar {r.limiar_regra_a}), mediana de {inteiro(r.mediana_intervalo_apos_s)} s entre eventos')
    if r.submissao_lote:
        partes.append(f'submissão em lote: até {r.max_avaliacoes_mesmo_segundo} avaliações no mesmo segundo '
                      f'({r.pct_eventos_lote:.0f}% dos eventos com 2 ou mais), primeiro dia {r.primeiro_dia}')
    if not partes:
        partes.append(f'depois do registo: máx. {inteiro(r.max_eventos_10min_apos)} eventos em 10 min (limiar '
                      f'{r.limiar_regra_a}); {r.eventos_registo} eventos no registo (não contam); '
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


# ---------------------------------------------------------------------------
def relatorio_analises(pasta, ds, origem, resumo, verif, segundos):
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
    reg = ler(pasta, 'registo_24h')
    if reg is not None:
        g = reg.iloc[0]
        L += ['', '## Primeiras 24 h de cada utilizador (registo_24h)', '',
              'Porque é que a regra A ignora as primeiras 24 h: no registo, quase todos avaliam 20 filmes '
              'em poucos minutos.', '',
              '| Indicador | Valor |', '|---|---:|',
              f'| Utilizadores com >= 20 avaliações nas primeiras 24 h | {g.pct_20_nas_24h:.1f}% |',
              f'| Chegam à 20.ª avaliação em menos de 10 min | {g.pct_20a_em_10min:.1f}% |',
              f'| Chegam à 20.ª avaliação em menos de 1 h | {g.pct_20a_em_1h:.1f}% |',
              f'| Tempo mediano até à 20.ª avaliação | {g.mediana_min_ate_20a:.1f} min |',
              f'| Utilizadores com toda a atividade nas primeiras 24 h (a regra A não os vê) | {g.pct_tudo_nas_24h:.1f}% |']
    flags, calib = ler(pasta, '10_flag_bots'), ler(pasta, '10_flag_bots_calibracao')
    if flags is not None and calib is not None:
        c = calib.iloc[0]
        L += ['', '## Deteção de bots (10_flag_bots)', '',
              f"- Utilizadores: {int(c.utilizadores)}; suspeitos (regra A, >= 100 eventos em 10 min depois "
              f"do registo): {int(c.suspeitos)} ({c.pct_suspeitos:.2f}%).",
              f"- Submissão em lote (reportada à parte, não é bot): {int(c.submissao_lote)} utilizadores, "
              f"dos quais {int(c.so_submissao_lote)} sem outra classificação.",
              f"- Ritmo sustentado depois do registo (máx. de eventos em 10 min), "
              f"{int(c.utilizadores_com_atividade_apos_registo)} utilizadores: p50 {c.p50:.1f}, p90 {c.p90:.1f}, "
              f"p99 {c.p99:.1f}, p99,9 {c.p99_9:.1f}, máximo {c.maximo:.0f}.",
              f"- Sinalizados com o limiar em 50 / 60 / 100 eventos: {int(c.sinalizados_50)} / "
              f"{int(c.sinalizados_60)} / {int(c.sinalizados_100)} (a regra usa 100).", '']
        lote = flags[flags.submissao_lote]
        if len(lote):
            # Década do primeiro rating: '2016-03-01'[:3] = '201' -> '2010s'
            decadas =(lote.primeiro_dia.str[:3] + '0s').value_counts().sort_index()
            L.append('Submissão em lote por década do primeiro rating: '
                     + ', '.join(f'{d}: {n}' for d, n in decadas.items()) + '.')
            L.append('')
        susp = flags[flags.regra_a]
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
    (pasta / 'analises_relatorio.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


def correr_analises(cfg):
    """Corre as queries de sql/analise/, verifica os resultados e escreve o relatório."""
    ds = cfg['dataset']
    pasta = cfg['paths']['results'] / ds / 'analises'
    pasta.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()

    # 1. Queries: cada uma grava o seu CSV, por ordem alfabética
    con, origem = ligar_analises(cfg)
    print(f'[analises] dataset={ds}')
    resumo = []
    for ficheiro in sorted(PASTA_SQL.glob('*.sql')):
        nome = ficheiro.stem
        linhas, seg = correr(con, nome, ficheiro, FONTES_DUCKDB, pasta / f'{nome}.csv')
        resumo.append({'query': nome, 'linhas': linhas, 'segundos': round(seg, 4)})
        print(f'  {nome:24} {seg * 1000:9.1f} ms  {linhas:>9,} linhas'.replace(',', ' '))
    con.close()
    pd.DataFrame(resumo).to_csv(pasta / 'analises_resumo.csv', index=False)

    # 2. Verificações, relatório e, se alguma falhar, erro (o pipeline pára)
    verif = verificar(pasta, ds) + referencia_bots(pasta, ds)
    segundos = time.perf_counter() - t0
    relatorio_analises(pasta, ds, origem, resumo, verif, segundos)
    for nome, valor, ok in verif:
        print(f"  [{'ok' if ok else 'FALHA'}] {nome}: {valor}")
    print(f'[analises] {len(resumo)} queries em {pasta.relative_to(ROOT)} ({segundos:.1f} s)')

    falhas = [v for v in verif if not v[2]]
    if falhas:
        raise SystemExit(f'[analises] {len(falhas)} verificações falharam (ver analises_relatorio.md)')


def main():
    """Corre a EDA e as análises."""
    cfg = load_config()
    correr_eda(cfg['dataset'], cfg['paths']['results'])
    correr_analises(cfg)


if __name__ == '__main__':
    main()
