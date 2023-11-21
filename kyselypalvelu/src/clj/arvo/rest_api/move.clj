(ns arvo.rest-api.move
  (:require
    [buddy.auth.middleware :refer (wrap-authentication)]
    [buddy.auth :refer [authenticated? throw-unauthorized]]
    [buddy.auth.backends.token :refer (jws-backend)]
    [oph.common.util.http-util :refer [response-or-404]]
    [schema.core :as s]
    [arvo.service.move :as move]))

(defn reitit []
  [["/luo-tunnukset/:tunniste"
    {:post {:parameters {:path {:tunniste s/Str}}
            :handler (fn [{{:keys [path]} :parameters}]
                       (response-or-404 (move/luo-tunnukset (:tunniste path))))}}]])
