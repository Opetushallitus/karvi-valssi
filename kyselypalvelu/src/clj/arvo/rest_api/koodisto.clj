(ns arvo.rest-api.koodisto
  (:require
    [schema.core :as s]
    [oph.common.util.http-util :refer [response-or-404]]
    [arvo.db.core :refer [*db*] :as db]))

(defn reitit []
  [["/oppilaitos/:oppilaitosnumero"
    {:get {:parameters {:path {:oppilaitosnumero s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (let [oppilaitos (db/oppilaitos {:oppilaitoskoodi (:oppilaitosnumero path)})]
                        (response-or-404 (into {}
                                               (filter second {"fi" (:nimi_fi oppilaitos)
                                                               "sv" (:nimi_sv oppilaitos)
                                                               "en" (:nimi_en oppilaitos)})))))}}]
   ["/koulutus/:koulutuskoodi"
    {:get {:parameters {:path {:koulutuskoodi s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (let [tutkinto (db/tutkinto {:tutkintotunnus (:koulutuskoodi path)})]
                        (response-or-404 (into {}
                                               (filter second {"fi" (:nimi_fi tutkinto)
                                                               "sv" (:nimi_sv tutkinto)
                                                               "en" (:nimi_en tutkinto)})))))}}]])
