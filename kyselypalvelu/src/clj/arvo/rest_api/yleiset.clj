(ns arvo.rest-api.yleiset
  (:require
    [schema.core :as s]
    [arvo.db.core :refer [*db*] :as db]
    [clojure.java.jdbc :as jdbc]
    [clojure.tools.logging :as log]
    [ring.util.http-status :as status]
    [arvo.arkisto.organisaatio :as organisaatio-arkisto]
    [arvo.infra.kayttaja.vakiot :as vakiot]
    [arvo.service.vastaajatunnus :as vt]
    [oph.common.util.http-util :refer [validate-response]]
    [arvo.integraatio.organisaatiopalvelu :as organisaatiopalvelu]))

(s/defschema Vastaajatunnus
  {:tunnusten_lkm s/Int
   :kohteiden_lkm s/Int
   :voimassa_alkupvm java.time.LocalDate
   (s/optional-key :voimassa_loppupvm) java.time.LocalDate
   (s/optional-key :kayttaja_oid) s/Str
   (s/optional-key :taustatiedot) {s/Keyword s/Str}
   (s/optional-key :metatiedot) {s/Keyword s/Str}})

(defn validoi-organisaatiot [organisaatiot alkulataus]
  (when (> (count organisaatiot) 10000)
    "organisaatiot.maksimi-maara-ylitetty"))

(defn paivita-organisaatiot [organisaatiot alkulataus]
  (jdbc/with-db-transaction
   [tx *db*]
   (when alkulataus (organisaatio-arkisto/aseta-kaikki-vanhentuneiksi))
   (organisaatiopalvelu/paivita-organisaatiotiedot! organisaatiot)))

(s/defschema Yhteystieto
  {(s/optional-key :www) s/Str
   (s/optional-key :email) s/Str
   (s/optional-key :numero) s/Str
   (s/optional-key :tyyppi) s/Str})

(s/defschema PostiOsoite
  {:postinumeroUri s/Str
   :osoite s/Str
   :postitoimipaikka s/Str})

(s/defschema Organisaatio
  {:nimi {:fi s/Str :sv s/Str :en s/Str}
   :oid s/Str
   (s/optional-key :lakkautusPvm) java.time.LocalDate
   :parentOid s/Str
   :tyypit [s/Str]
   (s/optional-key :yhteystiedot) [Yhteystieto]
   (s/optional-key :postiosoite) PostiOsoite
   (s/optional-key :kotipaikkaUri) s/Str
   (s/optional-key :oppilaitosKoodi) s/Str
   (s/optional-key :oppilaitostyyppi) s/Str
   (s/optional-key :toimipistekoodi) s/Str
   (s/optional-key :ytunnus) s/Str
   (s/optional-key :metatiedot) {s/Keyword (s/if string? s/Str  [s/Str])}})

(defn yleiset-v1 []
  [["/vastaajatunnus/:kyselykertaid"
    {:post {:summary "Yleisen vastaajatunnuksen luonti"
            :description "Sallii tietomallin mukaisen vastaajatunnuksen syöttämisen lähes suoraan. Kutsujan on kuitenkin tiedettävä
        kyselykerran id johon tunnus liitetään. Jos käyttäjä-tieto annetaan edellytetään tämän olevan voimassa oleva
        opintopolun käyttäjä, jolla on järjestelmään oikeudet."
            :responses {status/created {:body [{:tunnus s/Str}]}}
            :parameters {:path {:kyselykertaid s/Int}
                         :body Vastaajatunnus}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (let [vastaajatunnus (assoc body
                                                   :kyselykertaid (:kyselykertaid path)
                                                   :kayttaja_oid (or (:kayttaja_oid body) vakiot/integraatio-oid))]
                         (validate-response vt/lisaa-vastaajatunnus! [vt/validoi-vastaajatunnus] vastaajatunnus)))}}]
   ["/paivita-organisaatiot"
    {:post {:summary "Yleinen organisaation päivitys"
            :description "Sallii organisaatioiden päivityksen rajapinnan kautta. Sallii maksimissaan 10000 organisaation päivityksen kerralla.
         Erona organisaatiopalveluun oppilaitostyyppiä ei anneta uri muodossa. Organisaation nimi max 200 merkkiä."
            :responses {status/ok {:body [{(s/optional-key :luotu) {:oid s/Str} (s/optional-key :paivitetty) {:oid s/Str}}]}}
            :parameters {:query {(s/optional-key :alkulataus) s/Int}
                         :body [Organisaatio]}
            :handler (fn [{{:keys [query body]} :parameters}]
                       (validate-response paivita-organisaatiot [validoi-organisaatiot] body (:alkulataus query)))}}]])
