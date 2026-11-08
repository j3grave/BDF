"""
prepare_cloud.py - Fase 2: preparar localmente os ficheiros que vão para o S3.

Objetivo:
    Criar em data/cloud/<pasta>/ um espelho exato do que vai ser enviado para o S3 e
    catalogado pelo Glue Data Catalog para consulta no Athena. O Glue e o Athena tratam
    cada pasta como uma tabela, por isso cada tabela fica na sua própria pasta e não há
    ficheiros soltos na raiz. Todas as tabelas são reescritas em Parquet com compressão
    zstd, sem alterar os tipos da fase 1 (não há casts). Os ratings ficam em duas versões
    (sem partição e particionados por ano) e há ainda uma cópia do ratings.csv, para
    comparar no Athena os bytes lidos em CSV e em Parquet.
    Este script não faz nenhuma chamada à AWS: só escreve ficheiros no disco local.

Entradas:
    data/<dataset>/parquet/<tabela>.parquet   criados pelo 02_to_parquet.py
    data/<dataset>/parquet/ratings_by_year/   idem (só para comparar as contagens por ano)
    data/<dataset>/csv/ratings.csv            criado pelo 01_ingest.py
    (data/<dataset> pode ser um symlink para outra cópia do repositório)

Saídas:
    data/cloud/<pasta>/ratings/ratings.parquet        ratings sem partição
    data/cloud/<pasta>/ratings_part/year=AAAA/*.parquet  ratings particionado por ano
    data/cloud/<pasta>/movies/, tags/, links/         uma tabela por pasta (o 1M só tem movies)
    data/cloud/<pasta>/ratings_csv/ratings.csv        cópia do CSV, byte a byte
    reports/cloud_manifest_<dataset>.md               manifesto (só se todas as verificações passarem)
    <pasta> é o nome da pasta do GroupLens: ml-latest-small, ml-1m ou ml-32m.

Como correr:
    python scripts/prepare_cloud.py --dataset small
    python scripts/prepare_cloud.py               (por omissão usa o dataset do config.yaml)
    O envio para o S3 é feito pelo passo cloud: python run_pipeline.py --dataset small --steps cloud
"""
import argparse
import shutil
import sys
import time

import duckdb

from common import DATASETS, ROOT, SCHEMAS, duckdb_columns, load_config, now, size_on_disk

# Mapeamento dos tipos do DuckDB para os tipos do DDL do Athena (Hive)
ATHENA_TYPES = {'INTEGER': 'int', 'BIGINT': 'bigint', 'DOUBLE': 'double', 'VARCHAR': 'string'}



