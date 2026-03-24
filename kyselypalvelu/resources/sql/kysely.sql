-- :name hae-vastaukset :? :*
SELECT v.vastausid,
       k.kysymysid,
       vs.vastaajaid,
       v.vapaateksti,
       v.numerovalinta::int,
       v.vaihtoehto, v.luku,
       v.en_osaa_sanoa,
       vs.luotuaika AS vastausaika,
       vt.tunnus AS vastaajatunnus,
       n.tunniste AS nippu,
       vt.tutkintotunnus,
       k.kysymysryhmaid, k.vastaustyyppi,
       k.metatiedot->>'koodisto' AS koodisto
FROM vastaus v
         JOIN kysymys k ON v.kysymysid = k.kysymysid
         JOIN kysymysryhma kr ON k.kysymysryhmaid = kr.kysymysryhmaid
         JOIN vastaaja vs ON v.vastaajaid = vs.vastaajaid
         JOIN kyselykerta kk ON vs.kyselykertaid = kk.kyselykertaid
         JOIN vastaajatunnus vt ON vt.vastaajatunnusid = vs.vastaajatunnusid
         LEFT JOIN nippu n ON vt.metatiedot->>'nippu' = n.tunniste
WHERE kk.kyselyid = :kyselyid;

-- :name hae-monivalinnat :? :*
SELECT * FROM monivalintavaihtoehto
WHERE kysymysid IN (:v*:kysymysidt);

-- :name hae-kysely :? :1
SELECT k.*, k.kaytettavissa,
   NOT EXISTS(SELECT 1
              FROM kyselykerta kk
                       JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
                       JOIN vastaaja v ON vt.vastaajatunnusid = v.vastaajatunnusid
              WHERE kk.kyselyid = k.kyselyid) AS poistettavissa,
    kt.nimi_fi AS koulutustoimija_fi, kt.nimi_sv AS koulutustoimija_sv, kt.nimi_en AS koulutustoimija_en
FROM kysely k
JOIN organisaatio kt ON kt.oid = k.koulutustoimija WHERE kyselyid = :kyselyid;

-- :name hae-kyselyt :? :*
SELECT k.kyselyid, k.nimi_fi, k.nimi_sv, k.nimi_en, k.voimassa_alkupvm, k.voimassa_loppupvm,
       k.tila,
       k.uudelleenohjaus_url, k.sivutettu, kt.ytunnus AS koulutustoimija,
       k.metatiedot, k.tyyppi, k.oppilaitos,
       (SELECT COUNT(*) FROM kysely_kysymysryhma kkr WHERE kkr.kyselyid = k.kyselyid) AS kysymysryhmien_lkm,
       (SELECT now() < k.voimassa_alkupvm) AS tulevaisuudessa,
       (SELECT CASE WHEN k.tila = 'luonnos' THEN 'luonnos'
                    WHEN k.kaytettavissa OR now() < k.voimassa_alkupvm THEN 'julkaistu'
                    ELSE 'suljettu' END) AS sijainti
FROM kysely k JOIN organisaatio kt ON k.koulutustoimija = kt.oid
WHERE k.koulutustoimija = :koulutustoimija
--~(if (:oppilaitokset params) "AND k.oppilaitos IN (:v*:oppilaitokset)")
ORDER BY k.kyselyid;

-- :name hae-kyselykerran-kysely :? :1
SELECT k.* FROM kyselykerta kk
JOIN kysely k on kk.kyselyid = k.kyselyid
WHERE kk.kyselykertaid = :kyselykertaid;

-- :name aseta-kyselyn-tila! :! :n
UPDATE kysely SET tila = :tila,
                  muutettu_kayttaja = :muutettu_kayttaja
WHERE kyselyid = :kyselyid;

-- :name luo-kysely! :<!
INSERT INTO kysely (koulutustoimija, oppilaitos, voimassa_alkupvm, voimassa_loppupvm, nimi_fi, nimi_sv, nimi_en, selite_fi, selite_sv, selite_en, kyselypohjaid, tyyppi, tila,
                    metatiedot, uudelleenohjaus_url, luotu_kayttaja, muutettu_kayttaja, muutettuaika, luotuaika)
VALUES (:koulutustoimija, :oppilaitos, :voimassa_alkupvm, :voimassa_loppupvm, :nimi_fi, :nimi_sv, :nimi_en, :selite_fi, :selite_sv, :selite_en, :kyselypohjaid, :tyyppi, :tila,
        :metatiedot, :uudelleenohjaus_url, :kayttaja, :kayttaja, now(), now())
RETURNING kyselyid;

-- :name muokkaa-kyselya! :<!
UPDATE kysely SET
      nimi_fi = :nimi_fi, nimi_sv = :nimi_sv, nimi_en = :nimi_en, selite_fi = :selite_fi, selite_sv = :selite_sv, selite_en = :selite_en,
      voimassa_alkupvm = :voimassa_alkupvm, voimassa_loppupvm = :voimassa_loppupvm,
      tila = :tila, uudelleenohjaus_url = :uudelleenohjaus_url, sivutettu = :sivutettu, tyyppi = :tyyppi, metatiedot = metatiedot || :metatiedot
WHERE kyselyid = :kyselyid
RETURNING kyselyid;

-- :name lisaa-kyselyn-kysymysryhma! :! :n
INSERT INTO kysely_kysymysryhma (kyselyid, kysymysryhmaid, jarjestys, luotu_kayttaja, muutettu_kayttaja)
VALUES (:kyselyid, :kysymysryhmaid, :jarjestys, :kayttaja, :kayttaja);


-- :name poista-kyselyn-kysymysryhmat! :! :n
DELETE FROM kysely_kysymysryhma WHERE kyselyid = :kyselyid;

