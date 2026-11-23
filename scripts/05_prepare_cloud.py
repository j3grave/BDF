"""
05_prepare_cloud.py - Bloco cloud, passo 1/4: preparar localmente os ficheiros que vão para o S3 da AWS.

Objetivo:
    (1)Criar em data/cloud/<pasta>/ um espelho exato do que vai ser enviado para o S3 e catalogado pelo Glue Data Catalog para consulta no Athena. 
    (2) O Glue e o Athena tratam cada pasta como uma tabela, por isso cada tabela fica na sua própria pasta e não há ficheiros soltos na raiz. 
    (3) Todas as tabelas são reescritas em Parquet com compressão zstd, algoritmo de compactação de dados sem perdas e de código aberto, sem alterar os tipos da fase 1 (não há casts). 
    (4) Os ratings ficam em duas versões
        (4.1) sem partição e particionados por ano
        (4.2) Cópia do ratings.csv, para comparar no Athena os bytes lidos em CSV e em Parquet.
    (5) Este script não faz nenhuma chamada à AWS, requeria credenciais, só escreve ficheiros no disco local.
    (6) Se data/cloud/<pasta>/ já existir, for mais recente do que os ficheiros da fase 1 e passar as verificações, não faz nada.

Entradas:
    data/<dataset>/parquet/<tabela>.parquet   criados pelo 02_to_parquet.py
    data/<dataset>/parquet/ratings_by_year/   idem (só para comparar as contagens por ano)
    data/<dataset>/csv/ratings.csv            criado pelo 01_ingest.py
    (data/<dataset> pode ser um symlink para outra cópia do repositório)

Saídas:
    data/cloud/<pasta>/ratings/ratings.parquet        ratings sem partição
    data/cloud/<pasta>/ratings_part/year=AAAA/*.parquet  ratings particionado por ano
    data/cloud/<pasta>/movies/movies.parquet          movies
    data/cloud/<pasta>/ratings_csv/ratings.csv        cópia do CSV, byte a byte
    <pasta> é o nome da pasta do GroupLens: ml-latest-small, ml-1m ou ml-32m.

"""
import shutil
import sys
import time

import duckdb

from athena_common import compression_of, count_of, counts_by_year, schema_of
from common import ROOT, SCHEMAS, duckdb_columns, load_config, size_on_disk

# Tabelas que vão para a cloud. O tags e o links não são usados por nenhuma query do Athena.
TABELAS_CLOUD = ['ratings', 'movies']


def motivo_para_preparar(cloud_dir, pq_dir, csv_file):
    """Motivo para preparar data/cloud/<pasta>/ de novo, ou None se as datas mostram que está atualizada.

    Se algum ficheiro da fase 1 for mais recente do que o ficheiro mais antigo de data/cloud/,
    a pasta foi feita com dados antigos. Uma preparação interrompida a meio é apanhada depois
    pelas verificações.
    """
    if not cloud_dir.exists():
        return f'não existe {cloud_dir.relative_to(ROOT)}'
    destino = [f.stat().st_mtime for f in cloud_dir.rglob('*') if f.is_file()]
    if not destino:
        return f'{cloud_dir.relative_to(ROOT)} está vazia'
    origens = [csv_file] + [f for f in pq_dir.rglob('*') if f.is_file()]
    for f in origens:
        if f.exists() and f.stat().st_mtime > min(destino):
            return f'{f.name} é mais recente do que data/cloud/'
    return None


def mb(path):
    """Tamanho em MB (10^6 bytes, como no results/sizes.csv) de um ficheiro ou pasta."""
    return size_on_disk(path) / 1e6


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
    # (item.name[5:] é o que vem depois de "year=", ex.: "2015", e tem de ser só algarismos)
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


def copiar_tabelas(con, tables, pq_dir, cloud_dir):
    """Passo 1: uma pasta por tabela, com um ficheiro Parquet zstd. SELECT * sem casts mantém os tipos."""
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


def particionar_ratings(con, pq_dir, part_dir):
    """Passo 2: ratings particionado por ano.

    Com PARTITION_BY, o DuckDB não escreve a coluna year dentro dos ficheiros: o valor fica
    só no nome da pasta (year=2015/). É assim que o Athena espera as partições.
    """
    t0 = time.perf_counter()
    con.execute(f"""
        COPY (SELECT *, year(to_timestamp("timestamp")) AS year
              FROM read_parquet('{(pq_dir / 'ratings.parquet').as_posix()}'))
        TO '{part_dir.as_posix()}' (FORMAT parquet, PARTITION_BY (year), COMPRESSION zstd)
    """)
    n_part = len(list(part_dir.glob('year=*')))
    print(f'  {"ratings_part":12} {mb(part_dir):>8.2f} MB zstd em {n_part} partições, {time.perf_counter() - t0:.2f} s')


