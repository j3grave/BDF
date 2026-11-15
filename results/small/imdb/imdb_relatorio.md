# IMDb vs MovieLens · MovieLens small

Gerado por `scripts/07_imdb.py` em 7.0 s (sessão DuckDB em UTC).

## Método

- **Fontes:** `title.ratings.tsv.gz` e `title.basics.tsv.gz` de <https://datasets.imdbws.com/> (uso pessoal e não comercial), ligados ao MovieLens pelo `imdbId` do `links.csv`.
- **Ligação:** `tconst = 'tt' || imdbId`, com `lpad(imdbId, 7, '0')` só para ids com menos de 7 algarismos. O `lpad` sozinho cortaria os ids de 8 algarismos (`lpad('12345678', 7, '0') = '1234567'`) e ligaria esses filmes a títulos errados.
- **Escala:** nota do MovieLens × 2. Passa a escala de 0,5–5 para 1–10, com os mesmos extremos do IMDb (0,5 → 1 e 5 → 10). É linear, por isso não muda a ordem dos filmes nem as correlações; só torna o gap legível em pontos do IMDb. **Gap = IMDb − MovieLens×2**: positivo quando o IMDb dá nota mais alta.
- **Limiares (config.yaml):** pelo menos 50 avaliações no MovieLens e 1000 votos no IMDb. Com poucas avaliações a média é instável. A secção "Sensibilidade" repete a análise sem e com outros limiares.
- **Tipo de título:** não se filtra pelo `titleType` do IMDb (ver a tabela da ligação).
- **IC 95%:** média ± 1,96 × desvio-padrão / √n. **Spearman:** Pearson sobre as posições, com a posição média nos empates.

## Ligação entre as fontes

9 701 de 9 724 filmes avaliados no MovieLens (99,8%) ligam a um título do IMDb com nota.

| categoria | filmes | pct_filmes | avaliacoes_ml | pct_avaliacoes_ml |
|---|---|---|---|---|
| 2. tconst não existe no title.basics | 23 | 0,2 | 77 | 0,1 |
| 4. ligado e com nota | 9701 | 99,8 | 100759 | 99,9 |

Porquê: a categoria 2 são ids que já não existem no `title.basics` (o IMDb remove ou funde títulos e o ficheiro público não diz qual); a 3 são títulos sem votos no `title.ratings`.

Tipo de título dos filmes ligados:

| tipo_imdb | filmes | pct_filmes | com_nota_imdb |
|---|---|---|---|
| movie | 9050 | 93,3 | 9050 |
| video | 170 | 1,8 | 170 |
| tvMovie | 167 | 1,7 | 167 |
| short | 104 | 1,1 | 104 |
| tvMiniSeries | 80 | 0,8 | 80 |
| tvSpecial | 79 | 0,8 | 79 |
| tvEpisode | 33 | 0,3 | 33 |
| tvShort | 11 | 0,1 | 11 |
| tvSeries | 7 | 0,1 | 7 |

## P1. As notas concordam?

| filmes | media_ml_10 | media_imdb | gap_medio | gap_ic95_inf | gap_ic95_sup | gap_abs_medio | pct_imdb_acima | pearson | spearman |
|---|---|---|---|---|---|---|---|---|---|
| 450,000 | 7,326 | 7,554 | 0,228 | 0,197 | 0,259 | 0,322 | 76,222 | 0,898 | 0,895 |

**Interpretação.** A correlação é forte (Pearson 0,90, Spearman 0,89): os dois sites ordenam os filmes de forma parecida. Em média, o IMDb dá uma nota mais alta do que o MovieLens×2, por 0,23 pontos (IC 95% 0,20 a 0,26). Filme a filme, a diferença absoluta média é 0,32 pontos.

### Por género

