(ns arvo.arkisto.koulutustoimija
  (:require [clojure.tools.logging :as log]
            [arvo.db.core :refer [*db*] :as db]))

(def oph-koulutustoimija {:ytunnus "0920632-0"})

(defn hae [oid]
  (db/hae-organisaatio {:oid oid}))

(defn hae-kaikki []
  (db/hae-kaikki-ytunnukselliset))

(defn hae-koulutusluvalliset []
  (db/hae-koulutustoimijat-joilla-koulutuslupa))

(defn hae-nimella [termi]
  (db/hae-koulutustoimija-nimella {:termi termi}))
