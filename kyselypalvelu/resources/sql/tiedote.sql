-- :name lisaa-tiedote! :! :n
INSERT INTO tiedote(otsikko_fi, otsikko_sv, otsikko_en, teksti_fi, teksti_sv, teksti_en, voimassa_alkupvm, voimassa_loppupvm)
VALUES (:otsikko_fi, :otsikko_sv, :otsikko_en, :teksti_fi, :teksti_sv, :teksti_en, :voimassa_alkupvm::DATE, :voimassa_loppupvm::DATE);

--:name paivita-tiedote! :! :n
UPDATE tiedote SET otsikko_fi = :otsikko_fi, otsikko_sv = :otsikko_sv, otsikko_en = :otsikko_en,
                   teksti_fi = :teksti_fi, teksti_sv = :teksti_sv, teksti_en = :teksti_en,
                   voimassa_alkupvm = :voimassa_alkupvm::DATE, voimassa_loppupvm = :voimassa_loppupvm::DATE
WHERE tiedoteid = :tiedoteid;

-- :name poista-tiedote! :! :n
DELETE FROM tiedote WHERE tiedoteid = :tiedoteid;

-- :name hae-tiedote :? :1
SELECT * FROM tiedote LIMIT 1;

-- :name hae-tiedotteet :? :*
SELECT * FROM tiedote WHERE current_date BETWEEN  voimassa_alkupvm AND voimassa_loppupvm ORDER BY voimassa_alkupvm DESC;