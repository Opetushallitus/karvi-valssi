(ns arvo.db.tiedote
  (:require [arvo.db.core :refer [*db*] :as db]
            [clojure.java.jdbc :as jdbc]))

(defn hae []
  (db/hae-tiedotteet))

(defn poista-tiedote! [tiedoteid]
  (db/poista-tiedote! {:tiedoteid tiedoteid}))

(def tiedote-fields [:otsikko_fi :otsikko_sv :otsikko_en :teksti_fi :teksti_sv :teksti_en :voimassa_alkupvm :voimassa_loppupvm])

(defn lisaa-tiedote! [tiedote]
  (let [tyhja-tiedote (zipmap tiedote-fields (repeat nil))]
    (db/lisaa-tiedote! (merge tyhja-tiedote tiedote))))

(defn paivita-tiedote! [tiedote]
  (let [tyhja-tiedote (zipmap tiedote-fields (repeat nil))]
    (db/paivita-tiedote! (merge tyhja-tiedote tiedote))))