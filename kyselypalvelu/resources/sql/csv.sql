-- :name hae-csv-kohteet :? :*
SELECT vt.*, v.luotuaika AS vastausaika,
       o.oppilaitoskoodi,
       kk.nimi AS kyselykerta_nimi,
       o.nimi_fi AS oppilaitos_nimi_fi, o.nimi_sv AS oppilaitos_nimi_sv, o.nimi_en AS oppilaitos_nimi_en
    FROM vastaajatunnus vt
    JOIN kyselykerta kk ON vt.kyselykertaid = kk.kyselykertaid
    JOIN kysely k on k.kyselyid = kk.kyselyid
    LEFT JOIN vastaaja v ON vt.vastaajatunnusid = v.vastaajatunnusid
    LEFT JOIN organisaatio o ON vt.valmistavan_koulutuksen_oppilaitos = o.oid
WHERE k.kyselyid = :kyselyid
AND (:vastaamattomat OR
    EXISTS (SELECT 1 FROM vastaaja v WHERE v.vastaajatunnusid = vt.vastaajatunnusid));