-- :name liita-kyselyn-kyselypohja! :! :n
INSERT INTO kysely_kysymysryhma (kyselyid, kysymysryhmaid, jarjestys, luotu_kayttaja, muutettu_kayttaja)
SELECT :kyselyid, kysymysryhmaid, jarjestys, :kayttaja, :kayttaja FROM kysymysryhma_kyselypohja WHERE kyselypohjaid = :kyselypohjaid;

-- :name liita-kyselyn-kysymykset! :! :n
INSERT INTO kysely_kysymys (kyselyid, kysymysid, luotu_kayttaja, muutettu_kayttaja)
SELECT :kyselyid, kysymysid, :kayttaja, :kayttaja FROM kysymys
WHERE kysymysryhmaid IN (SELECT kysymysryhmaid FROM kysely_kysymysryhma WHERE kyselyid = :kyselyid);

-- :name hae-automaattikysely-data :? :*
SELECT * FROM automaattikysely WHERE tunniste IN (SELECT MAX(tunniste) FROM automaattikysely GROUP BY LEFT(tunniste, -4));

-- :name hae-tiedonkeruu :? :1
SELECT * FROM automaattikysely WHERE tunniste = :tunniste;

-- :name muuta-kyselyn-tila! :! :n
UPDATE kysely SET tila = :tila, muutettu_kayttaja = :kayttaja WHERE kyselyid = :kyselyid;

-- :name kysely-poistettavissa? :? :1
SELECT 1 AS poistettavissa FROM kysely
WHERE NOT EXISTS (SELECT 1
            FROM (vastaaja JOIN vastaajatunnus ON vastaajatunnus.vastaajatunnusid = vastaaja.vastaajatunnusid)
                           JOIN kyselykerta ON kyselykerta.kyselykertaid = vastaajatunnus.kyselykertaid
            WHERE (kyselykerta.kyselyid = kysely.kyselyid))
  AND tila IN ('luonnos', 'suljettu') AND kyselyid = :kyselyid;

-- :name poista-kyselyn-kysymysryhmat! :! :n
DELETE FROM kysely_kysymysryhma WHERE kyselyid = :kyselyid ;

-- :name lisaa-kysymys-kyselyyn! :! :n
INSERT INTO kysely_kysymys (kyselyid, kysymysid, luotu_kayttaja, muutettu_kayttaja)
VALUES (:kyselyid, :kysymysid, :kayttaja, :kayttaja);

-- :name poista-kyselyn-kysymykset! :! :n
DELETE FROM kysely_kysymys WHERE kyselyid = :kyselyid;

-- :name poista-kysely! :! :n
DELETE FROM kysely WHERE kyselyid = :kyselyid;

-- :name hae-kyselyn-pakolliset-kysymysryhmat :? :*
SELECT kkr.kysymysryhmaid FROM kysely_kysymysryhma kkr
                                   JOIN kysymysryhma kr ON kkr.kysymysryhmaid = kr.kysymysryhmaid
WHERE kkr.kyselyid = :kyselyid AND (kr.taustakysymykset = TRUE
                                    OR (kr.valtakunnallinen = TRUE AND kr.metatiedot->>'lisattavissa_kyselyyn' IS NULL));

-- :name samanniminen-kysely? :? :1
SELECT EXISTS (SELECT FROM kysely
WHERE koulutustoimija = :koulutustoimija
AND (
    false
--~(if (not-empty (:nimet_fi params)) "OR nimi_fi IN (:v*:nimet_fi)")
--~(if (not-empty (:nimet_sv params)) "OR nimi_sv IN (:v*:nimet_sv)")
--~(if (not-empty (:nimet_en params)) "OR nimi_en IN (:v*:nimet_en)")
    ));

-- :name hae-kyselyn-taustakysymysryhmaid :? :1
SELECT kkr.kysymysryhmaid FROM kysely_kysymysryhma kkr
JOIN kysymysryhma k on kkr.kysymysryhmaid = k.kysymysryhmaid
WHERE k.valtakunnallinen = TRUE AND k.taustakysymykset = TRUE
AND kkr.kyselyid = :kyselyid;

-- :name hae-kyselyn-oppilaitokset :? :*
SELECT DISTINCT o.oppilaitoskoodi, o.nimi_fi, o.nimi_sv, o.nimi_en, o.oid
FROM kysely k
         JOIN kyselykerta kk ON kk.kyselyid = k.kyselyid
         JOIN vastaajatunnus vt on kk.kyselykertaid = vt.kyselykertaid
         JOIN organisaatio o on vt.valmistavan_koulutuksen_oppilaitos = o.oid
WHERE k.kyselyid = :kyselyid;

-- :name hae-kysely-tyyppi :? :1
SELECT tyyppi FROM kysely WHERE kyselyid = :kyselyid;

-- :name hae-raportointi-kysely :? :1
SELECT k.kyselyid, k.nimi_fi AS kysely_fi, k.nimi_sv AS kysely_sv, k.nimi_en AS kysely_en, k.voimassa_alkupvm, k.voimassa_loppupvm,
       kt.nimi_fi AS koulutustoimija_fi, kt.nimi_sv AS koulutustoimija_sv, kt.nimi_en AS koulutustoimija_en
FROM kysely k JOIN organisaatio kt ON k.koulutustoimija = kt.oid
WHERE k.kyselyid = :kyselyid;


-- :name hae-tiedonkeruu :? :1
SELECT * FROM automaattikysely WHERE tunniste = :tunniste;

-- :name hae-tiedonkeruun-tunnukset :? :*
SELECT vt.tunnus FROM vastaajatunnus vt
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
JOIN kysely k ON kk.kyselyid = k.kyselyid
WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
AND NOT EXISTS (SELECT 1 FROM vastaaja v WHERE v.vastaajatunnusid = vt.vastaajatunnusid);