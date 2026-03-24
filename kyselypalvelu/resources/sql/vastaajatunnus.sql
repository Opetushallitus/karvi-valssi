-- :name kyselykerran-tyyppi :? :1
SELECT k.tyyppi FROM kysely k
  JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
  WHERE kk.kyselykertaid = :kyselykertaid;

-- :name lisaa-vastaajatunnus! :<!
INSERT INTO vastaajatunnus (tunnus, kyselykertaid, suorituskieli, tutkintotunnus, taustatiedot, metatiedot,
                          kohteiden_lkm,
                          valmistavan_koulutuksen_oppilaitos,
                          voimassa_alkupvm, voimassa_loppupvm, luotu_kayttaja, muutettu_kayttaja, luotuaika, muutettuaika)
VALUES (:tunnus, :kyselykertaid, :kieli, :tutkinto, :taustatiedot, :metatiedot,
      :kohteiden_lkm, :valmistavan_koulutuksen_oppilaitos,
      :voimassa_alkupvm, :voimassa_loppupvm, :kayttaja, :kayttaja, now(), now())
RETURNING vastaajatunnusid;

-- :name lisaa-yleinen-vastaajatunnus! :<! :1
INSERT INTO vastaajatunnus (tunnus, kyselykertaid, kohteiden_lkm, voimassa_alkupvm, voimassa_loppupvm, luotu_kayttaja, muutettu_kayttaja, taustatiedot, metatiedot, luotuaika, muutettuaika)
VALUES (:tunnus, :kyselykertaid, :kohteiden_lkm, :voimassa_alkupvm, :voimassa_loppupvm, :kayttaja_oid, :kayttaja_oid, :taustatiedot, :metatiedot, now(), now())
RETURNING tunnus;

-- :name paivita-taustatiedot! :! :n
UPDATE vastaajatunnus SET
taustatiedot =  COALESCE(taustatiedot || :taustatiedot, :taustatiedot)
WHERE tunnus = :vastaajatunnus;

-- :name paivita-metatiedot! :! :n
UPDATE vastaajatunnus
SET metatiedot = COALESCE(metatiedot || :metatiedot, :metatiedot), muutettu_kayttaja = :kayttaja
WHERE tunnus = :tunnus AND luotu_kayttaja = :kayttaja;

-- :name hae-viimeisin-tutkinto :? :*
SELECT t.* FROM vastaajatunnus vt
JOIN tutkinto t ON t.tutkintotunnus = vt.tutkintotunnus
JOIN koulutustoimija_ja_tutkinto ktt
  ON (ktt.tutkinto = t.tutkintotunnus AND ktt.koulutustoimija = :koulutustoimija)
WHERE vt.kyselykertaid = :kyselykertaid
ORDER BY vt.luotuaika DESC;

-- :name hae-vastaajatunnus :? :*
SELECT vt.vastaajatunnusid, vt.kyselykertaid, vt.tutkintotunnus, vt.tunnus, vt.lukittu, vt.luotu_kayttaja, vt.muutettu_kayttaja,
       vt.luotuaika, vt.muutettuaika, vt.valmistavan_koulutuksen_oppilaitos, vt.metatiedot,
       vt.suorituskieli, vt.kunta, vt.taustatiedot, vt.voimassa_alkupvm, vt.voimassa_loppupvm, vt.kohteiden_lkm, vt.kaytettavissa,
       t.nimi_fi, t.nimi_sv, t.nimi_en, (vt.taustatiedot ->> 'koulutusmuoto') AS koulutusmuoto,
