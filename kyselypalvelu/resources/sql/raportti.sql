-- :snip cond-snip
AND :i:cond.0 :sql:cond.1 :v:cond.2

--:snip osaamisala-snip
AND vt.taustatiedot->'osaamisala'::jsonb @> :osaamisala

-- :snip tehtava-snip
AND EXISTS (SELECT 1 FROM vastaus v2 JOIN kysymys k2 ON v2.kysymysid = k2.kysymysid
  WHERE v2.vastaajaid = vs.vastaajaid AND k2.metatiedot->>'taustakysymyksen_tyyppi' = 'tehtava_tyonantajalla' AND v2.numerovalinta = :vaihtoehto)

-- :snip koulutusala-snip
AND EXISTS (SELECT 1 FROM tutkinto t
JOIN opintoala oa ON t.opintoala = oa.opintoalatunnus
WHERE t.tutkintotunnus = vt.taustatiedot->>'tutkinto'
AND oa.koulutusala = :koulutusala)

-- :name hae-kyselyraportti :? :*
SELECT k.kyselypohjaid, v.kysymysid, v.numerovalinta::INT AS numerovalinta, v.vaihtoehto, v.luku, v.en_osaa_sanoa, count(v) AS vastausten_lkm
FROM kysely k
    JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
    JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
    JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
    LEFT JOIN vastaus v ON vs.vastaajaid = v.vastaajaid
    LEFT JOIN kysymys kys ON v.kysymysid = kys.kysymysid
WHERE k.kyselyid = :kyselyid
    AND :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
    --~ (when (not-empty (:where params)) ":snip*:where")
    AND kys.vastaustyyppi NOT IN ('valiotsikko')
    AND ((kys.vastaustyyppi != 'luku') OR ((kys.metatiedot->>'kategoriat') IS NOT NULL))
GROUP BY k.kyselypohjaid, v.kysymysid, v.numerovalinta, v.vaihtoehto, v.luku, v.en_osaa_sanoa;

-- :name hae-lukukysymysten-vastaukset :? :*
SELECT k.kyselypohjaid, v.kysymysid, v.luku, count(v) AS vastausten_lkm
FROM kysely k
    JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
    JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
    JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
    LEFT JOIN vastaus v ON vs.vastaajaid = v.vastaajaid
    LEFT JOIN kysymys kys ON v.kysymysid = kys.kysymysid
WHERE k.kyselyid = :kyselyid
  AND :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
    --~ (when (not-empty (:where params)) ":snip*:where")
  AND kys.vastaustyyppi = 'luku'
  AND (kys.metatiedot->>'kategoriat') IS NOT NULL
GROUP BY k.kyselypohjaid, v.kysymysid, v.luku);

-- :name hae-vapaatekstikysymysten-raportti :? :*
SELECT k.kyselypohjaid, v.kysymysid, v.vapaateksti, v.en_osaa_sanoa, count(v) AS vastausten_lkm
FROM kysely k
         JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
         JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
         JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
         LEFT JOIN vastaus v ON vs.vastaajaid = v.vastaajaid
         LEFT JOIN kysymys kys ON v.kysymysid = kys.kysymysid
WHERE k.kyselyid = :kyselyid
  AND :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
  --~ (when (not-empty (:where params)) ":snip*:where")
  AND kys.vastaustyyppi = 'vapaateksti'
GROUP BY k.kyselypohjaid, v.kysymysid, v.en_osaa_sanoa, v.vapaateksti;

-- :name hae-vertailuraportti :? :*
SELECT kysymysid, numerovalinta::INT AS numerovalinta, vaihtoehto, en_osaa_sanoa, sum(vastausten_lkm)::INT AS vastausten_lkm FROM vertailuraportti
WHERE kyselypohjaid = :kyselypohjaid
  AND alkupvm >= :alkupvm::DATE
  AND loppupvm <= :loppupvm::DATE
GROUP BY kysymysid, numerovalinta, vaihtoehto, en_osaa_sanoa;

