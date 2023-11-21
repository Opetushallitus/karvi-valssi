-- :name lisaa-kysymysryhma! :<!
INSERT INTO kysymysryhma (taustakysymykset, valtakunnallinen, nimi_fi, nimi_sv, selite_fi, selite_sv, koulutustoimija, oppilaitos, luotu_kayttaja, muutettu_kayttaja, luotuaika, muutettuaika, tila, kuvaus_fi, kuvaus_sv, nimi_en, selite_en, kuvaus_en, metatiedot)
VALUES (:taustakysymykset, :valtakunnallinen, :nimi_fi, :nimi_sv, :selite_fi, :selite_sv, :koulutustoimija, :oppilaitos, :kayttaja, :kayttaja, now(), now(), :tila, :kuvaus_fi, :kuvaus_sv, :nimi_en, :selite_en, :kuvaus_en, :metatiedot)
RETURNING kysymysryhmaid;

-- :name paivita-kysymysryhma! :<! :1
UPDATE kysymysryhma SET taustakysymykset = :taustakysymykset,
                        valtakunnallinen = :valtakunnallinen,
                        nimi_fi = :nimi_fi, nimi_sv = :nimi_sv, nimi_en = :nimi_en,
                        selite_fi = :selite_fi, selite_sv = :selite_sv, selite_en = :selite_en,
                        kuvaus_fi = :kuvaus_fi, kuvaus_sv = :kuvaus_sv, kuvaus_en = :kuvaus_en,
                        muutettu_kayttaja = :kayttaja,
--~ (if (:metatiedot params) "metatiedot = :metatiedot," "metatiedot = metatiedot,")
                        muutettuaika = now()
WHERE kysymysryhmaid = :kysymysryhmaid
RETURNING *;

--:name poista-kysymysryhma! :! :n
DELETE FROM kysymysryhma WHERE kysymysryhmaid = :kysymysryhmaid;

-- :name hae-kysymysryhman-kysymykset :? :*
SELECT k.*, kr.nimi_fi AS kysymysryhma_fi, kr.nimi_sv AS kysymysryhma_sv, kr.nimi_en AS kysymysryhma_en,
       kr.taustakysymykset AS taustakysymys,
       k.metatiedot AS kysymys_metatiedot FROM kysymys k
  JOIN kysymysryhma kr ON k.kysymysryhmaid = kr.kysymysryhmaid
WHERE k.kysymysryhmaid = :kysymysryhmaid
--~ (when (:vain_rahoitusmallikysymykset params) "AND k.metatiedot->>'rahoitusmallikysymys' = TRUE")
ORDER BY k.jarjestys, k.matriisi_jarjestys;

-- :name hae-kysymysryhma :? :1
SELECT * FROM kysymysryhma WHERE kysymysryhmaid = :kysymysryhmaid;

-- :name hae-kyselypohjan-kysymysryhmat :? :*
SELECT * FROM kysymysryhma_kyselypohja WHERE kyselypohjaid = :kyselypohjaid;

-- :name hae-kysymysryhmatiedot-kyselypohjalla :? :*
SELECT kr.*, kk.jarjestys, kk.kyselypohjaid
FROM kysymysryhma kr JOIN kysymysryhma_kyselypohja kk ON kr.kysymysryhmaid = kk.kysymysryhmaid
WHERE kk.kyselypohjaid = :kyselypohjaid AND kr.tila IN ('julkaistu', 'luonnos')
ORDER BY kk.jarjestys;

-- :name hae-asteikot :? :*
SELECT * FROM asteikko WHERE koulutustoimija = :koulutustoimija;

-- :name tallenna-asteikko :! :n
INSERT INTO asteikko (koulutustoimija, nimi, asteikko) VALUES (:koulutustoimija, :nimi, :asteikko::json);

-- :name hae-kyselyn-kysymysryhmat :? :*
SELECT kkr.jarjestys, kr.* FROM kysely_kysymysryhma kkr
JOIN kysymysryhma kr ON kkr.kysymysryhmaid = kr.kysymysryhmaid
WHERE kyselyid = :kyselyid
--~(when (:valtakunnalliset params) "AND kr.valtakunnallinen = :valtakunnalliset")
ORDER BY kkr.jarjestys;

-- :name hae-monivalintavaihtoehdot :? :*
SELECT jarjestys, arvo, teksti_fi, teksti_sv, teksti_en FROM monivalintavaihtoehto
WHERE kysymysid = :kysymysid
ORDER BY jarjestys;

