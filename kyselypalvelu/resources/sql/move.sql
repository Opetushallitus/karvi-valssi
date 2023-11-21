-- :name hae-move-oppilaitokset-ilman-tunnusta :? :*
SELECT o.oid, o.nimi_fi, o.nimi_sv, o.sahkoposti
FROM organisaatio o
WHERE oppilaitostyyppi IN ('11','12','19')
  AND voimassa = TRUE
  AND postinumero NOT ILIKE '22%'
  AND NOT EXISTS(
      SELECT vastaajatunnusid FROM vastaajatunnus vt
      WHERE vt.kyselykertaid = :kyselykertaid
      AND vt.valmistavan_koulutuksen_oppilaitos = o.oid);

-- :name hae-move-kyselykerta :? :1
SELECT kk.kyselykertaid FROM kysely k
JOIN kyselykerta kk ON k.kyselyid = kk.kyselyid
WHERE k.tyyppi = 'move' AND k.metatiedot->>'automatisointi_tunniste' = :tunniste
AND kk.automaattinen @> NOW()::DATE;

-- :name lisaa-move-tunnus! :! :n
INSERT INTO vastaajatunnus (kyselykertaid, tunnus, kohteiden_lkm, valmistavan_koulutuksen_oppilaitos, luotu_kayttaja, muutettu_kayttaja, luotuaika, muutettuaika, voimassa_alkupvm)
VALUES (:kyselykertaid, :tunnus, null, :oid, 'JARJESTELMA', 'JARJESTELMA', now(), now(), now());

-- :name hae-move-tunnisteen-tunnukset :? :*
SELECT vt.tunnus, o.sahkoposti
FROM vastaajatunnus vt
    JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
    JOIN kysely k ON kk.kyselyid = k.kyselyid
    JOIN organisaatio o on vt.valmistavan_koulutuksen_oppilaitos = o.oid
WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste;

-- :name move-paivita-lahetyskerta-tunniste :! :n
UPDATE vastaajatunnus vt
SET metatiedot = jsonb_set(
    coalesce(vt.metatiedot, '{}'),
    '{lahetyskerta_tunnisteet}',
    coalesce(vt.metatiedot->'lahetyskerta_tunnisteet', '[]') || jsonb_build_array(:lahetyskertatunniste)
    )
WHERE tunnus IN (:v*:tunnukset);

-- :name hae-lahetyskerta-max-uusintalahetyskerta :? :1
SELECT coalesce(max(uusintalahetyskerta), 0) AS uusintalahetyskerta FROM lahetyskerta lk WHERE lk.kysely_tunniste = :tunniste;

-- :name lisaa-lahetyskerta :! :n
INSERT INTO lahetyskerta VALUES (default, :kysely_tunniste, :teksti_tyyppi, :lahetystyyppi, :kyselytyyppi, :lahettaja, now(), :tila, :uusintalahetyskerta);