def parse_args():
    """Lê a opção --dataset (small | 1m | 32m; por omissão, o do config.yaml, como nos outros passos)."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=list(DATASETS), help='dataset a preparar (sobrepõe o valor de config.yaml)')
    return parser.parse_args()


def mb(path):
    """Tamanho em MB (10^6 bytes, como no results/sizes.csv) de um ficheiro ou pasta."""
    return size_on_disk(path) / 1e6


def schema_of(con, glob, hive=False):
    """Lista [(coluna, tipo), ...] dos ficheiros Parquet indicados pelo glob."""
    rows = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{glob}', hive_partitioning={hive})").fetchall()
    return [(r[0], r[1]) for r in rows]


def count_of(con, glob, hive=False):
    """Número de linhas dos ficheiros Parquet indicados pelo glob."""
    return con.execute(f"SELECT count(*) FROM read_parquet('{glob}', hive_partitioning={hive})").fetchone()[0]


def compression_of(con, glob):
    """Compressões usadas nas colunas dos ficheiros Parquet (ex.: 'SNAPPY', 'ZSTD')."""
    rows = con.execute(f"SELECT DISTINCT compression FROM parquet_metadata('{glob}') ORDER BY 1").fetchall()
    return ', '.join(r[0] for r in rows)


def counts_by_year(con, glob):
    """Dicionário {ano: n.º de linhas} de uma pasta particionada por year=AAAA."""
    rows = con.execute(f"""
        SELECT year, count(*) FROM read_parquet('{glob}', hive_partitioning=true)
        GROUP BY year ORDER BY year
    """).fetchall()
    return {int(ano): n for ano, n in rows}


def check_structure(cloud_dir, tables):
    """Confirma que só há pastas de tabelas na raiz e só ficheiros da tabela em cada pasta.

    Devolve a lista de problemas encontrados (vazia se estiver tudo bem).
    """
    problemas = []
    esperadas = set(tables) | {'ratings_part', 'ratings_csv'}

    # Raiz: só pastas, e só as das tabelas (nada de .DS_Store, _SUCCESS, etc.)
    for item in cloud_dir.iterdir():
        if not item.is_dir():
            problemas.append(f'ficheiro solto na raiz: {item.name}')
        elif item.name not in esperadas:
            problemas.append(f'pasta inesperada na raiz: {item.name}')

    # Tabelas simples: só um ficheiro, <tabela>.parquet
    for table in tables:
        ficheiros = sorted(p.name for p in (cloud_dir / table).iterdir())
        if ficheiros != [f'{table}.parquet']:
            problemas.append(f'{table}/ devia ter só {table}.parquet e tem: {ficheiros}')

    # ratings_part: só pastas year=AAAA, cada uma só com ficheiros .parquet
    for item in (cloud_dir / 'ratings_part').iterdir():
        if not (item.is_dir() and item.name.startswith('year=') and item.name[5:].isdigit()):
            problemas.append(f'item inesperado em ratings_part/: {item.name}')
            continue
        for f in item.iterdir():
            if not (f.is_file() and f.suffix == '.parquet'):
                problemas.append(f'item inesperado em ratings_part/{item.name}/: {f.name}')

    # ratings_csv: só o ratings.csv
    ficheiros = sorted(p.name for p in (cloud_dir / 'ratings_csv').iterdir())
    if ficheiros != ['ratings.csv']:
        problemas.append(f'ratings_csv/ devia ter só ratings.csv e tem: {ficheiros}')
    return problemas


def write_manifest(path, info):
    """Escreve o manifesto em Markdown a partir do dicionário montado no main()."""
    ds, pasta = info['dataset'], info['pasta']
    L = []
    L.append(f'# Manifesto para a cloud: {pasta}')
    L.append('')
    L.append(f'- Dataset: `{ds}`')
    L.append(f'- Gerado em: {info["gerado_em"]} (DuckDB {duckdb.__version__}, {info["segundos"]:.1f} s)')
    L.append(f'- Pasta local: `data/cloud/{pasta}/` (origem: `data/{ds}/parquet/` e `data/{ds}/csv/ratings.csv`)')
    L.append(f'- Upload: `python run_pipeline.py --dataset {ds} --steps cloud` (envia para `s3://<bucket-dados>/{pasta}/`)')
    L.append('- Verificações: contagens iguais à origem, soma das partições igual a `ratings`, contagens por ano '
             'iguais ao `ratings_by_year` da fase 1, tipos iguais à origem, `year` só no nome das pastas, '
             'compressão zstd e só ficheiros da tabela em cada pasta. Todas passaram.')
    L.append('')
    L.append('> **Nota:** o benchmark DuckDB vs Athena deve ler os ficheiros de `data/cloud/`, que são '
             'exatamente os mesmos que vão para o S3 (zstd), e não os Parquet da fase 1 (snappy). '
             'Assim os dois motores leem os mesmos bytes.')
    L.append('')

    L.append('## Tabelas')
    L.append('')
    L.append('| Tabela | Caminho | Ficheiros | Tamanho (MB) | Linhas | Compressão |')
    L.append('|---|---|---:|---:|---:|---|')
    for t in info['tabelas']:
        L.append(f'| {t["nome"]} | `{t["caminho"]}` | {t["ficheiros"]} | {t["mb"]:.2f} | '
                 f'{t["linhas"]:,} | {t["compressao"]} |'.replace(',', ' '))
    L.append('')

    L.append('## Compressão: fase 1 vs cloud')
    L.append('')
    L.append('| Tabela | Origem (fase 1) | Compressão origem | MB origem | MB cloud (zstd) | Variação |')
    L.append('|---|---|---|---:|---:|---:|')
    for c in info['compressao']:
        variacao = (c['mb_cloud'] / c['mb_origem'] - 1) * 100 if c['mb_origem'] else 0
        L.append(f'| {c["nome"]} | `{c["origem"]}` | {c["comp_origem"]} | {c["mb_origem"]:.2f} | '
                 f'{c["mb_cloud"]:.2f} | {variacao:+.1f} % |')
    L.append('')
    L.append('O `ratings_csv` é uma cópia byte a byte do CSV, sem compressão.')
    L.append('')

    L.append('## Schemas')
    L.append('')
    for t in info['tabelas']:
        L.append(f'### {t["nome"]}')
        L.append('')
        L.append('| Coluna | Tipo (DuckDB) |')
        L.append('|---|---|')
        for coluna, tipo in t['schema']:
            L.append(f'| {coluna} | {tipo} |')
        if t['nome'] == 'ratings_part':
            L.append('| year *(partição: só no nome da pasta)* | BIGINT |')
        if t['nome'] == 'ratings_csv':
            L.append('')
            L.append('Tipos fixados pelo `SCHEMAS` do `common.py` ao ler o CSV (com cabeçalho, separador `,`).')
        L.append('')

    L.append('## ratings_part: partições')
    L.append('')
    L.append('| Ano | Linhas | Tamanho (MB) | Ficheiros |')
    L.append('|---|---:|---:|---:|')
    for p in info['particoes']:
        L.append(f'| {p["ano"]} | {p["linhas"]:,} | {p["mb"]:.2f} | {p["ficheiros"]} |'.replace(',', ' '))
    total_linhas = sum(p['linhas'] for p in info['particoes'])
    total_mb = sum(p['mb'] for p in info['particoes'])
    total_fich = sum(p['ficheiros'] for p in info['particoes'])
    L.append(f'| **Total ({len(info["particoes"])} anos)** | **{total_linhas:,}** | **{total_mb:.2f}** | '
             f'**{total_fich}** |'.replace(',', ' '))
    L.append('')
    L.append('Ano calculado com `year(to_timestamp("timestamp"))` em UTC.')
    L.append('')

    L.append('## Tipos para o DDL do Athena')
    L.append('')
    L.append('O Athena (catálogo Glue/Hive) guarda os nomes das colunas em minúsculas: `userId` passa a `userid`. '
             'Na leitura de Parquet a correspondência de nomes não distingue maiúsculas, por isso os ficheiros '
             'não precisam de ser alterados.')
    L.append('')
    L.append('`timestamp` é uma palavra reservada no Athena: no DDL escreve-se `` `timestamp` `` (entre backticks) '
             'e nas queries `"timestamp"` (entre aspas duplas).')
    L.append('')
    L.append('| DuckDB | Athena |')
    L.append('|---|---|')
    for d, a in ATHENA_TYPES.items():
        L.append(f'| {d} | {a} |')
    L.append('')
    for t in info['tabelas']:
        L.append(f'### {t["nome"]}')
        L.append('')
        L.append('| Coluna no Athena | Tipo no Athena |')
        L.append('|---|---|')
        for coluna, tipo in t['schema']:
            L.append(f'| {coluna.lower()} | {ATHENA_TYPES[tipo]} |')
        L.append('')
        if t['nome'] == 'ratings_part':
            L.append('Partição: `PARTITIONED BY (year int)`. Depois de criar a tabela, carregar as partições com '
                     '`MSCK REPAIR TABLE` ou com um crawler do Glue (ou usar partition projection).')
            L.append('')
        if t['nome'] == 'ratings_csv':
            L.append("CSV com cabeçalho: `ROW FORMAT DELIMITED FIELDS TERMINATED BY ','` e "
                     "`TBLPROPERTIES ('skip.header.line.count'='1')`.")
            L.append('')

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(L).rstrip() + '\n')


def main():
    """Escreve data/cloud/<pasta>/, verifica tudo e, se estiver tudo certo, gera o manifesto."""
    args = parse_args()
    cfg = load_config(args.dataset)
    ds = cfg['dataset']
    pasta = cfg['source']['folder']          # ml-latest-small, ml-1m ou ml-32m
    pq_dir = cfg['paths']['parquet']
    csv_file = cfg['paths']['csv'] / 'ratings.csv'
    fase1_part = pq_dir / 'ratings_by_year'
    cloud_dir = ROOT / 'data' / 'cloud' / pasta
    manifest = ROOT / 'reports' / f'cloud_manifest_{ds}.md'
    print(f'[prepare_cloud] dataset={ds} -> data/cloud/{pasta}/')

    # 0. As entradas da fase 1 têm de existir
    tables = [t for t in SCHEMAS if (pq_dir / f'{t}.parquet').exists()]   # o 1M não tem tags nem links
    em_falta = [str(p) for p in (pq_dir / 'ratings.parquet', fase1_part, csv_file) if not p.exists()]
    if em_falta:
        sys.exit('Erro: faltam ficheiros da fase 1: ' + ', '.join(em_falta) +
                 f'\nCorre primeiro: python run_pipeline.py --dataset {ds} --steps ingest parquet')

    # Um manifesto antigo deixaria de corresponder aos ficheiros: apaga-se já, e só se
    # volta a escrever no fim, se todas as verificações passarem.
    if manifest.exists():
        manifest.unlink()

    # Idempotência: apaga e recria a pasta inteira deste dataset
    if cloud_dir.exists():
        shutil.rmtree(cloud_dir)
    cloud_dir.mkdir(parents=True)

    t_inicio = time.perf_counter()
    con = duckdb.connect()
    # to_timestamp devolve TIMESTAMP WITH TIME ZONE: sem fixar o fuso, o ano de um rating
    # perto da meia-noite de 31/12 dependeria do fuso da máquina. Em UTC fica igual à fase 1.
    con.execute("SET TimeZone = 'UTC'")
    # A ordem das linhas não interessa e desligá-la poupa memória no 32M (como no 02_to_parquet.py)
    con.execute('SET preserve_insertion_order = false')

    # 1. Uma pasta por tabela, um ficheiro Parquet zstd em cada. SELECT * sem casts mantém os tipos.
    for table in tables:
        src = pq_dir / f'{table}.parquet'
        dst = cloud_dir / table / f'{table}.parquet'
        dst.parent.mkdir()
        t0 = time.perf_counter()
        con.execute(f"""
            COPY (SELECT * FROM read_parquet('{src.as_posix()}'))
            TO '{dst.as_posix()}' (FORMAT parquet, COMPRESSION zstd)
        """)
        print(f'  {table:12} {mb(src):>8.2f} MB (fase 1) -> {mb(dst):>8.2f} MB zstd em {time.perf_counter() - t0:.2f} s')

    # 2. ratings particionado por ano. Com PARTITION_BY, o DuckDB não escreve a coluna
    # year dentro dos ficheiros: o valor fica só no nome da pasta (year=2015/).
    part_dir = cloud_dir / 'ratings_part'
    t0 = time.perf_counter()
    con.execute(f"""
        COPY (SELECT *, year(to_timestamp("timestamp")) AS year
              FROM read_parquet('{(pq_dir / 'ratings.parquet').as_posix()}'))
        TO '{part_dir.as_posix()}' (FORMAT parquet, PARTITION_BY (year), COMPRESSION zstd)
    """)
    n_part = len(list(part_dir.glob('year=*')))
    print(f'  {"ratings_part":12} {mb(part_dir):>8.2f} MB zstd em {n_part} partições, {time.perf_counter() - t0:.2f} s')

    # 3. Cópia do CSV, byte a byte (no 1M é o CSV normalizado, porque o original vem em .dat)
    (cloud_dir / 'ratings_csv').mkdir()
    csv_dst = cloud_dir / 'ratings_csv' / 'ratings.csv'
    shutil.copyfile(csv_file, csv_dst)
    print(f'  {"ratings_csv":12} {mb(csv_dst):>8.2f} MB (cópia do CSV)')

    # 4. Verificações. Juntam-se todos os problemas para os mostrar de uma vez.
    print('[prepare_cloud] verificações')
    problemas = check_structure(cloud_dir, tables)
    info_tabelas, info_comp = [], []

    for table in tables:
        src = (pq_dir / f'{table}.parquet').as_posix()
        dst_dir = cloud_dir / table
        dst = (dst_dir / '*.parquet').as_posix()
        n_src, n_dst = count_of(con, src), count_of(con, dst)
        if n_src != n_dst:
            problemas.append(f'{table}: {n_dst} linhas em data/cloud, {n_src} na origem')
        sch_src, sch_dst = schema_of(con, src), schema_of(con, dst)
        if sch_src != sch_dst:
            problemas.append(f'{table}: schema diferente da origem: {sch_dst} vs {sch_src}')
        comp = compression_of(con, dst)
        if comp != 'ZSTD':
            problemas.append(f'{table}: compressão {comp}, esperada ZSTD')
        info_tabelas.append({'nome': table, 'caminho': f'{table}/', 'ficheiros': len(list(dst_dir.iterdir())),
                             'mb': mb(dst_dir), 'linhas': n_dst, 'compressao': comp, 'schema': sch_dst})
        info_comp.append({'nome': table, 'origem': f'data/{ds}/parquet/{table}.parquet',
                          'comp_origem': compression_of(con, src), 'mb_origem': mb(pq_dir / f'{table}.parquet'),
                          'mb_cloud': mb(dst_dir)})
    n_ratings = info_tabelas[0]['linhas']   # ratings é sempre a primeira tabela do SCHEMAS

    # ratings_part: soma das partições, year ausente dos ficheiros, tipos e contagens por ano
    part_glob = (part_dir / '*' / '*.parquet').as_posix()
    n_part_total = count_of(con, part_glob, hive=True)
    if n_part_total != n_ratings:
        problemas.append(f'ratings_part: {n_part_total} linhas na soma das partições, {n_ratings} em ratings')
    sch_part = schema_of(con, part_glob, hive=False)   # sem hive: só o que está dentro dos ficheiros
    if any(c.lower() == 'year' for c, _ in sch_part):
        problemas.append('ratings_part: a coluna year está repetida dentro dos ficheiros')
    if sch_part != info_tabelas[0]['schema']:
        problemas.append(f'ratings_part: schema diferente de ratings: {sch_part}')
    comp_part = compression_of(con, part_glob)
    if comp_part != 'ZSTD':
        problemas.append(f'ratings_part: compressão {comp_part}, esperada ZSTD')

    por_ano = counts_by_year(con, part_glob)
    por_ano_fase1 = counts_by_year(con, (fase1_part / '*' / '*.parquet').as_posix())
    for ano in sorted(set(por_ano) | set(por_ano_fase1)):
        if por_ano.get(ano, 0) != por_ano_fase1.get(ano, 0):
            problemas.append(f'ratings_part: ano {ano} com {por_ano.get(ano, 0)} linhas, '
                             f'{por_ano_fase1.get(ano, 0)} no ratings_by_year da fase 1')

    particoes = []
    for ano in sorted(por_ano):
        d = part_dir / f'year={ano}'
        particoes.append({'ano': ano, 'linhas': por_ano[ano], 'mb': mb(d), 'ficheiros': len(list(d.iterdir()))})
    info_tabelas.insert(1, {'nome': 'ratings_part', 'caminho': 'ratings_part/year=AAAA/',
                            'ficheiros': sum(p['ficheiros'] for p in particoes), 'mb': mb(part_dir),
                            'linhas': n_part_total, 'compressao': comp_part, 'schema': sch_part})
    info_comp.insert(1, {'nome': 'ratings_part', 'origem': f'data/{ds}/parquet/ratings_by_year/',
                         'comp_origem': compression_of(con, (fase1_part / '*' / '*.parquet').as_posix()),
                         'mb_origem': mb(fase1_part), 'mb_cloud': mb(part_dir)})

    # ratings_csv: mesmo tamanho que a origem e mesmo n.º de linhas que ratings
    if csv_dst.stat().st_size != csv_file.stat().st_size:
        problemas.append('ratings_csv: tamanho diferente do CSV de origem')
    # Mesmas opções de leitura que o 02_to_parquet.py usa para o CSV
    n_csv = con.execute(f"""
        SELECT count(*) FROM read_csv('{csv_dst.as_posix()}', header=true, delim=',', quote='"', escape='"',
                                      columns={duckdb_columns(SCHEMAS['ratings'])})
    """).fetchone()[0]
    if n_csv != n_ratings:
        problemas.append(f'ratings_csv: {n_csv} linhas, {n_ratings} em ratings')
    info_tabelas.insert(2, {'nome': 'ratings_csv', 'caminho': 'ratings_csv/', 'ficheiros': 1, 'mb': mb(csv_dst),
                            'linhas': n_csv, 'compressao': 'nenhuma (CSV)',
                            'schema': list(SCHEMAS['ratings'].items())})

    for t in info_tabelas:
        print(f'  {t["nome"]:12} {t["linhas"]:>12,} linhas  {t["ficheiros"]:>3} ficheiro(s)  {t["mb"]:>8.2f} MB')

    if problemas:
        print('[prepare_cloud] ERRO: as verificações falharam; o manifesto não foi gerado.', file=sys.stderr)
        for p in problemas:
            print(f'  - {p}', file=sys.stderr)
        sys.exit(1)

    # 5. Manifesto
    write_manifest(manifest, {'dataset': ds, 'pasta': pasta, 'gerado_em': now(),
                              'segundos': time.perf_counter() - t_inicio, 'tabelas': info_tabelas,
                              'compressao': info_comp, 'particoes': particoes})
    print(f'[prepare_cloud] verificações OK; manifesto em {manifest.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