COALESCE(COALESCE(vt.voimassa_loppupvm, kk.voimassa_loppupvm, k.voimassa_loppupvm) + 30 > CURRENT_DATE, TRUE) AS muokattavissa,
(SELECT count(*) FROM vastaaja WHERE vastaajatunnusid = vt.vastaajatunnusid) AS vastausten_lkm,
o.oppilaitoskoodi, o.nimi_fi AS oppilaitos_nimi_fi, o.nimi_sv AS oppilaitos_nimi_sv, o.nimi_en AS oppilaitos_nimi_en, o.oid AS oppilaitos_oid,
tmp.toimipistekoodi, tmp.nimi_fi AS toimipiste_nimi_fi, tmp.nimi_sv AS toimipiste_nimi_sv, tmp.nimi_en AS toimipiste_nimi_en, tmp.oid AS toimipiste_oid
FROM vastaajatunnus vt
LEFT JOIN tutkinto t ON vt.tutkintotunnus = t.tutkintotunnus
LEFT JOIN organisaatio o ON vt.valmistavan_koulutuksen_oppilaitos = o.oid
LEFT JOIN organisaatio tmp ON vt.taustatiedot->>'toimipiste_oid' = tmp.oid
    AND 'organisaatiotyyppi_03' = ANY(tmp.tyypit) AND tmp.toimipistekoodi IS NOT NULL
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
JOIN kysely k ON kk.kyselyid = k.kyselyid
WHERE vt.kyselykertaid = :kyselykertaid
--~ (if (:tunnus params) "AND tunnus = :tunnus")
--~ (if (:oid params) "AND vt.luotu_kayttaja = :oid")
ORDER BY vt.luotuaika DESC;

-- :name hae-tyopaikkakysely-tunnus :? :*
WITH jaksot AS (
    SELECT jakso.taustatiedot, jakso.voimassa_alkupvm
    FROM vastaajatunnus jakso
    JOIN kyselykerta kk on kk.kyselykertaid = jakso.kyselykertaid
    JOIN kysely k on k.kyselyid = kk.kyselyid
    WHERE k.tyyppi = 'tyopaikkaohjaajakysely' AND k.koulutustoimija = :koulutustoimija
    AND (jakso.taustatiedot->>'oppisopimuksen_perusta' IS NULL
        OR jakso.taustatiedot->>'oppisopimuksen_perusta'!= '02'))
SELECT vt.vastaajatunnusid, vt.kyselykertaid, vt.tutkintotunnus, vt.tunnus, vt.lukittu, vt.luotu_kayttaja, vt.muutettu_kayttaja, vt.taustatiedot,
       vt.luotuaika, vt.muutettuaika, vt.valmistavan_koulutuksen_oppilaitos, vt.metatiedot,
       vt.voimassa_alkupvm, vt.voimassa_loppupvm, vt.kohteiden_lkm, vt.kaytettavissa, count(j) AS jaksojen_lkm,
       (SELECT count(*) FROM vastaaja WHERE vastaajatunnusid = vt.vastaajatunnusid) AS vastausten_lkm
FROM vastaajatunnus vt
JOIN kyselykerta k ON k.kyselykertaid = vt.kyselykertaid
JOIN jaksot j ON j.taustatiedot->>'tyopaikka_normalisoitu' = vt.taustatiedot->>'tyopaikka_normalisoitu'
    AND j.taustatiedot->>'tyonantaja' = vt.taustatiedot->>'tyonantaja'
    AND (j.taustatiedot->>'tyopaikkajakson_loppupvm')::date >= (vt.taustatiedot->>'tiedonkeruu_alkupvm')::date
    AND (j.taustatiedot->>'tyopaikkajakson_loppupvm')::date <= (vt.taustatiedot->>'tiedonkeruu_loppupvm')::date
WHERE vt.kyselykertaid = :kyselykertaid
GROUP BY vt.vastaajatunnusid, vt.kyselykertaid, vt.tutkintotunnus, vt.tunnus, vt.lukittu, vt.luotu_kayttaja, vt.muutettu_kayttaja, vt.taustatiedot,
         vt.luotuaika, vt.muutettuaika, vt.valmistavan_koulutuksen_oppilaitos, vt.metatiedot,
         vt.taustatiedot, vt.voimassa_alkupvm, vt.voimassa_loppupvm, vt.kohteiden_lkm, vt.kaytettavissa;

