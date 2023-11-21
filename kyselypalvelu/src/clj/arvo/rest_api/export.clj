(ns arvo.rest-api.export
  (:require
    [arvo.db.core :refer [*db*] :as db]
    [arvo.schema.export :refer :all]
    [oph.common.util.http-util :refer [response-or-404]]
    [clojure.tools.logging :as log]
    [ring.util.http-status :as status]
    [arvo.integraatio.kyselyynohjaus :as ko]
    [schema.core :as s]
    [schema-tools.core :as st]
    [arvo.util :refer [api-response paginated-response]]
    [arvo.config :refer [env]]))

(defn export-params [request type]
  (let [params {:koulutustoimija (:organisaatio request)
                :vipunen (-> request :oikeudet :vipunen)
                :kyselytyypit (-> request :oikeudet :kyselytyypit)}]
    (log/info "Export" type ":" params)
    params))

(defn muunna-vastaajatiedot-v1-schemaan [taustatiedot]
  "Säilytä v1 rajapinnan yhteensopivuus nimeämällä (taustatietojen) toimipiste->toimipaikka"
  (update-in taustatiedot [:taustatiedot] clojure.set/rename-keys {:toimipiste :toimipaikka}))

(s/defschema Pagination
  {(s/optional-key :next_url) (s/maybe s/Str)})

(def api-location "/api/export/v1/")

