(ns arvo.arkisto.kayttajaoikeus
  (:require [arvo.arkisto.kayttaja :as kayttaja-arkisto]
            [arvo.infra.kayttaja :refer [*kayttaja*]]
            [arvo.infra.kayttaja.vakiot :refer [integraatio-uid]]
            [arvo.db.core :refer [*db*] :as db]
            [clojure.tools.logging :as log]
            [clojure.java.jdbc :as jdbc]
            [clojure.set :as set]
            [arvo.arkisto.organisaatio :as organisaatio-arkisto]
            [arvo.toimiala.kayttajaroolit :refer [kayttooikeus->rooli kayttooikeus->kyselytyypit oikeudet]]))

(defonce organisaatio->koulutustoimija {:oid :organisaatio
                                        :organisaatio_nimi_fi :koulutustoimija_fi
                                        :organisaatio_nimi_sv :koulutustoimija_sv
                                        :organisaatio_nimi_en :koulutustoimija_en})
(defonce parent->koulutustoimija {:parent_oid :organisaatio
                                  :parent_nimi_fi :koulutustoimija_fi
                                  :parent_nimi_sv :koulutustoimija_sv
                                  :parent_nimi_en :koulutustoimija_en})
(defonce organisaatio->oppilaitos {:oid :oppilaitos_oid
                                   :organisaatio_nimi_fi :oppilaitos_fi
                                   :organisaatio_nimi_sv :oppilaitos_sv
                                   :organisaatio_nimi_en :oppilaitos_en})

(defonce koulutustoimija-kentat [:rooli_organisaatio_id :kayttooikeus :organisaatio :koulutustoimija_fi :koulutustoimija_sv :koulutustoimija_en])
(defonce oppilaitos-kentat [:oppilaitos_oid :oppilaitos_fi :oppilaitos_sv :oppilaitos_en])

(defn hae-roolit
  ([tx kayttaja-oid]
   (let [parentoid-kayttooikeus->kayttooikeudet (->> (db/hae-voimassaolevat-roolit tx {:kayttajaOid kayttaja-oid})
                                                     (group-by (juxt :parent_oid :kayttooikeus)))
         koulutustoimija-oikeudet (for [[parent_oid-kayttooikeus kayttooikeudet] parentoid-kayttooikeus->kayttooikeudet
                                        :when (= (first parent_oid-kayttooikeus) organisaatio-arkisto/root-organisaatio-oid)]
                                    (map #(-> %
                                           (clojure.set/rename-keys organisaatio->koulutustoimija)
                                           (select-keys koulutustoimija-kentat)
                                           (assoc :oppilaitokset nil))
                                         kayttooikeudet))
         oppilaitos-oikeudet (for [[parent_oid-kayttooikeus kayttooikeudet] parentoid-kayttooikeus->kayttooikeudet
                                   :let [kayttooikeus-pohja (-> (first kayttooikeudet)
                                                                (clojure.set/rename-keys parent->koulutustoimija)
                                                                (select-keys koulutustoimija-kentat))
                                         kayttooikeudet-oppilaitokset (map #(-> %
                                                                             (clojure.set/rename-keys organisaatio->oppilaitos)
                                                                             (select-keys oppilaitos-kentat))
                                                                           kayttooikeudet)]
                                   :when (not= (first parent_oid-kayttooikeus) organisaatio-arkisto/root-organisaatio-oid)]
                               (assoc kayttooikeus-pohja :oppilaitokset kayttooikeudet-oppilaitokset))]
     (->> (concat (flatten koulutustoimija-oikeudet) oppilaitos-oikeudet)
          (map #(merge % {:rooli (kayttooikeus->rooli (:kayttooikeus %))
                          :kyselytyypit (kayttooikeus->kyselytyypit (:kayttooikeus %))
                          :oikeudet (oikeudet (kayttooikeus->rooli (:kayttooikeus %)))})))))
  ([kayttaja-oid]
   (jdbc/with-db-transaction [tx *db*]
     (hae-roolit tx kayttaja-oid))))

(defn hae-oikeudet
  ([oid]
   (let [kayttaja (kayttaja-arkisto/hae oid)
         roolit (hae-roolit oid)
         laajennettu (db/hae-laajennettu {:koulutustoimijat (map :organisaatio roolit)})]
     (-> kayttaja
         (merge laajennettu)
         (assoc :roolit roolit))))
  ([]
   (hae-oikeudet (:oid *kayttaja*))))

(defn paivita-roolit! [tx k impersonoitu-oid]
  (let [vanhat-roolit (->> (db/hae-roolit tx {:kayttaja (:oid k)})
                           (into #{}))
        poistuneet-roolit (set/difference
                              vanhat-roolit
                              (into #{} (map #(select-keys % [:kayttooikeus :organisaatio]) (:roolit k))))]
    (doseq [r poistuneet-roolit]
      (db/aseta-roolin-tila! tx (merge r {:kayttaja (:oid k) :voimassa false})))
    (doseq [r (:roolit k)]
      (if (contains? vanhat-roolit (select-keys r [:kayttooikeus :organisaatio]))
        (db/aseta-roolin-tila! tx (merge r {:kayttaja (:oid k) :voimassa true}))
        (db/lisaa-rooli! tx (assoc r :kayttaja (:oid k)))))
    (hae-roolit tx (or impersonoitu-oid (:oid k)))))


(defn paivita-kayttaja! [k impersonoitu-oid]
  (jdbc/with-db-transaction [tx *db*]
    (let [olemassa? (db/hae-kayttaja {:kayttajaOid (:oid k)})]
      (if olemassa?
        (db/paivita-kayttaja! tx {:kayttajaOid (:oid k) :etunimi (:etunimi k) :sukunimi (:sukunimi k)})
        (db/lisaa-kayttaja! tx (assoc k :kayttajaOid (:oid k)))))
    (assoc k :roolit (paivita-roolit! tx k impersonoitu-oid))))
