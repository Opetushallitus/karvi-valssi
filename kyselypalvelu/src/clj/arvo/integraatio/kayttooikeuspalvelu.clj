(ns arvo.integraatio.kayttooikeuspalvelu
  (:require [clojure.tools.logging :as log]
            [oph.common.util.cas :as cas]
            [cheshire.core :as cheshire]
            [clojure.walk :refer [keywordize-keys]]
            [arvo.config :refer [env]]
            [oph.common.util.util :refer [get-json-from-url]]))

(defn palvelukutsu [palvelu url options]
  (-> (cas/get-with-cas-auth palvelu url options)
      :body
      cheshire/parse-string
      keywordize-keys))

(defn postpalvelukutsu [palvelu url options]
  (-> (cas/post-with-cas-auth palvelu url options)
      :body
      cheshire/parse-string
      keywordize-keys))

(defn kayttoikeudet [kayttaja]
  (for [organisaatio (:organisaatiot kayttaja)]
   (let [oikeudet (->> (:kayttooikeudet organisaatio)
                      (filter #(= (:palvelu %) (-> env :kayttooikeuspalvelu :palvelu)))
                      (map #(merge % {:organisaatioOid (:organisaatioOid organisaatio)})))]
     oikeudet)))

(defn kayttaja [uid]
  (log/info "Haetaan käyttäjän" uid "tiedot Opintopolusta")
  (let [kayttooikeus-url (str (-> env :kayttooikeuspalvelu :url) "/kayttooikeus/kayttaja")
        oppijanumerorekisteri-url (str (-> env :oppijanumerorekisteri :url) "/henkilo/")
        kayttaja (first (palvelukutsu :kayttooikeuspalvelu kayttooikeus-url {:query-params {"username" uid}}))
        oikeudet (->> (kayttoikeudet kayttaja)
                      flatten)
        tiedot (when kayttaja (palvelukutsu :oppijanumerorekisteri (str oppijanumerorekisteri-url (:oidHenkilo kayttaja)) {}))]
    (log/info "Saatiin käyttäjälle" uid "oikeudet" oikeudet)
    {:oid      (:oidHenkilo kayttaja)
     :etunimi  (or (:kutsumanimi tiedot) (:etunimet tiedot))
     :sukunimi (:sukunimi tiedot)
     :uid      uid
     :voimassa ((complement empty?) oikeudet)
     :oikeudet oikeudet}))

(defn kaikki-oidit [oid]
  (let [oppijanumerorekisteri-url (format "%s/s2s/duplicateHenkilos" (-> env :oppijanumerorekisteri :url))
        vastaus (postpalvelukutsu :oppijanumerorekisteri oppijanumerorekisteri-url {:body (format "{\"henkiloOids\": [\"%s\"]}" oid) :content-type :json})
        oidit (->> vastaus
                   (mapcat vals)
                   distinct)]
;    Normaali tapaus on, että henkilöllä ei ole duplikaatteja
    (if (empty? oidit)
      (list oid)
      oidit)))
