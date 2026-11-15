# IMDb vs MovieLens · MovieLens 32m

Gerado por `scripts/07_imdb.py` em 16.0 s (sessão DuckDB em UTC).

## Método

- **Fontes:** `title.ratings.tsv.gz` e `title.basics.tsv.gz` de <https://datasets.imdbws.com/> (uso pessoal e não comercial), ligados ao MovieLens pelo `imdbId` do `links.csv`.
- **Ligação:** `tconst = 'tt' || imdbId`, com `lpad(imdbId, 7, '0')` só para ids com menos de 7 algarismos. O `lpad` sozinho cortaria os ids de 8 algarismos (`lpad('12345678', 7, '0') = '1234567'`) e ligaria esses filmes a títulos errados.
- **Escala:** nota do MovieLens × 2. Passa a escala de 0,5–5 para 1–10, com os mesmos extremos do IMDb (0,5 → 1 e 5 → 10). É linear, por isso não muda a ordem dos filmes nem as correlações; só torna o gap legível em pontos do IMDb. **Gap = IMDb − MovieLens×2**: positivo quando o IMDb dá nota mais alta.
- **Limiares (config.yaml):** pelo menos 50 avaliações no MovieLens e 1000 votos no IMDb. Com poucas avaliações a média é instável. A secção "Sensibilidade" repete a análise sem e com outros limiares.
- **Tipo de título:** só entram nas análises os títulos do tipo movie (`titleType` do IMDb; `imdb.tipos_titulo` no config.yaml). Séries, episódios, curtas, vídeos e filmes para TV ficam de fora (categoria 5 da ligação).
- **IC 95%:** média ± 1,96 × desvio-padrão / √n. **Spearman:** Pearson sobre as posições, com a posição média nos empates.

## Ligação entre as fontes

68 529 de 84 432 filmes avaliados no MovieLens (81,2%) ligam a um título do IMDb com nota e do tipo movie, e entram nas análises.

| categoria | filmes | pct_filmes | avaliacoes_ml | pct_avaliacoes_ml |
|---|---|---|---|---|
| 2. tconst não existe no title.basics | 223 | 0,3 | 22991 | 0,1 |
| 3. sem nota no title.ratings | 99 | 0,1 | 273 | 0,0 |
| 4. ligado e com nota (entra nas análises) | 68529 | 81,2 | 31586601 | 98,7 |
| 5. com nota mas tipo de título excluído | 15581 | 18,5 | 390339 | 1,2 |

Porquê: a categoria 2 são ids que já não existem no `title.basics` (o IMDb remove ou funde títulos e o ficheiro público não diz qual); a 3 são títulos sem votos no `title.ratings`.

Tipo de título dos filmes ligados:

| tipo_imdb | filmes | pct_filmes | com_nota_imdb |
|---|---|---|---|
| movie | 68574 | 81,4 | 68529 |
| tvMovie | 5800 | 6,9 | 5791 |
| short | 5178 | 6,1 | 5136 |
| video | 2209 | 2,6 | 2206 |
| tvSpecial | 862 | 1,0 | 862 |
| tvEpisode | 741 | 0,9 | 741 |
| tvMiniSeries | 531 | 0,6 | 531 |
| tvShort | 181 | 0,2 | 181 |
| tvSeries | 131 | 0,2 | 131 |
| videoGame | 2 | 0,0 | 2 |

## P1. As notas concordam?

| filmes | media_ml_10 | media_imdb | gap_medio | gap_ic95_inf | gap_ic95_sup | gap_abs_medio | pct_imdb_acima | pearson | spearman |
|---|---|---|---|---|---|---|---|---|---|
| 14 806,000 | 6,509 | 6,584 | 0,075 | 0,069 | 0,080 | 0,275 | 57,585 | 0,926 | 0,927 |

**Interpretação.** A correlação é forte (Pearson 0,93, Spearman 0,93): os dois sites ordenam os filmes de forma parecida. Em média, o IMDb dá uma nota mais alta do que o MovieLens×2, por 0,07 pontos (IC 95% 0,07 a 0,08). Filme a filme, a diferença absoluta média é 0,27 pontos.

### Por género

