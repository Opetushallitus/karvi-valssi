(ns arvo.rest-api.kysely
  (:require
    [schema.core :as s]
    [arvo.arkisto.kysely :as arkisto]
    [ring.util.http-response :as response]
    [arvo.service.kysely :as service]
    [arvo.arkisto.kyselykerta :as kyselykerta-arkisto]
    [arvo.arkisto.kysymysryhma :as kysymysryhma-arkisto]
    [arvo.rest-api.validate-util :as validate-util]
    [arvo.infra.kayttaja :refer [*kayttaja* yllapitaja?]]
    [arvo.util :refer [add-index]]
    [clojure.tools.logging :as log]
    [oph.common.util.http-util :refer [response-or-404 parse-iso-date validate-response file-download-response]]
    [oph.common.util.util :refer [map-by paivita-arvot]]))

(defn lisakysymysten-lukumaara
  [kysymysryhmat]
  (->> kysymysryhmat
       (remove :valtakunnallinen)
       (mapcat :kysymykset)
       (remove :poistettu)
       count))

(def ^:const max-kysymyksia 140)

(defn valmistele-luonnos-paivitys [kysely]
  (arkisto/paivita-kysely! kysely))

(defn validoi-vain-omia-organisaatioita [kysely]
  (let [loytyvat-pakolliset-kysymysryhmaidt (map :kysymysryhmaid (arkisto/get-kyselyn-pakolliset-kysymysryhmaidt (:kyselyid kysely)))
        kyselyn-kysymysryhmaidt (set (map :kysymysryhmaid (:kysymysryhmat kysely)))]
    (log/info loytyvat-pakolliset-kysymysryhmaidt)
    (log/info kyselyn-kysymysryhmaidt)
    (assert (every? kyselyn-kysymysryhmaidt loytyvat-pakolliset-kysymysryhmaidt))))

(defn valmistele-julkaistu-paivitys [kysely]
  (assert (= "julkaistu" (:tila kysely)))
  (validoi-vain-omia-organisaatioita kysely)
  (valmistele-luonnos-paivitys kysely))

(defn paivita-kysely!
  [kysely]
  (assert (not (> (lisakysymysten-lukumaara (:kysymysryhmat kysely)) max-kysymyksia)))
  (if (= "luonnos" (:tila kysely))
    (valmistele-luonnos-paivitys kysely)
    (valmistele-julkaistu-paivitys kysely)))

