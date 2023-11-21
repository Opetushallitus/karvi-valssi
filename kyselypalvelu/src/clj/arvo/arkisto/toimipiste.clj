(ns arvo.arkisto.toimipiste
  (:require [arvo.db.core :refer [*db*] :as db]))

(defn hae-oppilaitoksen-voimassaolevat-toimipisteet
  ([oppilaitos-oid]
   (hae-oppilaitoksen-voimassaolevat-toimipisteet oppilaitos-oid nil nil))
  ([oppilaitos-oid koulutustoimija-oid oppilaitos-oidit]
  (db/hae-oppilaitoksen-voimassaolevat-toimipisteet {:oid oppilaitos-oid
                                                     :koulutustoimija koulutustoimija-oid
                                                     :oppilaitokset oppilaitos-oidit
                                                     :voimassa true})))
