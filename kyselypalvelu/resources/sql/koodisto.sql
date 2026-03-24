-- :name oppilaitos :? :1
SELECT * FROM organisaatio
WHERE oppilaitoskoodi = :oppilaitoskoodi
AND tyypit @> '{organisaatiotyyppi_02}'
AND oppilaitoskoodi IS NOT NULL;

-- :name tutkinto :? :1
SELECT * FROM tutkinto WHERE tutkintotunnus = :tutkintotunnus;

-- :name hae-koodiston-koodit :? :*
SELECT * FROM koodi WHERE koodisto_uri = :koodistouri;

--:name hae-koodiston-koodi :? :1
SELECT * FROM koodi WHERE koodisto_uri = :koodistouri AND koodi_arvo = :koodi;

-- :name lisaa-koodiston-koodi! :! :n
INSERT INTO koodi (koodisto_uri, nimi_fi, nimi_sv, nimi_en, koodi_arvo, voimassa_alkupvm, voimassa_loppupvm)
    VALUES (:koodisto_uri, :nimi_fi, :nimi_sv, :nimi_en, :koodi_arvo, :voimassa_alkupvm, :voimassa_loppupvm);

-- :name paivita-koodiston-koodi! :! :n
UPDATE koodi SET nimi_fi = :nimi_fi, nimi_sv = :nimi_sv, nimi_en = :nimi_en, voimassa_alkupvm = :voimassa_alkupvm, voimassa_loppupvm = :voimassa_loppupvm
    WHERE koodisto_uri = :koodisto_uri AND koodi_arvo = :koodi_arvo;

-- :name hae-kyselyn-koodistot :? :*
SELECT koodi.* FROM kysely_kysymysryhma kkr
JOIN kysymysryhma kr ON kkr.kysymysryhmaid = kr.kysymysryhmaid
JOIN kysymys kys ON kr.kysymysryhmaid = kys.kysymysryhmaid
JOIN koodi ON koodi.koodisto_uri = kys.metatiedot->>'koodisto'
WHERE kkr.kyselyid = :kyselyid;