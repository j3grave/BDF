-- 03_ratings_part_particoes.sql
-- Regista no catálogo as partições de ratings_part: percorre as pastas year=AAAA no S3
-- e acrescenta uma partição por pasta. Tem de voltar a correr se forem acrescentados anos.
-- (Alternativa sem este passo: partition projection nas TBLPROPERTIES da tabela.)
--
-- Parâmetros: nenhum
MSCK REPAIR TABLE ratings_part
