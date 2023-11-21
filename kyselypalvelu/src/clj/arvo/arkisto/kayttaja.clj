(ns arvo.arkisto.kayttaja
  (:require [arvo.db.core :refer [*db*] :as db]
            [oph.common.util.util :refer [sisaltaako-kentat?]]
            [arvo.infra.kayttaja :refer [*kayttaja*]]))

(defn hae [oid]
  (db/hae-kayttaja {:kayttajaOid oid}))

(defn olemassa? [k]
  (boolean (hae (:oid k))))

(defn hae-impersonoitava-termilla [termi]
  (for [kayttaja (db/hae-impersonoitavat-kayttajat)
        :when (sisaltaako-kentat? kayttaja [:etunimi :sukunimi] termi)]
    {:nimi (str (:etunimi kayttaja) " " (:sukunimi kayttaja) " (" (:uid kayttaja) ")")
     :oid (:oid kayttaja)}))
