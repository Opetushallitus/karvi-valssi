(ns arvo.rest-api.kyselypohja
  (:require [schema.core :as s]
            [clojure.tools.logging :as log]
            [arvo.arkisto.kyselypohja :as arkisto]
            [ring.util.http-response :as response]
            [arvo.arkisto.kysymysryhma :as kysymysryhma-arkisto]
            [arvo.rest-api.validate-util :as validate-util]
            [arvo.infra.kayttaja :refer [*kayttaja* yllapitaja?]]
            [oph.common.util.http-util :refer [parse-iso-date response-or-404 file-download-response validate-response]]
            [oph.common.util.util :refer [paivita-arvot]]
            [cheshire.core :as cheshire]
            [arvo.rest-api.kysymysryhma :as kysymysryhma]
            [arvo.db.core :refer [*db*] :as db]
            [clojure.java.jdbc :as jdbc]))

(defn reitit []
  [[""
    {:get {:kayttooikeus :katselu
           :parameters {:query {(s/optional-key :voimassa) s/Bool}}
           :handler (fn [{{:keys [query]} :parameters}]
                      (response-or-404 (arkisto/hae-kyselypohjat (:aktiivinen-koulutustoimija *kayttaja*) (:aktiiviset-oppilaitokset *kayttaja*) (-> query :voimassa))))}
     :post {:kayttooikeus :kyselypohja
            :parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [kyselypohja (paivita-arvot body [:voimassa_alkupvm :voimassa_loppupvm] parse-iso-date)
                             valtakunnallinen (and (yllapitaja?) (true? (:valtakunnallinen kyselypohja)))]
                         (validate-response arkisto/luo-kyselypohja! [validate-util/validoi-oppilaitos]
                                            (assoc kyselypohja
                                                   :koulutustoimija (:aktiivinen-koulutustoimija *kayttaja*)
                                                   :valtakunnallinen valtakunnallinen))))}}]
   ["/:kyselypohjaid"
    {:conflicting true  ;/api/kyselypohja/lisaa-tiedostosta
     :get {:kayttooikeus [:katselu :kyselypohjaid]
           :parameters {:path {:kyselypohjaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (let [kyselypohja (arkisto/hae-kyselypohja (-> path :kyselypohjaid))
                            kysymysryhmat (kysymysryhma-arkisto/hae-kyselypohjasta (-> path :kyselypohjaid))]
                        (when kyselypohja
                          (response-or-404 (assoc kyselypohja :kysymysryhmat kysymysryhmat)))))}
     :put {:kayttooikeus [:kyselypohja :kyselypohjaid]
           :parameters {:path {:kyselypohjaid s/Int}
                        :body s/Any}
           :handler (fn [{{:keys [path body]} :parameters}]
                      (let [kyselypohja (paivita-arvot body [:voimassa_alkupvm :voimassa_loppupvm] parse-iso-date)
                            valtakunnallinen (and (yllapitaja?) (true? (:valtakunnallinen kyselypohja)))]
                        (response-or-404 (arkisto/tallenna-kyselypohja! (-> path :kyselypohjaid) (assoc kyselypohja :valtakunnallinen valtakunnallinen)))))}
     :delete {:kayttooikeus [:kyselypohja :kyselypohjaid]
              :parameters {:path {:kyselypohjaid s/Int}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (arkisto/poista-kyselypohja! (-> path :kyselypohjaid))
                         (response/no-content))}}]
   ["/:kyselypohjaid/julkaise"
    {:put {:kayttooikeus [:kyselypohja :kyselypohjaid]
           :parameters {:path {:kyselypohjaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (validate-response arkisto/julkaise-kyselypohja! [arkisto/validoi-kyselypohja-kysymysryhmat-julkaistu] (-> path :kyselypohjaid)))}}]
   ["/:kyselypohjaid/palauta"
    {:put {:kayttooikeus [:kyselypohja :kyselypohjaid]
           :parameters {:path {:kyselypohjaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/palauta-kyselypohja-luonnokseksi! (-> path :kyselypohjaid))))}}]
   ["/:kyselypohjaid/sulje"
    {:put {:kayttooikeus [:kyselypohja :kyselypohjaid]
           :parameters {:path {:kyselypohjaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/sulje-kyselypohja! (-> path :kyselypohjaid))))}}]
   ["/:kyselypohjaid/kysymysryhmat"
    {:get {:kayttooikeus [:katselu :kyselypohjaid]
           :parameters {:path {:kyselypohjaid s/Int}}
           :handler (fn [{{:keys [path body]} :parameters}]
                      (response-or-404 (kysymysryhma-arkisto/hae-kyselypohjasta (-> path :kyselypohjaid))))}}]])

(defn- validoi-kyselypohjan-kysymysryhmat [kyselypohja]
  (let [kysymysryhmat (:kysymysryhmat kyselypohja)]
    (map validate-util/validoi-oppilaitos kysymysryhmat)))

(defn- lisaa-kyselypohja-ja-kysymysryhmat [kyselypohja]
  (let [kysymysryhmat (doall (map kysymysryhma/lisaa-kysymysryhma! (:kysymysryhmat kyselypohja)))
        tallennettu-pohja (arkisto/luo-kyselypohja! kyselypohja)
        kyselypohjaid (:kyselypohjaid tallennettu-pohja)
        kysymysryhmaidt (map :kysymysryhmaid kysymysryhmat)]
    (arkisto/tallenna-kyselypohjan-kysymysryhmat! nil kyselypohjaid kysymysryhmat)
    (doseq [kysymysryhmaid kysymysryhmaidt]
      (kysymysryhma-arkisto/julkaise! kysymysryhmaid))
    (assoc tallennettu-pohja :kysymysryhmat kysymysryhmat)))

(defn tiedosto-reitit []
  [["/:kyselypohjaid/lataa"
    {:get {:kayttooikeus [:kyselypohja :kyselypohjaid]
           :parameters {:path {:kyselypohjaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (let [id (:kyselypohjaid path)
                            kyselypohja (arkisto/hae-kyselypohja id)
                            kysymysryhmat (kysymysryhma-arkisto/hae-kyselypohjaan-kuuluvat id)
                            filename (str "Kyselypohja_"(:kyselypohjaid kyselypohja)".json")
                            data (-> kyselypohja
                                     (assoc :kysymysryhmat kysymysryhmat)
                                     (dissoc :luotuaika :muutettuaika :luotu_kayttaja :muutettu_kayttaja :voimassa_alkupvm :voimassa_loppupvm)
                                     (cheshire/generate-string))]
                        (file-download-response data filename "application/json" {:charset "UTF-8"})))}}]
   ["/lisaa-tiedostosta"
    {:conflicting true  ; /api/kyselypohja/ /api/kyselypohja/:kyselypohjaid
     :post {:kayttooikeus :kyselypohja
            :parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [kysymysryhmat (:kysymysryhmat body)
                             kyselypohja (assoc body
                                                :koulutustoimija (:aktiivinen-koulutustoimija *kayttaja*)
                                                :kysymysryhmat (map #(assoc % :koulutustoimija (:aktiivinen-koulutustoimija *kayttaja*)) kysymysryhmat))]
                         (validate-response lisaa-kyselypohja-ja-kysymysryhmat [validate-util/validoi-oppilaitos validoi-kyselypohjan-kysymysryhmat] kyselypohja)))}}]])