-- :name tyopaikkakyselyn-tunnus-olemassa? :? :1
SELECT TRUE FROM vastaajatunnus vt
JOIN kyselykerta k ON k.kyselykertaid = vt.kyselykertaid
WHERE vt.kyselykertaid = :kyselykertaid
AND vt.taustatiedot->>'tyonantaja' = :tyonantaja
AND vt.taustatiedot->>'tyopaikka_normalisoitu' = :tyopaikka_normalisoitu
AND vt.taustatiedot->>'tiedonkeruu_alkupvm' = :tiedonkeruu_alkupvm
AND vt.taustatiedot->>'tiedonkeruu_loppupvm' = :tiedonkeruu_loppupvm
AND vt.taustatiedot->>'tiedonkeruu_loppupvm' = :tiedonkeruu_loppupvm;

-- :name hae-tyopaikkakyselyn-jaksot :? :*
SELECT jakso.tunnus, jakso.taustatiedot, jakso.voimassa_alkupvm, vt.tunnus AS tyopaikkakysely_tunnus
FROM vastaajatunnus jakso
    JOIN vastaajatunnus vt ON jakso.taustatiedot->>'tyopaikka_normalisoitu' = vt.taustatiedot->>'tyopaikka_normalisoitu'
    JOIN kyselykerta vt_kk ON vt.kyselykertaid = vt_kk.kyselykertaid
    JOIN kysely vt_k ON vt_kk.kyselyid = vt_k.kyselyid
    JOIN kyselykerta jakso_kk ON jakso.kyselykertaid = jakso_kk.kyselykertaid
    JOIN kysely jakso_k ON jakso_k.kyselyid = jakso_kk.kyselyid
WHERE vt_k.koulutustoimija = jakso_k.koulutustoimija
    AND jakso.taustatiedot->>'tyonantaja' = vt.taustatiedot->>'tyonantaja'
    AND (jakso.taustatiedot->>'tyopaikkajakson_loppupvm')::date BETWEEN (vt.taustatiedot->>'tiedonkeruu_alkupvm')::date AND (vt.taustatiedot->>'tiedonkeruu_loppupvm')::date
    AND vt.kyselykertaid = :kyselykertaid;

-- :name hae-tyoelamapalaute-tunnukset :? :*
WITH tyopaikkakysely_tunnukset AS (
    SELECT vt.tunnus, vt.taustatiedot FROM vastaajatunnus vt
                                               JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
                                               JOIN kysely k on k.kyselyid = kk.kyselyid
    WHERE k.tyyppi = 'tyopaikkakysely' AND k.koulutustoimija = :koulutustoimija
)
SELECT jakso.vastaajatunnusid, jakso.kyselykertaid, jakso.tutkintotunnus, jakso.tunnus, jakso.lukittu, jakso.luotu_kayttaja, jakso.muutettu_kayttaja, jakso.taustatiedot,
       jakso.luotuaika, jakso.muutettuaika, jakso.valmistavan_koulutuksen_oppilaitos, jakso.metatiedot,
       jakso.voimassa_alkupvm, jakso.voimassa_loppupvm, jakso.kohteiden_lkm, jakso.kaytettavissa AS jaksojen_lkm,
       (SELECT count(*) FROM vastaaja WHERE vastaajatunnusid = jakso.vastaajatunnusid) AS vastausten_lkm,
       tpk_vt.tunnus AS tyopaikkakysely_tunnus
FROM vastaajatunnus jakso
         LEFT JOIN tyopaikkakysely_tunnukset tpk_vt ON
                jakso.taustatiedot->>'tyonantaja' = tpk_vt.taustatiedot->>'tyonantaja' AND
                jakso.taustatiedot->>'tyopaikka_normalisoitu' = tpk_vt.taustatiedot->>'tyopaikka_normalisoitu' AND
                ((jakso.taustatiedot->>'tyopaikkajakson_loppupvm')::date BETWEEN
                    (tpk_vt.taustatiedot->>'tiedonkeruu_alkupvm')::date AND
                    (tpk_vt.taustatiedot->>'tiedonkeruu_loppupvm')::date)
