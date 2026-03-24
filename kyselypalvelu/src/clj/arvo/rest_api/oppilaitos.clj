(ns arvo.rest-api.oppilaitos
  (:require
    [schema.core :as s]
    [arvo.infra.kayttaja :refer [yllapitaja? *kayttaja*]]
    [arvo.arkisto.oppilaitos :as oppilaitos]
    [oph.common.util.http-util :refer [response-or-404]]))

(defn reitit []
  [["/aktiivisen-koulutustoimijan"
    {:conflicting true
     :get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (oppilaitos/hae-koulutustoimijan-oppilaitokset (:aktiivinen-koulutustoimija *kayttaja*) (:aktiiviset-oppilaitokset *kayttaja*))))}}]
   ["/:koulutustoimija"
    {:conflicting true
     :get {:kayttooikeus :yllapitaja
           :parameters {:path {:koulutustoimija s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (oppilaitos/hae-koulutustoimijan-oppilaitokset (:koulutustoimija path))))}}]])
