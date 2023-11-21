-- :name hae-koulutustoimijat-joilla-koulutuslupa :? :*
SELECT DISTINCT ytunnus, nimi_fi, nimi_sv, nimi_en FROM organisaatio
  WHERE oid IN (SELECT koulutustoimija FROM koulutustoimija_ja_tutkinto);

-- :name hae-koulutustoimijan-oppilaitokset-ytunnuksella :? :*
SELECT o.* FROM organisaatio o JOIN organisaatio kt ON o.parent_oid = kt.oid WHERE kt.ytunnus = :koulutustoimija;

-- :name hae-koulutustoimija-nimella :? :*
SELECT * FROM organisaatio
WHERE ytunnus IS NOT NULL AND
    (nimi_fi ILIKE '%' || :termi  || '%'
        OR nimi_sv ILIKE '%' || :termi  || '%'
        OR nimi_en ILIKE '%' || :termi  || '%');

-- :name hae-oidilla :? :1
SELECT * FROM organisaatio WHERE oid = :oid
AND voimassa = TRUE;

-- :name hae-automaattikysely-oid :? :*
SELECT o.oid
FROM organisaatio o
WHERE o.oid = :oid
  AND NOT EXISTS (SELECT 1 FROM kysely k
                  WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
                    AND k.koulutustoimija = :oid);

-- :name hae-automaattikysely-korkeakoulut :? :*
SELECT DISTINCT kt.oid FROM organisaatio kt
 JOIN organisaatio o on kt.oid = o.parent_oid
 JOIN oppilaitostyyppi_tutkintotyyppi ot ON o.oppilaitostyyppi = ot.oppilaitostyyppi
WHERE kt.lakkautuspaiva IS NULL
 AND o.lakkautuspaiva IS NULL
AND NOT EXISTS (SELECT 1 FROM kysely k
    WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
    AND k.koulutustoimija = kt.oid);

-- :name hae-automaattikysely-koulutustoimijat :? :*
SELECT oid, nimi_fi FROM organisaatio kt
-- löytyy aiempi halutun tyyppinen kysely
WHERE EXISTS (SELECT 1 FROM kysely k WHERE k.koulutustoimija = kt.oid AND k.tyyppi = :kyselytyyppi)
  AND kt.voimassa = TRUE AND kt.postinumero NOT ILIKE '22%'
-- muttei löydy voimassaolevaa automaattisesti luotua
  AND NOT EXISTS (SELECT 1 FROM kysely k
        WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
        AND koulutustoimija = kt.oid);

-- :name hae-ammattikorkeakoulut :? :*
SELECT oid, nimi_fi FROM organisaatio kt
WHERE EXISTS (SELECT 1 FROM organisaatio o WHERE o.parent_oid = kt.oid AND o.oppilaitostyyppi = '41' AND o.voimassa = TRUE)
    AND kt.voimassa = TRUE AND kt.postinumero NOT ILIKE '22%'
    AND NOT EXISTS (SELECT 1 FROM kysely k
                    WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
                      AND k.koulutustoimija = kt.oid)
ORDER BY nimi_fi;

-- :name hae-yliopistot :? :*
SELECT oid, nimi_fi FROM organisaatio kt
WHERE EXISTS (SELECT 1 FROM organisaatio o WHERE o.parent_oid = kt.oid AND o.oppilaitostyyppi = '42' AND o.voimassa = TRUE)
  AND kt.voimassa = TRUE AND kt.postinumero NOT ILIKE '22%'
  AND NOT EXISTS (SELECT 1 FROM kysely k
                  WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
                    AND k.koulutustoimija = kt.oid)
ORDER BY nimi_fi;

-- :name hae-ammatilliset-koulutustoimijat :?
SELECT DISTINCT ktt.koulutustoimija AS oid FROM koulutustoimija_ja_tutkinto ktt
JOIN organisaatio kt on ktt.koulutustoimija = kt.oid
WHERE kt.lakkautuspaiva is NULL
  AND NOT EXISTS (
        SELECT 1
        FROM kysely k
        WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
          AND k.koulutustoimija = kt.oid
    );
