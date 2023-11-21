(ns arvo.rest-api.admin
  (:require [buddy.auth.middleware :refer (wrap-authentication)]
            [buddy.auth.backends.token :refer (jws-backend)]
            [schema.core :as s]
            [arvo.config :refer [env]]
            [buddy.auth :refer [authenticated? throw-unauthorized]]
            [oph.common.util.http-util :refer [response-or-404 file-download-response]]
            [ring.util.http-status :as status]
            [ring.util.http-response :as response]
            [ring.swagger.upload :refer [TempFileUpload]]
            [arvo.service.osio-tunnukset :as o]
            [arvo.infra.eraajo.koulutustoimijoiden-tutkinnot :refer [paivita-koulutustoimijoiden-tutkinnot!]]
            [arvo.service.uraseuranta :as uraseuranta]
            [arvo.infra.eraajo.koodistot :as koodistot]
            [arvo.infra.eraajo.organisaatiot :as organisaatiot]
            [arvo.infra.eraajo.automaattikyselyt :refer [luo-automaattikyselyt!]]
            [arvo.service.viestinta :as viestinta]
            [clojure.tools.logging :as log]
            [arvo.service.raportointi :as r]
            [arvo.service.move :as move]))

(def oletus-kieli "fi")

(defn admin-routes []
  [["/osio-tunnukset"
    {:post {:parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [res (o/luo-osio-tunnukset (:ohjaus-kyselykerta body) (:osio-kyselykerrat body))]
                         (response-or-404 res)))}}]
   ["/uraseuranta/upload"
    {:no-doc true
     :post {:parameters {:multipart {:upload TempFileUpload
                                     :tunniste s/Str}}
            :handler (fn [{{{:keys [upload tunniste]} :multipart} :parameters}]
                       (file-download-response
                        (uraseuranta/lisaa-kohteet tunniste (:tempfile upload) (:filename upload))
                        "vrk.xlsx"
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))}}]
   ["/uraseuranta/yo-poiminta/:tunniste"
    {:no-doc true
     :post {:parameters {:multipart {:poiminta TempFileUpload}
                         :path {:tunniste s/Str}}
            :handler (fn [{{{:keys [poiminta]} :multipart path :path} :parameters}]
                       (response-or-404
                        (str (uraseuranta/lisaa-yo-poiminta (:tunniste path) (:tempfile poiminta) (:filename poiminta)))))}}]
   ["/uraseuranta/yo-osoitteet/:tunniste"
    {:no-doc true
     :post {:parameters {:multipart {:osoitteet TempFileUpload}
                         :path {:tunniste s/Str}}
            :handler (fn [{{{:keys [osoitteet]} :multipart path :path} :parameters}]
                       (response-or-404
                        (str (uraseuranta/lisaa-yo-osoitetiedot (:tunniste path) (:tempfile osoitteet) (:filename osoitteet)))))}}]
   ["/uraseuranta/yo-puhelinnumerot/:tunniste"
    {:no-doc true
     :post {:parameters {:multipart {:puhelinnumerot TempFileUpload}
                         :path {:tunniste s/Str}}
            :handler (fn [{{{:keys [puhelinnumerot]} :multipart path :path} :parameters}]
                       (response-or-404
                        (str (uraseuranta/lisaa-yo-puhelinnumerot (:tunniste path) (:tempfile puhelinnumerot) (:filename puhelinnumerot)))))}}]
   ["/uraseuranta/tupa-lista/:tunniste"
    {:get {:parameters {:path {:tunniste s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (let [lista (uraseuranta/hae-tupa-lista (:tunniste path))]
                        (file-download-response lista (str (:tunniste path) ".xlsx")
                                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")))}}]
   ["/eraajo/:tyyppi"
    {:post {:parameters {:path {:tyyppi s/Str}
                         :query {(s/optional-key :tyhjenna) s/Bool}}
            :handler (fn [{{:keys [path query]} :parameters}]
                       (case (:tyyppi path)
                         "automaattikyselyt" (luo-automaattikyselyt!)
                         "oiva-integraatio" (paivita-koulutustoimijoiden-tutkinnot!)
                         "paivita-organisaatiot" (organisaatiot/paivita-organisaatiot! (:organisaatiopalvelu env))
                         "paivita-koodistot" (koodistot/paivita-koodistot! (:koodistopalvelu env))
                         "luo-vertailudata" (r/luo-vertailudata! "2021-01-01" (:tyhjenna query))
                         "paivita-vertailudata" (r/paivita-vertailudata!)
                         nil)
                       "OK")}}]
   ["/viestit/laheta/:lahetyskertaid"
    {:post {:parameters {:path {:lahetyskertaid s/Str}}
            :responses {status/ok {:body s/Str}
                        status/bad-request {:body s/Str}}
            :handler (fn [{{:keys [path]} :parameters}]
                       (future
                         (try
                           (viestinta/laheta-viestit (:lahetyskertaid path))
                           (catch Exception e
                             (log/error e "Virhe viestien lähetyksessä"))))
                       (if (get-in env [:ominaisuus :massaviestien-lahetys])
                         (response-or-404 "Lähetys käynnistetty")
                         (-> "Massaviestien lähetys ei ole päällä."
                             response/bad-request)))}}]
   ["/viestit/lahetyskerta/:tunniste"
    {:get {:parameters {:path {:tunniste s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (viestinta/hae-seuraava-lahetyskerta (:tunniste path))))}}]
   ["/viestit/laheta-testaus-sahkoposti/:lahetyskertaid"
    {:post {:summary "Testisähköpostin lähetys"
            :description "Halutun lähetyskerran tunniste. Tämä lähetyskerta ei saa olla 'lahetetty'-tilassa."
            :parameters {:path {:lahetyskertaid s/Num}
                         :query {(s/optional-key :kieli) (s/enum "fi" "sv" "en")}
                         :body {:sahkoposti s/Str}}
            :responses {status/ok {:body s/Str}}
            :handler (fn [{{:keys [path body query]} :parameters}]
                       (viestinta/laheta-testisahkoposti (:lahetyskertaid path) (:sahkoposti body) (or (:kieli query) oletus-kieli)))}}]
   ["/viestit/laheta-testaus-sms/:lahetyskertaid"
    {:post {:summary "Testi-tekstiviestin lähetys"
            :description "Halutun lähetyskerran tunniste. Tämä lähetyskerta ei saa olla 'lahetetty'-tilassa."
            :parameters {:path {:lahetyskertaid s/Num}
                         :query {(s/optional-key :kieli) (s/enum "fi" "sv" "en")}
                         :body {:puhelinnumero s/Str}}
            :responses {status/ok {:body s/Str}}
            :handler (fn [{{:keys [path body query]} :parameters}]
                       (viestinta/laheta-testi-sms (:lahetyskertaid path) (:puhelinnumero body) (or (:kieli query) oletus-kieli)))}}]
   ["/move/luo-tunnukset/:tunniste"
    {:post {:parameters {:path {:tunniste s/Str}}
            :handler (fn [{{:keys [path]} :parameters}]
                       (response-or-404 (move/luo-tunnukset (:tunniste path))))}}]
   ["/move/luo-uudelleenlahetyskerta/:lahetyskertaid/viestipohjatyyppi=:viestipohjatyyppi"
    {:post {:summary "Uusintalähetyskerran luonti"
            :description "Luo vanhasta lähetyskerrasta uuden samanlaisen lähetyskerran valitulla viestipohjalla ja ottaa
        mukaan ne vastaajatunnukset joiden sähköposti on muuttunut. Ottaa nämä aiemmin lähetetyt sähköpostit syötteenä."
            :parameters {:path {:lahetyskertaid s/Num
                                :viestipohjatyyppi s/Str}
                         :body [{:tunnus s/Str :sahkoposti s/Str}]}
            :responses {status/ok {:body s/Str}}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (response-or-404 (str (move/luo-uudelleenlahetyskerta (:lahetyskertaid path) (:viestipohjatyyppi path) body))))}}]])