| genero | filmes | gap_medio | gap_ic95_inf | gap_ic95_sup | pearson | spearman |
|---|---|---|---|---|---|---|
| Children | 47 | 0,385 | 0,284 | 0,486 | 0,871 | 0,883 |
| Musical | 21 | 0,375 | 0,258 | 0,492 | 0,841 | 0,818 |
| Animation | 32 | 0,352 | 0,264 | 0,439 | 0,912 | 0,913 |
| Horror | 26 | 0,337 | 0,177 | 0,496 | 0,876 | 0,832 |
| Western | 12 | 0,325 | 0,149 | 0,501 | 0,963 | 0,916 |
| IMAX | 28 | 0,324 | 0,222 | 0,426 | 0,896 | 0,877 |
| Sci-Fi | 92 | 0,304 | 0,238 | 0,369 | 0,932 | 0,923 |
| Fantasy | 66 | 0,284 | 0,202 | 0,366 | 0,889 | 0,873 |
| Adventure | 132 | 0,265 | 0,210 | 0,319 | 0,914 | 0,923 |
| Documentary | 2 | 0,264 | 0,099 | 0,429 | 1,000 | 1,000 |
| Action | 164 | 0,250 | 0,202 | 0,297 | 0,927 | 0,921 |
| War | 19 | 0,237 | 0,111 | 0,363 | 0,926 | 0,925 |
| Thriller | 121 | 0,228 | 0,171 | 0,285 | 0,911 | 0,918 |
| Drama | 166 | 0,214 | 0,167 | 0,260 | 0,873 | 0,885 |
| Crime | 87 | 0,210 | 0,145 | 0,275 | 0,913 | 0,874 |
| Mystery | 38 | 0,204 | 0,103 | 0,306 | 0,857 | 0,867 |
| Comedy | 181 | 0,202 | 0,145 | 0,258 | 0,874 | 0,859 |
| Romance | 85 | 0,139 | 0,074 | 0,204 | 0,890 | 0,870 |
| Film-Noir | 4 | 0,063 | -0,204 | 0,330 | 0,739 | 0,800 |

### Por década de estreia

| decada | filmes | gap_medio | gap_ic95_inf | gap_ic95_sup | pearson | spearman |
|---|---|---|---|---|---|---|
| 1 930,000 | 2,000 | 0,353 | 0,326 | 0,379 | 1,000 | 1,000 |
| 1 940,000 | 5,000 | 0,260 | 0,051 | 0,468 | 0,923 | 0,700 |
| 1 950,000 | 6,000 | 0,207 | -0,067 | 0,480 | 0,837 | 0,698 |
| 1 960,000 | 13,000 | 0,094 | -0,077 | 0,264 | 0,532 | 0,577 |
| 1 970,000 | 24,000 | 0,206 | 0,086 | 0,326 | 0,850 | 0,867 |
| 1 980,000 | 53,000 | 0,197 | 0,102 | 0,291 | 0,833 | 0,811 |
| 1 990,000 | 193,000 | 0,260 | 0,206 | 0,314 | 0,888 | 0,871 |
| 2 000,000 | 136,000 | 0,203 | 0,155 | 0,250 | 0,901 | 0,869 |
| 2 010,000 | 18,000 | 0,275 | 0,159 | 0,391 | 0,729 | 0,538 |

### Por popularidade no IMDb (5 grupos pelo n.º de votos; 1 = menos votados)

| quantil | filmes | votos_min | votos_max | gap_medio | gap_ic95_inf | gap_ic95_sup | pearson | spearman |
|---|---|---|---|---|---|---|---|---|
| 1,000 | 90,000 | 21 997,000 | 203 348,000 | 0,117 | 0,040 | 0,194 | 0,888 | 0,858 |
| 2,000 | 90,000 | 209 138,000 | 340 247,000 | 0,193 | 0,122 | 0,265 | 0,871 | 0,863 |
| 3,000 | 90,000 | 341 654,000 | 536 124,000 | 0,299 | 0,227 | 0,372 | 0,861 | 0,847 |
| 4,000 | 90,000 | 537 071,000 | 918 276,000 | 0,172 | 0,107 | 0,236 | 0,823 | 0,815 |
| 5,000 | 90,000 | 923 238,000 | 3 264 913,000 | 0,358 | 0,309 | 0,407 | 0,848 | 0,807 |

