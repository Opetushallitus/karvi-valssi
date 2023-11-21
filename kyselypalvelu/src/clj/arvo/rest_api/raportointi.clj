(ns arvo.rest-api.raportointi
  (:require
    [ring.util.http-status :as status]
    [schema.core :as s]
    [ring.util.http-response :as response]
    [oph.common.util.http-util :refer [response-or-404 file-download-response]]
    [arvo.service.raportointi :as r]
    [arvo.schema.raportointi :as rs]))

(defn reitit []
  [["/kyselyt"
    {:get {:kayttooikeus [:katselu]
           :handler (fn [req]
                      (response-or-404
                       (r/hae-kyselyt)))}}]
   ["/kysely/:kyselyid"
    {:get {:kayttooikeus [:katselu :kyselyid]
           :parameters {:path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404
                       (r/hae-kyselyn-tiedot (:kyselyid path))))}
     :post {:kayttooikeus [:katselu :kyselyid]
            :parameters {:path {:kyselyid s/Int}
                         :body rs/Raportti-parametrit}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (let [res (r/luo-kyselyraportti (:kyselyid path) body)]
                         (if (:error res)
                           (response/not-found res)
                           (response/ok res))))}}]])
