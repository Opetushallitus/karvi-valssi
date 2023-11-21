(ns arvo.arkisto.oppilaitos
  (:require [clojure.tools.logging :as log]
            [arvo.db.core :refer [*db*] :as db]))

(defn hae-koulutustoimijan-oppilaitokset
  ([koulutustoimija-oid]
   (hae-koulutustoimijan-oppilaitokset koulutustoimija-oid nil))
  ([koulutustoimija-oid oppilaitos-oidit]
   (db/hae-koulutustoimijan-oppilaitokset {:koulutustoimija koulutustoimija-oid
                                           :oppilaitokset oppilaitos-oidit
                                           :voimassa true})))
