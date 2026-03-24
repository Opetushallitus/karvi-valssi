(ns arvo.rest-api.vastaajatunnus
  (:require
    [schema.core :as s]
    [ring.util.http-response :as response]
    [arvo.arkisto.vastaajatunnus :as vastaajatunnus]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [clojure.tools.logging :as log]
    [oph.common.util.http-util :refer [parse-iso-date response-or-404]]
    [oph.common.util.util :refer [paivita-arvot]]))

(defn ui->vastaajatunnus [vastaajatunnus kyselykertaid]
  {:kyselykertaid kyselykertaid
   :tunnusten-lkm (if (:henkilokohtainen vastaajatunnus) (:kohteiden_lkm vastaajatunnus) 1)
   :kohteiden_lkm (if (:henkilokohtainen vastaajatunnus) 1 (:kohteiden_lkm vastaajatunnus))
   :tutkinto (get-in vastaajatunnus [:tutkinto :tutkintotunnus])
   :kieli (:suorituskieli vastaajatunnus)
   :kunta (get-in vastaajatunnus [:koulutuksen_toimipiste :kunta])
   :koulutusmuoto (:koulutusmuoto vastaajatunnus)
   :valmistavan_koulutuksen_oppilaitos (get-in vastaajatunnus [:koulutuksen_jarjestaja_oppilaitos :oid])
   :toimipiste (get-in vastaajatunnus [:koulutuksen_toimipiste :toimipistekoodi])
   :toimipiste_oid (get-in vastaajatunnus [:koulutuksen_toimipiste :oid])
   :voimassa_alkupvm (:voimassa_alkupvm vastaajatunnus)
   :voimassa_loppupvm (:voimassa_loppupvm vastaajatunnus)
   :haun_numero (:haun_numero vastaajatunnus)
   :henkilonumero (:henkilonumero vastaajatunnus)
   :hankintakoulutuksen_toteuttaja (get-in vastaajatunnus [:hankintakoulutuksen_toteuttaja :oid])
   :tutkintomuoto (:tutkintomuoto vastaajatunnus)
   :tutkinnon_osa (:koodi_arvo (:tutkinnon_osa vastaajatunnus))})

(defn reitit []
  [["/:kyselykertaid"
    {:get {:kayttooikeus [:katselu :kyselykertaid]
           :parameters {:path {:kyselykertaid s/Int}
                        :query {(s/optional-key :omat) s/Bool}}
           :handler (fn [{{:keys [path query]} :parameters}]
                      (response-or-404 (vastaajatunnus/hae-kyselykerralla (-> path :kyselykertaid) (query :omat))))}
     :post {:kayttooikeus [:vastaajatunnus :kyselykertaid]
            :parameters {:path {:kyselykertaid s/Int}
                         :body s/Any}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (let [vastaajatunnus (-> body
                                                (ui->vastaajatunnus (:kyselykertaid path))
                                                (paivita-arvot [:voimassa_alkupvm :voimassa_loppupvm] parse-iso-date))]
                         (response-or-404 (vastaajatunnus/lisaa! vastaajatunnus))))}}]
   ["/:kyselykertaid/tunnus/:tunnus/lukitse"
    {:post {:kayttooikeus [:vastaajatunnus :kyselykertaid]
            :parameters {:path {:kyselykertaid s/Int
                                :tunnus s/Str}
                         :body {:lukitse s/Bool}}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (response-or-404 (vastaajatunnus/aseta-lukittu! (:kyselykertaid path) (:tunnus path) (:lukitse body))))}}]
   ["/:kyselykertaid/tunnus/:tunnus/muokkaa-lukumaaraa"
    {:post {:kayttooikeus [:vastaajatunnus :kyselykertaid]
            :parameters {:path {:kyselykertaid s/Int
                                :tunnus s/Str}
                         :body {:lukumaara s/Int}}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (let [vastaajatunnus (vastaajatunnus/hae (:kyselykertaid path) (:tunnus path))
                             vastaajat (vastaajatunnus/laske-vastaajat (:vastaajatunnusid vastaajatunnus))]
                         (when-not (:muokattavissa vastaajatunnus)
                           (throw (IllegalArgumentException. "Vastaajatunnus ei ole enää muokattavissa")))
                         (if (and (pos? (:lukumaara body)) (>= (:lukumaara body) vastaajat))
                           (response-or-404 (vastaajatunnus/muokkaa-lukumaaraa! (:kyselykertaid path) (:tunnus path) (:lukumaara body)))
                           (response/forbidden))))}}]
   ["/:kyselykertaid/tunnus/:tunnus"
    {:delete {:kayttooikeus [:vastaajatunnus :kyselykertaid]
              :parameters {:path {:kyselykertaid s/Int
                                  :tunnus s/Str}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (let [vastaajatunnus (vastaajatunnus/hae (:kyselykertaid path) (:tunnus path))
                               vastaajat (vastaajatunnus/laske-vastaajat (:vastaajatunnusid vastaajatunnus))]
                           (if (and (zero? vastaajat) (vastaajatunnus/tunnus-poistettavissa? (:kyselykertaid path) (:tunnus path)))
                             (do
                               (vastaajatunnus/poista! (:tunnus path))
                               (response/no-content))
                             (response/forbidden))))}}]
   ["/:kyselykertaid/niput"
    {:get {:kayttooikeus [:katselu :kyselykertaid]
           :parameters {:path {:kyselykertaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (vastaajatunnus/hae-niput (:kyselykertaid path))))}}]
   ["/:kyselykertaid/tutkinto"
    {:get {:kayttooikeus [:katselu :kyselykertaid]
           :parameters {:path {:kyselykertaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (if-let [tutkinto (vastaajatunnus/hae-viimeisin-tutkinto (:kyselykertaid path) (:aktiivinen-koulutustoimija *kayttaja*))]
                        (response-or-404 tutkinto)
                        (response/ok)))}}]])
