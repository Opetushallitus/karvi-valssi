(ns arvo.rest-api.henkilo
  (:require
    [schema.core :as s]
    [arvo.util :as arvo-util]
    [ring.util.http-status :as status]
    [clojure.tools.logging :as log]
    [arvo.integraatio.kayttooikeuspalvelu :as kayttooikeuspalvelu]))

(defn hae-kaikki-oidit []
  [["/kaikki-oidit/:oid"
    {:get {:summary "Palauttaa henkilön kaikki oidit"
           :description "Palauttaa listan oideja. Ei kerro, löytyykö henkilö oppijanumerorekisteristä."
           :responses {status/ok {:body [s/Str]}}
           :parameters {:path {:oid s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (arvo-util/api-response (kayttooikeuspalvelu/kaikki-oidit (:oid path))))}}]])