### Maior divergência

| sentido | posicao | title | ano_estreia | tipo_imdb | n_ml | nota_ml_10 | votos_imdb | nota_imdb | gap |
|---|---|---|---|---|---|---|---|---|---|
| IMDb acima do MovieLens | 1 | Home Alone (1990) | 1990 | movie | 116 | 5,99 | 759531 | 7,80 | 1,81 |
| IMDb acima do MovieLens | 2 | Dumb & Dumber (Dumb and Dumber) (1994) | 1994 | movie | 133 | 6,12 | 450093 | 7,30 | 1,18 |
| IMDb acima do MovieLens | 3 | Titanic (1997) | 1997 | movie | 140 | 6,83 | 1420426 | 8,00 | 1,17 |
| IMDb acima do MovieLens | 4 | Scream (1996) | 1996 | movie | 70 | 6,40 | 459944 | 7,50 | 1,10 |
| IMDb acima do MovieLens | 5 | Lost World: Jurassic Park, The (1997) | 1997 | movie | 67 | 5,51 | 485694 | 6,60 | 1,09 |
| IMDb acima do MovieLens | 6 | Space Jam (1996) | 1996 | movie | 53 | 5,42 | 233311 | 6,50 | 1,08 |
| IMDb acima do MovieLens | 7 | My Cousin Vinny (1992) | 1992 | movie | 59 | 6,53 | 163234 | 7,60 | 1,07 |
| IMDb acima do MovieLens | 8 | Batman Returns (1992) | 1992 | movie | 60 | 6,05 | 354744 | 7,10 | 1,05 |
| IMDb acima do MovieLens | 9 | Honey, I Shrunk the Kids (1989) | 1989 | movie | 68 | 5,51 | 179983 | 6,50 | 0,99 |
| IMDb acima do MovieLens | 10 | Ace Ventura: When Nature Calls (1995) | 1995 | movie | 88 | 5,45 | 252782 | 6,40 | 0,95 |
| MovieLens acima do IMDb | 1 | Disclosure (1994) | 1994 | movie | 52 | 7,08 | 59314 | 6,20 | -0,88 |
| MovieLens acima do IMDb | 2 | Raising Arizona (1987) | 1987 | movie | 58 | 7,98 | 162957 | 7,30 | -0,68 |
| MovieLens acima do IMDb | 3 | Army of Darkness (1993) | 1992 | movie | 51 | 8,08 | 214477 | 7,40 | -0,68 |
| MovieLens acima do IMDb | 4 | Office Space (1999) | 1999 | movie | 94 | 8,18 | 313387 | 7,60 | -0,58 |
| MovieLens acima do IMDb | 5 | Brazil (1985) | 1985 | movie | 59 | 8,36 | 224185 | 7,80 | -0,56 |
| MovieLens acima do IMDb | 6 | Cool Hand Luke (1967) | 1967 | movie | 57 | 8,54 | 197930 | 8,00 | -0,54 |
| MovieLens acima do IMDb | 7 | Zoolander (2001) | 2001 | movie | 54 | 7,02 | 322252 | 6,50 | -0,52 |
| MovieLens acima do IMDb | 8 | Truth About Cats & Dogs, The (1996) | 1996 | movie | 58 | 6,78 | 29190 | 6,30 | -0,48 |
| MovieLens acima do IMDb | 9 | Princess Bride, The (1987) | 1987 | movie | 142 | 8,46 | 493559 | 8,00 | -0,46 |
| MovieLens acima do IMDb | 10 | Tommy Boy (1995) | 1995 | movie | 50 | 7,56 | 106339 | 7,10 | -0,46 |

### Sensibilidade aos limiares