| genero | filmes | gap_medio | gap_ic95_inf | gap_ic95_sup | pearson | spearman |
|---|---|---|---|---|---|---|
| IMAX | 160 | 0,280 | 0,235 | 0,325 | 0,940 | 0,930 |
| Animation | 648 | 0,275 | 0,247 | 0,303 | 0,920 | 0,926 |
| Children | 803 | 0,273 | 0,245 | 0,301 | 0,918 | 0,923 |
| Documentary | 686 | 0,198 | 0,169 | 0,226 | 0,844 | 0,736 |
| Musical | 470 | 0,174 | 0,140 | 0,207 | 0,905 | 0,866 |
| Adventure | 1601 | 0,167 | 0,150 | 0,185 | 0,933 | 0,928 |
| Action | 2457 | 0,133 | 0,119 | 0,146 | 0,936 | 0,936 |
| Western | 289 | 0,127 | 0,092 | 0,161 | 0,921 | 0,918 |
| Fantasy | 1010 | 0,112 | 0,089 | 0,136 | 0,927 | 0,922 |
| War | 608 | 0,108 | 0,083 | 0,133 | 0,918 | 0,890 |
| Crime | 1795 | 0,078 | 0,064 | 0,092 | 0,933 | 0,934 |
| Horror | 1695 | 0,078 | 0,058 | 0,097 | 0,901 | 0,899 |
| Comedy | 4976 | 0,068 | 0,058 | 0,079 | 0,923 | 0,926 |
| Sci-Fi | 1310 | 0,059 | 0,038 | 0,079 | 0,931 | 0,926 |
| Film-Noir | 148 | 0,056 | 0,009 | 0,103 | 0,881 | 0,852 |
| Drama | 7177 | 0,043 | 0,036 | 0,051 | 0,910 | 0,905 |
| Thriller | 3024 | 0,030 | 0,018 | 0,042 | 0,930 | 0,934 |
| Mystery | 922 | 0,021 | -0,000 | 0,042 | 0,932 | 0,933 |
| Romance | 2320 | 0,005 | -0,009 | 0,019 | 0,915 | 0,910 |

### Por década de estreia

| decada | filmes | gap_medio | gap_ic95_inf | gap_ic95_sup | pearson | spearman |
|---|---|---|---|---|---|---|
| 1 910,000 | 6,000 | 0,122 | -0,157 | 0,402 | 0,897 | 0,943 |
| 1 920,000 | 76,000 | 0,287 | 0,198 | 0,375 | 0,773 | 0,847 |
| 1 930,000 | 214,000 | 0,084 | 0,039 | 0,130 | 0,849 | 0,820 |
| 1 940,000 | 342,000 | 0,107 | 0,074 | 0,139 | 0,874 | 0,853 |
| 1 950,000 | 463,000 | 0,086 | 0,057 | 0,116 | 0,918 | 0,891 |
| 1 960,000 | 665,000 | 0,094 | 0,068 | 0,120 | 0,912 | 0,911 |
| 1 970,000 | 842,000 | 0,100 | 0,076 | 0,124 | 0,915 | 0,900 |
| 1 980,000 | 1 583,000 | 0,166 | 0,145 | 0,186 | 0,927 | 0,935 |
| 1 990,000 | 2 525,000 | 0,099 | 0,082 | 0,115 | 0,910 | 0,916 |
| 2 000,000 | 3 596,000 | 0,059 | 0,049 | 0,070 | 0,940 | 0,938 |
| 2 010,000 | 3 828,000 | 0,012 | 0,001 | 0,022 | 0,930 | 0,929 |
| 2 020,000 | 666,000 | 0,109 | 0,082 | 0,135 | 0,912 | 0,918 |

### Por popularidade no IMDb (5 grupos pelo n.º de votos; 1 = menos votados)

| quantil | filmes | votos_min | votos_max | gap_medio | gap_ic95_inf | gap_ic95_sup | pearson | spearman |
|---|---|---|---|---|---|---|---|---|
| 1,000 | 2 962,000 | 1 000,000 | 6 801,000 | 0,092 | 0,076 | 0,107 | 0,893 | 0,884 |
| 2,000 | 2 961,000 | 6 801,000 | 13 497,000 | 0,062 | 0,048 | 0,076 | 0,912 | 0,915 |
| 3,000 | 2 961,000 | 13 502,000 | 29 449,000 | 0,043 | 0,030 | 0,055 | 0,933 | 0,938 |
| 4,000 | 2 961,000 | 29 466,000 | 84 312,000 | 0,050 | 0,039 | 0,062 | 0,944 | 0,945 |
| 5,000 | 2 961,000 | 84 395,000 | 3 264 913,000 | 0,127 | 0,116 | 0,137 | 0,940 | 0,939 |

### Maior divergência