-- :name hae-raportin-kohteet :? :1
SELECT sum(kohteiden_lkm) AS kohteita, count(vs) AS vastaajia
FROM vastaajatunnus vt
    LEFT JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
    JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
    JOIN kysely k ON kk.kyselyid = k.kyselyid
WHERE :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
--~(if (:kyselypohjaid params) "AND k.kyselypohjaid = :kyselypohjaid")
--~ (when (not-empty (:where params)) ":snip*:where")
;

-- :name hae-raportin-kohteet-rahoitusryhmittain :? :*
SELECT sum(kohteiden_lkm) AS kohteita,
       count(vs) AS vastaajia,
       vt.taustatiedot->>'rahoitusryhma' as rahoitusryhmatunnus
FROM vastaajatunnus vt
    LEFT JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
    JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
    JOIN kysely k ON kk.kyselyid = k.kyselyid
WHERE :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
--~(if (:kyselypohjaid params) "AND k.kyselypohjaid = :kyselypohjaid")
--~ (when (not-empty (:where params)) ":snip*:where")
GROUP BY vt.taustatiedot->>'rahoitusryhma'
ORDER BY vt.taustatiedot->>'rahoitusryhma';

-- :name hae-raportin-kohteet-tutkinnoittain :? :*
SELECT sum(kohteiden_lkm) AS kohteita,
       count(vs) AS vastaajia,
       vt.taustatiedot->>'tutkinto' AS tutkintotunnus,
       t.nimi_fi,
       t.nimi_sv,
       t.nimi_en
FROM vastaajatunnus vt
         LEFT JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
         JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
         JOIN kysely k ON kk.kyselyid = k.kyselyid
         LEFT JOIN tutkinto t ON t.tutkintotunnus = vt.taustatiedot->>'tutkinto'
WHERE :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
--~(if (:kyselypohjaid params) "AND k.kyselypohjaid = :kyselypohjaid")
--~ (when (not-empty (:where params)) ":snip*:where")
GROUP BY vt.taustatiedot->>'tutkinto', t.nimi_fi, t.nimi_sv, t.nimi_en
ORDER BY vt.taustatiedot->>'tutkinto';

-- :name hae-tyopaikkakyselyn-kohteet-tutkinnoittain :? :*
WITH jaksot AS (
    SELECT jakso.taustatiedot, jakso.voimassa_alkupvm, t.tutkintotunnus,
           t.nimi_fi AS tutkinto_fi, t.nimi_sv AS tutkinto_sv, t.nimi_en AS tutkinto_en
    FROM vastaajatunnus jakso
             JOIN kyselykerta kk on kk.kyselykertaid = jakso.kyselykertaid
             JOIN kysely k on k.kyselyid = kk.kyselyid
             LEFT JOIN tutkinto t ON t.tutkintotunnus = jakso.taustatiedot->>'tutkinto'
    WHERE k.tyyppi = 'tyopaikkaohjaajakysely' AND k.koulutustoimija = :koulutustoimija
      AND (jakso.taustatiedot->>'oppisopimuksen_perusta' IS NULL
        OR jakso.taustatiedot->>'oppisopimuksen_perusta'!= '02'))
SELECT DISTINCT sum(vt.kohteiden_lkm) AS kohteita,
                count(vs) AS vastaajia
FROM kysely k
         JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
         JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
         LEFT JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
WHERE k.kyselyid = :kyselyid
  AND :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
  AND EXISTS (SELECT 1 FROM jaksot j WHERE (j.taustatiedot->>'tyopaikka_normalisoitu' = vt.taustatiedot->>'tyopaikka_normalisoitu'
    AND j.taustatiedot->>'tyonantaja' = vt.taustatiedot->>'tyonantaja'
    AND (j.taustatiedot->>'tyopaikkajakson_loppupvm')::date >= (vt.taustatiedot->>'tiedonkeruu_alkupvm')::date
    AND (j.taustatiedot->>'tyopaikkajakson_loppupvm')::date <= (vt.taustatiedot->>'tiedonkeruu_loppupvm')::date)
    --~ (when (not-empty (:where params)) ":snip*:where")
    )
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
--~(if (:kyselypohjaid params) "AND k.kyselypohjaid = :kyselypohjaid")
;

