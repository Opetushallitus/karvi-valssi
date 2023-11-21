(ns arvo.rest-api.kysymysryhma
  (:require
    [clojure.tools.logging :as log]
    [schema.core :as s]
    [schema-tools.core :as st]
    [arvo.service.kysymys :as kysymys]
    [arvo.rest-api.validate-util :as validate-util]
    [arvo.arkisto.kysymysryhma :as arkisto]
    [arvo.db.core :refer [*db*] :as db]
    [clojure.java.jdbc :as jdbc]
    [arvo.infra.kayttaja :refer [*kayttaja* yllapitaja?]]
    [oph.common.util.http-util :refer [response-or-404 validate-response]]
    [arvo.util :refer [add-index]]
    [ring.util.http-response :as response]))

(defn add-kysymykset-index [kysymykset]
  (let [index (ref 0)]
    (doall (map #(kysymys/add-kysymys-index % index) kysymykset))))

(defn lisaa-kysymykset-kysymysryhmaan! [tx kysymykset kysymysryhmaid]
  (doseq [kysymys (add-kysymykset-index kysymykset)]
    (kysymys/lisaa-kysymys! tx kysymys kysymysryhmaid)))

(defn ^:private valitse-kysymysryhman-peruskentat [kysymysryhma]
  (select-keys kysymysryhma [:nimi_fi
                              :nimi_sv
                              :nimi_en
                              :selite_fi
                              :selite_sv
                              :selite_en
                              :kuvaus_fi
                              :kuvaus_sv
                              :kuvaus_en
                              :koulutustoimija
                              :oppilaitos
                              :metatiedot]))

(defn ^:private suodata-vain-yllapitajalle [kysymysryhma kentta]
  (if (yllapitaja?)
    (true? (kentta kysymysryhma))
    false))

(defn lisaa-kysymysryhma! [kysymysryhma-data]
  (jdbc/with-db-transaction
   [tx *db*]
   (let [kysymysryhma (arkisto/lisaa-kysymysryhma! tx (merge (valitse-kysymysryhman-peruskentat kysymysryhma-data)
                                                             {:taustakysymykset (suodata-vain-yllapitajalle kysymysryhma-data :taustakysymykset)
                                                              :valtakunnallinen (suodata-vain-yllapitajalle kysymysryhma-data :valtakunnallinen)}))]
     (lisaa-kysymykset-kysymysryhmaan! tx (:kysymykset kysymysryhma-data) (:kysymysryhmaid kysymysryhma))
     (doall kysymysryhma))))

(defn- validoi-kysymysryhma [kysymysryhma]
  (when-not (arkisto/luonnos? (:kysymysryhmaid kysymysryhma))
    "kysymysryhma.ei-luonnos-tilassa"))

(defn- paikkaa-kysymysryhma! [kysymysryhma-data]
  (let [kysymysryhma (merge (arkisto/hae (:kysymysryhmaid kysymysryhma-data) false) kysymysryhma-data)]
    (arkisto/paivita! kysymysryhma)))

(defn paivita-kysymysryhma! [kysymysryhma]
  (when (arkisto/luonnos? (:kysymysryhmaid kysymysryhma))
    (let [kysymysryhma (-> kysymysryhma
                           kysymys/korjaa-eos-vastaus-sallittu
                           (assoc :valtakunnallinen (suodata-vain-yllapitajalle kysymysryhma :valtakunnallinen)
                                  :taustakysymykset (suodata-vain-yllapitajalle kysymysryhma :taustakysymykset)))
          kysymysryhmaid (:kysymysryhmaid kysymysryhma)
          kysymykset (:kysymykset kysymysryhma)]
      (jdbc/with-db-transaction
       [tx *db*]
       (arkisto/poista-kysymysryhman-kysymykset! tx kysymysryhmaid)
       (lisaa-kysymykset-kysymysryhmaan! tx kysymykset kysymysryhmaid)
       (arkisto/paivita! kysymysryhma)
       kysymysryhma))))


(defn poista-kysymysryhma! [kysymysryhmaid]
  (when (arkisto/luonnos? kysymysryhmaid)
    (jdbc/with-db-transaction
     [tx *db*]
     (arkisto/poista-kysymysryhman-kysymykset! tx kysymysryhmaid)
     (arkisto/poista! tx kysymysryhmaid))))

(s/defschema Kysymysryhma
  {(s/optional-key :nimi_fi) s/Str
   (s/optional-key :nimi_sv) s/Str
   (s/optional-key :nimi_en) s/Str
   (s/optional-key :selite_fi) s/Str
   (s/optional-key :selite_sv) s/Str
   (s/optional-key :selite_en) s/Str
   (s/optional-key :kuvaus_fi) s/Str
   (s/optional-key :kuvaus_sv) s/Str
   (s/optional-key :kuvaus_en) s/Str
   (s/optional-key :valtakunnallinen) s/Bool
   (s/optional-key :metatiedot) s/Any})

(defn reitit []
  [[""
    {:get {:kayttooikeus :katselu
           :parameters {:query (st/optional-keys {:taustakysymysryhmat s/Bool
                                                  :voimassa s/Bool})}
           :handler (fn [{{:keys [query]} :parameters}]
                      (response-or-404
                       (if (-> query :taustakysymysryhmat)
                         (arkisto/hae-taustakysymysryhmat)
                         (arkisto/hae-kysymysryhmat (:aktiivinen-koulutustoimija *kayttaja*) (:aktiiviset-oppilaitokset *kayttaja*) (-> query :voimassa)))))}
     :post {:kayttooikeus :kysymysryhma
            :parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [kysymysryhma-data (assoc body :koulutustoimija (:aktiivinen-koulutustoimija *kayttaja*))]
                         (validate-response lisaa-kysymysryhma! [validate-util/validoi-oppilaitos] kysymysryhma-data)))}}]
   ["/asteikot"
    {:conflicting true
     :get {:kayttooikeus :katselu
           :handler (fn [req]
                      (response-or-404 (arkisto/hae-asteikot (:aktiivinen-koulutustoimija *kayttaja*))))}
     :post {:kayttooikeus :kysymysryhma
            :parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [tallennettava-asteikko (assoc body :koulutustoimija (:aktiivinen-koulutustoimija *kayttaja*))]
                         (response-or-404 (arkisto/tallenna-asteikko tallennettava-asteikko))))}}]
   ["/:kysymysryhmaid"
    {:conflicting true
     :get {:kayttooikeus [:katselu :kysymysryhmaid]
           :parameters {:path {:kysymysryhmaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/hae (-> path :kysymysryhmaid))))}
     :put {:kayttooikeus [:kysymysryhma :kysymysryhmaid]
           :parameters {:path {:kysymysryhmaid s/Int}
                        :body s/Any}
           :handler (fn [{{:keys [path body]} :parameters}]
                      (response-or-404 (paivita-kysymysryhma! (assoc body :kysymysryhmaid (-> path :kysymysryhmaid)))))}
     :patch {:kayttooikeus [:kysymysryhma :kysymysryhmaid]
             :parameters {:path {:kysymysryhmaid s/Int}
                          :body Kysymysryhma}
             :handler (fn [{{:keys [path body]} :parameters}]
                        (validate-response paikkaa-kysymysryhma! [validoi-kysymysryhma] (assoc body :kysymysryhmaid (-> path :kysymysryhmaid))))}
     :delete {:kayttooikeus [:kysymysryhma :kysymysryhmaid]
              :parameters {:path {:kysymysryhmaid s/Int}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (poista-kysymysryhma! (-> path :kysymysryhmaid))
                         (response/no-content))}}]
   ;; Muuten sama kuin GET /:kysymysryhmaid, mutta haettaessa vuoden 2015 taustakysymysryhmiä yhdistää hakeutumis- ja suoritusvaiheen kysymysryhmät
   ;  Tämä toiminto kommentoitu pois joten tarkalleen sama kuin yllä.
   ["/taustakysymysryhma/:kysymysryhmaid"
    {:conflicting true
     :get {:kayttooikeus [:katselu :kysymysryhmaid]
           :parameters {:path {:kysymysryhmaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/hae-taustakysymysryhma (-> path :kysymysryhmaid))))}}]
   ["/:kysymysryhmaid/julkaise"
    {:conflicting true
     :put {:kayttooikeus [:kysymysryhma :kysymysryhmaid]
           :parameters {:path {:kysymysryhmaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (if (pos? (arkisto/laske-kysymykset (-> path :kysymysryhmaid)))
                        (response-or-404 (arkisto/julkaise! (-> path :kysymysryhmaid)))
                        (response/forbidden)))}}]
   ["/:kysymysryhmaid/palauta"
    {:conflicting true
     :put {:kayttooikeus [:kysymysryhma :kysymysryhmaid]
           :parameters {:path {:kysymysryhmaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (if (and
                           (zero? (arkisto/laske-kyselyt (-> path :kysymysryhmaid)))
                           (zero? (arkisto/laske-kyselypohjat (-> path :kysymysryhmaid))))
                        (response-or-404 (arkisto/palauta-luonnokseksi! (-> path :kysymysryhmaid)))
                        (response/forbidden)))}}]
   ["/:kysymysryhmaid/sulje"
    {:conflicting true
     :put {:kayttooikeus [:kysymysryhma :kysymysryhmaid]
           :parameters {:path {:kysymysryhmaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/sulje! (-> path :kysymysryhmaid))))}}]
   ["/:kysymysryhmaid/esikatselu"
    {:conflicting true
     :get {:kayttooikeus [:katselu :kysymysryhmaid]
           :parameters {:path {:kysymysryhmaid s/Int}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (response-or-404 (arkisto/hae-esikatselulle (-> path :kysymysryhmaid))))}}]])
