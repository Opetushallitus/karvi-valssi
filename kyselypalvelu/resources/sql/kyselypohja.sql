-- :name hae-kyselypohjat :? :*
SELECT kp.kyselypohjaid, kp.nimi_fi, kp.nimi_sv, kp.nimi_en, kp.valtakunnallinen, kp.tila, kp.kaytettavissa AS voimassa
FROM kyselypohja kp
WHERE kp.koulutustoimija = :koulutustoimija
--~(if (:oppilaitokset params) "AND kp.oppilaitos IN (:v*:oppilaitokset)")
--~(if (:valtakunnallinen params) "OR kp.valtakunnallinen = :valtakunnallinen")
--~(if (:voimassa params) "AND (kp.voimassa_alkupvm IS NULL OR kp.voimassa_alkupvm < now()) AND (kp.voimassa_loppupvm > now() OR kp.voimassa_loppupvm IS NULL)")
AND kp.tila = 'julkaistu' ORDER BY muutettuaika;

-- :name hae-kyselypohja :? :1
SELECT * FROM kyselypohja WHERE kyselypohjaid = :kyselypohjaid;

-- :name poista-kyselypohjan-kysymysryhmat! :! :n
DELETE FROM kysymysryhma_kyselypohja WHERE kyselypohjaid = :kyselypohjaid;

-- :name tallenna-kyselypohjan-kysymysryhma! :! :n
INSERT INTO kysymysryhma_kyselypohja (kysymysryhmaid, kyselypohjaid, jarjestys, luotu_kayttaja, muutettu_kayttaja)
    VALUES (:kysymysryhmaid,:kyselypohjaid, :jarjestys, :kayttaja, :kayttaja);

-- :name tallenna-kyselypohja! :! :n
UPDATE kyselypohja SET valtakunnallinen = :valtakunnallinen, voimassa_alkupvm = :voimassa_alkupvm, voimassa_loppupvm = :voimassa_loppupvm,
  nimi_fi = :nimi_fi, nimi_sv = :nimi_sv, nimi_en = :nimi_en, selite_fi = :selite_fi, selite_en = :selite_en, muutettu_kayttaja = :kayttaja
WHERE kyselypohjaid = :kyselypohjaid;

-- :name luo-kyselypohja! :<!
INSERT INTO kyselypohja (valtakunnallinen, voimassa_alkupvm, voimassa_loppupvm, nimi_fi, nimi_sv, nimi_en,
selite_fi, selite_sv, selite_en, koulutustoimija, oppilaitos, luotu_kayttaja, muutettu_kayttaja)
VALUES (:valtakunnallinen, :voimassa_alkupvm, :voimassa_loppupvm, :nimi_fi, :nimi_sv, :nimi_en,
:selite_fi, :selite_sv, :selite_en, :koulutustoimija, :oppilaitos, :kayttaja, :kayttaja)
RETURNING kyselypohjaid;

-- :name aseta-kyselypohjan-tila! :! :n
UPDATE kyselypohja SET tila = :tila, muutettu_kayttaja = :kayttaja WHERE kyselypohjaid = :kyselypohjaid;

-- :name poista-kyselypohja! :! :n
DELETE FROM kyselypohja WHERE kyselypohjaid = :kyselypohjaid;

-- :name kyselypohjan-kysymysryhmia-julkaisematta? :? :1
SELECT COUNT(*) FROM kysymysryhma_kyselypohja kk JOIN kysymysryhma kr ON kr.kysymysryhmaid = kk.kysymysryhmaid WHERE kk.kyselypohjaid = :kyselypohjaid AND kr.tila != 'julkaistu';

-- :name laske-kyselypohjan-kysymysryhmat :? :1
SELECT count(*) FROM kysymysryhma_kyselypohja WHERE kysymysryhmaid = :kysymysryhmaid;