-- :name hae-raportin-kohteet :? :1
SELECT sum(kohteiden_lkm) AS kohteita,
       count(vs) AS vastaajia
FROM vastaajatunnus vt
         LEFT JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
         JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
         JOIN kysely k ON kk.kyselyid = k.kyselyid
         LEFT JOIN tutkinto t ON t.tutkintotunnus = vt.taustatiedot->>'tutkinto'
WHERE :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
--~(if (:kyselypohjaid params) "AND k.kyselypohjaid = :kyselypohjaid")
--~ (when (not-empty (:where params)) ":snip*:where")
;

-- :name hae-raportin-tutkinnot :? :*
SELECT vt.taustatiedot->>'tutkinto' AS tutkintotunnus,
       t.nimi_fi, t.nimi_sv, t.nimi_en, count(vs) AS vastaajia
FROM vastaajatunnus vt
    JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
    JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
    JOIN kysely k ON kk.kyselyid = k.kyselyid
    JOIN tutkinto t ON vt.taustatiedot->>'tutkinto' = t.tutkintotunnus
WHERE k.kyselyid = :kyselyid
  AND :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
GROUP BY vt.taustatiedot->>'tutkinto', t.nimi_fi, t.nimi_sv, t.nimi_en;


-- :name laske-vertailudata! :! :n
INSERT INTO vertailuraportti (kyselypohjaid, alkupvm, loppupvm, kysymysid, numerovalinta, vaihtoehto, en_osaa_sanoa, vastausten_lkm)
SELECT k.kyselypohjaid, :alkupvm::DATE, :loppupvm::DATE, v.kysymysid, v.numerovalinta, v.vaihtoehto, v.en_osaa_sanoa, count(v)
FROM kysely k
         JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
         JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
         JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
         JOIN vastaus v ON vs.vastaajaid = v.vastaajaid
         JOIN kysymys kys ON v.kysymysid = kys.kysymysid
WHERE k.kyselypohjaid IS NOT NULL
  AND (vs.luotuaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE)
  AND kys.vastaustyyppi NOT IN ('vapaateksti', 'valiotsikko', 'luku')
GROUP BY k.kyselypohjaid, v.kysymysid, v.numerovalinta, v.vaihtoehto, v.en_osaa_sanoa;

-- :name laske-vertailu-keskiarvot! :! :n
INSERT INTO vertailuraportti (kyselypohjaid, alkupvm, loppupvm, kysymysid, vastausten_lkm, keskiarvo)
SELECT k.kyselypohjaid, :alkupvm::DATE, :loppupvm::DATE, kys.kysymysid, avg(v.luku) AS keskiarvo, count(v) AS vastausten_lkm
FROM vastaus v
         JOIN vastaaja vs ON v.vastaajaid = vs.vastaajaid
         JOIN vastaajatunnus vt ON vs.vastaajatunnusid = vt.vastaajatunnusid
         JOIN kyselykerta kk on kk.kyselykertaid = vs.kyselykertaid
         JOIN kysely k on k.kyselyid = kk.kyselyid
         JOIN kysymys kys ON v.kysymysid = kys.kysymysid
WHERE k.kyselypohjaid IS NOT NULL
  AND kys.vastaustyyppi = 'luku'
  AND (vs.luotuaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE)
GROUP BY k.kyselypohjaid, kys.kysymysid;

-- :name poista-kuukauden-vertailudata! :! :n
DELETE FROM vertailuraportti WHERE alkupvm = :alkupvm::DATE;

