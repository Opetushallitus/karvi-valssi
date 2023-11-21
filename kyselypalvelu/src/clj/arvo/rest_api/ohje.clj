(ns arvo.rest-api.ohje
  (:require
    [schema.core :as s]
    [ring.util.http-response :as response]
    [arvo.arkisto.ohje :as arkisto]
    [oph.common.util.http-util :refer [response-or-404]]))

(defn reitit []
  [["/:ohjetunniste"
    {:get {:kayttooikeus :katselu
           :parameters {:path {:ohjetunniste s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (if-let [ohje (arkisto/hae (:ohjetunniste path))]
                        (response-or-404 ohje)
                        (response/ok)))}
     :put {:kayttooikeus :yllapitaja
           :parameters {:path {:ohjetunniste s/Str}
                        :body {:ohjetunniste s/Str
                               :teksti_fi s/Str
                               :teksti_sv s/Str
                               :teksti_en s/Str}}
           :handler (fn [{{:keys [body]} :parameters}]
                      (arkisto/muokkaa-tai-luo-uusi! body)
                      (response/ok))}}]])
