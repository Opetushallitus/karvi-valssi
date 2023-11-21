-- :name export-kyselyt :? :*
SELECT kt.ytunnus AS koulutustoimija, k.tyyppi,
  k.kyselyid, k.nimi_fi AS kysely_fi, k.nimi_sv AS kysely_sv, k.nimi_en AS kysely_en,
  to_char(k.voimassa_alkupvm, 'YYYY-MM-DD') AS kysely_voimassa_alkupvm, to_char(k.voimassa_loppupvm, 'YYYY-MM-DD')AS kysely_voimassa_loppupvm, k.tila AS kysely_tila,
  kk.kyselykertaid, kk.nimi AS kyselykerta, kk.metatiedot->>'vuosi' AS kyselykerta_vuosi,
  kp.kyselypohjaid, kp.nimi_fi AS kyselypohja_nimi, kp.metatiedot->>'tarkenne' AS kyselypohja_tarkenne
FROM kyselykerta kk
JOIN kysely k ON kk.kyselyid = k.kyselyid
JOIN organisaatio kt ON k.koulutustoimija = kt.oid
LEFT JOIN kyselypohja kp ON k.kyselypohjaid = kp.kyselypohjaid
WHERE coalesce((kk.metatiedot->>'ei_raportoida')::BOOLEAN, FALSE ) = FALSE
AND (kt.oid = :koulutustoimija
     --~(if (:vipunen params) "OR TRUE")
    )
AND k.tyyppi IN (:v*:kyselytyypit);

-- :name export-vastaukset :? :*
SELECT kt.ytunnus AS koulutustoimija,
       k.kyselyid,
       kk.kyselykertaid,
       v.vastaajaid,
       vt.vastaajatunnusid,
       v.vastausid,
       v.kysymysid,
       to_char(vs.luotuaika, 'YYYY-MM-DD') AS vastausaika,
       coalesce(v.numerovalinta, v.luku) AS numerovalinta, v.vapaateksti,v.vaihtoehto,
       monivalintavaihtoehto.teksti_fi AS monivalintavaihtoehto_fi,
       monivalintavaihtoehto.teksti_sv AS monivalintavaihtoehto_sv,
       monivalintavaihtoehto.teksti_en AS monivalintavaihtoehto_en
FROM vastaus v
         JOIN vastaaja vs ON v.vastaajaid = vs.vastaajaid
         JOIN kysymys kys ON v.kysymysid = kys.kysymysid
         JOIN kysymysryhma kr ON kys.kysymysryhmaid = kr.kysymysryhmaid
         LEFT JOIN monivalintavaihtoehto ON kys.vastaustyyppi = 'monivalinta'
            AND monivalintavaihtoehto.kysymysid = kys.kysymysid
            AND v.numerovalinta::int = monivalintavaihtoehto.arvo
         JOIN vastaajatunnus vt ON vs.vastaajatunnusid = vt.vastaajatunnusid
         JOIN kyselykerta kk ON vs.kyselykertaid = kk.kyselykertaid
         JOIN kysely k ON kk.kyselyid = k.kyselyid
         JOIN organisaatio kt ON k.koulutustoimija = kt.oid
WHERE k.tila != 'luonnos'
  AND k.tyyppi IN (:v*:kyselytyypit)
  AND coalesce((kk.metatiedot->>'ei_raportoida')::BOOLEAN, FALSE ) = FALSE
  AND coalesce((k.metatiedot->'raportointi'->>'export')::BOOLEAN, TRUE) = TRUE
--~(if (:alkupvm params) "AND vs.luotuaika >= :alkupvm::date")
--~(if (:loppupvm params) "AND vs.luotuaika < (:loppupvm::date + 1)")
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
--~(if (:vipunen params) "AND kys.valtakunnallinen = TRUE" "AND kt.oid = :koulutustoimija")
--~(if (:vipunen params) "AND kys.vastaustyyppi != 'vapaateksti'")
--~(if (:since params) "AND v.vastausid > :since")
ORDER BY v.vastausid LIMIT :pagelength;


