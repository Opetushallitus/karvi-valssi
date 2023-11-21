(ns arvo.arkisto.organisaatio
  (:require [clojure.tools.logging :as log]
            [arvo.db.core :refer [*db*] :as db]))

(def root-organisaatio-oid "1.2.246.562.10.00000000001")

(defn hae-kaikki-oidit []
  (map :oid (db/hae-kaikki-organisaatio-oidit)))

(defn luo-uusi-organisaatio [organisaatio]
  (log/info "Lisätty organisaatio" (:tyypit organisaatio) (:oid organisaatio))
  {:luotu (first (db/luo-uusi-organisaatio! organisaatio))})

(defn paivita-organisaatio [organisaatio]
  (log/info "Paivitetty organisaatio" (:tyypit organisaatio) (:oid organisaatio))
  {:paivitetty (first (db/paivita-organisaatio! organisaatio))})

(defn paivita-voimassaolot []
  (db/paivita-voimassaolot!))

(defn aseta-kaikki-vanhentuneiksi []
  (db/aseta-kaikki-vanhentuneiksi!))

(defn hae-viimeisin-paivitys []
  (:paivitetty (db/hae-viimeisin-paivitys)))

(defn tallenna-paivitys! [ajankohta]
  (db/tallenna-paivitys! {:paivitetty ajankohta}))

(defn hae-organisaatiot [oidit]
  (if (empty? oidit)
    []
    (db/hae-organisaatiot {:oidit oidit})))

(defn hae-organisaatio [oid]
  (when-not (clojure.string/blank? oid) (db/hae-organisaatio {:oid oid})))