| sentido | posicao | title | ano_estreia | tipo_imdb | n_ml | nota_ml_10 | votos_imdb | nota_imdb | gap |
|---|---|---|---|---|---|---|---|---|---|
| IMDb acima do MovieLens | 1 | I Am Greta (2020) | 2020 | movie | 65 | 4,28 | 8639 | 7,50 | 3,22 |
| IMDb acima do MovieLens | 2 | Pokémon Heroes (2003) | 2002 | movie | 411 | 2,97 | 7936 | 6,10 | 3,13 |
| IMDb acima do MovieLens | 3 | Digimon: The Movie (2000) | 2000 | movie | 585 | 4,08 | 8693 | 6,10 | 2,02 |
| IMDb acima do MovieLens | 4 | Devils on the Doorstep (Guizi lai le) (2000) | 2000 | movie | 96 | 6,22 | 9522 | 8,20 | 1,98 |
| IMDb acima do MovieLens | 5 | Pokémon the Movie 2000 (2000) | 1999 | movie | 1384 | 4,18 | 26539 | 6,10 | 1,92 |
| IMDb acima do MovieLens | 6 | The Little Mermaid (2023) | 2023 | movie | 135 | 5,28 | 181141 | 7,20 | 1,92 |
| IMDb acima do MovieLens | 7 | Yu-Gi-Oh! (2004) | 2004 | movie | 312 | 3,30 | 9796 | 5,10 | 1,80 |
| IMDb acima do MovieLens | 8 | Pokémon: The First Movie (1998) | 1998 | movie | 1974 | 4,65 | 51169 | 6,40 | 1,75 |
| IMDb acima do MovieLens | 9 | Eddie and the Cruisers II: Eddie Lives! (1989) | 1989 | movie | 144 | 4,62 | 3590 | 6,30 | 1,67 |
| IMDb acima do MovieLens | 10 | Ronaldo (2015) | 2015 | movie | 69 | 4,68 | 18022 | 6,30 | 1,62 |
| MovieLens acima do IMDb | 1 | Santa with Muscles (1996) | 1996 | movie | 163 | 5,10 | 9988 | 2,70 | -2,40 |
| MovieLens acima do IMDb | 2 | Ed (1996) | 1996 | movie | 723 | 5,09 | 9173 | 2,80 | -2,29 |
| MovieLens acima do IMDb | 3 | Theodore Rex (1995) | 1995 | movie | 354 | 4,50 | 5164 | 2,40 | -2,10 |
| MovieLens acima do IMDb | 4 | Going Overboard (1989) | 1989 | movie | 159 | 3,78 | 15149 | 1,80 | -1,98 |
| MovieLens acima do IMDb | 5 | Of Love and Shadows (1994) | 1994 | movie | 137 | 6,83 | 2687 | 4,90 | -1,93 |
| MovieLens acima do IMDb | 6 | Hearts and Minds (1996) | 1995 | movie | 181 | 7,65 | 3308 | 5,90 | -1,75 |
| MovieLens acima do IMDb | 7 | Manos: The Hands of Fate (1966) | 1966 | movie | 153 | 3,42 | 38674 | 1,70 | -1,72 |
| MovieLens acima do IMDb | 8 | Lawnmower Man 2: Beyond Cyberspace (1996) | 1995 | movie | 2415 | 4,27 | 10845 | 2,60 | -1,67 |
| MovieLens acima do IMDb | 9 | Birdemic: Shock and Terror (2010) | 2010 | movie | 204 | 3,36 | 27411 | 1,70 | -1,66 |
| MovieLens acima do IMDb | 10 | Wizard of Oz, The (1925) | 1925 | movie | 87 | 6,53 | 2001 | 4,90 | -1,63 |

### Sensibilidade aos limiares

| cenario | filmes | gap_medio | gap_ic95_inf | gap_ic95_sup | gap_abs_medio | pearson | spearman |
|---|---|---|---|---|---|---|---|
| sem limiares | 68529 | 0,112 | 0,102 | 0,123 | 0,885 | 0,552 | 0,605 |
| só MovieLens >= 50 | 14989 | 0,074 | 0,068 | 0,080 | 0,279 | 0,922 | 0,923 |
| só IMDb >= 1000 | 38782 | 0,117 | 0,108 | 0,125 | 0,562 | 0,734 | 0,765 |
| ambos (análise principal) | 14806 | 0,075 | 0,069 | 0,080 | 0,275 | 0,926 | 0,927 |
| ambos x 4 (mais exigente) | 8699 | 0,066 | 0,059 | 0,073 | 0,253 | 0,939 | 0,942 |

## P2. Diferenças entre tipos de utilizadores

> **Limitação:** o IMDb só publica agregados por filme (nota média e n.º de votos), sem dados por utilizador. Não é possível comparar utilizadores do IMDb com utilizadores do MovieLens. O que se compara é a nota média de cada **segmento de utilizadores do MovieLens** em cada filme com a nota agregada do IMDb, sobre o **mesmo conjunto de filmes** dentro de cada tipo de segmento.