-- :name hae-kyselyiden-perustiedot :? :*
SELECT kyselyid, koulutustoimija, nimi_fi, nimi_sv, nimi_en, voimassa_alkupvm, voimassa_loppupvm, tyyppi, tila,
       CASE WHEN voimassa_alkupvm > current_date THEN 'tuleva'
            WHEN voimassa_alkupvm <= current_date AND (voimassa_loppupvm >= current_date OR voimassa_loppupvm IS NULL) THEN 'kaynnissa'
            WHEN voimassa_loppupvm < current_date AND voimassa_loppupvm > (current_date - 31) THEN 'juuri_paattynyt'
            ELSE 'arkistoitu'
        END AS kategoria
FROM kysely
WHERE koulutustoimija = :koulutustoimija
AND tila != 'luonnos';

-- :name hae-raportin-tutkintonimikkeet :? :*
SELECT DISTINCT tn.koodi_arvo AS arvo, tn.nimi_fi, tn.nimi_sv, tn.nimi_en
FROM kysely k
         JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
         JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
         JOIN koodi tn ON tn.koodisto_uri = 'tutkintonimikkeet' AND (vt.taustatiedot->>'tutkintonimike')::JSONB ?? tn.koodi_arvo
WHERE k.kyselyid = :kyselyid;

--:name hae-raportin-toimipisteet :? :*
SELECT DISTINCT o.toimipistekoodi AS arvo, o.nimi_fi, o.nimi_sv , o.nimi_en
FROM kysely k
JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
JOIN organisaatio o ON vt.taustatiedot->>'toimipiste' = o.toimipistekoodi
WHERE k.kyselyid = :kyselyid;

--:name hae-raportin-oppilaitokset :? :*
SELECT DISTINCT o.oid AS arvo, o.oppilaitoskoodi, o.nimi_fi, o.nimi_sv, o.nimi_en
FROM kysely k
 JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
 JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
 JOIN organisaatio o ON vt.valmistavan_koulutuksen_oppilaitos = o.oid
WHERE k.kyselyid = :kyselyid;

-- :name hae-raportin-osaamisalat :? :*
SELECT DISTINCT oa.koodi_arvo AS arvo, oa.nimi_fi, oa.nimi_sv, oa.nimi_en
FROM kysely k
    JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
    JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
    JOIN koodi oa ON oa.koodisto_uri = 'osaamisala' AND oa.koodi_arvo = vt.taustatiedot->>'osaamisala'
WHERE k.kyselyid = :kyselyid;

--:name hae-raportin-hankintakoulutuksen-toteuttajat :? :*
SELECT DISTINCT o.oid AS arvo, o.ytunnus, o.nimi_fi, o.nimi_sv, o.nimi_en
FROM kyselykerta kk
    JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
    JOIN organisaatio o ON vt.taustatiedot->>'hankintakoulutuksen_toteuttaja' = o.ytunnus
WHERE kk.kyselyid = :kyselyid;

--:name hae-raportin-tutkinnon-tasot :? :*
SELECT DISTINCT vt.taustatiedot->>'tutkinnon_taso' AS arvo, k.nimi_fi, k.nimi_sv, k.nimi_en
FROM vastaajatunnus vt
 JOIN kyselykerta kk ON kk.kyselykertaid = vt.kyselykertaid
 JOIN koodi k ON vt.taustatiedot->>'tutkinnon_taso' = k.koodi_arvo AND k.koodisto_uri = 'virtaopiskeluoikeudentyyppi'
WHERE kk.kyselyid = :kyselyid;

--:name hae-raportin-tyonantajat :? :*
SELECT DISTINCT vt.taustatiedot->>'tyonantaja' AS arvo, vt.taustatiedot->>'tyonantaja' AS nimi_fi,
                vt.taustatiedot->>'tyonantaja' AS nimi_sv, vt.taustatiedot->>'tyonantaja' AS nimi_en
FROM vastaajatunnus vt
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
WHERE kk.kyselyid = :kyselyid AND vt.taustatiedot->>'tyonantaja' IS NOT NULL;

