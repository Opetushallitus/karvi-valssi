(ns arvo.rest-api.raportti.kysely
  (:require
            [schema.core :as s]
            [arvo.rest-api.i18n :as i18n]
            [arvo.service.csv :refer [kysely-csv-vastaajittain kysely-csv-vastauksittain vastaajatunnukset-csv kohteet-csv vastanneet-csv]]
            [oph.common.util.http-util :refer [csv-download-response]]))


(defn get-csv-name
  ([csv-data modifier]
   (str (:nimi csv-data) "-" (:date csv-data) "-" (:koulutustoimija csv-data) (when modifier (str "-" modifier))".csv"))
  ([csv-data]
   (get-csv-name csv-data nil)))

(def default-lang "fi")

(defn csv []
  [["/kysely/:kyselyid"
    {:get {:kayttooikeus [:kysely :kyselyid]
           :parameters {:query {(s/optional-key :lang) s/Str}
                        :path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path query]} :parameters}]
                      (let [csv-data (kysely-csv-vastaajittain (:kyselyid path) (keyword (or (:lang query) default-lang)))]
                        (csv-download-response (:csv csv-data) (get-csv-name csv-data))))}}]
   ["/kysely/vastauksittain/:kyselyid"
    {:get {:kayttooikeus [:kysely :kyselyid]
           :parameters {:query {(s/optional-key :lang) s/Str}
                        :path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path query]} :parameters}]
                      (let [csv-data (kysely-csv-vastauksittain (:kyselyid path) (keyword (or (:lang query) default-lang)))]
                        (csv-download-response (:csv csv-data) (get-csv-name csv-data))))}}]
   ["/kysely/kohteet/:kyselyid"
    {:get {:kayttooikeus [:kysely :kyselyid]
           :parameters {:query {(s/optional-key :lang) s/Str}
                        :path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path query]} :parameters}]
                      (let [csv-data (kohteet-csv (:kyselyid path) (keyword (or (:lang query) default-lang)))]
                        (csv-download-response csv-data (str "Kohteet -" (:kyselyid path) ".csv"))))}}]
   ["/kysely/vastaajat/:kyselyid"
    {:get {:kayttooikeus [:kysely :kyselyid]
           :parameters {:query {(s/optional-key :lang) s/Str}
                        :path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path query]} :parameters}]
                      (let [csv-data (vastanneet-csv (:kyselyid path) (keyword (or (:lang query) default-lang)))]
                        (csv-download-response csv-data (str "Vastaajat -"(:kyselyid path) ".csv"))))}}]
   ["/vastaajatunnus/:kyselykertaid"
    {:get {:kayttooikeus [:katselu :kyselykertaid]
           :parameters {:query {(s/optional-key :lang) s/Str}
                        :path {:kyselykertaid s/Int}}
           :handler (fn [{{:keys [path query]} :parameters}]
                      (let [csv-data (vastaajatunnukset-csv (:kyselykertaid path) (keyword (or (:lang query) default-lang)))]
                        (csv-download-response csv-data (str "vastaajatunnukset -" (:kyselykertaid path) ".csv"))))}}]])
