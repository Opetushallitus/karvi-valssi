(ns arvo.util.kysely-util
  (:require
    [arvo.util.paivamaara-util :as pvm-util]))

(defn kysely-kaytettavissa? [{:keys [tila voimassa_alkupvm voimassa_loppupvm] :as kysely}]
  (and (= tila "julkaistu")
       (pvm-util/voimassa-java-date? voimassa_alkupvm voimassa_loppupvm)))

(defn kyselykerta-kaytettavissa?
  ([{:keys [lukittu voimassa_alkupvm voimassa_loppupvm] :as kyselykerta}]
   (and (not lukittu)
        (pvm-util/voimassa-java-date? voimassa_alkupvm voimassa_loppupvm)))
  ([kyselykerta kysely]
   (and (kyselykerta-kaytettavissa? kyselykerta)
        (kysely-kaytettavissa? kysely))))
