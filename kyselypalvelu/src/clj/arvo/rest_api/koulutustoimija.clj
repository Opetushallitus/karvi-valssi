(ns arvo.rest-api.koulutustoimija
  (:require
    [arvo.arkisto.koulutustoimija :as koulutustoimija]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [clojure.tools.logging :as log]
    [oph.common.util.http-util :refer [response-or-404]]
    [schema.core :as s]))

(defn reitit []
  [["/aktiivinen"
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (koulutustoimija/hae (:aktiivinen-koulutustoimija *kayttaja*))))}}]
   [""
    {:get {:kayttooikeus :yllapitaja
           :handler (fn [req]
                      (response-or-404 (koulutustoimija/hae-kaikki)))}}]
   ["/koulutusluvalliset"
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (koulutustoimija/hae-koulutusluvalliset)))}}]
   ["/hae-nimella"
    {:get {:kayttooikeus :yllapitaja
           :parameters {:query {:termi s/Str}}
           :handler (fn [{{:keys [query]} :parameters}]
                      (response-or-404 (koulutustoimija/hae-nimella (-> query :termi))))}}]])
