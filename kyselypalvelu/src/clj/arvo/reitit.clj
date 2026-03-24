(ns arvo.reitit
  (:require [clojure.pprint :refer [pprint]]
            [cheshire.core :as cheshire]
            [ring.util.http-response :as response]
            [reitit.swagger :as swagger]
            [reitit.swagger-ui :as swagger-ui]
            [clojure.tools.logging :as log]
            [stencil.core :as s]
            [oph.common.infra.csrf-token :refer [aseta-csrf-token wrap-tarkasta-csrf-token]]
            [arvo.basic-auth :refer [wrap-basic-authentication]]
            arvo.rest-api.i18n
            arvo.rest-api.healthcheck
            arvo.rest-api.kysely
            arvo.rest-api.kyselykerta
            arvo.rest-api.kyselypohja
            arvo.rest-api.kysymys
            arvo.rest-api.kysymysryhma
            arvo.rest-api.ohje
            arvo.rest-api.oppilaitos
            arvo.rest-api.toimipiste
            arvo.rest-api.raportti.kysely
            arvo.rest_api.js-log
            arvo.rest-api.vastaajatunnus
            arvo.rest-api.automaattitunnus
            arvo.rest-api.yleiset
            arvo.rest-api.henkilo
            arvo.rest-api.uraseuranta
            arvo.rest-api.koodisto
            arvo.rest-api.kayttaja
            arvo.rest-api.tutkinto
            arvo.rest-api.tutkintotyyppi
            arvo.rest-api.koulutustoimija
            arvo.rest-api.tiedote
            arvo.rest-api.export
            arvo.rest-api.move
            arvo.rest-api.admin
            arvo.rest-api.raportointi
            arvo.rest-api.yllapitaja
            [arvo.auth.api :refer [wrap-authentication]]
            [arvo.infra.kayttaja :refer [*kayttaja*]]
            [arvo.util :refer [service-path]]
            [arvo.layout :as layout]
            [oph.common.util.cas :as cas]
            [ring.middleware.format :refer [wrap-restful-format]]
            [arvo.config :refer [project-version]]
            [cheshire.core :as json]
            [schema.core :as sc]))

(defn wrap-formats [handler]
  (let [wrapped (wrap-restful-format
                  handler
                  {:formats [:json-kw :transit-json :transit-msgpack]})]
    (fn [request]
      ;; disable wrap-formats for websockets
      ;; since they're not compatible with this middleware
      ((if (:websocket? request) handler wrapped) request))))

(defn ui-route [asetukset]
  {:status 200
   :headers {"Content-type" "text/html; charset=utf-8"
             "Set-cookie" (aseta-csrf-token (service-path asetukset))}
;   :body (s/render-file "public/app/index.html"
;                        (merge {:base-url (-> asetukset :server :base-url)
;                                :vastaus-base-url (-> asetukset :vastaus-base-url)
;                                :current-user (:nimi *kayttaja*)
;                                :project-version @project-version
;                                :development-mode (pr-str (:development-mode asetukset))
;                                :ominaisuus (cheshire/generate-string (:ominaisuus asetukset))}
;                               (when-let [cas-url (cas/cas-login-url)]
;                                 {:logout-url (str cas-url "/logout")})))
   :body "<html><head></head><body><h1>ARVO</h1></body></html>"
   })