| cenario | filmes | gap_medio | gap_ic95_inf | gap_ic95_sup | gap_abs_medio | pearson | spearman |
|---|---|---|---|---|---|---|---|
| sem limiares | 9701 | 0,112 | 0,084 | 0,140 | 1,003 | 0,595 | 0,610 |
| só MovieLens >= 50 | 450 | 0,228 | 0,197 | 0,259 | 0,322 | 0,898 | 0,895 |
| só IMDb >= 1000 | 9490 | 0,125 | 0,097 | 0,152 | 0,987 | 0,607 | 0,621 |
| ambos (análise principal) | 450 | 0,228 | 0,197 | 0,259 | 0,322 | 0,898 | 0,895 |
| ambos x 4 (mais exigente) | 19 | 0,323 | 0,223 | 0,423 | 0,325 | 0,893 | 0,746 |

## P2. Diferenças entre tipos de utilizadores

> **Limitação:** o IMDb só publica agregados por filme (nota média e n.º de votos), sem dados por utilizador. Não é possível comparar utilizadores do IMDb com utilizadores do MovieLens. O que se compara é a nota média de cada **segmento de utilizadores do MovieLens** em cada filme com a nota agregada do IMDb, sobre o **mesmo conjunto de filmes** dentro de cada tipo de segmento.

Um filme entra num tipo se cada segmento desse tipo o avaliou pelo menos 5 vezes e se tem pelo menos 1000 votos no IMDb. Era: primeira avaliação antes ou a partir de 18/02/2003 (início das meias estrelas). **Os resultados do tipo "bots" são PROVISÓRIOS: as regras do `10_flag_bots.sql` ainda estão a ser validadas pelo Luís.**

| tipo | segmento | utilizadores | filmes_comuns | avaliacoes | media_segmento_10 | media_imdb | gap_medio | gap_ic95_inf | gap_ic95_sup | pearson | spearman |
|---|---|---|---|---|---|---|---|---|---|---|---|
| atividade | 20–49 | 225 | 256 | 3 654,000 | 7,699 | 7,689 | -0,010 | -0,091 | 0,071 | 0,736 | 0,741 |
| atividade | 50–99 | 137 | 256 | 4 533,000 | 7,675 | 7,689 | 0,014 | -0,063 | 0,092 | 0,711 | 0,697 |
| atividade | 100–249 | 143 | 256 | 7 885,000 | 7,460 | 7,689 | 0,229 | 0,170 | 0,288 | 0,825 | 0,806 |
| atividade | 250–999 | 93 | 256 | 9 982,000 | 7,284 | 7,689 | 0,405 | 0,359 | 0,451 | 0,912 | 0,882 |
| atividade | 1000 ou mais | 12 | 256 | 2 189,000 | 7,396 | 7,689 | 0,293 | 0,217 | 0,369 | 0,843 | 0,812 |
| bots (PROVISÓRIO) | não sinalizados | 608 | 0 |  |  |  |  |  |  |  |  |
| bots (PROVISÓRIO) | sinalizados | 2 | 0 |  |  |  |  |  |  |  |  |
| era | antes de 18/02/2003 | 249 | 1219 | 23 817,000 | 6,986 | 7,077 | 0,091 | 0,048 | 0,134 | 0,781 | 0,794 |
| era | a partir de 18/02/2003 | 361 | 1219 | 34 636,000 | 6,801 | 7,077 | 0,276 | 0,243 | 0,308 | 0,834 | 0,831 |

## Desempenho

Join MovieLens × IMDb (`00_filmes.sql`), mediana de 3 corridas: CSV/TSV.gz 1 927 ms, Parquet 92 ms (21,1 vezes mais rápido). O CSV/TSV inclui descomprimir o gzip e converter texto em números em cada corrida. Os tamanhos estão em `results/sizes.csv` (dataset `imdb`).

## Versões Athena emuladas no DuckDB

| Query | Linhas | Iguais | Nota |
|---|---:|---|---|
| 00_filmes | 9724 | sim |  |
| 01_ligacao | 2 | sim |  |
| 02_ligacao_tipos | 9 | sim |  |
| 03_concordancia | 1 | sim |  |
| 04_gap_genero | 19 | sim |  |
| 05_gap_decada | 9 | sim |  |
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