-- :name export-kysymykset :? :*
SELECT DISTINCT k.kysymysid, k.vastaustyyppi, k.kysymys_fi, k.kysymys_sv, k.kysymys_en, k.metatiedot AS kategoria, k.jatkokysymys,
  kjk.kysymysid AS jatkokysymys_kysymysid, k.jarjestys,
  kr.kysymysryhmaid, kr.nimi_fi AS kysymysryhma_fi, kr.nimi_sv AS kysymysryhma_sv, kr.nimi_en AS kysymysryhma_en,
  kr.valtakunnallinen
FROM kysymys k
LEFT JOIN kysymys_jatkokysymys kjk ON k.kysymysid = kjk.jatkokysymysid
JOIN kysymysryhma kr ON k.kysymysryhmaid = kr.kysymysryhmaid
JOIN kysely_kysymysryhma kkr ON kr.kysymysryhmaid = kkr.kysymysryhmaid
JOIN kysely kys ON kkr.kyselyid = kys.kyselyid
JOIN organisaatio kt ON kys.koulutustoimija = kt.oid
-- TODO: Vapaatekstien ja omien kysymysten rajaus pois tarvittaessa (vipunen)
WHERE kr.tila != 'luonnos'
AND kys.tyyppi IN (:v*:kyselytyypit)
--~(if (:kyselyid params) "AND kys.kyselyid = :kyselyid")
AND (kt.oid = :koulutustoimija
--~(if (:vipunen params) "OR k.valtakunnallinen = TRUE")
);

-- :name export-taustatiedot :? :*
SELECT v.vastaajaid,
       vt.vastaajatunnusid,
       kk.kyselykertaid,
       vt.tunnus AS vastaajatunnus,
       to_char(vt.voimassa_alkupvm, 'YYYY-MM-DD') AS vastaajatunnus_alkupvm,
       to_char(vt.voimassa_loppupvm, 'YYYY-MM-DD') AS vastaajatunnus_loppupvm,
       o.oppilaitoskoodi AS oppilaitos, vt.suorituskieli,
       vt.taustatiedot
FROM vastaajatunnus vt
LEFT JOIN organisaatio o ON vt.valmistavan_koulutuksen_oppilaitos = o.oid
LEFT JOIN vastaaja v ON v.vastaajatunnusid = vt.vastaajatunnusid
JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
JOIN kysely k on kk.kyselyid = k.kyselyid
JOIN organisaatio kt on k.koulutustoimija = kt.oid
WHERE coalesce((kk.metatiedot->>'ei_raportoida')::BOOLEAN, FALSE ) = FALSE
AND(kt.oid = :koulutustoimija
--~(if (:vipunen params) "OR TRUE")
)
AND k.tyyppi IN (:v*:kyselytyypit)
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
--~(if (:voimassa_alkupvm_from params) "AND vt.voimassa_alkupvm >= :voimassa_alkupvm_from")
--~(if (:voimassa_alkupvm_until params) "AND vt.voimassa_alkupvm <= :voimassa_alkupvm_until")
--~(if (not (:nayta_vastaamattomat params)) "AND v.vastaajaid is not null")
--~(if (:since params) "AND v.vastaajaid > :since")
ORDER BY v.vastaajaid ASC LIMIT :pagelength;

-- :name export-uniikit-taustatiedot :? :*
SELECT vt.vastaajatunnusid,
       kk.kyselykertaid,
       vt.tunnus AS vastaajatunnus,
       to_char(vt.voimassa_alkupvm, 'YYYY-MM-DD') AS vastaajatunnus_alkupvm,
       to_char(vt.voimassa_loppupvm, 'YYYY-MM-DD') AS vastaajatunnus_loppupvm,
       o.oppilaitoskoodi AS oppilaitos, vt.suorituskieli,
       vt.taustatiedot
FROM vastaajatunnus as vt
         LEFT JOIN organisaatio o ON vt.valmistavan_koulutuksen_oppilaitos = o.oid
         JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
         JOIN kysely k on kk.kyselyid = k.kyselyid
         JOIN organisaatio kt on k.koulutustoimija = kt.oid
