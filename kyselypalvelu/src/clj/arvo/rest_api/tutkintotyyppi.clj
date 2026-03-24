(ns arvo.rest-api.tutkintotyyppi
  (:require
    [arvo.arkisto.tutkintotyyppi :as tutkintotyyppi]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [oph.common.util.http-util :refer [response-or-404]]))

(defn reitit []
  [[""
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (tutkintotyyppi/hae-kayttajalle (:aktiivinen-koulutustoimija *kayttaja*))))}}]])