Um filme entra num tipo se cada segmento desse tipo o avaliou pelo menos 5 vezes e se tem pelo menos 1000 votos no IMDb. Era: primeira avaliação antes ou a partir de 18/02/2003 (início das meias estrelas). **Os resultados do tipo "bots" são PROVISÓRIOS: as regras do `10_flag_bots.sql` ainda estão a ser validadas pelo Luís.**

| tipo | segmento | utilizadores | filmes_comuns | avaliacoes | media_segmento_10 | media_imdb | gap_medio | gap_ic95_inf | gap_ic95_sup | pearson | spearman |
|---|---|---|---|---|---|---|---|---|---|---|---|
| atividade | 20–49 | 72604 | 8315 | 2260891 | 7,231 | 6,700 | -0,530 | -0,547 | -0,513 | 0,699 | 0,676 |
| atividade | 50–99 | 47669 | 8315 | 3296693 | 7,145 | 6,700 | -0,444 | -0,459 | -0,430 | 0,776 | 0,754 |
| atividade | 100–249 | 48064 | 8315 | 7326403 | 6,982 | 6,700 | -0,282 | -0,292 | -0,271 | 0,869 | 0,858 |
| atividade | 250–999 | 28990 | 8315 | 12455016 | 6,653 | 6,700 | 0,047 | 0,039 | 0,056 | 0,918 | 0,917 |
| atividade | 1000 ou mais | 3621 | 8315 | 4947207 | 6,276 | 6,700 | 0,424 | 0,416 | 0,432 | 0,931 | 0,928 |
| bots (PROVISÓRIO) | não sinalizados | 200488 | 9183 | 29986485 | 6,631 | 6,682 | 0,051 | 0,044 | 0,058 | 0,938 | 0,940 |
| bots (PROVISÓRIO) | sinalizados | 460 | 9183 | 271911 | 5,731 | 6,682 | 0,951 | 0,935 | 0,966 | 0,729 | 0,716 |
| era | antes de 18/02/2003 | 70115 | 14367 | 8873510 | 6,397 | 6,581 | 0,184 | 0,174 | 0,193 | 0,848 | 0,850 |
| era | a partir de 18/02/2003 | 130833 | 14367 | 22139709 | 6,460 | 6,581 | 0,121 | 0,115 | 0,127 | 0,919 | 0,915 |

## Desempenho

| Tabela | TSV (MB) | TSV.gz (MB) | Parquet snappy (MB) | Parquet / TSV |
|---|---:|---:|---:|---:|
| title_ratings | 30,3 | 8,8 | 13,2 | 44% |
| title_basics | 1 126,6 | 230,4 | 459,6 | 41% |

O Parquet ocupa muito menos do que o TSV descomprimido. Comparado com o TSV.gz, o `title_basics` (quase só texto: títulos) pode até ficar maior, porque o gzip comprime o ficheiro inteiro. A vantagem do Parquet está na leitura: uma query lê só as colunas de que precisa (no join, só `tconst` e `titleType` das 9 colunas do `title_basics`), sem descomprimir nem converter o resto.

Join MovieLens × IMDb (`00_filmes.sql`), mediana de 3 corridas: CSV/TSV.gz 2 419 ms, Parquet 231 ms (10,5 vezes mais rápido). O CSV/TSV inclui descomprimir o gzip e converter texto em números em cada corrida. Os tamanhos estão em `results/sizes.csv` (dataset `imdb`).

## Versões Athena emuladas no DuckDB

| Query | Linhas | Iguais | Nota |
|---|---:|---|---|
| 00_filmes | 84432 | sim |  |
| 01_ligacao | 4 | sim |  |
| 02_ligacao_tipos | 10 | sim |  |
| 03_concordancia | 1 | sim |  |
| 04_gap_genero | 19 | sim |  |
| 05_gap_decada | 12 | sim |  |
| 06_gap_popularidade | 5 | sim |  |
| 07_top_divergencia | 20 | sim |  |
| 08_segmentos | 9 | sim |  |

## Limitações

- O IMDb não tem dados por utilizador (ver P2).
- Os votos do IMDb são de outra população e de outra época: o ficheiro é atualizado todos os dias, e o MovieLens tem avaliações de 1995 a 2023. Parte do gap pode ser só diferença de população ou de tempo.
- O IMDb pondera a nota média com um método que não publica; o MovieLens usa a média simples.
- Os filmes que não ligam (ver "Ligação") ficam de fora; são poucos e têm poucas avaliações.
- O segmento de bots é provisório e, nos datasets pequenos, tem muito poucos utilizadores.

## Figuras

- `fig1_dispersao_ml_imdb.png`
- `fig2_gap_genero.png`
- `fig3_gap_decada.png`
- `fig4_gap_segmentos.png`