WHERE coalesce((kk.metatiedot->>'ei_raportoida')::BOOLEAN, FALSE ) = FALSE
  AND(kt.oid = :koulutustoimija
--~(if (:vipunen params) "OR TRUE")
    )
  AND k.tyyppi IN (:v*:kyselytyypit)
--~(if (not (:nayta_vastaamattomat params)) "AND EXISTS(select v.vastaajaid FROM vastaaja v WHERE  v.vastaajatunnusid = vt.vastaajatunnusid)")
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
--~(if (:voimassa_alkupvm_from params) "AND vt.voimassa_alkupvm >= :voimassa_alkupvm_from")
--~(if (:voimassa_alkupvm_until params) "AND vt.voimassa_alkupvm <= :voimassa_alkupvm_until")
--~(if (:since params) "AND vt.vastaajatunnusid > :since")
ORDER BY vt.vastaajatunnusid ASC LIMIT :pagelength;

-- :name export-kysely-kysymysryhma :? :*
SELECT kkr.kyselyid, kkr.kysymysryhmaid, kkr.jarjestys
FROM kysely_kysymysryhma kkr
JOIN kysely k on kkr.kyselyid = k.kyselyid
JOIN organisaatio kt on k.koulutustoimija = kt.oid
WHERE (kt.oid = :koulutustoimija
--~(if (:vipunen params) "OR TRUE")
)
--~(if (:kyselyid params) "AND kkr.kyselyid = :kyselyid")
AND k.tyyppi IN (:v*:kyselytyypit);

-- :name export-luodut-tunnukset :? :*
SELECT kk.kyselykertaid, o.oppilaitoskoodi, vt.taustatiedot->>'tutkinto' AS tutkintotunnus,
       to_char(vt.voimassa_alkupvm, 'YYYY-MM') AS kuukausi,
       count(vt) AS tunnuksia, coalesce (sum(vt.kohteiden_lkm), 0) AS vastauskertoja
FROM kyselykerta kk
JOIN kysely k ON kk.kyselyid = k.kyselyid
JOIN organisaatio kt ON kt.oid = k.koulutustoimija
LEFT JOIN vastaajatunnus vt ON kk.kyselykertaid = vt.kyselykertaid
LEFT JOIN organisaatio o ON vt.valmistavan_koulutuksen_oppilaitos = o.oid
AND coalesce((kk.metatiedot->>'ei_raportoida')::BOOLEAN, FALSE ) = FALSE
--~(if-not (:vipunen params) "AND kt.oid = :koulutustoimija")
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
GROUP BY kk.kyselykertaid, o.oppilaitoskoodi, vt.taustatiedot->>'tutkinto', kuukausi
ORDER BY kk.kyselykertaid, vt.taustatiedot->>'tutkinto';

-- :name export-monivalintavaihtoehdot :? :*
SELECT DISTINCT m.kysymysid, m.arvo AS jarjestys, m.teksti_fi, m.teksti_sv, m.teksti_en
FROM kysely k
JOIN organisaatio kt ON kt.oid = k.koulutustoimija
JOIN kysely_kysymysryhma kkr ON k.kyselyid = kkr.kyselyid
JOIN kysymysryhma kr ON kkr.kysymysryhmaid = kr.kysymysryhmaid
JOIN kysymys kys ON kkr.kysymysryhmaid = kys.kysymysryhmaid
JOIN monivalintavaihtoehto m on kys.kysymysid = m.kysymysid
WHERE k.tyyppi IN (:v*:kyselytyypit)
AND (
kt.oid = :koulutustoimija
--~(if (:vipunen params) "OR kr.valtakunnallinen = TRUE")
)
--~(if (:kyselyid params) "AND k.kyselyid = :kyselyid")
ORDER BY m.kysymysid, m.arvo;

-- :name hae-api-kayttaja :? :1
SELECT * FROM api_kayttajat WHERE tunnus = :tunnus;
