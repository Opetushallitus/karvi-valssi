(ns arvo.rest-api.yllapitaja
  (:require [buddy.auth.middleware :refer (wrap-authentication)]
            [buddy.auth.backends.token :refer (jws-backend)]
            [schema.core :as s]
            [ring.swagger.upload :refer [TempFileUpload]]
            [arvo.config :refer [env]]
            [buddy.auth :refer [authenticated? throw-unauthorized]]
            [oph.common.util.http-util :refer [response-or-404 file-download-response]]
            [arvo.db.core :refer [*db*] :as db]
            [arvo.service.yllapito :as yllapito]
            [arvo.service.vastaus :as vastaus]))

(def eraajot [:automaattikyselyt :oiva :koodistot])

(defn yllapitaja-routes []
  [["/tiedonkeruut"
    {:get {:kayttooikeus [:yllapitaja]
           :handler (fn [req]
                      (response-or-404 (db/hae-tiedonkeruut)))}}]
   ["/tiedonkeruu-tiedosto/:tunniste"
    {:post {:kayttooikeus [:yllapitaja]
            :parameters {:path {:tunniste s/Str}}
            :handler (fn [{{:keys [path]} :parameters}]
                       (let [vastaukset (yllapito/hae-vastaustiedosto (:tunniste path))]
                         (file-download-response vastaukset (str "vastaukset-"(:tunniste path)".xlsx")
                                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")))}}]
   ["/lisaa-vastaukset/:tunniste"
    {:no-doc true
     :post {:kayttooikeus [:yllapitaja]
            :parameters {:multipart {:vastaukset TempFileUpload}
                         :path {:tunniste s/Int}}
            :handler (fn [{{{:keys [vastaukset]} :multipart path :path} :parameters}]
                       (let [res (vastaus/tallenna-tiedostosta (:tunniste path) (:tempfile vastaukset) (:filename vastaukset) nil)]
                         (response-or-404 {:count res})))}}]
   ["/eraajot"
    {:get {:kayttooikeus [:yllapitaja]
           :handler (fn [req]
                      (response-or-404 eraajot))}}]
   ["/eraajot/:tyyppi"
    {:post {:kayttooikeus [:yllapitaja]
            :parameters {:path {:tyyppi s/Str}}
            :handler (fn [{{:keys [path]} :parameters}]
                       (let [res (yllapito/kaynnista-eraajo (keyword (:tyyppi path)))]
                         (response-or-404 "OK")))}}]])