def copiar_csv(csv_file, cloud_dir):
    """Passo 3: cópia do CSV, byte a byte (no 1M é o CSV normalizado, porque o original vem em .dat)."""
    (cloud_dir / 'ratings_csv').mkdir()
    csv_dst = cloud_dir / 'ratings_csv' / 'ratings.csv'
    shutil.copyfile(csv_file, csv_dst)
    print(f'  {"ratings_csv":12} {mb(csv_dst):>8.2f} MB (cópia do CSV)')
    return csv_dst


def verificar_tabelas(con, tables, pq_dir, cloud_dir, problemas):
    """Verifica cada tabela simples contra a origem (linhas, schema e compressão).

    Acrescenta os problemas encontrados à lista problemas e devolve os dados de cada tabela para o resumo.
    """
    info_tabelas = []
    for table in tables:
        src = (pq_dir / f'{table}.parquet').as_posix()
        dst_dir = cloud_dir / table
        dst = (dst_dir / '*.parquet').as_posix()

        # Mesmo n.º de linhas e mesmo schema que o Parquet da fase 1; compressão zstd
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
    return info_tabelas


def verificar_particoes(con, part_dir, fase1_part, n_ratings, schema_ratings, problemas):
    """Verifica ratings_part: soma das partições, year fora dos ficheiros, schema, compressão e
    contagens por ano iguais às do ratings_by_year da fase 1.

    Devolve os dados da tabela para o resumo.
    """
    part_glob = (part_dir / '*' / '*.parquet').as_posix()

    # A soma das partições tem de dar o total de ratings
    n_part_total = count_of(con, part_glob, hive=True)
    if n_part_total != n_ratings:
        problemas.append(f'ratings_part: {n_part_total} linhas na soma das partições, {n_ratings} em ratings')

    # Sem hive_partitioning vemos só o que está dentro dos ficheiros: year não pode lá estar
    sch_part = schema_of(con, part_glob, hive=False)
    nomes_colunas = [coluna.lower() for coluna, _ in sch_part]
    if 'year' in nomes_colunas:
        problemas.append('ratings_part: a coluna year está repetida dentro dos ficheiros')
    if sch_part != schema_ratings:
        problemas.append(f'ratings_part: schema diferente de ratings: {sch_part}')
    comp_part = compression_of(con, part_glob)
    if comp_part != 'ZSTD':
        problemas.append(f'ratings_part: compressão {comp_part}, esperada ZSTD')

    # Contagens por ano iguais às da fase 1 (anos que faltem num dos lados contam como 0)
    por_ano = counts_by_year(con, part_glob)
    por_ano_fase1 = counts_by_year(con, (fase1_part / '*' / '*.parquet').as_posix())
    for ano in sorted(set(por_ano) | set(por_ano_fase1)):
        if por_ano.get(ano, 0) != por_ano_fase1.get(ano, 0):
            problemas.append(f'ratings_part: ano {ano} com {por_ano.get(ano, 0)} linhas, '
                             f'{por_ano_fase1.get(ano, 0)} no ratings_by_year da fase 1')

    total_ficheiros = len(list(part_dir.glob('*/*.parquet')))
    return {'nome': 'ratings_part', 'caminho': 'ratings_part/year=AAAA/',
            'ficheiros': total_ficheiros, 'mb': mb(part_dir),
            'linhas': n_part_total, 'compressao': comp_part, 'schema': sch_part}


def verificar_csv(con, csv_file, csv_dst, n_ratings, problemas):
    """Verifica ratings_csv (mesmo tamanho que a origem e mesmo n.º de linhas que ratings).

    Devolve os dados da tabela para o resumo.
    """
    if csv_dst.stat().st_size != csv_file.stat().st_size:
        problemas.append('ratings_csv: tamanho diferente do CSV de origem')
    # Mesmas opções de leitura que o 02_to_parquet.py usa para o CSV
    n_csv = con.execute(f"""
        SELECT count(*) FROM read_csv('{csv_dst.as_posix()}', header=true, delim=',', quote='"', escape='"',
                                      columns={duckdb_columns(SCHEMAS['ratings'])})
    """).fetchone()[0]
    if n_csv != n_ratings:
        problemas.append(f'ratings_csv: {n_csv} linhas, {n_ratings} em ratings')
    return {'nome': 'ratings_csv', 'caminho': 'ratings_csv/', 'ficheiros': 1, 'mb': mb(csv_dst),
            'linhas': n_csv, 'compressao': 'nenhuma (CSV)', 'schema': list(SCHEMAS['ratings'].items())}


