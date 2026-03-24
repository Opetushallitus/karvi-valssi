(ns arvo.rest-api.kyselykerta
  (:require
    [schema.core :as s]
    [arvo.util :as arvo-util]
    [ring.util.http-response :as response]
    [arvo.arkisto.kyselykerta :as arkisto]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [oph.common.util.http-util :refer [parse-iso-date response-or-404]]
    [oph.common.util.util :refer [paivita-arvot]]))

(defn reitit []
  [[""
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (arkisto/hae-koulutustoimijan-kyselykerrat (:aktiivinen-koulutustoimija *kayttaja*) (:aktiiviset-oppilaitokset *kayttaja*))))}
     :post {:kayttooikeus [:kyselykerta :kyselyid]
            :parameters {:body {:kyselyid s/Int
                                :kyselykerta s/Any}}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [{:keys [kyselyid kyselykerta]} body
                             kyselykerta-parsittu (paivita-arvot kyselykerta [:voimassa_alkupvm :voimassa_loppupvm] parse-iso-date)]
                         (if (arkisto/samanniminen-kyselykerta? kyselyid (:nimi kyselykerta))
                           (arvo-util/api-response response/bad-request "kyselykerta.samanniminen_kyselykerta")
                           (response-or-404 (arkisto/lisaa! kyselyid kyselykerta-parsittu)))))}}]
   ["/:kyselykertaid"
    {:get {:kayttooikeus [:katselu :kyselykertaid]
           :parameters {:path {:kyselykertaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/hae-yksi (:kyselykertaid path))))}
     :post {:kayttooikeus [:kyselykerta :kyselykertaid]
            :parameters {:path {:kyselykertaid s/Int}
                         :body s/Any}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (let [kyselykertaid (-> path :kyselykertaid)
                             kyselykerta-parsittu (paivita-arvot body [:voimassa_alkupvm :voimassa_loppupvm] parse-iso-date)]
                         (if (arkisto/samanniminen-kyselykerta? (:kyselyid body) (:nimi body) kyselykertaid)
                           (arvo-util/api-response response/bad-request "kyselykerta.samanniminen_kyselykerta")
                           (response-or-404 (arkisto/paivita! kyselykertaid kyselykerta-parsittu)))))}
     :delete {:kayttooikeus [:kyselykerta :kyselykertaid]
              :parameters {:path {:kyselykertaid s/Int}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (arkisto/poista! (:kyselykertaid path))
                         (response/no-content))}}]
   ["/:kyselykertaid/vastaustunnustiedot"
    {:get {:kayttooikeus [:katselu :kyselykertaid]
           :parameters {:path {:kyselykertaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/hae-kyselykerran-oppilaitokset (-> path :kyselykertaid))))}}]
   ["/:kyselykertaid/lukitse"
    {:put {:kayttooikeus [:kyselykerta :kyselykertaid]
           :parameters {:path {:kyselykertaid s/Int}
                        :body {:lukitse s/Bool}}
           :handler (fn [{{:keys [path body]} :parameters}]
                      (response-or-404 (arkisto/aseta-lukittu! (-> path :kyselykertaid) (-> body :lukitse))))}}]])
