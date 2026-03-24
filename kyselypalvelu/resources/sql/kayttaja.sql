--:name hae-voimassaoleva-kayttaja :? :1
SELECT * FROM kayttaja
WHERE uid ILIKE :uid
      AND voimassa = TRUE
      AND (muutettuaika + :voimassaolo::interval >= now()
           OR uid IN ('JARJESTELMA', 'KONVERSIO', 'INTEGRAATIO', 'VASTAAJA'));

--:name passivoi-kayttaja! :! :n
UPDATE kayttaja SET voimassa = FALSE WHERE uid = :uid;

--:name hae-kayttaja :? :1
SELECT * FROM kayttaja WHERE oid = :kayttajaOid;

--:name paivita-kayttaja! :! :n
UPDATE kayttaja SET etunimi = :etunimi, sukunimi = :sukunimi, voimassa = TRUE
WHERE oid = :kayttajaOid;

--:name lisaa-kayttaja! :! :n
INSERT INTO kayttaja (oid, uid, etunimi, sukunimi, voimassa)
    VALUES (:kayttajaOid, :uid, :etunimi, :sukunimi, TRUE );

--:name hae-roolit :? :*
SELECT organisaatio, kayttooikeus FROM rooli_organisaatio WHERE kayttaja = :kayttaja;

--:name aseta-roolin-tila! :! :n
UPDATE rooli_organisaatio SET voimassa = :voimassa
WHERE kayttaja = :kayttaja AND kayttooikeus = :kayttooikeus AND organisaatio = :organisaatio;

--:name lisaa-rooli! :! :n
INSERT INTO rooli_organisaatio (kayttaja, kayttooikeus, organisaatio, voimassa) VALUES (:kayttaja, :kayttooikeus, :organisaatio, TRUE);

-- :name hae-voimassaolevat-roolit :? :*
SELECT ro.kayttooikeus,
       o.oid,
       o.parent_oid,
       ro.rooli_organisaatio_id,
       o.nimi_fi AS organisaatio_nimi_fi,
       o.nimi_sv AS organisaatio_nimi_sv,
       o.nimi_en AS organisaatio_nimi_en,
       p.nimi_fi AS parent_nimi_fi,
       p.nimi_sv AS parent_nimi_sv,
       p.nimi_en AS parent_nimi_en
FROM rooli_organisaatio ro
JOIN organisaatio o ON ro.organisaatio = o.oid
LEFT JOIN organisaatio p ON o.parent_oid = p.oid
WHERE ro.kayttaja = :kayttajaOid
AND ro.voimassa = TRUE;

-- :name hae-impersonoitavat-kayttajat :? :*
SELECT oid, uid, etunimi, sukunimi
FROM kayttaja
WHERE NOT EXISTS (SELECT rooli_organisaatio_id FROM rooli_organisaatio ro WHERE ro.kayttaja = oid AND ro.kayttooikeus = 'YLLAPITAJA' AND ro.voimassa = TRUE)
AND oid NOT IN ('JARJESTELMA', 'KONVERSIO', 'INTEGRAATIO', 'VASTAAJA', 'DATANTUONTI')
AND voimassa = TRUE;

-- :name hae-laajennettu :? :1
SELECT EXISTS(SELECT * FROM koulutustoimija_ja_tutkinto WHERE koulutustoimija IN (:v*:koulutustoimijat) AND laaja_oppisopimuskoulutus = TRUE) AS laajennettu;
