-- :name vaihda-kysymysten-jarjestys! :! :n
UPDATE kysymys SET jarjestys =
                         CASE
                             WHEN (matriisi_kysymysid = :kysymysid1 OR (matriisi_kysymysid IS NULL AND kysymysid = :kysymysid1))
                                 THEN (SELECT jarjestys FROM kysymys WHERE kysymysid = :kysymysid2)
                             WHEN (matriisi_kysymysid = :kysymysid2 OR (matriisi_kysymysid IS NULL AND kysymysid = :kysymysid2))
                                 THEN (SELECT jarjestys FROM kysymys WHERE kysymysid = :kysymysid1)
                             ELSE jarjestys
                             END,
                   matriisi_jarjestys =
                       CASE
                           WHEN (kysymysid = :kysymysid1 AND matriisi_jarjestys > 0)
                               THEN (SELECT matriisi_jarjestys FROM kysymys WHERE kysymysid = :kysymysid2)
                           WHEN (kysymysid = :kysymysid2 AND matriisi_jarjestys > 0)
                               THEN (SELECT matriisi_jarjestys FROM kysymys WHERE kysymysid = :kysymysid1)
                           ELSE matriisi_jarjestys
                           END
WHERE kysymysid IN (SELECT DISTINCT kysymysid FROM kysymys WHERE matriisi_kysymysid IN (:kysymysid1, :kysymysid2) OR kysymysid IN (:kysymysid1, :kysymysid2));

-- :name paivita-matriisi-kysymysid! :! :n
UPDATE kysymys SET matriisi_kysymysid = :matriisi_kysymysid WHERE kysymysid = :kysymysid;

-- :name kysymysryhman-kysymykset-olemassa-count :? :1
SELECT COUNT(*) FROM kysymys WHERE kysymysid IN (:kysymysid1, :kysymysid2) AND kysymysryhmaid = :kysymysryhmaid;

-- :name kysymyksen-matriisi-jarjestys :? :*
SELECT matriisi_jarjestys, matriisi_kysymysid FROM kysymys WHERE kysymysid IN (:v*:kysymysidt);

-- :name poista-kysymykset! :! :n
DELETE FROM kysymys WHERE kysymysid IN (:v*:kysymysidt);

-- :name hae-kysymyksen-jatkokysymykset :? :*
SELECT jatkokysymysid FROM kysymys_jatkokysymys WHERE kysymysid = :kysymysid;

-- :name hae-kysymyksen-matriisikysymykset :? :*
SELECT kysymysid FROM kysymys WHERE matriisi_kysymysid = :kysymysid;

-- :name poista-monivalintavaihtoehdot! :! :n
DELETE FROM monivalintavaihtoehto WHERE kysymysid IN (:v*:kysymysidt);

-- :name poista-jatkokysymysliitokset! :! :n
DELETE FROM kysymys_jatkokysymys WHERE kysymysid IN (:v*:kysymysidt) or jatkokysymysid IN (:v*:kysymysidt);

-- :name paivita-kysymys! :! :n
UPDATE kysymys SET kysymys_fi = :kysymys_fi, kysymys_sv = :kysymys_sv, kysymys_en = :kysymys_en,
                   selite_fi = :selite_fi::TEXT, selite_sv = :selite_sv, selite_en = :selite_en,
                   eos_vastaus_sallittu = :eos_vastaus_sallittu, pakollinen = :pakollinen, poistettava = :poistettava,
                   muutettu_kayttaja = :kayttaja, metatiedot = :metatiedot
WHERE kysymysid = :kysymysid;

-- :name hae-kysymys :? :1
SELECT * FROM kysymys WHERE kysymysid = :kysymysid;

-- :name lisaa-kysymys! :<!
INSERT INTO kysymys (pakollinen, poistettava, vastaustyyppi, kysymysryhmaid, kysymys_fi, kysymys_sv, kysymys_en,
                     selite_fi, selite_sv, selite_en, rajoite,
                     jarjestys, monivalinta_max, max_vastaus, eos_vastaus_sallittu, luotu_kayttaja, muutettu_kayttaja, metatiedot,
                     luotuaika, muutettuaika, jatkokysymys, matriisi_jarjestys, matriisi_kysymysid)
VALUES (:pakollinen, :poistettava, :vastaustyyppi, :kysymysryhmaid, :kysymys_fi, :kysymys_sv, :kysymys_en,
        :selite_fi, :selite_sv, :selite_en, :rajoite,
        :jarjestys, :monivalinta_max, :max_vastaus, :eos_vastaus_sallittu, :kayttaja, :kayttaja, :metatiedot,
        now(), now(), :jatkokysymys, :matriisi_jarjestys, :matriisi_kysymysid)
RETURNING kysymysid;

-- :name liita-jatkokysymys! :! :n
INSERT INTO kysymys_jatkokysymys(kysymysid, jatkokysymysid, vastaus) VALUES (:kysymysid, :jatkokysymysid, :vastaus);

-- :name hae-monivalintavaihtoehto :? :*
SELECT jarjestys, teksti_fi, teksti_sv, teksti_en FROM monivalintavaihtoehto WHERE kysymysid = :kysymysid;

-- :name lisaa-monivalintavaihtoehto! :! :n
INSERT INTO monivalintavaihtoehto (kysymysid, jarjestys, arvo,  teksti_fi, teksti_sv, teksti_en, luotu_kayttaja, muutettu_kayttaja, luotuaika, muutettuaika)
VALUES (:kysymysid, :jarjestys, :jarjestys, :teksti_fi, :teksti_sv, :teksti_en, :kayttaja, :kayttaja, NOW(), NOW());

-- :name paivita-monivalintavaihtoehto! :! :n
UPDATE monivalintavaihtoehto SET jarjestys = :jarjestys, teksti_fi = :teksti_fi, teksti_sv = :teksti_sv, teksti_en = :teksti_en,
                                 muutettu_kayttaja = :kayttaja, muutettuaika = now()
WHERE monivalintavaihtoehtoid = :monivalintavaihtoehtoid;

-- :name hae-kysymysryhman-viimeinen-jarjestys :? :1
SELECT MAX(jarjestys) FROM kysymys WHERE kysymysryhmaid = :kysymysryhmaid;

-- :name hae-matriisin-viimeinen-jarjestys :? :1
SELECT MAX(matriisi_jarjestys) FROM kysymys WHERE matriisi_kysymysid = :kysymysid;

-- :name hae-kysymysryhman-kysymyksien-idt :? :*
SELECT kysymysid FROM kysymys WHERE kysymysryhmaid = :kysymysryhmaid;

-- :name laske-kysymysryhman-kysymykset :? :1
SELECT count(*) FROM kysymys WHERE kysymysryhmaid = :kysymysryhmaid;

