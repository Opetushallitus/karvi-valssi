(ns arvo.rest-api.healthcheck
  (:require
    [oph.common.util.http-util :refer [response-or-404]]
    [ring.util.response :refer [header]]
    [arvo.service.healthcheck :as healthcheck]))

(defn reitit []
  [""
   {:get {:summary "Kuntotarkistus"
          :description "Yksinkertainen tarkistus palvelun kunnosta"
          :handler (fn [req]
                     (-> (healthcheck/check)
                         response-or-404
                         (header "Content-Type" "text/plain")))}}])