WHERE jakso.kyselykertaid = :kyselykertaid;

-- :name hae-vastaajatunnuksen-tiedot :? :1
SELECT vt.*, k.tyyppi AS kyselytyyppi
FROM vastaajatunnus vt
JOIN kyselykerta kk on kk.kyselykertaid = vt.kyselykertaid
JOIN kysely k on k.kyselyid = kk.kyselyid
WHERE tunnus = :tunnus;

-- :name vastaajatunnus-olemassa? :? :1
SELECT TRUE AS olemassa FROM vastaajatunnus WHERE tunnus = :vastaajatunnus;

-- :name lukitse-vastaajatunnus! :! :n
UPDATE vastaajatunnus SET lukittu = :lukittu WHERE tunnus = :tunnus;

-- :name poista-vastaajatunnus! :! :n
DELETE FROM vastaajatunnus WHERE tunnus = :tunnus;

-- :name poista-kyselykerran-tunnukset! :! :n
DELETE FROM vastaajatunnus WHERE kyselykertaid = :kyselykertaid;

-- :name muokkaa-vastaajien-maaraa! :! :n
UPDATE vastaajatunnus SET kohteiden_lkm = :vastaajia WHERE tunnus = :tunnus;

-- :name vastaajien-lkm :? :1
SELECT count(*) FROM vastaaja AS vastaajia WHERE vastaajatunnusid = :vastaajatunnusid;

-- :name vastaajatunnus-status :? :1
SELECT vt.vastaajatunnusid, vt.tunnus, vt.voimassa_loppupvm, k.tyyppi AS kyselytyyppi,
EXISTS(SELECT 1 FROM vastaaja v WHERE v.vastaajatunnusid = vt.vastaajatunnusid) AS vastattu
FROM vastaajatunnus vt
JOIN kyselykerta kk ON kk.kyselykertaid = vt.kyselykertaid
JOIN kysely k on k.kyselyid = kk.kyselyid
WHERE vt.tunnus = :tunnus;

-- :name nippu-status :? :1
SELECT n.tunniste, n.voimassa_loppupvm,
EXISTS (
    SELECT 1 FROM vastaajatunnus vt
    JOIN vastaaja v ON v.vastaajatunnusid = vt.vastaajatunnusid
    AND vt.metatiedot->>'nippu' = n.tunniste)
AS vastattu
FROM nippu n
WHERE n.tunniste = :tunniste;

-- :name hae-kyselyn-kohteet :? :*
SELECT vt.tunnus, kk.nimi, vt.voimassa_alkupvm,
       vt.kohteiden_lkm, count(v) AS vastaajien_lkm,
       t.tutkintotunnus, t.nimi_fi AS tutkinto_selite_fi, t.nimi_sv AS tutkinto_selite_sv, t.nimi_en AS tutkinto_selite_en
FROM vastaajatunnus vt
LEFT JOIN vastaaja v on vt.vastaajatunnusid = v.vastaajatunnusid
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
LEFT JOIN tutkinto t ON vt.taustatiedot->>'tutkinto' = t.tutkintotunnus
WHERE kk.kyselyid = :kyselyid
GROUP BY vt.tunnus, kk.nimi, vt.voimassa_alkupvm, vt.kohteiden_lkm,
         t.tutkintotunnus, t.nimi_fi, t.nimi_sv, t.nimi_en;

-- :name hae-kyselyn-vastaajat :? :*
SELECT vt.tunnus,
       kk.nimi,
       vt.voimassa_alkupvm,
       v.luotuaika AS vastausaika,
       t.tutkintotunnus,
       t.nimi_fi AS tutkinto_selite_fi,
       t.nimi_sv AS tutkinto_selite_sv,
       t.nimi_en AS tutkinto_selite_en
FROM vastaaja v
JOIN vastaajatunnus vt ON v.vastaajatunnusid = vt.vastaajatunnusid
LEFT JOIN tutkinto t ON vt.taustatiedot->>'tutkinto' = t.tutkintotunnus
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
WHERE kk.kyselyid = :kyselyid;

