"""
07_imdb.py - Passo imdb (fase 3): juntar o IMDb ao MovieLens e comparar as notas.

Objetivo:
    Mostrar que o pipeline se adapta a um dataset complementar e responder a duas perguntas:
      P1. As notas do MovieLens e do IMDb concordam? Onde e quanto divergem?
      P2. Que diferenças existem entre os tipos de utilizadores?
    O IMDb só publica agregados por filme (nota média e n.º de votos), sem dados por
    utilizador. Por isso a P2 segmenta os utilizadores do MovieLens e compara a concordância
    de cada segmento com a nota do IMDb.

    Etapas:
      1. Download do title.ratings e do title.basics (só se ainda não existirem).
      2. Conversão TSV -> Parquet com o DuckDB: \\N passa a nulo, tipos corretos e géneros em
         lista. Regista os tamanhos (TSV, TSV comprimido e Parquet) em results/sizes.csv.
         Só converte se o Parquet não existir ou for mais antigo do que o TSV.
      3. Análises: sql/imdb/*.sql, um CSV por query em results/<dataset>/imdb/.
      4. Sensibilidade: a concordância (03) com e sem limiares mínimos de votos.
      5. Benchmark: o join MovieLens x IMDb (00_filmes.sql) em CSV/TSV e em Parquet,
         mediana de 3 corridas, em results/benchmarks.csv.
      6. (Opcional, --emular-athena) as versões de sql/athena/imdb/ emuladas no DuckDB e
         comparadas com as versões DuckDB.
      7. Figuras (estilo NOVA do 04_eda.py) e relatório imdb_relatorio.md.

Entradas:
    https://datasets.imdbws.com/title.ratings.tsv.gz e title.basics.tsv.gz
    (uso pessoal e não comercial; ver README) -> data/imdb/raw/
    data/<dataset>/parquet/ratings.parquet, movies.parquet e links.parquet (passos ingest e parquet)
    data/<dataset>/csv/*.csv (só para o benchmark em CSV)
    sql/imdb/*.sql e sql/analise/10_flag_bots.sql (segmento de bots da P2)
    config.yaml, secção imdb (limiares)

Saídas:
    data/imdb/parquet/title_ratings.parquet, title_basics.parquet, qualidade.csv
    results/<dataset>/imdb/<query>.csv, sensibilidade.csv, imdb_qualidade.csv,
                           figuras PNG e imdb_relatorio.md
    results/sizes.csv (dataset = imdb) e results/benchmarks.csv (query = imdb_join)

Como correr:
    python scripts/07_imdb.py --dataset small
    python scripts/07_imdb.py --dataset small --emular-athena
    (ou, dentro do pipeline: python run_pipeline.py --dataset small --steps imdb)

Notas:
    - O 1M não tem links.csv (não tem o imdbId de cada filme), por isso o passo só corre
      com o small e o 32M.
    - A sessão DuckDB fica em UTC, como nos outros passos.
"""
import argparse
import gzip
import importlib.util
import statistics
import time
import urllib.request
from datetime import datetime, timezone
from string import Template

import duckdb
import pandas as pd

from common import DATASETS, ROOT, SCHEMAS, append_row, duckdb_columns, load_config, now, size_on_disk


