(ns arvo.integraatio.koodistopalvelu
  (:require [arvo.arkisto.tutkinto :as tutkinto-arkisto]
            [arvo.arkisto.tutkintotyyppi :as tutkintotyyppi-arkisto]
            [arvo.arkisto.koulutusala :as koulutusala-arkisto]
            [arvo.arkisto.opintoala :as opintoala-arkisto]
            [clojure.set :refer [intersection difference rename-keys]]
            [oph.common.util.util :refer :all]
            [arvo.util.paivamaara-util :as pvm-util]
            [arvo.config :refer [env]]
            [clojure.tools.logging :as log]
            [clojure.java.jdbc :as jdbc]
            [arvo.db.core :refer [*db*] :as db]
            [clojure.set :as set]))

;  "koulutusalaoph2002"
(def ^:private koulutusala-koodisto "isced2011koulutusalataso1")

; "opintoalaoph2002"
(def ^:private opintoala-koodisto "isced2011koulutusalataso2")

;; Tässä nimiavaruudessa viitataan "koodi"-sanalla koodistopalvelun palauttamaan tietorakenteeseen.
;; Jos koodi on muutettu Arvon käyttämään muotoon, siihen viitataan ko. käsitteen nimellä, esim. "osatutkinto".

(defn- kieli->rank [kieli ranks]
  (case kieli
    "FI" (:fi ranks)
    "SV" (:sv ranks)
    "EN" (:en ranks)
    999))

