-- :name hae-vastaajat :? :*
SELECT DISTINCT vt.tunnus FROM vastaajatunnus vt JOIN vastaaja v ON vt.vastaajatunnusid = v.vastaajatunnusid WHERE vt.kyselykertaid = :kyselykertaid;

-- :name hae-uraseuranta-kyselykerrat :? :*
SELECT kk.kyselykertaid, o.oid, o.oppilaitoskoodi, kk.metatiedot->>'uraseuranta_tyyppi' AS tyyppi FROM kyselykerta kk
JOIN kysely k on k.kyselyid = kk.kyselyid
JOIN organisaatio kt on k.koulutustoimija = kt.oid
JOIN organisaatio o ON kt.oid = o.parent_oid AND o.voimassa = TRUE AND o.oppilaitostyyppi =
CASE k.tyyppi WHEN 'amk-uraseuranta' THEN '41' WHEN 'yo-uraseuranta' THEN '42' END
WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste;

-- :name vastaajatunnusten-lkm :? :1
SELECT count(1) AS tunnuksia FROM vastaajatunnus;

-- :name lisaa-uraseuranta-yhteystieto! :<!
INSERT INTO yhteystiedot.alumnirekisteri (vastaajatunnusid, opiskelijatunnus) VALUES (:vastaajatunnusid, :opiskelijatunnus)
RETURNING id;

-- :name hae-yhteystiedot :? :*
SELECT ar.id, ar.opiskelijatunnus, ar.sahkoposti, ar.puhelinnumero, ar.asiointikieli FROM yhteystiedot.alumnirekisteri ar
JOIN vastaajatunnus vt ON vt.vastaajatunnusid = ar.vastaajatunnusid
JOIN kyselykerta k on k.kyselykertaid = vt.kyselykertaid
WHERE k.kyselykertaid = :kyselykertaid
ORDER BY ar.id;

-- :name paivita-yhteystieto! :! :n
UPDATE yhteystiedot.alumnirekisteri ar
SET sahkoposti = :sahkoposti, puhelinnumero = :puhelinnumero, asiointikieli = :asiointikieli
WHERE id = :id
AND EXISTS (SELECT 1 FROM vastaajatunnus vt WHERE vt.vastaajatunnusid = ar.vastaajatunnusid AND vt.kyselykertaid = :kyselykertaid);


--:name lisaa-yo-osoitetieto! :! :n
INSERT INTO yhteystiedot.osoitetiedot(tiedonkeruu, tunniste, sukunimi, etunimet, lahiosoite, postinumero, postitoimipaikka, kotim_osoitt_muuttopaiva, aidinkieli, kuolinpaiva,
                                     vakinainen_ulkomainen_osoite, ulkomaisen_osoitteen_paikkakunta,ulkomaisen_asuinvaltion_postinimi, asuinvaltio, ulkomaille_muuton_pv, ulkom_asuinvaltion_nimi, kotikunta, kotikunnan_nimi, sukupuoli)
VALUES (:tiedonkeruu, :tunniste, :sukunimi, :etunimet, :lahiosoite, :postinumero, :postitoimipaikka, :kotim_osoitt_muuttopaiva, :aidinkieli, :kuolinpaiva,
        :vakinainen_ulkomainen_osoite, :ulkomaisen_osoitteen_paikkakunta, :ulkomaisen_asuinvaltion_postinimi, :asuinvaltio, :ulkomaille_muuton_pv, :ulkom_asuinvaltion_nimi, :kotikunta, :kotikunnan_nimi, :sukupuoli);

-- :name lisaa-yo-puhelinnumero! :! :n
INSERT INTO yhteystiedot.puhelinnumerot(tiedonkeruu, tunniste, puhelinnumero, yritysliittyma)
VALUES (:tiedonkeruu, :tunniste, :gsmnumero, :gsmyritys);

-- :name lisaa-yo-uraseuranta-tunniste! :<!
INSERT INTO yhteystiedot.yo_uraseuranta_tunnukset(vastaajatunnusid, tunniste, opiskelijatunnus, tiedonkeruu)
VALUES (:vastaajatunnusid, :tunniste, :opiskelijatunnus, :tiedonkeruu)
RETURNING vastaajatunnusid;

-- :name hae-tupa-lista :? :*
SELECT vt.tunnus, o.nimi_fi AS oppilaitos_nimi, vt.taustatiedot, yt.opiskelijatunnus, ot.*,
       pn.puhelinnumero AS matkapuhelin, pn.yritysliittyma,
       vt.taustatiedot->>'tutkinto' AS tutkinto_koulutuskoodi, t.nimi_fi AS tutkinto_nimi, ka.nimi_fi AS koulutusala,
       ot.sukunimi, ot.etunimet, ot.lahiosoite, ot.postinumero, ot.postitoimipaikka, ot.kotim_osoitt_muuttopaiva,
       ot.aidinkieli AS dvv_aidinkieli, ot.sukupuoli AS dvv_sukupuoli, ot.vakinainen_ulkomainen_osoite, ot.ulkomaisen_osoitteen_paikkakunta,
       ot.ulkomaisen_asuinvaltion_postinimi, ot.asuinvaltio, ot.ulkom_asuinvaltion_nimi, ot.ulkomaille_muuton_pv, ot.kotikunta, ot.kotikunnan_nimi
FROM vastaajatunnus vt
 JOIN yhteystiedot.yo_uraseuranta_tunnukset yt ON vt.vastaajatunnusid = yt.vastaajatunnusid
 JOIN yhteystiedot.osoitetiedot ot ON lower(yt.tunniste) = lower(ot.tunniste)
 JOIN yhteystiedot.puhelinnumerot pn ON lower(yt.tunniste) = lower(pn.tunniste)
 JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
 JOIN kysely k on kk.kyselyid = k.kyselyid
 LEFT JOIN organisaatio o ON o.oppilaitoskoodi = vt.taustatiedot->>'oppilaitoskoodi'
 LEFT JOIN tutkinto t ON vt.taustatiedot->>'tutkinto' = t.tutkintotunnus
 LEFT JOIN opintoala oa ON t.opintoala = oa.opintoalatunnus
 LEFT JOIN koulutusala ka ON oa.koulutusala = ka.koulutusalatunnus
WHERE k.metatiedot->>'automatisointi_tunniste' = :tunniste
AND ot.kuolinpaiva IS NULL
ORDER BY oppilaitos_nimi, tutkinto_nimi;
