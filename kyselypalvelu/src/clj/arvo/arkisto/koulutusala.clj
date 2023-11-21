(ns arvo.arkisto.koulutusala
  (:require [arvo.db.core :refer [*db*] :as db]))

(defn ^:integration-api lisaa!
  ([tiedot]
   (db/lisaa-koulutusala! tiedot))
  ([tx tiedot]
   (db/lisaa-koulutusala! tx tiedot)))

(defn ^:integration-api paivita!
  ([tiedot]
   (db/paivita-koulutusala! tiedot))
  ([tx tiedot]
   (db/paivita-koulutusala! tx tiedot)))

(defn hae-kaikki []
  (db/hae-koulutusalat))

(defn hae [koulutusalatunnus]
  (first
    (db/hae-koulutusala {:koulutusalatunnus koulutusalatunnus})))