-- :name hae-raportin-oppisopimuksen-perustat :? :*
SELECT DISTINCT k.koodi_arvo AS arvo, k.nimi_fi, k.nimi_sv, k.nimi_en
FROM vastaajatunnus vt
 JOIN kyselykerta kk ON kk.kyselykertaid = vt.kyselykertaid
 JOIN koodi k ON k.koodisto_uri = 'oppisopimuksenperusta' AND k.koodi_arvo = vt.taustatiedot->>'oppisopimuksen_perusta'
WHERE kk.kyselyid = :kyselyid;

-- :name hae-raportin-sopimustyypit :? :*
SELECT DISTINCT vt.taustatiedot->>'sopimustyyppi' AS arvo, k.nimi_fi, k.nimi_sv, k.nimi_en
FROM vastaajatunnus vt
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
JOIN koodi k ON k.koodisto_uri = 'arvo-sopimustyyppi' AND k.koodi_arvo = vt.taustatiedot->>'sopimustyyppi'
WHERE kk.kyselyid = :kyselyid;

--:name hae-raportin-tehtavat :? :*
SELECT DISTINCT mvv.arvo, mvv.teksti_fi AS nimi_fi, mvv.teksti_sv AS nimi_sv, mvv.teksti_en AS nimi_en
FROM vastaus v
  JOIN kysymys k on k.kysymysid = v.kysymysid
  JOIN monivalintavaihtoehto mvv ON k.kysymysid = mvv.kysymysid AND v.numerovalinta = mvv.arvo
  JOIN vastaaja vs ON v.vastaajaid = vs.vastaajaid
  JOIN vastaajatunnus vt ON vs.vastaajatunnusid = vt.vastaajatunnusid
  JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
WHERE k.metatiedot->>'taustakysymyksen_tyyppi' = 'tehtava_tyonantajalla'
  AND kk.kyselyid = :kyselyid;

--:name hae-raportin-kyselykerrat :? :*
SELECT DISTINCT kyselykertaid AS arvo, kk.nimi AS nimi_fi
FROM kyselykerta kk
WHERE kyselyid = :kyselyid;

-- :name hae-tyopaikkakyselyn-raportti :? :*
WITH jaksot AS (
    SELECT jakso.taustatiedot, jakso.voimassa_alkupvm
    FROM vastaajatunnus jakso
             JOIN kyselykerta kk on kk.kyselykertaid = jakso.kyselykertaid
             JOIN kysely k on k.kyselyid = kk.kyselyid
    WHERE k.tyyppi = 'tyopaikkaohjaajakysely' AND k.koulutustoimija = :koulutustoimija
      AND (jakso.taustatiedot->>'oppisopimuksen_perusta' IS NULL
        OR jakso.taustatiedot->>'oppisopimuksen_perusta'!= '02'))
SELECT k.kyselypohjaid, v.kysymysid, v.numerovalinta::INT AS numerovalinta, v.vaihtoehto, v.luku, v.en_osaa_sanoa, count(v) AS vastausten_lkm
FROM kysely k
 JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
 JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
 JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
 LEFT JOIN vastaus v ON vs.vastaajaid = v.vastaajaid
 LEFT JOIN kysymys kys ON v.kysymysid = kys.kysymysid
WHERE k.kyselyid = :kyselyid
  AND :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE

  AND kys.vastaustyyppi NOT IN ('valiotsikko')
  AND EXISTS (SELECT 1 FROM jaksot j WHERE (j.taustatiedot->>'tyopaikka_normalisoitu' = vt.taustatiedot->>'tyopaikka_normalisoitu'
    AND j.taustatiedot->>'tyonantaja' = vt.taustatiedot->>'tyonantaja'
    AND (j.taustatiedot->>'tyopaikkajakson_loppupvm')::date >= (vt.taustatiedot->>'tiedonkeruu_alkupvm')::date
    AND (j.taustatiedot->>'tyopaikkajakson_loppupvm')::date <= (vt.taustatiedot->>'tiedonkeruu_loppupvm')::date)
    --~ (when (not-empty (:where params)) ":snip*:where")
      )
  AND ((kys.vastaustyyppi != 'luku') OR ((kys.metatiedot->>'kategoriat') IS NOT NULL))