(defn reitit [asetukset]
  (let [no-doc? (get-in asetukset [:ominaisuus :no-show-all-swagger])
        base-path (get-in asetukset [:server :base-path])]
    [base-path {:no-doc no-doc?}
     ["" {:no-doc true}
      [["/" {:get {:handler (fn [req] (ui-route asetukset))}
             ;For logout from cas
             :post {:handler (fn [req] (response/ok))}}]
       ["/new" {:get {:handler (fn [req] (layout/render "home.html"))}}]]]
     ["" {:no-doc true}
      ["/swagger.json" {:get {:swagger {:info {:title "Arvo API"
                                               :version "1.0.0"
                                               :description "Arvon rajapinnat.
                         Glossary: https://wiki.eduuni.fi/display/CscArvo/Glossary"}
                                        :basePath base-path
                                        :tags (concat [{:name "export" :description "Kyselytietojen siirtorajapinta"}
                                                       {:name "vastauslinkki" :description "Ammatillisen tiedonkeruun vastauslinkkien hallinta"}
                                                       {:name "tyoelamapalaute" :description "Työelämäpalautteen vastauslinkkien hallinta"}]
                                                      (when-not no-doc? [
                                                                      {:name "admin" :description "Ylläpidon tekniset rajapinnat"}
                                                                      {:name "ui" :description "Käyttöliittymän rajapinnat"}
                                                                      {:name "sisainen" :description "Järjestelmän sisäiset integraatiot"}]))}
                              :handler (swagger/create-swagger-handler)}}]
      ["/api-docs/*" {:get (swagger-ui/create-swagger-ui-handler {:url (str base-path "/swagger.json")})}]]
     ["/api"
      [["/i18n" {:swagger {:tags ["ui"]}} (arvo.rest-api.i18n/reitit)]
       ["/healthcheck" {:swagger {:tags ["sisainen"]}} (arvo.rest-api.healthcheck/reitit)]
       ["/csv" {:swagger {:tags ["ui"]}} (arvo.rest-api.raportti.kysely/csv)]
;;       ["/tiedonkeruu" (arvo.rest-api.yllapitaja/tiedonkeruu)]
       ["/uraseuranta" (arvo.rest-api.uraseuranta/uraseuranta-routes)]
       ["/yllapito" {:swagger {:tags ["ui"]}} (arvo.rest-api.yllapitaja/yllapitaja-routes)]
       ["/kyselypohja" {:swagger {:tags ["ui"]}} (arvo.rest-api.kyselypohja/tiedosto-reitit)]]]
     ["/api" {:middleware [wrap-tarkasta-csrf-token]
              :swagger {:tags ["ui"]}}
      [["/jslog" (arvo.rest_api.js-log/reitit)]
       ["/kyselykerta" (arvo.rest-api.kyselykerta/reitit)]
       ["/kyselypohja" (arvo.rest-api.kyselypohja/reitit)]
       ["/ohje" (arvo.rest-api.ohje/reitit)]
       ["/oppilaitos" (arvo.rest-api.oppilaitos/reitit)]
       ["/toimipiste" (arvo.rest-api.toimipiste/reitit)]
       ["/kysely" (arvo.rest-api.kysely/reitit)]
       ["/kysymysryhma" (arvo.rest-api.kysymysryhma/reitit)]
       ["/kysymys" (arvo.rest-api.kysymys/reitit)]
       ["/vastaajatunnus" (arvo.rest-api.vastaajatunnus/reitit)]
       ["/kayttaja" (arvo.rest-api.kayttaja/reitit)]
       ["/tutkinto" (arvo.rest-api.tutkinto/reitit)]
       ["/tutkintotyyppi" (arvo.rest-api.tutkintotyyppi/reitit)]
       ["/koulutustoimija" (arvo.rest-api.koulutustoimija/reitit)]
       ["/tiedote" (arvo.rest-api.tiedote/reitit)]
       ["/raportointi" (arvo.rest-api.raportointi/reitit)]
;;      ["/arvoapi" (arvo.rest-api.kayttaja/api-tunnukset)]
      ]]
     ["/api" {:middleware [#(wrap-authentication :admin %)]}
      [["/public/move" {:swagger {:tags ["admin"]}} (arvo.rest-api.move/reitit)]
       ["/admin" {:swagger {:tags ["admin"]}} (arvo.rest-api.admin/admin-routes)]]]
     ["/api/public" {:middleware [#(wrap-authentication :kyselyynohjaus %)]
                     :swagger {:tags ["sisainen"]}}
      [["/koodisto" (arvo.rest-api.koodisto/reitit)]
       ["/luovastaajatunnus" (arvo.rest-api.automaattitunnus/kyselyynohjaus-v1)]
       ["/henkilo" (arvo.rest-api.henkilo/hae-kaikki-oidit)]]]
     ["/api" {:middleware [#(wrap-authentication :export %)]
              :swagger {:tags ["export"]}
              :no-doc false}
      ["/export/v1" (arvo.rest-api.export/v1)]]
     ["/api" {:middleware [#(wrap-authentication :ehoks_tunnukset %)]
              :no-doc false}
      [["/vastauslinkki/v1" {:swagger {:tags ["vastauslinkki"]}} (arvo.rest-api.automaattitunnus/ehoks-v1)]
       ["/tyoelamapalaute/v1" {:swagger {:tags ["tyoelamapalaute"]}} (arvo.rest-api.automaattitunnus/tyoelamapalaute-v1)]]]
     ["/api" {:middleware [#(wrap-authentication :yleinen %)]}
      ["/yleinen/v1" {:swagger {:tags ["sisainen"]}} (arvo.rest-api.yleiset/yleiset-v1)]]]))