def tabelas_da_fase1(pq_dir, fase1_part, csv_file):
    """Confirma que as entradas da fase 1 existem e devolve as tabelas a copiar. Termina se faltar alguma."""
    em_falta = []
    for p in [pq_dir / f'{t}.parquet' for t in TABELAS_CLOUD] + [fase1_part, csv_file]:
        if not p.exists():
            em_falta.append(str(p))
    if em_falta:
        sys.exit('Erro: faltam ficheiros da fase 1: ' + ', '.join(em_falta) +
                 '\nCorre primeiro o pipeline local (run_pipeline.py, blocos 1 a 3).')
    return TABELAS_CLOUD


def verificar_tudo(con, tables, pq_dir, cloud_dir, fase1_part, csv_file):
    """Corre todas as verificações, mostra um resumo e devolve a lista de problemas (vazia se estiver tudo bem)."""
    print('[prepare_cloud] verificações')
    problemas = []
    try:
        problemas += check_structure(cloud_dir, tables)
        info_tabelas = verificar_tabelas(con, tables, pq_dir, cloud_dir, problemas)
        n_ratings = info_tabelas[0]['linhas']        # ratings é sempre a primeira de TABELAS_CLOUD
        schema_ratings = info_tabelas[0]['schema']
        info_tabelas.insert(1, verificar_particoes(con, cloud_dir / 'ratings_part', fase1_part,
                                                   n_ratings, schema_ratings, problemas))
        info_tabelas.insert(2, verificar_csv(con, csv_file, cloud_dir / 'ratings_csv' / 'ratings.csv',
                                             n_ratings, problemas))
    except (OSError, duckdb.Error) as erro:
        # Ex.: falta uma pasta, se uma preparação anterior foi interrompida a meio
        return problemas + [f'não foi possível verificar: {erro}']

    for t in info_tabelas:
        print(f'  {t["nome"]:12} {t["linhas"]:>12,} linhas  {t["ficheiros"]:>3} ficheiro(s)  {t["mb"]:>8.2f} MB')
    return problemas


def main():
    """Escreve data/cloud/<pasta>/ (se não estiver atualizada) e verifica tudo."""
    cfg = load_config()
    ds = cfg['dataset']
    pasta = cfg['source']['folder']          # ml-latest-small, ml-1m ou ml-32m - 1 pasta por dataset
    pq_dir = cfg['paths']['parquet']
    csv_file = cfg['paths']['csv'] / 'ratings.csv'
    fase1_part = pq_dir / 'ratings_by_year'
    cloud_dir = ROOT / 'data' / 'cloud' / pasta
    part_dir = cloud_dir / 'ratings_part'
    print(f'[prepare_cloud] dataset={ds} -> data/cloud/{pasta}/')

    tables = tabelas_da_fase1(pq_dir, fase1_part, csv_file)
    con = duckdb.connect()
    # to_timestamp devolve TIMESTAMP WITH TIME ZONE: sem fixar o fuso, o ano de um rating perto da meia-noite de 31/12 dependeria do fuso da máquina. Em UTC fica igual à fase sem cloud, que também usa UTC. O Athena também usa UTC.
    con.execute("SET TimeZone = 'UTC'")
    # A ordem das linhas não interessa e desligá-la poupa memória no 32M (como no 02_to_parquet.py)
    con.execute('SET preserve_insertion_order = false')

    # Como no download do 01_ingest.py: se já estiver feito e correto, não faz de novo
    motivo = motivo_para_preparar(cloud_dir, pq_dir, csv_file)
    if not motivo:
        problemas = verificar_tudo(con, tables, pq_dir, cloud_dir, fase1_part, csv_file)
        if not problemas:
            print(f'[prepare_cloud] data/cloud/{pasta}/ já está atualizada, não prepara de novo')
            return
        motivo = 'a pasta existente não passou as verificações'
    print(f'[prepare_cloud] a preparar: {motivo}')

    # Idempotência - apaga e recria a pasta inteira deste dataset
    if cloud_dir.exists():
        shutil.rmtree(cloud_dir)
    cloud_dir.mkdir(parents=True)

    # 1 a 3. Escrever os ficheiros
    copiar_tabelas(con, tables, pq_dir, cloud_dir)
    particionar_ratings(con, pq_dir, part_dir)
    copiar_csv(csv_file, cloud_dir)

    # 4. Verificações: se alguma falhar, o script termina com erro (o pipeline pára)
    problemas = verificar_tudo(con, tables, pq_dir, cloud_dir, fase1_part, csv_file)
    if problemas:
        print('[prepare_cloud] ERRO: as verificações falharam:', file=sys.stderr)
        for p in problemas:
            print(f'  - {p}', file=sys.stderr)
        sys.exit(1)
    print('[prepare_cloud] verificações OK')


if __name__ == '__main__':
    main()