GROUP BY k.kyselypohjaid, v.kysymysid, v.numerovalinta, v.vaihtoehto, v.luku, v.en_osaa_sanoa;

-- :name hae-tyopaikkakyselyn-tutkinnot :? :*
SELECT DISTINCT t.tutkintotunnus, t.nimi_fi AS tutkinto_fi, t.nimi_sv AS tutkinto_sv, t.nimi_en AS tutkinto_en
FROM vastaajatunnus jakso
         JOIN vastaajatunnus vt ON jakso.taustatiedot->>'tyopaikka_normalisoitu' = vt.taustatiedot->>'tyopaikka_normalisoitu'
         JOIN kyselykerta vt_kk ON vt.kyselykertaid = vt_kk.kyselykertaid
         JOIN kysely vt_k ON vt_kk.kyselyid = vt_k.kyselyid
         JOIN kyselykerta jakso_kk ON jakso.kyselykertaid = jakso_kk.kyselykertaid
         JOIN kysely jakso_k ON jakso_k.kyselyid = jakso_kk.kyselyid
         JOIN tutkinto t ON jakso.taustatiedot->>'tutkinto' = t.tutkintotunnus
WHERE vt_k.koulutustoimija = jakso_k.koulutustoimija
  AND jakso.taustatiedot->>'tyonantaja' = vt.taustatiedot->>'tyonantaja'
  AND (jakso.taustatiedot->>'tyopaikkajakson_loppupvm')::date BETWEEN (vt.taustatiedot->>'tiedonkeruu_alkupvm')::date AND (vt.taustatiedot->>'tiedonkeruu_loppupvm')::date
  AND vt_k.kyselyid = :kyselyid;


-- :name hae-tyopaikkakyselyn-vapaatekstikysymysten-raportti :? :*
WITH jaksot AS (
    SELECT jakso.taustatiedot, jakso.voimassa_alkupvm
    FROM vastaajatunnus jakso
             JOIN kyselykerta kk on kk.kyselykertaid = jakso.kyselykertaid
             JOIN kysely k on k.kyselyid = kk.kyselyid
    WHERE k.tyyppi = 'tyopaikkaohjaajakysely' AND k.koulutustoimija = :koulutustoimija
      AND (jakso.taustatiedot->>'oppisopimuksen_perusta' IS NULL
        OR jakso.taustatiedot->>'oppisopimuksen_perusta'!= '02'))
SELECT DISTINCT k.kyselypohjaid, v.kysymysid, v.vapaateksti, v.en_osaa_sanoa, count(v) AS vastausten_lkm
FROM kysely k
         JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
         JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
         JOIN vastaaja vs ON vt.vastaajatunnusid = vs.vastaajatunnusid
         LEFT JOIN vastaus v ON vs.vastaajaid = v.vastaajaid
         LEFT JOIN kysymys kys ON v.kysymysid = kys.kysymysid
WHERE k.kyselyid = :kyselyid
  AND :i:vastausaika BETWEEN :alkupvm::DATE AND :loppupvm::DATE
  AND kys.vastaustyyppi = 'vapaateksti'
  AND EXISTS (SELECT 1 FROM jaksot j WHERE (j.taustatiedot->>'tyopaikka_normalisoitu' = vt.taustatiedot->>'tyopaikka_normalisoitu'
    AND j.taustatiedot->>'tyonantaja' = vt.taustatiedot->>'tyonantaja'
    AND (j.taustatiedot->>'tyopaikkajakson_loppupvm')::date >= (vt.taustatiedot->>'tiedonkeruu_alkupvm')::date
    AND (j.taustatiedot->>'tyopaikkajakson_loppupvm')::date <= (vt.taustatiedot->>'tiedonkeruu_loppupvm')::date)
    --~ (when (not-empty (:where params)) ":snip*:where")
      )
GROUP BY k.kyselypohjaid, v.kysymysid, v.en_osaa_sanoa, v.vapaateksti;
