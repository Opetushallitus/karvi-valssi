(ns arvo.rest-api.tutkinto
  (:require
    [arvo.arkisto.tutkinto :as tutkinto]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [oph.common.util.http-util :refer [response-or-404]]
    [schema.core :as s]
    [clojure.tools.logging :as log]))

(defn reitit []
  [["/voimassaolevat-listana"
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (tutkinto/hae-voimassaolevat-tutkinnot-listana)))}}]
   ["/voimassaolevat"
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (tutkinto/hae-voimassaolevat-tutkinnot)))}}]
   ["/vanhentuneet"
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (tutkinto/hae-vanhentuneet-tutkinnot)))}}]
   ["/koulutustoimija"
    {:get {:kayttooikeus :katselu
           :parameters {:query {(s/optional-key :kyselytyyppi) s/Str}}
           :handler (fn [{{:keys [query]} :parameters}]
                      (response-or-404 (tutkinto/hae-koulutustoimijan-voimassaolevat-tutkinnot (:aktiivinen-koulutustoimija *kayttaja*) (query :kyselytyyppi))))}}]
   ["/koulutustoimija/:y-tunnus"
    {:get {:kayttooikeus :katselu
           :parameters {:path {:y-tunnus s/Str}
                        :query {(s/optional-key :kyselytyyppi) s/Str}}
           :handler (fn [{{:keys [path query]} :parameters}]
                      (response-or-404 (tutkinto/hae-koulutustoimijan-voimassaolevat-tutkinnot (path :y-tunnus) (query :kyselytyyppi))))}}]
   ["/kyselytyyppi/:kyselytyyppi"
    {:get {:kayttooikeus :katselu
           :parameters {:path {:kyselytyyppi s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (tutkinto/hae-kyselytyypin-tutkinnot (path :kyselytyyppi))))}}]
   ["/jarjestajat/:tutkintotunnus"
    {:get {:kayttooikeus :katselu
           :parameters {:path {:tutkintotunnus s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (tutkinto/hae-tutkinnon-jarjestajat (path :tutkintotunnus))))}}]
   ["/tutkinnonosat"
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (tutkinto/hae-tutkinnon-osat)))}}]])
