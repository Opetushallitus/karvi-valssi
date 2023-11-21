(ns arvo.arkisto.ohje
  (:require
    [arvo.db.core :refer [*db*] :as db]))

(defn hae
  "Hakee ohjeen id:n perusteella."
  [ohjetunniste]
  (db/hae-ohje {:ohjetunniste ohjetunniste}))

(defn muokkaa-tai-luo-uusi!
  "Muokkaa ohjetta tai luo uuden jos tunnisteelle ei löydy ohjetta"
  [uusi-ohje]
  (if-let [olemassa-oleva (hae (:ohjetunniste uusi-ohje))]
    (db/paivita-ohje! uusi-ohje)
    (db/luo-uusi-ohje! uusi-ohje)))
