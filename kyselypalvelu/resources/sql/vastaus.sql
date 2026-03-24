-- :name luo-vastaaja! :<!
INSERT INTO vastaaja (kyselykertaid, vastaajatunnusid, luotuaika, muutettuaika, tyyppi)
SELECT kyselykertaid, vastaajatunnusid, now(), now(), 'henkilokohtainen'
FROM vastaajatunnus WHERE tunnus = :tunnus
RETURNING vastaajaid;

-- :name lisaa-vastaus! :! :n
INSERT INTO vastaus (kysymysid, vastaajaid, vapaateksti, numerovalinta, luku, vaihtoehto, en_osaa_sanoa, luotuaika, muutettuaika)
VALUES (:kysymysid, :vastaajaid, :vapaateksti, :numerovalinta, :luku, :vaihtoehto, :en_osaa_sanoa, now(), now());