(defn koodi->kasite
  "Muuttaa koodistopalvelun koodin ohjelmassa käytettyyn muotoon.
Koodin arvo laitetaan arvokentta-avaimen alle."
  [koodi arvokentta]
  (when koodi
    (let [metadatat (:metadata koodi)
          metadata_fi (first (sort-by #(kieli->rank (:kieli %) {:fi 1 :sv 2 :en 3}) < metadatat))
          metadata_sv (first (sort-by #(kieli->rank (:kieli %) {:fi 2 :sv 1 :en 3}) < metadatat))
          metadata_en (first (sort-by #(kieli->rank (:kieli %) {:fi 2 :sv 3 :en 1}) < metadatat))]
      {:nimi_fi (:nimi metadata_fi)
       :nimi_sv (:nimi metadata_sv)
       :nimi_en (:nimi metadata_en)
       :voimassa_alkupvm (some-> (:voimassaAlkuPvm koodi) pvm-util/parse-ymd)
       :voimassa_loppupvm (some-> (:voimassaLoppuPvm koodi) pvm-util/parse-ymd)
       :koodiUri (:koodiUri koodi)
       arvokentta (:koodiArvo koodi)})))

(defn koodi->tutkintotyyppi [koodi]
  (koodi->kasite koodi :tutkintotyyppi))

(defn koodi->tutkinto [koodi]
  (koodi->kasite koodi :tutkintotunnus))

(defn koodi->koulutusala [koodi]
  (koodi->kasite koodi :koulutusalatunnus))

(defn koodi->opintoala [koodi]
  (koodi->kasite koodi :opintoalatunnus))

(defn koodi->koodi [koodi]
  (koodi->kasite koodi :koodi_arvo))

(defn ^:private hae-koodit
  "Hakee kaikki koodit annetusta koodistosta ja asettaa koodin koodiarvon avaimeksi arvokentta"
  ([asetukset koodisto] (get-json-from-url (str (:url asetukset) koodisto "/koodi")))
  ([asetukset koodisto versio] (get-json-from-url (str (:url asetukset) koodisto "/koodi?koodistoVersio=" versio))))

(defn kuuluu-koodistoon
  "Filtteröi koodilistasta annetun koodiston koodit"
  [koodisto]
  (fn [koodi]
    (= koodisto (get-in koodi [:koodisto :koodistoUri]))))

(defn ^:private opintoala-koodi?
  [koodi]
  ((kuuluu-koodistoon opintoala-koodisto) koodi))

(defn ^:private koulutusala-koodi?
  [koodi]
  ((kuuluu-koodistoon koulutusala-koodisto) koodi))

(defn ^:private tyyppikoodi?
  [koodi]
  ((kuuluu-koodistoon "tutkintotyyppi") koodi))

(defn uusin-hyvaksytty-koodisto
  [asetukset koodisto]
  (loop [versio nil]
     (when-let [json (get-json-from-url (str (:url asetukset)
                                             koodisto
                                             (when versio (str "?koodistoVersio=" versio))))]
       (if (= "HYVAKSYTTY" (:tila json))
         (:versio json)
         (recur (dec (:versio json)))))))

(defn ^:private lisaa-opintoalaan-koulutusala
  [asetukset opintoala]
  (let [ylakoodit (get-json-from-url (str (:url asetukset) "relaatio/sisaltyy-ylakoodit/" (:koodiUri opintoala)))
        koulutusala (some-value koulutusala-koodi? ylakoodit)]
    (assoc opintoala :koulutusala (:koodiArvo koulutusala))))

(defn ^:private hae-alakoodit
  [asetukset koodi] (get-json-from-url (str (:url asetukset) "relaatio/sisaltyy-alakoodit/" (:koodiUri koodi))))

(defn lisaa-alakoodien-data
  [asetukset tutkinto]
  (let [alakoodit (hae-alakoodit asetukset tutkinto)
        opintoala (some-value opintoala-koodi? alakoodit)
        tyyppi (some-value tyyppikoodi? alakoodit)]
    (assoc tutkinto
           :opintoala (:koodiArvo opintoala)
           :tutkintotyyppi (:koodiArvo tyyppi))))

(defn hae-tutkintotyypit [asetukset]
  (map koodi->tutkintotyyppi (hae-koodit asetukset "tutkintotyyppi")))

(defn hae-tutkinnot [asetukset]
  (map koodi->tutkinto (hae-koodit asetukset "koulutus")))

(defn hae-koulutusalat
  [asetukset]
  (->> (hae-koodit asetukset koulutusala-koodisto)
    (map koodi->koulutusala)
    (map #(dissoc % :kuvaus_fi :kuvaus_sv :kuvaus_en))))

(defn hae-opintoalat
  [asetukset]
  (->> (hae-koodit asetukset opintoala-koodisto)
    (map koodi->opintoala)
    (map (partial lisaa-opintoalaan-koulutusala asetukset))
    (map #(dissoc % :kuvaus_fi :kuvaus_sv :kuvaus_en))))

; TODO pitääkö hakea kannasta?
(defn hae-kunnat [asetukset]
  (->> (hae-koodit asetukset "kunta")
       (map #(koodi->kasite % :kuntakoodi))))

(defn hae-osaamisalat [asetukset]
  (->> (hae-koodit asetukset "osaamisala")
       (map #(koodi->kasite % :osaamisalakoodi))))

(defn hae-tutkintonimikkeet [asetukset]
  (->> (hae-koodit asetukset "tutkintonimikkeet")
       (map #(koodi->kasite % :tutkintonimikekoodi))))

(defn hae-rahoitusryhmat [asetukset]
  (->> (hae-koodit asetukset "rahoitusryhma")
       (map #(koodi->kasite % :rahoitusryhmakoodi))))

(defn in? [coll elem]
  (some #(= elem %) coll))

(defn hae-muuttuneet
  "Lajittelee koodit lisättäviin ja päivitettäviin. Ei tutki löytyykö ennestään samoilla tiedoilla."
  [uudet vanhat tunniste]
  (let [muuttuneet (set/difference (into #{} uudet) (into #{} vanhat))
        vanhat-idt (map tunniste vanhat)
        lisattavat (remove #(in? vanhat-idt (tunniste %)) muuttuneet)]
    {:lisattavat    lisattavat
     :paivitettavat (set/difference muuttuneet lisattavat)}))

(defn hae-tutkintotyyppi-muutokset [asetukset]
  (let [tutkintotyypi_kentat [:tutkintotyyppi :nimi_fi :nimi_sv :nimi_en]
        vanhat (->> (tutkintotyyppi-arkisto/hae-kaikki)
                    (map #(select-keys % tutkintotyypi_kentat)))
        uudet (map #(select-keys % tutkintotyypi_kentat) (hae-tutkintotyypit asetukset))]
    (hae-muuttuneet uudet vanhat :tutkintotyyppi)))

(defn hae-tutkinto-muutokset [asetukset]
  (let [tutkinto-kentat [:nimi_fi :nimi_sv :nimi_en :voimassa_alkupvm :voimassa_loppupvm :tutkintotunnus :opintoala :tutkintotyyppi]
        vanhat (->> (tutkinto-arkisto/hae-kaikki)
                    (map #(select-keys % tutkinto-kentat)))
        uudet (->> (hae-tutkinnot asetukset)
                   (map (partial lisaa-alakoodien-data asetukset))
                   (map #(select-keys % tutkinto-kentat)))]
    (hae-muuttuneet uudet vanhat :tutkintotunnus)))

(defn hae-koulutusala-muutokset [asetukset]
  (let [koulutusala-kentat [:nimi_fi :nimi_sv :nimi_en :koulutusalatunnus]
        vanhat (->> (koulutusala-arkisto/hae-kaikki)
                    (map #(select-keys % koulutusala-kentat)))
        uudet (map #(select-keys % koulutusala-kentat) (hae-koulutusalat asetukset))]
    (hae-muuttuneet uudet vanhat :koulutusalatunnus)))

(defn hae-opintoala-muutokset [asetukset]
  (let [opintoala-kentat [:nimi_fi :nimi_sv :nimi_en :opintoalatunnus :koulutusala]
        vanhat (->> (opintoala-arkisto/hae-kaikki)
                    (map #(select-keys % opintoala-kentat)))
        uudet (map #(select-keys % opintoala-kentat) (hae-opintoalat asetukset))]
    (hae-muuttuneet uudet vanhat :opintoalatunnus)))

(defn ^:integration-api tallenna-uudet-koulutusalat! [tx koulutusalat]
  (doseq [ala koulutusalat]
    (log/info "Lisätään koulutusala " (:koulutusalatunnus ala))
    (koulutusala-arkisto/lisaa! tx ala)))

(defn ^:integration-api tallenna-muuttuneet-koulutusalat! [tx koulutusalat]
  (doseq [ala koulutusalat]
    (log/info "Päivitetään koulutusala " (:koulutusalatunnus ala))
    (koulutusala-arkisto/paivita! tx ala)))

(defn ^:integration-api tallenna-koulutusalat! [tx koulutusalat]
    (tallenna-uudet-koulutusalat! tx (:lisattavat koulutusalat))
    (tallenna-muuttuneet-koulutusalat! tx (:paivitettavat koulutusalat)))

(defn ^:integration-api tallenna-uudet-opintoalat! [tx opintoalat]
  (doseq [ala opintoalat]
    (log/info "Lisätään opintoala " (:opintoalatunnus ala))
    (opintoala-arkisto/lisaa! tx ala)))

(defn ^:integration-api tallenna-muuttuneet-opintoalat! [tx opintoalat]
  (doseq [ala opintoalat]
    (log/info "Päivitetään opintoala " (:opintoalatunnus ala))
    (opintoala-arkisto/paivita! tx ala)))

(defn ^:integration-api tallenna-opintoalat! [tx opintoalat]
  (tallenna-uudet-opintoalat! tx (filter :koulutusala (:lisattavat opintoalat)))
  (tallenna-muuttuneet-opintoalat! tx (filter :koulutusala (:paivitettavat opintoalat))))

(defn ^:integration-api tallenna-uudet-tutkinnot! [tx tutkinnot]
  (doseq [tutkinto tutkinnot]
    (log/info "Lisätään tutkinto " (:tutkintotunnus tutkinto))
    (tutkinto-arkisto/lisaa! tx tutkinto)))

(defn ^:integration-api tallenna-muuttuneet-tutkinnot! [tx tutkinnot]
  (doseq [tutkinto tutkinnot]
    (log/info "Päivitetään tutkinto " (:tutkintotunnus tutkinto))
    (tutkinto-arkisto/paivita! tx tutkinto)))

(defn logita-puutteelliset-tutkinnot [tutkinnot]
  (log/info "Uudet tutkinnot ilman opintoalaa " (map :tutkintotunnus (filter #(nil? (:opintoala %))(:lisattavat tutkinnot))))
  (log/info "Muuttuneet tutkinnot ilman opintoalaa " (map :tutkintotunnus (filter #(nil? (:opintoala %))(:paivitettavat tutkinnot)))))

(defn ^:integration-api tallenna-tutkinnot! [tx tutkinnot]
  (logita-puutteelliset-tutkinnot tutkinnot)
  (tallenna-uudet-tutkinnot! tx (:lisattavat tutkinnot))
  (tallenna-muuttuneet-tutkinnot! tx (:paivitettavat tutkinnot)))

(defn ^:integration-api tallenna-uudet-tutkintotyypit! [tx tutkintotyypit]
  (doseq [tutkintotyyppi tutkintotyypit]
    (log/info "Lisätään tutkintotyyppi" (:tutkintotyyppi tutkintotyyppi))
    (tutkintotyyppi-arkisto/lisaa! tx tutkintotyyppi)))

(defn ^:integration-api tallenna-muuttuneet-tutkintotyypit! [tx tutkintotyypit]
  (doseq [tutkintotyyppi tutkintotyypit]
    (log/info "Päivitetään tutkintotyyppi" (:tutkintotyyppi tutkintotyyppi))
    (tutkintotyyppi-arkisto/paivita! tx tutkintotyyppi)))

(defn ^:integration-api tallenna-tutkintotyypit! [tx tutkintotyypit]
    (tallenna-uudet-tutkintotyypit! tx (filter :tutkintotyyppi (:lisattavat tutkintotyypit)))
    (tallenna-muuttuneet-tutkintotyypit! tx (filter :tutkintotyyppi (:paivitettavat tutkintotyypit))))

(defn ^:integration-api tallenna-uudet-koodisto! [tx uudet-koodit koodisto-uri]
  (doseq [koodi uudet-koodit]
    (db/lisaa-koodiston-koodi! tx (assoc koodi :koodisto_uri koodisto-uri)))
  (log/info (count uudet-koodit) "uutta tallennettiin"))

(defn ^:integration-api tallenna-muuttuneet-koodisto! [tx muuttuneet-koodit koodisto-uri]
  (doseq [koodi muuttuneet-koodit]
    (db/paivita-koodiston-koodi! tx (assoc koodi :koodisto_uri koodisto-uri)))
  (log/info (count muuttuneet-koodit) "muutosta tallenttiin"))

(defn ^:integration-api tallenna-koodisto! [koodistomuutokset koodisto-uri tx]
  (tallenna-uudet-koodisto! tx (filter :koodi_arvo (:lisattavat koodistomuutokset)) koodisto-uri)
  (tallenna-muuttuneet-koodisto! tx (filter :koodi_arvo (:paivitettavat koodistomuutokset)) koodisto-uri))

(defn hae-koodisto-muutokset [koodisto-uri asetukset tx]
  (let [vanhat (db/hae-koodiston-koodit tx {:koodistouri koodisto-uri})
        uudet (map koodi->koodi (hae-koodit asetukset koodisto-uri))
        muuttuneet (hae-muuttuneet uudet vanhat :koodi_arvo)]
    (log/info (count vanhat) "vanhaa" (count uudet) "haettu")
    (log/info "lisattavia" (count (:lisattavat muuttuneet)) "paivitettavia" (count (:paivitettavat muuttuneet)))
    muuttuneet))

(defn paivita-koodisto! [asetukset koodisto-uri]
  (log/info "Päivitetään koodisto" koodisto-uri)
  (jdbc/with-db-transaction [tx *db*]
  (-> koodisto-uri
      (hae-koodisto-muutokset asetukset tx)
      (tallenna-koodisto! koodisto-uri tx))))

(defn ^:integration-api paivita-koodistot! [asetukset]
  (try
    (when (get-in env [:koodistopalvelu :hae-tutkintokoodit])
      (jdbc/with-db-transaction
       [tx *db*]
       (log/info "Aloitetaan tutkintojen päivitys koodistopalvelusta")
       (tallenna-tutkintotyypit! tx (hae-tutkintotyyppi-muutokset asetukset))
       (tallenna-koulutusalat! tx (hae-koulutusala-muutokset asetukset))
       (tallenna-opintoalat! tx (hae-opintoala-muutokset asetukset))
       (tallenna-tutkinnot! tx (hae-tutkinto-muutokset asetukset))
       (log/info "Tutkintojen päivitys koodistopalvelusta valmis")))
    (log/info "Päivitetään muut koodistot")
    (doseq [koodisto (get-in env [:koodistopalvelu :koodit])]
      (paivita-koodisto! asetukset koodisto))
    (log/info "Muiden koodistojen päivitys valmis")
    (catch org.postgresql.util.PSQLException e
      (log/error e "Tutkintojen päivitys koodistopalvelusta epäonnistui"))))
