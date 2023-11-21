(ns arvo.arkisto.tutkinto
  (:require
    [arvo.util.paivamaara-util :as pvm-util]
    [clojure.tools.logging :as log]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [arvo.db.core :refer [*db*] :as db]))

(def kyselytyyppi-tutkintotyypit {"avop" ["06" "07" "12"]
                                  "yo-uraseuranta" ["06" "07" "12" "13" "14" "15" "16"]
                                  "kandipalaute" ["13" "14" "15" "16"]})


(def opintoala-koulutusala-defaults
  {:opintoala_nimi_fi "Ei opintoalaa" :koulutusala_nimi_fi "Ei koulutusalaa"
   :opintoala_nimi_sv "Studieområde saknas" :koulutusala_nimi_sv "Utbildningsområde saknas"
   :opintoala_nimi_en "Missing field of study" :koulutusala_nimi_en "Missing field of education"})

(defn tutkinto-voimassa? [tutkinto]
  (let [alkupvm (:voimassa_alkupvm tutkinto)
        loppupvm (:voimassa_loppupvm tutkinto)
        siirtymaajan-loppupvm (:siirtymaajan_loppupvm tutkinto)]
    (and (or (nil? alkupvm)
             (pvm-util/pvm-tanaan-tai-menneisyydessa? alkupvm))
         (or (nil? loppupvm)
             (pvm-util/pvm-tanaan-tai-tulevaisuudessa? loppupvm)
             (and siirtymaajan-loppupvm
                  (pvm-util/pvm-tanaan-tai-tulevaisuudessa? siirtymaajan-loppupvm))))))

(defn ^:integration-api lisaa!
  ([tutkinto]
   (db/lisaa-tutkinto! tutkinto))
  ([tx tutkinto]
   (db/lisaa-tutkinto! tx tutkinto)))

(defn ^:integration-api paivita!
  ([tutkinto]
   (db/paivita-tutkinto! tutkinto))
  ([tx tutkinto]
   (db/paivita-tutkinto! tx tutkinto)))

(defn hae-kaikki []
  (db/hae-tutkinnot))

(defn hae [tutkintotunnus]
  (db/hae-tutkinto {:tutkintotunnus tutkintotunnus}))

(defn fix-opintoala [tutkinto]
  (if (nil? (:opintoala tutkinto))
      (merge tutkinto opintoala-koulutusala-defaults)
      tutkinto))

(defn hae-koulutustoimijan-tutkinnot [koulutustoimija kyselytyyppi]
  (let [tutkintotyypit (if kyselytyyppi
                         (get kyselytyyppi-tutkintotyypit kyselytyyppi)
                         (map :tutkintotyyppi (db/hae-kayttajan-tutkintotyypit {:koulutustoimija koulutustoimija})))]
    (->> (db/hae-koulutustoimijan-tutkinnot (merge {:koulutustoimija koulutustoimija}
                                                   (when (not-empty tutkintotyypit) {:tutkintotyypit tutkintotyypit})))
         (map fix-opintoala))))

(defn hae-koulutustoimijan-voimassaolevat-tutkinnot [oid kyselytyyppi]
  (filter tutkinto-voimassa? (hae-koulutustoimijan-tutkinnot oid kyselytyyppi)))

(defn hae-kyselytyypin-tutkinnot [kyselytyyppi]
  (let [tutkintotyypit (-> kyselytyyppi-tutkintotyypit
                           (dissoc kyselytyyppi)
                           vals
                           flatten)
        tutkinnot (db/hae-koulutustoimijan-kaikki-tutkinnot {:tutkintotyypit tutkintotyypit})]
    (if (= "ammatillisen-opiskelijapalaute"' kyselytyyppi) ;filtteröidään väliaikaisena ratkaisuna väärän alkuiset tutkinnot joilla ei ole opintoalaa tai tutkintotyyppiä
      (filter #(re-matches #"^[1234590]\w+"(:tutkintotunnus %)) tutkinnot)
      tutkinnot)))

(defn hae-tutkinnon-jarjestajat [tutkintotunnus]
  (db/hae-tutkinnon-jarjestajat {:tutkintotunnus tutkintotunnus}))

(defn hae-tutkinnon-osat []
  (db/hae-koodiston-koodit {:koodistouri "tutkinnonosat"}))

(defn tutkinnot-hierarkiaksi
  [tutkinnot]
  (let [opintoalatMap (group-by #(select-keys % [:opintoalatunnus :opintoala_nimi_fi :opintoala_nimi_sv :opintoala_nimi_en :koulutusalatunnus :koulutusala_nimi_fi :koulutusala_nimi_sv :koulutusala_nimi_en]) tutkinnot)
        opintoalat (for [[opintoala tutkinnot] opintoalatMap]
                     (assoc opintoala :tutkinnot (sort-by :tutkintotunnus (map #(select-keys % [:tutkintotunnus :nimi_fi :nimi_sv :nimi_en]) tutkinnot))))
        koulutusalatMap (group-by #(select-keys % [:koulutusalatunnus :koulutusala_nimi_fi :koulutusala_nimi_sv :koulutusala_nimi_en]) opintoalat)
        koulutusalat (for [[koulutusala opintoalat] koulutusalatMap]
                       (assoc koulutusala :opintoalat (sort-by :opintoalatunnus (map #(select-keys % [:opintoalatunnus :opintoala_nimi_fi :opintoala_nimi_sv :opintoala_nimi_en :tutkinnot]) opintoalat))))]
    (sort-by :koulutusalatunnus koulutusalat)))

(defn- hae-tutkinnot []
  (hae-koulutustoimijan-tutkinnot
    (:aktiivinen-koulutustoimija *kayttaja*) nil))

(defn hae-voimassaolevat-tutkinnot-listana []
  (->>
    (hae-tutkinnot)
    (filter tutkinto-voimassa?)
    (map #(select-keys % [:tutkintotunnus :nimi_fi :nimi_sv :nimi_en]))))

(defn hae-voimassaolevat-tutkinnot []
  (tutkinnot-hierarkiaksi
    (filter tutkinto-voimassa? (hae-tutkinnot))))

(defn hae-vanhentuneet-tutkinnot []
  (tutkinnot-hierarkiaksi
    (remove tutkinto-voimassa? (hae-tutkinnot))))