-- :name hae-kysymysryhmat :? :*
SELECT kr.kysymysryhmaid, kr.nimi_fi, kr.nimi_sv, kr.nimi_en, kr.selite_fi, kr.selite_sv, kr.selite_en, kr.valtakunnallinen,
       kr.taustakysymykset, kr.tila, kr.kuvaus_fi, kr.kuvaus_sv, kr.kuvaus_en, kr.metatiedot, kr.luotuaika, kr.muutettuaika,
       (SELECT COUNT(*) FROM kysymys where kysymys.kysymysryhmaid = kr.kysymysryhmaid) AS kysymyksien_lkm,
       (SELECT EXISTS(SELECT 1 FROM kysymysryhma_kyselypohja WHERE kysymysryhma_kyselypohja.kysymysryhmaid = kr.kysymysryhmaid)) AS lisatty_kyselypohjaan,
       (SELECT EXISTS(SELECT 1 FROM kysely_kysymysryhma WHERE kysely_kysymysryhma.kysymysryhmaid = kr.kysymysryhmaid)) AS lisatty_kyselyyn
FROM kysymysryhma kr
WHERE kr.koulutustoimija = :koulutustoimija
--~(if (:oppilaitokset params) "AND kr.oppilaitos IN (:v*:oppilaitokset)")
--~(if (:yllapitaja? params) "OR kr.valtakunnallinen = TRUE")
--~(if (:vain_voimassaolevat params) "AND kr.tila = 'julkaistu'")
--~(if (not (:yllapitaja? params)) "OR (kr.valtakunnallinen = TRUE AND kr.tila = 'julkaistu')")
ORDER BY kr.muutettuaika DESC;

-- :name hae-taustakysymysryhmat :? :*
SELECT kysymysryhmaid, nimi_fi, nimi_sv, nimi_en FROM kysymysryhma WHERE taustakysymykset is true AND valtakunnallinen is true ORDER BY muutettuaika DESC;

-- :name laske-kysymysryhman-kyselyt :? :1
SELECT count(*) FROM kysely_kysymysryhma WHERE kysymysryhmaid = :kysymysryhmaid;

-- :name aseta-kysymysryhman-tila! :! :n
UPDATE kysymysryhma SET tila = :tila, muutettu_kayttaja = :kayttaja WHERE kysymysryhmaid = :kysymysryhmaid;

-- :name hae-kysymysryhman-esikatselutiedot :? :*
SELECT kr.kysymysryhmaid, kr.nimi_fi, kr.nimi_sv, kr.nimi_en, kr.kuvaus_fi, kr.kuvaus_sv, kr.kuvaus_en, kr.tila, kr.valtakunnallinen, kr.taustakysymykset, kr.metatiedot,
       k.kysymysid, k.kysymys_fi, k.kysymys_sv, k.kysymys_en, k.poistettava, k.pakollinen, k.vastaustyyppi, k.monivalinta_max, k.eos_vastaus_sallittu, k.jatkokysymys, k.jarjestys, k.kysymysryhmaid, k.max_vastaus,
       kj.kysymysid AS jatkokysymys_kysymysid, kj.vastaus AS jatkokysymys_vastaus
FROM kysymysryhma kr
JOIN kysymys k ON k.kysymysryhmaid = kr.kysymysryhmaid
LEFT JOIN kysymys_jatkokysymys kj ON k.kysymysid = kj.jatkokysymysid
JOIN kysely_kysymysryhma kk ON k.kysymysryhmaid = kr.kysymysryhmaid
WHERE kr.kysymysryhmaid = :kysymysryhmaid
ORDER BY kk.jarjestys;

-- :name hae-kyselypohjan-kysymykset :? :*
SELECT k.*, kj.kysymysid AS jatkokysymys_kysymysid, kj.vastaus AS jatkokysymys_vastaus
FROM kysymys k
JOIN kysymysryhma_kyselypohja kkp ON kkp.kysymysryhmaid = k.kysymysryhmaid
LEFT JOIN kysymys_jatkokysymys kj ON k.kysymysid = kj.jatkokysymysid
WHERE kkp.kyselypohjaid = :kyselypohjaid
ORDER BY kkp.jarjestys, k.jarjestys;

-- :name hae-kyselyn-kysymykset :? :*
SELECT k.*, kj.kysymysid AS jatkokysymys_kysymysid, kj.vastaus AS jatkokysymys_vastaus, kk.kysymysid is null AS poistettu
FROM kysymys k
JOIN kysely_kysymysryhma kkr ON k.kysymysryhmaid = kkr.kysymysryhmaid
LEFT JOIN kysymys_jatkokysymys kj ON k.kysymysid = kj.jatkokysymysid
LEFT JOIN kysely_kysymys kk ON k.kysymysid = kk.kysymysid AND kk.kyselyid = :kyselyid
WHERE kkr.kyselyid = :kyselyid
ORDER BY k.kysymysryhmaid, k.jarjestys;
