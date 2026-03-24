-- :name hae-ohje :? :1
SELECT * FROM ohje WHERE ohjetunniste = :ohjetunniste;

-- :name luo-uusi-ohje! :<!
INSERT INTO ohje VALUES (:ohjetunniste, :teksti_fi, :teksti_sv, NOW(), NOW(), :teksti_en)
RETURNING ohjetunniste;

-- :name paivita-ohje! :<!
UPDATE ohje SET teksti_fi = :teksti_fi, teksti_sv = :teksti_sv, muutettuaika = NOW(), teksti_en = :teksti_en WHERE ohjetunniste = :ohjetunniste
RETURNING ohjetunniste;
