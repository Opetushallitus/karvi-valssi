(ns oph.common.infra.anon-auth
  "Testitarkoituksia varten anonyymi-autentikaatiofiltteri, joka emuloi CAS-autentikaatiota"
  (:require [clojure.tools.logging :as log]))

(defn auth-cas-user [ring-handler uid]
  (log/info "!! Anon auth enabled")
  (fn [request]
    (let [req (assoc request :username (get (:headers request) "uid" uid))
          _ (log/debug "authorized user " (:username req))]
      (ring-handler req))))