(defn v1 []
  [["/kyselykerrat"
    {:get {:summary "Kyselykerrat ja kyselyt"
           :description "Kyselykerran ja siihen liittyvän kyselyn tarkemmat tiedot"
           :responses {status/ok {:body {:data [Kyselykerta]}}}
           :handler (fn [req]
                      (api-response {:data (db/export-kyselyt (export-params req "kyselykerrat"))}))}}]
   ["/kysely_kysymysryhma"
    {:get {:summary "Kyselyt ja niiden kysymysryhmät"
           :description "Kyselyiden ja kysymysryhmien suhteet"
           :responses {status/ok {:body {:data [Kysely-kysymysryhma]}}}
           :parameters {:query {(s/optional-key :kyselyid) s/Int}}
           :handler (fn [{{:keys [query]} :parameters :as req}]
                      (api-response {:data (db/export-kysely-kysymysryhma (merge {:kyselyid (:kyselyid query)} (export-params req "kysely-kysymysryhma")))}))}}]
   ["/kysymykset"
    {:get {:summary "Kysymysten tiedot"
           :description "Kysymysten keskeiset (jatkokysymykset) suhteet ja kysymysryhmä johon kuuluvat"
           :responses {status/ok {:body {:data [Kysymys]}}}
           :parameters {:query {(s/optional-key :kyselyid) s/Int}}
           :handler (fn [{{:keys [query]} :parameters :as req}]
                      (let [query-params query]
                        (api-response {:data (db/export-kysymykset (merge (export-params req "kysymykset") query-params))})))}}]
    ["/monivalintavaihtoehdot"
     {:get {:summary "Monivalintakysymykset"
            :description "Vastausvaihtoehdot monivalintakysymykseen"
            :responses {status/ok {:body {:data [Monivalintavaihtoehto]}}}
            :parameters {:query {(s/optional-key :kyselyid) s/Int}}
            :handler (fn [{{:keys [query]} :parameters :as req}]
                       (api-response {:data (db/export-monivalintavaihtoehdot (merge query (export-params req "monivalintavaihtoehdot")))}))}}]
   ["/vastaukset"
    {:get {:summary "Kysymysten vastaukset"
           :description "Kysymysten vastaukset ja niihin liittyvä vastaaja ja vastaajatunnustieto. \"koulutustoimija\" ilmoitetaan y-tunnuksella."
           :responses {status/ok {:body {:data [Vastaus] :pagination Pagination}}}
           :parameters {:query (st/optional-keys {:kyselyid s/Int
                                                  :alkupvm java.time.LocalDate
                                                  :loppupvm java.time.LocalDate
                                                  :since s/Int
                                                  :limit s/Int})}
           :handler (fn [{{:keys [query]} :parameters :as req}]
                      (let [query-params query
                            page-length (if (:limit query) (min (:limit query) (:api-page-length env)) (:api-page-length env))
                            data (db/export-vastaukset (apply merge {:pagelength page-length} query-params (export-params req "vastaukset")))]
                        (paginated-response data :vastausid page-length (str api-location "vastaukset") query-params)))}}]
   ["/vastaajat"
    {:get {:summary "Vastaajat ja niiden vastaajatunnukset"
           :description "Vastaaja ja siiheen liittyvän vastaajatunnuksen tarkemmat tiedot. Query parametrit 'since' ja
       'nayta_vastaamattomat' eivät toimi yhdessä koska vastaamattomilla ei ole vastaajaid:tä. Tästä johtuen sivutus ei
       toimi 'nayta_vastaamattomat' vivun kanssa koska sivutus perustuu 'since' parametriin."
           :responses {status/ok {:body {:data [Vastaajatunnus] :pagination Pagination}}}
           :parameters {:query (st/optional-keys {:kyselyid s/Int
                                                  :voimassa_alkupvm_from java.time.LocalDate
                                                  :voimassa_alkupvm_until java.time.LocalDate
                                                  :nayta_vastaamattomat s/Bool
                                                  :since s/Int
                                                  :limit s/Int})}
           :handler (fn [{{:keys [query]} :parameters :as req}]
                      (let [page-length (if (:limit query) (min (:limit query) (:api-page-length env)) (:api-page-length env))
                            sql-params (merge query {:pagelength page-length} (export-params req "taustatiedot"))
                            vastaajatiedot (db/export-taustatiedot sql-params)
                            vastaajatiedot-v1-schema (map muunna-vastaajatiedot-v1-schemaan vastaajatiedot)]
                        (paginated-response vastaajatiedot-v1-schema :vastaajaid page-length (str api-location "vastaajat") {:limit (:limit query)})))}}]
   ["/kohteet"
    {:get {:summary "Vastaajatunnukset"
           :description "Vastaajatunnuksen tarkemmat tiedot. Eroaa /vastaajat rajapinnasta
       siten, että tulosjoukossa on uniikit vastaustununkset, vastaajat puuttuvat kokonaan sekä 'since' parametrin
       vertailu kohdistuu vastaajatunnuksen id:hen"
           :responses {status/ok {:body {:data [Vastaajatunnus] :pagination Pagination}}}
           :parameters {:query (st/optional-keys {:kyselyid s/Int
                                                  :voimassa_alkupvm_from java.time.LocalDate
                                                  :voimassa_alkupvm_until java.time.LocalDate
                                                  :nayta_vastaamattomat s/Bool
                                                  :since s/Int
                                                  :limit s/Int})}
           :handler (fn [{{:keys [query]} :parameters :as req}]
                      (let [page-length (if (:limit query) (min (:limit query) (:api-page-length env)) (:api-page-length env))
                            sql-params (merge query {:pagelength page-length} (export-params req "taustatiedot"))
                            vastaajatiedot (db/export-uniikit-taustatiedot sql-params)
                            vastaajatiedot-v1-schema (map muunna-vastaajatiedot-v1-schemaan vastaajatiedot)]
                        (paginated-response vastaajatiedot-v1-schema :vastaajatunnusid page-length (str api-location "kohteet") {:limit (:limit query)})))}}]
   ["/opiskeluoikeudet"
    {:get {:summary "Vastaajatunnukset ja sen opiskeluoikeus"
           :description "Vastaajatunnuksen ja virran opiskeluoikeuden suhteet. Vain kyselyynohjauksen kautta vastanneet saavat tämän esim. HAKA."
           :responses {status/ok {:body {:data [Opiskeluoikeus]}}}
           :handler (fn [req]
                      (let [params (export-params req "opiskeluoikeudet")
                            oppilaitokset (map :oppilaitoskoodi (db/hae-koulutustoimijan-oppilaitokset {:koulutustoimija (:koulutustoimija params)}))
                            opiskeluoikeudet (ko/get-opiskeluoikeus-data oppilaitokset)]
                        (api-response {:data opiskeluoikeudet})))}}]
   ["/luodut_tunnukset"
    {:get {:summary "Kooste"
           :description "Kooste kuukausittain luoduista tunnuksista kyselykertaa kohden"
           :responses {status/ok {:body {:data [Luodut-tunnukset]}}}
           :parameters {:query {(s/optional-key :kyselyid) s/Int}}
           :handler (fn [{{:keys [query]} :parameters :as req}]
                      (api-response {:data (db/export-luodut-tunnukset (merge {:kyselyid (:kyselyid query)} (export-params req "luodut-tunnukset")))}))}}]])
