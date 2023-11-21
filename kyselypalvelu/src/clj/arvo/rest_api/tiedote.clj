(ns arvo.rest-api.tiedote
  (:require
    [schema.core :as s]
    [arvo.util :as arvo-util]
    [ring.util.http-response :as response]
    [arvo.db.tiedote :as db]
    [oph.common.util.http-util :refer [response-or-404]]))

(defn reitit []
  [["/"
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (db/hae)))}
     :post {:kayttooikeus :yllapitaja
            :parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (db/lisaa-tiedote! body)
                       (arvo-util/api-response "OK"))}}]
   ["/:tiedoteid"
    {:put {:kayttooikeus :yllapitaja
           :parameters {:path {:tiedoteid s/Int}
                        :body s/Any}
           :handler (fn [{{:keys [body]} :parameters}]
                      (response-or-404 (str (db/paivita-tiedote! body))))}
     :delete {:kayttooikeus :yllapitaja
              :parameters {:path {:tiedoteid s/Int}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (db/poista-tiedote! (-> path :tiedoteid))
                         (response/ok))}}]])
