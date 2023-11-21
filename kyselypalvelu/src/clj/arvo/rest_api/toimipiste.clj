(ns arvo.rest-api.toimipiste
  (:require
    [schema.core :as s]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [arvo.arkisto.toimipiste :as toimipiste]
    [oph.common.util.http-util :refer [response-or-404]]))

(defn reitit []
  [["/:oppilaitos"
    {:get {:kayttooikeus :yllapitaja
           :parameters {:path {:oppilaitos s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (toimipiste/hae-oppilaitoksen-voimassaolevat-toimipisteet (:oppilaitos path))))}}]

   ["/:oppilaitos/aktiivisen-koulutustoimijan"
    {:get {:kayttooikeus :katselu
           :parameters {:path {:oppilaitos s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (toimipiste/hae-oppilaitoksen-voimassaolevat-toimipisteet (:oppilaitos path) (:aktiivinen-koulutustoimija *kayttaja*) (:aktiiviset-oppilaitokset *kayttaja*))))}}]])