def carregar_script(nome):
    """Importa um script de scripts/ cujo nome começa por um algarismo (ex.: 04_eda.py).

    Um "import 04_eda" normal não funciona, porque os nomes de módulos em Python não podem
    começar por um algarismo. O importlib carrega o ficheiro pelo caminho. Só são executadas
    as definições (o main() desses scripts só corre quando são chamados diretamente).
    """
    caminho = ROOT / 'scripts' / f'{nome}.py'
    spec = importlib.util.spec_from_file_location(f'm_{nome}', caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# Reutilizamos o estilo das figuras do 04_eda.py e a emulação do Athena do 05_analises.py
eda = carregar_script('04_eda')
analises = carregar_script('05_analises')
plt = eda.plt          # o 04_eda.py já escolheu o backend "Agg" (figuras sem janela)
NOVA = eda.NOVA

PASTA_SQL = ROOT / 'sql' / 'imdb'
PASTA_SQL_ATHENA = ROOT / 'sql' / 'athena' / 'imdb'
SQL_FLAG_BOTS = ROOT / 'sql' / 'analise' / '10_flag_bots.sql'
RUNS = 3   # corridas do benchmark

# Ficheiros do IMDb: nome da tabela -> nome do ficheiro no site
FICHEIROS_IMDB = {'title_ratings': 'title.ratings.tsv.gz', 'title_basics': 'title.basics.tsv.gz'}


# ---------------------------------------------------------------------------
# Opções
# ---------------------------------------------------------------------------
def parse_args():
    """Lê --dataset, --forcar-conversao e --emular-athena."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', choices=list(DATASETS), help='sobrepõe o valor de config.yaml')
    ap.add_argument('--forcar-conversao', action='store_true',
                    help='volta a converter o IMDb para Parquet, mesmo que já exista')
    ap.add_argument('--emular-athena', action='store_true',
                    help='corre também as versões de sql/athena/imdb/ emuladas no DuckDB e compara')
    return ap.parse_args()


def parametros_imdb(cfg):
    """Lê a secção imdb do config.yaml e calcula o corte da era em segundos (UTC)."""
    imdb = cfg.get('imdb') or {}
    # Tipos de título do IMDb que entram nas análises, escritos como lista SQL: ('movie')
    tipos = imdb.get('tipos_titulo') or ['movie']
    tipos_sql = '(' + ', '.join("'" + str(tipo).replace("'", "''") + "'" for tipo in tipos) + ')'
    corte = datetime.strptime(str(imdb.get('corte_era', '2003-02-18')), '%Y-%m-%d').replace(tzinfo=timezone.utc)
    return {
        'url_base': imdb.get('url_base', 'https://datasets.imdbws.com/'),
        'min_ml': int(imdb.get('min_avaliacoes_ml', 50)),
        'min_imdb': int(imdb.get('min_votos_imdb', 1000)),
        'min_seg': int(imdb.get('min_avaliacoes_segmento', 5)),
        'n_quantis': int(imdb.get('n_quantis_popularidade', 5)),
        'tipos': [str(tipo) for tipo in tipos],
        'tipos_sql': tipos_sql,
        'corte_era': int(corte.timestamp()),          # 2003-02-18 -> 1045526400
        'corte_era_txt': corte.strftime('%d/%m/%Y'),
    }


# ---------------------------------------------------------------------------
# 1. Download
# ---------------------------------------------------------------------------
def descarregar(url, destino):
    """Descarrega url para destino, a não ser que já exista (como no 01_ingest.py)."""
    if destino.exists():
        print(f'  já existe, não descarrega: {destino.name}')
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Escreve primeiro num .part: se o download for interrompido, a próxima corrida recomeça
    tmp = destino.with_suffix(destino.suffix + '.part')
    print(f'  a descarregar {url}')
    try:
        with urllib.request.urlopen(url) as resposta, tmp.open('wb') as f:
            while True:
                bloco = resposta.read(1024 * 1024)   # 1 MB de cada vez, sem encher a memória
                if not bloco:
                    break
                f.write(bloco)
    except OSError as erro:
        raise SystemExit(f'Erro ao descarregar {url}: {erro}\n'
                         f'Alternativa: copiar à mão o ficheiro {destino.name} para {destino.parent.relative_to(ROOT)}/ '
                         'e voltar a correr.') from erro
    tmp.rename(destino)
    print(f'  {destino.stat().st_size / 1e6:.1f} MB')


# ---------------------------------------------------------------------------
# 2. Conversão para Parquet
# ---------------------------------------------------------------------------
def ler_tsv(caminho):
    """Texto SQL que lê um TSV do IMDb com todas as colunas como texto.

    - delim='\\t': separador tabulação;
    - quote='' e escape='': o IMDb não usa aspas, e há títulos com aspas lá dentro;
    - nullstr='\\N': o IMDb escreve \\N quando não há valor; passa a nulo;
    - all_varchar: tudo como texto. Os tipos são postos depois, com TRY_CAST, para contarmos
      os valores que não se convertem em vez de o script falhar.
    O DuckDB descomprime o .gz sozinho, a partir da extensão.
    """
    return (f"read_csv('{caminho.as_posix()}', delim='\\t', header=true, quote='', escape='', "
            "nullstr='\\N', all_varchar=true)")


def sql_tipar(tabela, fonte):
    """SELECT que põe os tipos certos em cada coluna de uma tabela do IMDb (fonte = texto SQL)."""
    if tabela == 'title_ratings':
        return f"""SELECT tconst,
                          TRY_CAST(averageRating AS DOUBLE) AS averageRating,
                          TRY_CAST(numVotes AS INTEGER)     AS numVotes
                   FROM {fonte}"""
    # title_basics: isAdult é 0/1 -> booleano; anos e duração -> inteiros; géneros "Drama,Romance" -> lista
    return f"""SELECT tconst, titleType, primaryTitle, originalTitle,
                      TRY_CAST(isAdult AS INTEGER) = 1          AS isAdult,
                      TRY_CAST(startYear AS INTEGER)            AS startYear,
                      TRY_CAST(endYear AS INTEGER)              AS endYear,
                      TRY_CAST(runtimeMinutes AS INTEGER)       AS runtimeMinutes,
                      string_split(genres, ',')                 AS genres
               FROM {fonte}"""


# Colunas convertidas para número em cada tabela (para contar os valores que falham a conversão)
COLUNAS_NUMERICAS = {'title_ratings': ['averageRating', 'numVotes'],
                     'title_basics': ['isAdult', 'startYear', 'endYear', 'runtimeMinutes']}


def tamanho_descomprimido(caminho_gz):
    """Tamanho em bytes do TSV depois de descomprimido (lê o .gz até ao fim, sem o gravar)."""
    total = 0
    with gzip.open(caminho_gz, 'rb') as f:
        while True:
            bloco = f.read(4 * 1024 * 1024)
            if not bloco:
                break
            total += len(bloco)
    return total


def converter_imdb(raw_dir, pq_dir, forcar):
    """Converte os dois TSV do IMDb em Parquet e regista tamanhos, tempos e qualidade."""
    pq_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute('SET preserve_insertion_order = false')   # poupa memória, como no 02_to_parquet.py
    qualidade = []
    for tabela, ficheiro in FICHEIROS_IMDB.items():
        tsv = raw_dir / ficheiro
        pq = pq_dir / f'{tabela}.parquet'
        # Só converte se for preciso: Parquet em falta, mais antigo do que o TSV, ou --forcar-conversao
        if pq.exists() and pq.stat().st_mtime > tsv.stat().st_mtime and not forcar:
            print(f'  {tabela:14} Parquet já atualizado, não converte')
            continue

        t0 = time.perf_counter()
        con.execute(f"COPY ({sql_tipar(tabela, ler_tsv(tsv))}) TO '{pq.as_posix()}' (FORMAT parquet)")
        segundos = time.perf_counter() - t0

        # Verificações: mesmo n.º de linhas e quantos valores numéricos falharam a conversão
        # (texto que existia, não era \N, mas não é um número)
        n_tsv = con.execute(f'SELECT COUNT(*) FROM {ler_tsv(tsv)}').fetchone()[0]
        n_pq = con.execute(f"SELECT COUNT(*) FROM read_parquet('{pq.as_posix()}')").fetchone()[0]
        if n_tsv != n_pq:
            raise SystemExit(f'Erro: {tabela} tem {n_tsv} linhas no TSV e {n_pq} no Parquet')
        for coluna in COLUNAS_NUMERICAS[tabela]:
            falhas, nulos = con.execute(f"""
                SELECT count_if({coluna} IS NOT NULL AND TRY_CAST({coluna} AS DOUBLE) IS NULL),
                       count_if({coluna} IS NULL)
                FROM {ler_tsv(tsv)}""").fetchone()
            qualidade.append({'tabela': tabela, 'coluna': coluna, 'linhas': n_tsv,
                              'nulos_\\N': nulos, 'falhas_conversao': falhas})

        tsv_mb = tamanho_descomprimido(tsv) / 1e6
        linha = {'run_at': now(), 'dataset': 'imdb', 'table': tabela,
                 'csv_mb': round(tsv_mb, 2), 'parquet_mb': round(size_on_disk(pq) / 1e6, 2),
                 'parquet_by_year_mb': '', 'n_partitions': '', 'seconds': round(segundos, 3),
                 'seconds_by_year': '', 'tsv_gz_mb': round(size_on_disk(tsv) / 1e6, 2)}
        append_row(ROOT / 'results' / 'sizes.csv', linha)
        print(f"  {tabela:14} TSV {linha['csv_mb']:>8.1f} MB (gz {linha['tsv_gz_mb']:.1f} MB) -> "
              f"Parquet {linha['parquet_mb']:>7.1f} MB em {segundos:.1f} s, {n_pq:,} linhas".replace(',', ' '))

    # A tabela de qualidade fica junto ao Parquet (é a mesma para todos os datasets do MovieLens)
    if qualidade:
        pd.DataFrame(qualidade).to_csv(pq_dir / 'qualidade.csv', index=False)
    con.close()


# ---------------------------------------------------------------------------
# 3. Ligação e análises
# ---------------------------------------------------------------------------
def ligar(cfg, pq_imdb):
    """Ligação DuckDB em UTC com views para o MovieLens (Parquet) e o IMDb (Parquet)."""
    pasta = cfg['paths']['parquet']
    if not (pasta / 'links.parquet').exists():
        raise SystemExit(f"Erro: não existe {(pasta / 'links.parquet').relative_to(ROOT)}. "
                         'O passo imdb precisa do links.csv (imdbId de cada filme), que o 1M não tem. '
                         'Usa o small ou o 32M, depois dos passos ingest e parquet.')
    con = duckdb.connect()
    con.execute("SET TimeZone = 'UTC'")
    for tabela in ('ratings', 'movies', 'links'):
        con.execute(f"CREATE VIEW {tabela}_ml AS SELECT * FROM read_parquet('{(pasta / f'{tabela}.parquet').as_posix()}')")
    for tabela in FICHEIROS_IMDB:
        con.execute(f"CREATE VIEW {tabela} AS SELECT * FROM read_parquet('{(pq_imdb / f'{tabela}.parquet').as_posix()}')")
    return con


def fontes(p, ratings='ratings_ml', movies='movies_ml', links='links_ml',
           imdb_ratings='title_ratings', imdb_basics='title_basics'):
    """Valores que substituem os ${marcadores} nas queries (nomes das views e limiares)."""
    return {
        # ${ratings} tem sempre a coluna year (UTC), como no 03_benchmark.py e no 05_analises.py
        'ratings': f'(SELECT *, year(epoch_ms(timestamp * 1000)) AS year FROM {ratings})',
        'movies': movies, 'links': links,
        'imdb_ratings': imdb_ratings, 'imdb_basics': imdb_basics,
        'filmes': 'filmes', 'flag_bots': 'flag_bots',
        'min_ml': p['min_ml'], 'min_imdb': p['min_imdb'], 'min_seg': p['min_seg'],
        'n_quantis': p['n_quantis'], 'corte_era': p['corte_era'], 'tipos': p['tipos_sql'],
    }


def sql_de(ficheiro, valores):
    """Lê um .sql, tira as linhas de comentário, substitui os ${marcadores} e tira o ';' final.

    Os comentários saem antes da substituição: a linha "-- Parâmetros: ${ratings}" também tem
    marcadores e, se o valor tiver várias linhas (como no benchmark em CSV), só a primeira
    ficaria dentro do comentário e o resto partiria o SQL.
    """
    linhas = []
    for linha in ficheiro.read_text(encoding='utf-8').splitlines():
        if not linha.strip().startswith('--'):
            linhas.append(linha)
    return Template('\n'.join(linhas)).substitute(valores).strip().rstrip(';')


def materializar(con, valores, ficheiro_filmes=None):
    """Cria as tabelas temporárias flag_bots e filmes, que várias queries leem."""
    con.execute(f'CREATE OR REPLACE TEMP TABLE flag_bots AS {sql_de(SQL_FLAG_BOTS, valores)}')
    ficheiro_filmes = ficheiro_filmes or (PASTA_SQL / '00_filmes.sql')
    con.execute(f'CREATE OR REPLACE TEMP TABLE filmes AS {sql_de(ficheiro_filmes, valores)}')


def correr_queries(con, valores, saida):
    """Corre sql/imdb/01..08 e grava um CSV por query. Devolve a lista (query, linhas, segundos)."""
    resumo = []
    for ficheiro in sorted(PASTA_SQL.glob('*.sql')):
        if ficheiro.stem == '00_filmes':
            continue   # já está materializada na tabela filmes
        t0 = time.perf_counter()
        destino = saida / f'{ficheiro.stem}.csv'
        linhas = con.execute(f"COPY ({sql_de(ficheiro, valores)}) TO '{destino.as_posix()}' (HEADER)").fetchone()[0]
        resumo.append((ficheiro.stem, linhas, time.perf_counter() - t0))
        print(f'  {ficheiro.stem:22} {linhas:>6} linhas  {(time.perf_counter() - t0) * 1000:7.1f} ms')
    return resumo


# ---------------------------------------------------------------------------
# 4. Sensibilidade aos limiares
# ---------------------------------------------------------------------------
def sensibilidade(con, valores, p, saida):
    """Corre a concordância (03) com vários pares de limiares e grava sensibilidade.csv."""
    cenarios = [('sem limiares', 0, 0),
                (f"só MovieLens >= {p['min_ml']}", p['min_ml'], 0),
                (f"só IMDb >= {p['min_imdb']}", 0, p['min_imdb']),
                ('ambos (análise principal)', p['min_ml'], p['min_imdb']),
                ('ambos x 4 (mais exigente)', 4 * p['min_ml'], 4 * p['min_imdb'])]
    linhas = []
    for nome, min_ml, min_imdb in cenarios:
        v = dict(valores, min_ml=min_ml, min_imdb=min_imdb)   # cópia com os limiares do cenário
        df = con.execute(sql_de(PASTA_SQL / '03_concordancia.sql', v)).df()
        df.insert(0, 'cenario', nome)
        df.insert(1, 'min_avaliacoes_ml', min_ml)
        df.insert(2, 'min_votos_imdb', min_imdb)
        linhas.append(df)
    tabela = pd.concat(linhas, ignore_index=True)
    tabela.to_csv(saida / 'sensibilidade.csv', index=False)
    return tabela


# ---------------------------------------------------------------------------
# 5. Benchmark do join MovieLens x IMDb: CSV/TSV vs Parquet
# ---------------------------------------------------------------------------
def benchmark(cfg, p, pq_imdb, raw_imdb):
    """Mede o 00_filmes.sql (agregação + join) lendo CSV/TSV e lendo Parquet. Devolve as medianas."""
    csv_dir, pq_dir = cfg['paths']['csv'], cfg['paths']['parquet']
    resultados = {}
    for formato in ('csv', 'parquet'):
        tempos = []
        for _ in range(RUNS):
            # Ligação nova em cada corrida, para nenhuma aproveitar o trabalho da anterior
            con = duckdb.connect()
            con.execute("SET TimeZone = 'UTC'")
            if formato == 'csv':
                # MovieLens em CSV (com os tipos do common.SCHEMAS) e IMDb nos TSV comprimidos
                ml = {}
                for t in ('ratings', 'movies', 'links'):
                    ml[t] = (f"read_csv('{(csv_dir / f'{t}.csv').as_posix()}', header=true, delim=',', "
                             f"quote='\"', escape='\"', columns={duckdb_columns(SCHEMAS[t])})")
                imdb = {t: f'({sql_tipar(t, ler_tsv(raw_imdb / f))})' for t, f in FICHEIROS_IMDB.items()}
            else:
                ml = {t: f"read_parquet('{(pq_dir / f'{t}.parquet').as_posix()}')" for t in ('ratings', 'movies', 'links')}
                imdb = {t: f"read_parquet('{(pq_imdb / f'{t}.parquet').as_posix()}')" for t in FICHEIROS_IMDB}
            valores = fontes(p, ratings=ml['ratings'], movies=ml['movies'], links=ml['links'],
                             imdb_ratings=imdb['title_ratings'], imdb_basics=imdb['title_basics'])
            sql = sql_de(PASTA_SQL / '00_filmes.sql', valores)
            t0 = time.perf_counter()
            n = len(con.execute(sql).fetchall())
            tempos.append(time.perf_counter() - t0)
            con.close()
        mediana = statistics.median(tempos)
        resultados[formato] = (mediana, n)
        append_row(ROOT / 'results' / 'benchmarks.csv',
                   {'run_at': now(), 'dataset': cfg['dataset'], 'query': 'imdb_join', 'formato': formato,
                    'median_s': round(mediana, 4), 'n_rows': n})
        print(f'  imdb_join  {formato:8} {mediana * 1000:9.1f} ms  {n:>7} linhas (mediana de {RUNS})')
    return resultados


# ---------------------------------------------------------------------------
# 6. Emulação das versões Athena
# ---------------------------------------------------------------------------
def sem_nulos_texto(df):
    """Troca os valores em falta das colunas de texto por '' (para a comparação).

    Em pandas, NaN nunca é igual a NaN; sem isto, dois resultados com um título em falta na
    mesma linha seriam considerados diferentes.
    """
    df = df.copy()
    for coluna in df.columns:
        if not pd.api.types.is_numeric_dtype(df[coluna]):
            df[coluna] = df[coluna].astype(object).where(df[coluna].notna(), '')
    return df


def emular_athena(cfg, p, pq_imdb, saida):
    """Corre sql/athena/imdb/ numa ligação "à Trino" e compara com os CSV das versões DuckDB."""
    con = ligar(cfg, pq_imdb)
    # Versão DuckDB da tabela filmes, calculada ANTES de ligar a emulação, para a comparação
    con.execute('CREATE TEMP TABLE filmes_duckdb AS ' + sql_de(PASTA_SQL / '00_filmes.sql', fontes(p)))

    analises.preparar_emulacao(con)      # divisão inteira e macros (from_unixtime, ...)
    # ${ratings} sem partição, escrito como no athena_benchmark.py
    valores = fontes(p)
    valores['ratings'] = '(SELECT x.*, year(from_unixtime(x."timestamp")) AS year FROM ratings_ml AS x)'
    # flag_bots e filmes a partir das versões Athena
    con.execute('CREATE OR REPLACE TEMP TABLE flag_bots AS '
                + sql_de(ROOT / 'sql' / 'athena' / 'analise' / '10_flag_bots.sql', valores))
    con.execute('CREATE OR REPLACE TEMP TABLE filmes AS ' + sql_de(PASTA_SQL_ATHENA / '00_filmes.sql', valores))

    comparacao = []
    # 00_filmes: compara-se a tabela inteira, ordenada por movieId (a ordem do SELECT não é fixa)
    a = con.execute('SELECT * FROM filmes_duckdb ORDER BY movieId').df()
    b = con.execute('SELECT * FROM filmes ORDER BY movieId').df()
    ok, nota = analises.iguais(sem_nulos_texto(a), sem_nulos_texto(b))
    comparacao.append({'query': '00_filmes', 'linhas_athena': len(b), 'iguais': 'sim' if ok else 'NÃO', 'nota': nota})
    print(f"  {'00_filmes':22} {len(b):>6} linhas  iguais: {'sim' if ok else 'NÃO ' + nota}")

    for ficheiro in sorted(PASTA_SQL_ATHENA.glob('*.sql')):
        if ficheiro.stem == '00_filmes':
            continue
        b = con.execute(sql_de(ficheiro, valores)).df()
        csv_duckdb = saida / f'{ficheiro.stem}.csv'
        if not csv_duckdb.exists():
            ok, nota = False, 'sem versão DuckDB'
        else:
            ok, nota = analises.iguais(sem_nulos_texto(pd.read_csv(csv_duckdb)), sem_nulos_texto(b))
        comparacao.append({'query': ficheiro.stem, 'linhas_athena': len(b), 'iguais': 'sim' if ok else 'NÃO', 'nota': nota})
        print(f"  {ficheiro.stem:22} {len(b):>6} linhas  iguais: {'sim' if ok else 'NÃO ' + nota}")
    con.close()
    return comparacao


# ---------------------------------------------------------------------------
# 7. Figuras e relatório
# ---------------------------------------------------------------------------
def fig_dispersao(con, p, pasta, ds, figuras, conc):
    """Figura 1: nota no MovieLens (x2) contra nota no IMDb, um ponto por filme."""
    df = con.execute(f"""SELECT nota_ml_10, nota_imdb FROM filmes
                         WHERE nota_imdb IS NOT NULL AND n_ml >= {p['min_ml']}
                           AND votos_imdb >= {p['min_imdb']} AND tipo_imdb IN {p['tipos_sql']}""").df()
    fig, ax = plt.subplots(figsize=(7, 6.5))
    ax.scatter(df.nota_ml_10, df.nota_imdb, s=8, alpha=0.35, color=NOVA['verde_escuro'], edgecolor='none')
    ax.plot([1, 10], [1, 10], color=NOVA['cinza_medio'], linestyle='--', linewidth=1, label='notas iguais (y = x)')
    # Eixos iguais nos dois lados, do menor valor observado (arredondado para baixo) até 10
    limite_inf = max(1, int(min(df.nota_ml_10.min(), df.nota_imdb.min())))
    ax.set_xlim(limite_inf, 10)
    ax.set_ylim(limite_inf, 10)
    ax.set_xlabel('Nota média no MovieLens × 2 (escala 1–10)')
    ax.set_ylabel('Nota no IMDb (1–10)')
    ax.set_title('MovieLens vs IMDb: uma nota por filme')
    c = conc.iloc[0]
    ax.text(0.02, 0.98, f"{eda.num(c.filmes)} filmes\nPearson {eda.num(c.pearson, 2)} · Spearman {eda.num(c.spearman, 2)}\n"
            f"gap médio IMDb − ML {eda.num(c.gap_medio, 2)}", transform=ax.transAxes, va='top', fontsize=9,
            color=NOVA['cinza_escuro'])
    ax.legend(loc='lower right')
    eda.guardar(fig, pasta, 'fig1_dispersao_ml_imdb.png', ds, figuras)


def barras_gap(ax, rotulos, gap, inf, sup):
    """Barras horizontais com o gap médio e o intervalo de confiança a 95% (barra de erro)."""
    cores = []
    for g in gap:
        if g >= 0:
            cores.append(NOVA['verde'])        # IMDb acima
        else:
            cores.append(NOVA['cinza_medio'])  # MovieLens acima
    erro = [gap - inf, sup - gap]   # distância da média a cada extremo do IC
    ax.barh(rotulos, gap, xerr=erro, color=cores, edgecolor=NOVA['cinza'], linewidth=0.4,
            error_kw={'ecolor': NOVA['cinza_escuro'], 'elinewidth': 0.8, 'capsize': 2})
    ax.axvline(0, color=NOVA['cinza_escuro'], linewidth=0.8)
    ax.invert_yaxis()   # o primeiro da lista fica em cima


def fig_genero(saida, pasta, ds, figuras):
    """Figura 2: gap médio por género (MovieLens), com IC 95%."""
    df = pd.read_csv(saida / '04_gap_genero.csv')
    fig, ax = plt.subplots(figsize=(8, 6.5))
    rotulos = [f'{g} ({n})' for g, n in zip(df.genero, df.filmes)]
    barras_gap(ax, rotulos, df.gap_medio, df.gap_ic95_inf, df.gap_ic95_sup)
    ax.set_xlabel('Gap médio IMDb − MovieLens×2 (pontos, escala 1–10), com IC 95%')
    ax.set_title('Onde o IMDb e o MovieLens divergem: por género')
    eda.guardar(fig, pasta, 'fig2_gap_genero.png', ds, figuras)


def fig_decada(saida, pasta, ds, figuras):
    """Figura 3: gap médio por década de estreia, com a banda do IC 95%."""
    df = pd.read_csv(saida / '05_gap_decada.csv')
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.fill_between(df.decada, df.gap_ic95_inf, df.gap_ic95_sup, color=NOVA['verde_claro'], alpha=0.8, label='IC 95%')
    ax.plot(df.decada, df.gap_medio, marker='o', color=NOVA['verde_escuro'], linewidth=2, label='gap médio')
    ax.axhline(0, color=NOVA['cinza_escuro'], linewidth=0.8)
    for x, y, n in zip(df.decada, df.gap_medio, df.filmes):
        ax.annotate(str(n), (x, y), textcoords='offset points', xytext=(0, 6), ha='center', fontsize=7,
                    color=NOVA['cinza'])
    ax.set_xlabel('Década de estreia (IMDb startYear); número = filmes')
    ax.set_ylabel('IMDb − MovieLens×2')
    ax.set_title('Gap por década de estreia')
    ax.legend(loc='best')
    eda.guardar(fig, pasta, 'fig3_gap_decada.png', ds, figuras)


def fig_segmentos(saida, pasta, ds, figuras):
    """Figura 4: gap e Spearman por segmento de utilizadores (P2), um painel por tipo."""
    df = pd.read_csv(saida / '08_segmentos.csv')
    tipos = ['atividade', 'era', 'bots (PROVISÓRIO)']   # ordem dos painéis
    # Altura de cada painel proporcional ao n.º de barras (um painel vazio fica baixo)
    alturas = []
    for tipo in tipos:
        n_barras = int(((df.tipo == tipo) & (df.filmes_comuns > 0)).sum())
        alturas.append(max(n_barras, 1))
    fig, eixos = plt.subplots(len(tipos), 1, figsize=(8, 1.5 + 0.9 * sum(alturas)), squeeze=False,
                              gridspec_kw={'height_ratios': alturas})
    for ax, tipo in zip(eixos[:, 0], tipos):
        sub = df[df.tipo == tipo].sort_values('ordem')
        com_filmes = sub[sub.filmes_comuns > 0]
        rotulos = []
        for _, r in com_filmes.iterrows():
            rotulos.append(f"{r.segmento}\n{int(r.utilizadores)} utiliz. · Spearman {eda.num(r.spearman, 2)}")
        if len(com_filmes):
            barras_gap(ax, rotulos, com_filmes.gap_medio, com_filmes.gap_ic95_inf, com_filmes.gap_ic95_sup)
            n_filmes = int(com_filmes.filmes_comuns.iloc[0])
            ax.set_title(f'{tipo}: {n_filmes} filmes comuns', fontsize=11)
        else:
            # Sem filmes comuns (ex.: muito poucos utilizadores sinalizados): só uma nota de texto
            ax.axis('off')
            n_por_segmento = ', '.join(f'{s}: {int(n)} utiliz.' for s, n in zip(sub.segmento, sub.utilizadores))
            ax.text(0, 0.5, f'{tipo}: sem filmes avaliados por todos os segmentos ({n_por_segmento})',
                    ha='left', va='center', transform=ax.transAxes, fontsize=10, color=NOVA['cinza_escuro'])
    eixos[-1, 0].set_xlabel('Gap médio IMDb − segmento×2, com IC 95% (mesmos filmes em cada tipo)')
    fig.suptitle('P2: concordância com o IMDb por tipo de utilizador do MovieLens', x=0.01, ha='left',
                 fontweight='bold', color=NOVA['cinza_escuro'])
    fig.tight_layout()
    eda.guardar(fig, pasta, 'fig4_gap_segmentos.png', ds, figuras)


def tabela_md(df, colunas, casas=3):
    """Tabela Markdown com as colunas pedidas; números com vírgula decimal."""
    linhas = ['| ' + ' | '.join(colunas) + ' |', '|' + '---|' * len(colunas)]
    for _, r in df[colunas].iterrows():
        valores = []
        for v in r:
            if isinstance(v, float):
                valores.append('' if pd.isna(v) else eda.num(v, casas))
            else:
                valores.append(str(v))
        linhas.append('| ' + ' | '.join(valores) + ' |')
    return '\n'.join(linhas)


def interpretar_correlacao(r):
    """Texto curto para o valor de uma correlação (convenção habitual em ciências sociais)."""
    if pd.isna(r):
        return 'indefinida'
    if r >= 0.7:
        return 'forte'
    if r >= 0.4:
        return 'moderada'
    if r >= 0.2:
        return 'fraca'
    return 'muito fraca ou nula'


def escrever_relatorio(saida, ds, p, sens, bench, figuras, comparacao, segundos):
    """Escreve imdb_relatorio.md com os números principais, a interpretação e as limitações."""
    lig = pd.read_csv(saida / '01_ligacao.csv')
    tipos = pd.read_csv(saida / '02_ligacao_tipos.csv')
    conc = pd.read_csv(saida / '03_concordancia.csv').iloc[0]
    gen = pd.read_csv(saida / '04_gap_genero.csv')
    dec = pd.read_csv(saida / '05_gap_decada.csv')
    pop = pd.read_csv(saida / '06_gap_popularidade.csv')
    top = pd.read_csv(saida / '07_top_divergencia.csv')
    seg = pd.read_csv(saida / '08_segmentos.csv')

    total = int(lig.filmes.sum())
    ligados = int(lig[lig.categoria.str.startswith('4')].filmes.sum())
    sinal = 'mais alta' if conc.gap_medio > 0 else 'mais baixa'
    ic_inclui_zero = conc.gap_ic95_inf <= 0 <= conc.gap_ic95_sup

    L = [f'# IMDb vs MovieLens · MovieLens {ds}', '',
         f'Gerado por `scripts/07_imdb.py` em {segundos:.1f} s (sessão DuckDB em UTC).', '',
         '## Método', '',
         '- **Fontes:** `title.ratings.tsv.gz` e `title.basics.tsv.gz` de <https://datasets.imdbws.com/> '
         '(uso pessoal e não comercial), ligados ao MovieLens pelo `imdbId` do `links.csv`.',
         "- **Ligação:** `tconst = 'tt' || imdbId`, com `lpad(imdbId, 7, '0')` só para ids com menos de 7 "
         'algarismos. O `lpad` sozinho cortaria os ids de 8 algarismos (`lpad(\'12345678\', 7, \'0\') = \'1234567\'`) '
         'e ligaria esses filmes a títulos errados.',
         '- **Escala:** nota do MovieLens × 2. Passa a escala de 0,5–5 para 1–10, com os mesmos extremos do IMDb '
         '(0,5 → 1 e 5 → 10). É linear, por isso não muda a ordem dos filmes nem as correlações; só torna o gap '
         'legível em pontos do IMDb. **Gap = IMDb − MovieLens×2**: positivo quando o IMDb dá nota mais alta.',
         f"- **Limiares (config.yaml):** pelo menos {p['min_ml']} avaliações no MovieLens e {p['min_imdb']} votos "
         'no IMDb. Com poucas avaliações a média é instável. A secção "Sensibilidade" repete a análise sem e com '
         'outros limiares.',
         f"- **Tipo de título:** só entram nas análises os títulos do tipo {', '.join(p['tipos'])} "
         '(`titleType` do IMDb; `imdb.tipos_titulo` no config.yaml). Séries, episódios, curtas, vídeos e '
         'filmes para TV ficam de fora (categoria 5 da ligação).',
         '- **IC 95%:** média ± 1,96 × desvio-padrão / √n. **Spearman:** Pearson sobre as posições, com a '
         'posição média nos empates.', '',
         '## Ligação entre as fontes', '',
         f'{eda.num(ligados)} de {eda.num(total)} filmes avaliados no MovieLens ({eda.num(100 * ligados / total, 1)}%) '
         f"ligam a um título do IMDb com nota e do tipo {', '.join(p['tipos'])}, e entram nas análises.", '',
         tabela_md(lig, ['categoria', 'filmes', 'pct_filmes', 'avaliacoes_ml', 'pct_avaliacoes_ml'], 1), '',
         'Porquê: a categoria 2 são ids que já não existem no `title.basics` (o IMDb remove ou funde títulos e o '
         'ficheiro público não diz qual); a 3 são títulos sem votos no `title.ratings`.', '',
         'Tipo de título dos filmes ligados:', '',
         tabela_md(tipos, ['tipo_imdb', 'filmes', 'pct_filmes', 'com_nota_imdb'], 1), '',
         '## P1. As notas concordam?', '',
         tabela_md(pd.DataFrame([conc]), ['filmes', 'media_ml_10', 'media_imdb', 'gap_medio', 'gap_ic95_inf',
                                          'gap_ic95_sup', 'gap_abs_medio', 'pct_imdb_acima', 'pearson', 'spearman']), '',
         f"**Interpretação.** A correlação é {interpretar_correlacao(conc.pearson)} (Pearson "
         f"{eda.num(conc.pearson, 2)}, Spearman {eda.num(conc.spearman, 2)}): os dois sites ordenam os filmes de "
         f"forma {'parecida' if conc.spearman >= 0.6 else 'só em parte parecida'}. Em média, o IMDb dá uma nota "
         f"{sinal} do que o MovieLens×2, por {eda.num(abs(conc.gap_medio), 2)} pontos "
         f"(IC 95% {eda.num(conc.gap_ic95_inf, 2)} a {eda.num(conc.gap_ic95_sup, 2)}"
         f"{'; o intervalo inclui o zero' if ic_inclui_zero else ''}). Filme a filme, a diferença absoluta média é "
         f"{eda.num(conc.gap_abs_medio, 2)} pontos.", '',
         '### Por género', '',
         tabela_md(gen, ['genero', 'filmes', 'gap_medio', 'gap_ic95_inf', 'gap_ic95_sup', 'pearson', 'spearman']), '',
         '### Por década de estreia', '',
         tabela_md(dec, ['decada', 'filmes', 'gap_medio', 'gap_ic95_inf', 'gap_ic95_sup', 'pearson', 'spearman']), '',
         f"### Por popularidade no IMDb ({p['n_quantis']} grupos pelo n.º de votos; 1 = menos votados)", '',
         tabela_md(pop, ['quantil', 'filmes', 'votos_min', 'votos_max', 'gap_medio', 'gap_ic95_inf', 'gap_ic95_sup',
                         'pearson', 'spearman']), '',
         '### Maior divergência', '',
         tabela_md(top, ['sentido', 'posicao', 'title', 'ano_estreia', 'tipo_imdb', 'n_ml', 'nota_ml_10',
                         'votos_imdb', 'nota_imdb', 'gap'], 2), '',
         '### Sensibilidade aos limiares', '',
         tabela_md(sens, ['cenario', 'filmes', 'gap_medio', 'gap_ic95_inf', 'gap_ic95_sup', 'gap_abs_medio',
                          'pearson', 'spearman']), '',
         '## P2. Diferenças entre tipos de utilizadores', '',
         '> **Limitação:** o IMDb só publica agregados por filme (nota média e n.º de votos), sem dados por '
         'utilizador. Não é possível comparar utilizadores do IMDb com utilizadores do MovieLens. O que se compara '
         'é a nota média de cada **segmento de utilizadores do MovieLens** em cada filme com a nota agregada do '
         'IMDb, sobre o **mesmo conjunto de filmes** dentro de cada tipo de segmento.', '',
         f"Um filme entra num tipo se cada segmento desse tipo o avaliou pelo menos {p['min_seg']} vezes e se tem "
         f"pelo menos {p['min_imdb']} votos no IMDb. Era: primeira avaliação antes ou a partir de "
         f"{p['corte_era_txt']} (início das meias estrelas). "
         '**Os resultados do tipo "bots" são PROVISÓRIOS: as regras do `10_flag_bots.sql` ainda estão a ser '
         'validadas pelo Luís.**', '',
         tabela_md(seg, ['tipo', 'segmento', 'utilizadores', 'filmes_comuns', 'avaliacoes', 'media_segmento_10',
                         'media_imdb', 'gap_medio', 'gap_ic95_inf', 'gap_ic95_sup', 'pearson', 'spearman']), '',
         '## Desempenho', '']
    # Tamanhos: a última conversão de cada tabela do IMDb registada em results/sizes.csv
    tamanhos = pd.read_csv(ROOT / 'results' / 'sizes.csv')
    tamanhos = tamanhos[tamanhos.dataset == 'imdb'].drop_duplicates('table', keep='last')
    if len(tamanhos):
        L += ['| Tabela | TSV (MB) | TSV.gz (MB) | Parquet snappy (MB) | Parquet / TSV |', '|---|---:|---:|---:|---:|']
        for _, t in tamanhos.iterrows():
            L.append(f"| {t['table']} | {eda.num(t.csv_mb, 1)} | {eda.num(t.tsv_gz_mb, 1)} | "
                     f"{eda.num(t.parquet_mb, 1)} | {eda.num(100 * t.parquet_mb / t.csv_mb, 0)}% |")
        L += ['', 'O Parquet ocupa muito menos do que o TSV descomprimido. Comparado com o TSV.gz, o '
              '`title_basics` (quase só texto: títulos) pode até ficar maior, porque o gzip comprime o '
              'ficheiro inteiro. A vantagem do Parquet está na leitura: uma query lê só as colunas de que '
              'precisa (no join, só `tconst` e `titleType` das 9 colunas do `title_basics`), sem '
              'descomprimir nem converter o resto.', '']
    ganho = bench['csv'][0] / bench['parquet'][0] if bench['parquet'][0] else float('nan')
    L += [f"Join MovieLens × IMDb (`00_filmes.sql`), mediana de {RUNS} corridas: CSV/TSV.gz "
          f"{eda.num(bench['csv'][0] * 1000, 0)} ms, Parquet {eda.num(bench['parquet'][0] * 1000, 0)} ms "
          f"({eda.num(ganho, 1)} vezes mais rápido). O CSV/TSV inclui descomprimir o gzip e converter texto em "
          'números em cada corrida. Os tamanhos estão em `results/sizes.csv` (dataset `imdb`).', '']
    if comparacao:
        L += ['## Versões Athena emuladas no DuckDB', '',
              '| Query | Linhas | Iguais | Nota |', '|---|---:|---|---|']
        for c in comparacao:
            L.append(f"| {c['query']} | {c['linhas_athena']} | {c['iguais']} | {c['nota']} |")
        L.append('')
    L += ['## Limitações', '',
          '- O IMDb não tem dados por utilizador (ver P2).',
          '- Os votos do IMDb são de outra população e de outra época: o ficheiro é atualizado todos os dias, '
          'e o MovieLens tem avaliações de 1995 a 2023. Parte do gap pode ser só diferença de população ou de tempo.',
          '- O IMDb pondera a nota média com um método que não publica; o MovieLens usa a média simples.',
          '- Os filmes que não ligam (ver "Ligação") ficam de fora; são poucos e têm poucas avaliações.',
          '- O segmento de bots é provisório e, nos datasets pequenos, tem muito poucos utilizadores.', '',
          '## Figuras', '']
    for f in figuras:
        L.append(f'- `{f}`')
    (saida / 'imdb_relatorio.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


# ---------------------------------------------------------------------------
def main():
    """Download, conversão, análises, sensibilidade, benchmark, figuras e relatório."""
    args = parse_args()
    cfg = load_config(args.dataset)
    ds = cfg['dataset']
    p = parametros_imdb(cfg)
    raw_imdb = ROOT / cfg['data_dir'] / 'imdb' / 'raw'
    pq_imdb = ROOT / cfg['data_dir'] / 'imdb' / 'parquet'
    saida = ROOT / 'results' / ds / 'imdb'
    saida.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    print(f'[imdb] dataset={ds} limiares: ML >= {p["min_ml"]}, IMDb >= {p["min_imdb"]}; tipos: {p["tipos_sql"]}')

    # 1 e 2. IMDb: download e Parquet (iguais para todos os datasets do MovieLens)
    for ficheiro in FICHEIROS_IMDB.values():
        descarregar(p['url_base'] + ficheiro, raw_imdb / ficheiro)
    converter_imdb(raw_imdb, pq_imdb, args.forcar_conversao)
    if (pq_imdb / 'qualidade.csv').exists():
        pd.read_csv(pq_imdb / 'qualidade.csv').to_csv(saida / 'imdb_qualidade.csv', index=False)

    # 3. Análises
    con = ligar(cfg, pq_imdb)
    valores = fontes(p)
    materializar(con, valores)
    print('[imdb] análises')
    correr_queries(con, valores, saida)

    # 4. Sensibilidade
    sens = sensibilidade(con, valores, p, saida)

    # 7a. Figuras (a dispersão lê a tabela filmes, por isso faz-se antes de fechar a ligação)
    eda.aplicar_estilo_nova()
    figuras = []
    fig_dispersao(con, p, saida, ds, figuras, pd.read_csv(saida / '03_concordancia.csv'))
    con.close()
    fig_genero(saida, saida, ds, figuras)
    fig_decada(saida, saida, ds, figuras)
    fig_segmentos(saida, saida, ds, figuras)

    # 5. Benchmark
    print('[imdb] benchmark do join (CSV/TSV vs Parquet)')
    bench = benchmark(cfg, p, pq_imdb, raw_imdb)

    # 6. Emulação do Athena (opcional)
    comparacao = []
    if args.emular_athena:
        print('[imdb] versões Athena emuladas no DuckDB')
        comparacao = emular_athena(cfg, p, pq_imdb, saida)

    # 7b. Relatório
    segundos = time.perf_counter() - t0
    escrever_relatorio(saida, ds, p, sens, bench, figuras, comparacao, segundos)
    print(f'[imdb] resultados em {saida.relative_to(ROOT)} ({segundos:.1f} s)')

    diferentes = [c for c in comparacao if c['iguais'] != 'sim']
    if diferentes:
        raise SystemExit(f'[imdb] {len(diferentes)} versões Athena emuladas diferem (ver imdb_relatorio.md)')


if __name__ == '__main__':
    main()
