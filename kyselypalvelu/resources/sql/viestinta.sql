-- :name hae-lahetyskerta :? :1
SELECT * FROM lahetyskerta lk
WHERE lk.tila IS DISTINCT FROM 'lahetetty'
AND lk.lahetysaika < now()
--~ (if (:tunniste params) "AND lk.kysely_tunniste = :tunniste")
ORDER BY lahetysaika LIMIT 1;

-- :name hae-lahetyskerta-by-id :? :1
SELECT * FROM lahetyskerta lk
WHERE lk.tila IS DISTINCT FROM 'lahetetty'
--~ (if (:id params) "AND lk.id = :id")
LIMIT 1;

-- :name hae-uraseuranta-vastaanottajat :? :*
SELECT vt.vastaajatunnusid, vt.tunnus, ar.sahkoposti, ar.puhelinnumero, ar.asiointikieli,
       k.metatiedot->>'lahettaja_fi' AS lahettaja_fi, k.metatiedot->>'lahettaja_sv' AS lahettaja_sv,
       k.metatiedot->>'lahettaja_en' AS lahettaja_en
FROM vastaajatunnus vt
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
JOIN kysely k ON kk.kyselyid = k.kyselyid
JOIN yhteystiedot.alumnirekisteri ar ON ar.vastaajatunnusid = vt.vastaajatunnusid
WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
AND (ar.sahkoposti IS NOT NULL OR ar.puhelinnumero IS NOT NULL)
--~(when (= (:kohdejoukko params) "vastaajat") "AND NOT EXISTS (SELECT 1 FROM vastaaja vs WHERE vs.vastaajatunnusid = vt.vastaajatunnusid)")
--~(when (= (:kohdejoukko params) "vastanneet") "AND EXISTS (SELECT 1 FROM vastaaja vs WHERE vs.vastaajatunnusid = vt.vastaajatunnusid)")
AND NOT EXISTS (SELECT 1 FROM viestiloki l WHERE l.lahetyskerta_id = :lahetyskertaid AND l.vastaajatunnusid = vt.vastaajatunnusid);

-- :name hae-move-vastaanottajat :? :*
SELECT vt.vastaajatunnusid, vt.tunnus, o.sahkoposti, o.oppilaitoskoodi, o.nimi_fi AS oppilaitos_fi, o.nimi_sv AS oppilaitos_sv
FROM vastaajatunnus vt
JOIN organisaatio o ON vt.valmistavan_koulutuksen_oppilaitos = o.oid
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
JOIN kysely k ON kk.kyselyid = k.kyselyid
WHERE o.oppilaitostyyppi IN ('11','12','19')
  AND o.voimassa = TRUE
  AND o.sahkoposti IS NOT NULL
  AND o.postinumero NOT ILIKE '22%'
  AND k.metatiedot->>'automatisointi_tunniste' = :tunniste
  AND kk.automaattinen @> NOW()::DATE
  AND NOT EXISTS (SELECT 1 FROM vastaaja vs WHERE vs.vastaajatunnusid = vt.vastaajatunnusid)
  AND NOT EXISTS (SELECT 1 FROM viestiloki l WHERE l.lahetyskerta_id = :lahetyskertaid AND l.vastaajatunnusid = vt.vastaajatunnusid)
ORDER BY o.nimi_fi;

-- :name hae-move-uusintalahetys-vastaanottajat :? :*
SELECT vt.vastaajatunnusid, vt.tunnus, o.sahkoposti, o.oppilaitoskoodi, o.nimi_fi AS oppilaitos_fi, o.nimi_sv AS oppilaitos_sv
FROM vastaajatunnus vt JOIN organisaatio o ON vt.valmistavan_koulutuksen_oppilaitos = o.oid
WHERE vt.metatiedot->'lahetyskerta_tunnisteet' @> jsonb_build_array(:lahetyskertatunniste)
  AND NOT EXISTS (SELECT 1 FROM viestiloki l WHERE l.lahetyskerta_id = :lahetyskertaid AND l.vastaajatunnusid = vt.vastaajatunnusid)
ORDER BY o.nimi_fi;

-- :name hae-viesti :? :*
SELECT * FROM kysely_tekstit
WHERE tunniste = :tunniste AND tyyppi = :tyyppi;

-- :name lisaa-lahetystieto! :! :n
INSERT INTO viestiloki(lahetyskerta_id, vastaajatunnusid, status) VALUES (:lahetyskertaid, :vastaajatunnusid, :status);

-- :name paivita-lahetyskerta! :! :n
UPDATE lahetyskerta SET tila = :tila WHERE id = :id;
