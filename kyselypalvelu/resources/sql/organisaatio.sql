-- :name hae-organisaatio :? :1
SELECT * FROM organisaatio
--~(if (contains? params :ytunnus) "WHERE ytunnus = :ytunnus AND tyypit @> '{organisaatiotyyppi_01} 'AND ytunnus IS NOT NULL")
--~(if (contains? params :oid) "WHERE oid = :oid")
--~(if (contains? params :oppilaitoskoodi) "WHERE oppilaitoskoodi = :oppilaitoskoodi AND tyypit @> '{organisaatiotyyppi_02}' AND oppilaitoskoodi IS NOT NULL")
--~(if (contains? params :voimassa) "AND voimassa = :voimassa")
;

-- :name hae-organisaatiot :? :*
SELECT * FROM organisaatio WHERE oid IN (:v*:oidit);

-- :name hae-kaikki-ytunnukselliset :? :*
SELECT ytunnus, nimi_fi, nimi_sv, nimi_en, oid FROM organisaatio WHERE ytunnus IS NOT NULL ORDER BY ytunnus DESC;

-- :name hae-koulutustoimijan-oppilaitokset :? :*
SELECT o.oppilaitoskoodi, o.oid, kt.oid AS koulutustoimija, o.nimi_fi, o.nimi_sv, o.nimi_en, o.oppilaitostyyppi
FROM organisaatio o JOIN organisaatio kt ON kt.oid = o.parent_oid
WHERE kt.oid = :koulutustoimija AND kt.voimassa = TRUE
--~(if (:voimassa params) "AND o.voimassa = :voimassa")
--~(if (:oppilaitokset params) "AND o.oid IN (:v*:oppilaitokset)")
;

-- :name hae-oppilaitoksen-voimassaolevat-toimipisteet :? :*
SELECT t.*, o.oppilaitoskoodi AS oppilaitos
FROM organisaatio t JOIN organisaatio o ON o.oid = t.parent_oid JOIN organisaatio kt ON kt.oid = o.parent_oid
WHERE o.oid = :oid AND t.voimassa = :voimassa
--~(if (:koulutustoimija params) "AND kt.oid = :koulutustoimija")
--~(if (:oppilaitokset params) "AND o.oid IN (:v*:oppilaitokset)")
;

-- :name hae-kaikki-organisaatio-oidit :? :*
SELECT oid FROM organisaatio;

-- :name luo-uusi-organisaatio! :<!
INSERT INTO organisaatio (oid, ytunnus, nimi_fi, nimi_sv, nimi_en, sahkoposti, puhelin, osoite, postinumero, postitoimipaikka, www_osoite, luotuaika, muutettuaika, voimassa, lakkautuspaiva, tyypit, oppilaitoskoodi, parent_oid, oppilaitostyyppi, toimipistekoodi, kunta, metatiedot)
VALUES (:oid, :ytunnus, :nimi_fi, :nimi_sv, :nimi_en, :sahkoposti, :puhelin, :osoite, :postinumero, :postitoimipaikka, :www_osoite, NOW(), NOW(), :voimassa, :lakkautuspaiva, :tyypit, :oppilaitoskoodi, :parent_oid, :oppilaitostyyppi, :toimipistekoodi, :kunta, :metatiedot)
RETURNING oid;

-- :name paivita-organisaatio! :<!
UPDATE organisaatio
SET oid=:oid, ytunnus=:ytunnus, nimi_fi=:nimi_fi, nimi_sv=:nimi_sv, nimi_en=:nimi_en, sahkoposti=:sahkoposti, puhelin=:puhelin, osoite=:osoite, postinumero=:postinumero, postitoimipaikka=:postitoimipaikka, www_osoite=:www_osoite, luotuaika=NOW(), muutettuaika=NOW(), voimassa=:voimassa, lakkautuspaiva=:lakkautuspaiva, tyypit=:tyypit, oppilaitoskoodi=:oppilaitoskoodi, parent_oid=:parent_oid, oppilaitostyyppi=:oppilaitostyyppi, toimipistekoodi=:toimipistekoodi, kunta=:kunta, metatiedot=:metatiedot
WHERE oid = :oid
RETURNING oid;

-- :name paivita-voimassaolot! :! :n
UPDATE organisaatio SET voimassa = FALSE WHERE lakkautuspaiva < current_date;

-- :name aseta-kaikki-vanhentuneiksi! :! :n
UPDATE organisaatio SET voimassa = FALSE;

-- :name hae-viimeisin-paivitys :? :1
SELECT paivitetty FROM organisaatiopalvelu_log ORDER BY id DESC LIMIT 1;

-- :name tallenna-paivitys! :<!
INSERT INTO organisaatiopalvelu_log VALUES (DEFAULT, :paivitetty, NOW(), NOW()) RETURNING *;
