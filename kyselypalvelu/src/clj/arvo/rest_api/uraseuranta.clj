(ns arvo.rest-api.uraseuranta
  (:require [buddy.auth.middleware :refer (wrap-authentication)]
            [arvo.service.uraseuranta :as uraseuranta]
            [ring.util.http-status :as status]
            [ring.swagger.upload :refer [TempFileUpload]]
            [buddy.auth.backends.token :refer (jws-backend)]
            [reitit.ring.middleware.multipart :as multipart]
            [schema.core :as s]
            [buddy.auth :refer [authenticated? throw-unauthorized]]
            [oph.common.util.http-util :refer [response-or-404 file-download-response]]))

(defn uraseuranta-routes []
  [["/kohteet"
    {:no-doc true
     :post {:kayttooikeus :yllapitaja
            :parameters {:multipart {:upload TempFileUpload
                                     :tunniste s/Str}}
            :handler (fn [{{{:keys [upload tunniste]} :multipart} :parameters}]
                       (response-or-404
                        (uraseuranta/lisaa-kohteet tunniste (:tempfile upload) (:filename upload))))}}]
   ["/yhteystiedot/:kyselykertaid"
    {:no-doc true
     :get {:kayttooikeus [:kyselykerta :kyselykertaid]
           :parameters {:path {:kyselykertaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (let [yhteystiedot (uraseuranta/hae-yhteystiedot (:kyselykertaid path))]
                        (file-download-response yhteystiedot (str "kohteet-"(:kyselykertaid path)".xlsx")
                                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")))}
     :post {:kayttooikeus [:kyselykerta :kyselykertaid]
            :parameters {:multipart {:yhteystiedot TempFileUpload}
                         :path {:kyselykertaid s/Int}}
            :handler (fn [{{{:keys [yhteystiedot]} :multipart path :path} :parameters}]
                       (let [paivitetty (uraseuranta/lisaa-yhteystiedot (:kyselykertaid path) (:tempfile yhteystiedot) (:filename yhteystiedot))]
                         (response-or-404 {:paivitetty paivitetty})))}}]])