(defn valid-url? "jäljittelee angular-puolen äärisimppeliä validointia"
  [url]
  (let [cnt (count url)]
    (or (= cnt 0) (and (<= cnt 2000) (not (nil? (re-matches #"^http(s?):\/\/(.*)$", url)))))))

(s/defschema Kysymysryhma
  {:kysymysryhmaid s/Num})

(s/defschema Kyselykerta
  {:nimi s/Str
   :voimassa_alkupvm java.time.LocalDate
   :voimassa_loppupvm (s/maybe java.time.LocalDate)})

(s/defschema Kysely
  {(s/optional-key :oppilaitos) s/Str
   :tyyppi s/Str
   (s/optional-key :tila) (s/enum "luonnos" "julkaistu")
   (s/optional-key :kysymysryhmat) [Kysymysryhma]
   (s/optional-key :kyselykerrat) [Kyselykerta]
   :voimassa_alkupvm java.time.LocalDate
   :voimassa_loppupvm (s/maybe java.time.LocalDate)
   (s/optional-key :nimi_fi) s/Str
   (s/optional-key :nimi_sv) s/Str
   (s/optional-key :nimi_en) s/Str
   (s/optional-key :selite_fi) s/Str
   (s/optional-key :selite_sv) s/Str
   (s/optional-key :selite_en) s/Str
   (s/optional-key :kyselypohjaid) s/Num
   (s/optional-key :metatiedot) s/Any
   (s/optional-key :uudelleenohjaus_url) s/Str})

(s/defschema Kyselyt
  {:kyselyt [Kysely]})

(defn reitit []
  [["/"
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (arkisto/hae-kaikki (:aktiivinen-koulutustoimija *kayttaja*) (:aktiiviset-oppilaitokset *kayttaja*))))}
     :post {:kayttooikeus :kysely
            :parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [kysely (assoc (paivita-arvot body
                                                          [:voimassa_alkupvm :voimassa_loppupvm]
                                                          parse-iso-date)
                                           :tyyppi (-> body :tyyppi)
                                           :tila "luonnos"
                                           :koulutustoimija (:aktiivinen-koulutustoimija *kayttaja*))]
                         (validate-response arkisto/lisaa! [arkisto/validoi-lisaa! validate-util/validoi-oppilaitos] kysely)))}}]
   ["/massasyotto"
    {:conflicting true
     :post {:kayttooikeus :kysely
            :parameters {:body Kyselyt}
            :responses {200 {:body [{:kyselyid s/Int}]}}
            :handler (fn [{{:keys [body]} :parameters}]
                       (validate-response service/lisaa-massana [validate-util/validoi-koulutustoimijan-oppilaitokset service/validoi-lisaa-massana] (-> body :kyselyt) (:aktiivinen-koulutustoimija *kayttaja*)))}}]
   ["/kyselytyypit"
    {:conflicting true
     :get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (arkisto/hae-kyselytyypit)))}}]
   ["/:kyselyid"
    {:conflicting true
     :get {:kayttooikeus [:katselu :kyselyid]
           :parameters {:path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (when-let [kysely (arkisto/hae (-> path :kyselyid))]
                                         (assoc kysely :kysymysryhmat (kysymysryhma-arkisto/hae-kyselysta (-> path :kyselyid))))))}
     :post {:kayttooikeus [:kysely :kyselyid]
            :parameters {:path {:kyselyid s/Int}
                         :body s/Any}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (let [kysely (assoc (paivita-arvot (assoc body :kyselyid (-> path :kyselyid))
                                                          [:voimassa_alkupvm :voimassa_loppupvm]
                                                          parse-iso-date)
                                           :tyyppi (-> body :tyyppi))]
                         (response-or-404 (format "%s" (paivita-kysely! kysely)))))}
     :delete {:kayttooikeus [:kysely :kyselyid]
              :parameters {:path {:kyselyid s/Int}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (if (arkisto/kysely-poistettavissa? (-> path :kyselyid))
                           (do
                             (arkisto/poista-kysely! (-> path :kyselyid))
                             (response/no-content))
                           (response/forbidden)))}}]
   ["/:kyselyid/vastaustunnustiedot"
    {:conflicting true
     :get {:kayttooikeus [:katselu :kyselyid]
           :parameters {:path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (kyselykerta-arkisto/hae-kyselyn-oppilaitokset (-> path :kyselyid))))}}]
   ["/julkaise/:kyselyid"
    {:conflicting true
     :put {:kayttooikeus [:kysely :kyselyid]
           :parameters {:path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (if (> (arkisto/laske-kysymysryhmat (-> path :kyselyid)) 0)
                        (response-or-404 (arkisto/julkaise-kysely! (-> path :kyselyid)))
                        (response/forbidden)))}}]
   ["/sulje/:kyselyid"
    {:conflicting true
     :put {:kayttooikeus [:kysely :kyselyid]
           :parameters {:path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/sulje-kysely! (-> path :kyselyid))))}}]
   ["/palauta/:kyselyid"
    {:conflicting true
     :put {:kayttooikeus [:kysely :kyselyid]
           :parameters {:path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/julkaise-kysely! (-> path :kyselyid))))}}]
   ["/palauta-luonnokseksi/:kyselyid"
    {:conflicting true
     :put {:kayttooikeus [:kysely :kyselyid]
           :parameters {:path {:kyselyid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (if (= (arkisto/laske-kyselykerrat (-> path :kyselyid)) 0)
                        (response-or-404 (arkisto/palauta-luonnokseksi! (-> path :kyselyid)))
                        (response/forbidden)))}}]])
