(ns arvo.arkisto.opintoala
  (:require [arvo.db.core :refer [*db*] :as db]))

(defn ^:integration-api lisaa!
  ([tiedot]
   (db/lisaa-opintoala! tiedot))
  ([tx tiedot]
   (db/lisaa-opintoala! tx tiedot)))

(defn ^:integration-api paivita!
  ([tiedot]
   (db/paivita-opintoala! tiedot))
  ([tx tiedot]
   (db/paivita-opintoala! tx tiedot)))

(defn hae-kaikki []
  (db/hae-opintoalat))

(defn hae [opintoalatunnus]
  (db/hae-opintoala {:opintoalatunnus opintoalatunnus}))
