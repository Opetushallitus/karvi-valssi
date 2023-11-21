(ns arvo.arkisto.kyselypohja
  (:require [arvo.infra.kayttaja :refer [yllapitaja? *kayttaja*]]
            [arvo.db.core :refer [*db*] :as db]
            [clojure.java.jdbc :as jdbc]
            [clojure.tools.logging :as log]))

(defn hae-kyselypohjat
  ([koulutustoimija oppilaitokset vain-voimassaolevat]
   (db/hae-kyselypohjat {:koulutustoimija  koulutustoimija
                         :oppilaitokset    oppilaitokset
                         :voimassa         vain-voimassaolevat
                         :valtakunnallinen true}))
  ([koulutustoimija oppilaitokset]
   (hae-kyselypohjat koulutustoimija oppilaitokset false)))

(defn hae-kyselypohja [kyselypohjaid]
  (db/hae-kyselypohja {:kyselypohjaid kyselypohjaid}))

(def muokattavat-kentat [:nimi_fi :nimi_sv :nimi_en :selite_fi :selite_sv :selite_en :voimassa_alkupvm :voimassa_loppupvm :valtakunnallinen])

(def kyselypohja-defaults (assoc (zipmap muokattavat-kentat (repeat nil)) :oppilaitos nil))

(defn tallenna-kyselypohjan-kysymysryhmat! [tx kyselypohjaid kysymysryhmat]
  (db/poista-kyselypohjan-kysymysryhmat! tx {:kyselypohjaid kyselypohjaid})
  (doseq [[index kysymysryhma] (map-indexed vector kysymysryhmat)]
    (db/tallenna-kyselypohjan-kysymysryhma! tx {:kyselypohjaid kyselypohjaid
                                                :kysymysryhmaid (:kysymysryhmaid kysymysryhma)
                                                :kayttaja (:oid *kayttaja*)
                                                :jarjestys index})))

(defn tallenna-kyselypohja! [kyselypohjaid kyselypohja]
  (jdbc/with-db-transaction [tx *db*]
    (tallenna-kyselypohjan-kysymysryhmat! tx kyselypohjaid (:kysymysryhmat kyselypohja))
    (db/tallenna-kyselypohja! tx (merge (select-keys kyselypohja muokattavat-kentat) {:kyselypohjaid kyselypohjaid :kayttaja (:oid *kayttaja*)}))
    kyselypohja))

(defn luo-kyselypohja!
  [kyselypohja]
  (jdbc/with-db-transaction [tx *db*]
    (let [luotu-kyselypohja (first (db/luo-kyselypohja! tx
                                    (merge
                                      kyselypohja-defaults
                                      (select-keys kyselypohja (conj muokattavat-kentat :koulutustoimija :oppilaitos))
                                      {:kayttaja (:oid *kayttaja*)})))]
      (tallenna-kyselypohjan-kysymysryhmat! tx (:kyselypohjaid luotu-kyselypohja) (:kysymysryhmat kyselypohja))
      luotu-kyselypohja)))

(defn ^:private aseta-kyselypohjan-tila! [kyselypohjaid tila]
  (db/aseta-kyselypohjan-tila! {:kyselypohjaid kyselypohjaid :tila tila :kayttaja (:oid *kayttaja*)})
  (hae-kyselypohja kyselypohjaid))

(defn validoi-kyselypohja-kysymysryhmat-julkaistu [kyselypohjaid]
  (when (-> {:kyselypohjaid kyselypohjaid}
            db/kyselypohjan-kysymysryhmia-julkaisematta?
            :count
            (> 0))
    "kyselypohja.kysymysryhma.julkaisematta"))

(defn julkaise-kyselypohja! [kyselypohjaid]
  (aseta-kyselypohjan-tila! kyselypohjaid "julkaistu"))

(defn palauta-kyselypohja-luonnokseksi! [kyselypohjaid]
  (aseta-kyselypohjan-tila! kyselypohjaid "luonnos"))

(defn sulje-kyselypohja! [kyselypohjaid]
  (aseta-kyselypohjan-tila! kyselypohjaid "suljettu"))

(defn poista-kyselypohja! [kyselypohjaid]
  (jdbc/with-db-transaction [tx *db*]
    (db/poista-kyselypohjan-kysymysryhmat! tx {:kyselypohjaid kyselypohjaid})
    (db/poista-kyselypohja! tx {:kyselypohjaid kyselypohjaid})))