--:name lisaa-nippu! :! :n
INSERT INTO nippu (tunniste, kyselykertaid, voimassa_alkupvm, voimassa_loppupvm, taustatiedot)
VALUES (:tunniste, :kyselykertaid, :voimassa_alkupvm, :voimassa_loppupvm, :taustatiedot);

--:name liita-tunnukset-nippuun! :! :n
UPDATE vastaajatunnus SET metatiedot = coalesce(metatiedot, '{}') || jsonb_build_object('nippu', :tunniste)
WHERE tunnus IN (:v*:tunnukset);

--:name hae-niputettavat-tunnukset :? :*
SELECT vt.tunnus, vt.valmistavan_koulutuksen_oppilaitos, vt.taustatiedot, k.koulutustoimija FROM vastaajatunnus vt
JOIN kyselykerta kk on vt.kyselykertaid = kk.kyselykertaid
JOIN kysely k on kk.kyselyid = k.kyselyid
WHERE vt.tunnus IN (:v*:tunnukset)
AND vt.metatiedot->>'nippu' IS NULL;

-- :name hae-kyselykerran-niput :? :*
SELECT DISTINCT n.tunniste, kk.kyselyid, n.voimassa_alkupvm, n.voimassa_loppupvm, n.taustatiedot, n.metatiedot,
                t.nimi_fi AS tutkinto_fi, t.nimi_sv AS tutkinto_sv, t.nimi_en AS tutkinto_en,
                count(vt) AS kohteiden_lkm, count(v) AS vastausten_lkm,
                (n.voimassa_alkupvm <= current_date AND (n.voimassa_loppupvm >= current_date OR n.voimassa_loppupvm IS NULL)
                    AND k.kaytettavissa) AS kaytettavissa
FROM nippu n
JOIN kyselykerta kk ON kk.kyselykertaid = n.kyselykertaid
JOIN kysely k ON kk.kyselyid = k.kyselyid
LEFT JOIN vastaajatunnus vt ON vt.metatiedot->>'nippu' = n.tunniste
LEFT JOIN vastaaja v ON vt.vastaajatunnusid = v.vastaajatunnusid
LEFT JOIN tutkinto t ON n.taustatiedot->>'tutkinto' = t.tutkintotunnus
WHERE kk.kyselykertaid = :kyselykertaid
GROUP BY n.tunniste, kk.kyselyid, n.voimassa_alkupvm, n.tunniste, n.voimassa_loppupvm, n.taustatiedot,
         t.nimi_fi, t.nimi_sv, t.nimi_en, k.kaytettavissa
ORDER BY voimassa_alkupvm DESC;

-- :name hae-nippu :? :1
SELECT * FROM nippu WHERE tunniste = :tunniste;

-- :name hae-nipun-tunnukset :? :*
SELECT vt.*,
       EXISTS(SELECT 1 FROM vastaaja v WHERE v.vastaajatunnusid = vt.vastaajatunnusid) AS vastattu
FROM vastaajatunnus vt
WHERE vt.metatiedot->>'nippu' = :tunniste;

-- :name poista-nippu! :! :n
DELETE FROM nippu WHERE tunniste = :tunniste;

-- :name poista-tunnukset-nipusta! :! :n
UPDATE vastaajatunnus SET metatiedot = metatiedot - 'nippu' WHERE metatiedot->>'nippu' = :tunniste;

-- :name paivita-nipun-metatiedot! :! :n
UPDATE nippu SET metatiedot = COALESCE(metatiedot || :metatiedot, :metatiedot)
WHERE tunniste = :tunniste;

-- :name paivita-nippu! :! :n
UPDATE nippu SET metatiedot = COALESCE(metatiedot || :metatiedot, :metatiedot),
                 voimassa_loppupvm = :voimassa_loppupvm::DATE
WHERE tunniste = :tunniste;
