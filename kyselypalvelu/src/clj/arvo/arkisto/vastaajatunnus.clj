(ns arvo.arkisto.vastaajatunnus
  (:require [clojure.set :refer [rename-keys]]
            [clojure.core.match :refer [match]]
            [oph.common.util.util :refer [select-and-rename-keys]]
            [clojure.tools.logging :as log]
            [arvo.infra.kayttaja.vaihto :refer [with-kayttaja]]
            [arvo.infra.kayttaja :refer [*kayttaja*]]
            [arvo.infra.kayttaja.vakiot :refer [integraatio-uid]]
            [arvo.db.core :refer [*db*] :as db]
            [arvo.kyselytyypit :refer [kyselytyypit]]
            [clojure.java.jdbc :as jdbc]
            [arvo.util.vastaajatunnus :refer [luo-satunnaisia-tunnuksia]]))

(def errors {:ei-kyselykertaa {:error "ei-kyselykertaa" :msg "Ei kyselykertaa annetuille tiedoille"}})

(def sallitut-merkit "ABCDEFHJKLMNPRSTUVWXYZ23456789")

(def jarjestelma-kayttajat #{"INTEGRAATIO" "JARJESTELMA"})

(def common-props [:kyselykertaid
                   :tunnus
                   :voimassa_alkupvm
                   :voimassa_loppupvm
                   :kohteiden_lkm
                   :metatiedot
                   :valmistavan_koulutuksen_oppilaitos])

(def legacy-props [:toimipiste :kunta :koulutusmuoto :kieli :tutkinto])

(def ^:private common-and-legacy-props (vec (concat common-props legacy-props)))

(defn vastaajatunnus-base-data [vastaajatunnus tunnus]
  (-> vastaajatunnus
      (assoc :tunnus tunnus)
      (assoc :metatiedot (:metatiedot vastaajatunnus))
      (select-keys (concat common-props legacy-props))))

(defn ^:private erota-tutkinto
  [vastaajatunnus]
  (let [tutkinto (select-keys vastaajatunnus [:nimi_fi :nimi_sv :nimi_en :tutkintotunnus])]
    (some-> vastaajatunnus
      (dissoc :nimi_fi :nimi_sv :nimi_en :tutkintotunnus)
      (assoc :tutkinto tutkinto))))

(defn ^:private erota-oppilaitos
  [vastaajatunnus]
  (let [oppilaitos (select-and-rename-keys vastaajatunnus [:oppilaitos_oid :oppilaitoskoodi [:oppilaitos_nimi_fi :nimi_fi] [:oppilaitos_nimi_sv :nimi_sv] [:oppilaitos_nimi_en :nimi_en]])]
    (some-> vastaajatunnus
      (dissoc :oppilaitoskoodi :oppilaitos_nimi_fi :oppilaitos_nimi_sv :oppilaitos_nimi_en :oppilaitos_oid)
      (assoc :valmistavan_koulutuksen_oppilaitos oppilaitos))))

(defn ^:private erota-toimipiste
  [vastaajatunnus]
  (let [toimipiste (select-and-rename-keys vastaajatunnus [:toimipiste_oid :toimipistekoodi [:toimipiste_nimi_fi :nimi_fi] [:toimipiste_nimi_sv :nimi_sv] [:toimipiste_nimi_en :nimi_en]])]
    (some-> vastaajatunnus
            (dissoc :toimipistekoodi :toimipiste_nimi_fi :toimipiste_nimi_sv :toimipiste_nimi_en :toimipiste_oid)
            (assoc :toimipiste toimipiste))))

(defn yhdista-taustatiedot [vastaajatunnus]
  (let [taustatiedot (:taustatiedot vastaajatunnus)]
    (merge vastaajatunnus {:suorituskieli (:kieli taustatiedot)
                           :koulutusmuoto (:koulutusmuoto taustatiedot)})))

(defn format-vastaajatunnus [vastaajatunnus]
  (-> vastaajatunnus
      yhdista-taustatiedot
      erota-tutkinto
      erota-oppilaitos
      erota-toimipiste))

(defn hae-tyopaikkakysely-tunnukset [kyselykertaid koulutustoimija hae-kayttajalle]
  (map format-vastaajatunnus
    (db/hae-tyopaikkakysely-tunnus (merge {:kyselykertaid kyselykertaid
                                           :koulutustoimija koulutustoimija}
                                          (when hae-kayttajalle {:oid (:aktiivinen-oid *kayttaja*)})))))

(defn hae-vastaajatunnukset [kyselykertaid hae-kayttajalle]
  (map format-vastaajatunnus
    (db/hae-vastaajatunnus (merge
                              {:kyselykertaid kyselykertaid}
                              (when hae-kayttajalle {:oid (:aktiivinen-oid *kayttaja*)})))))

(defn hae-kyselykerralla
  "Hae kyselykerran vastaajatunnukset"
  [kyselykertaid hae-kayttajalle]
  (let [kysely (db/hae-kyselykerran-kysely {:kyselykertaid kyselykertaid})]
    (case (:tyyppi kysely)
      "tyopaikkakysely" (hae-tyopaikkakysely-tunnukset kyselykertaid (:koulutustoimija kysely) hae-kayttajalle)
      (hae-vastaajatunnukset kyselykertaid hae-kayttajalle))))

(defn hae-viimeisin-tutkinto
  "Hakee vastaajatunnuksiin tallennetuista tutkinnoista viimeisimmän koulutustoimijalle kuuluvan"
  [kyselykertaid koulutustoimija]
  (first
    (db/hae-viimeisin-tutkinto {:koulutustoimija koulutustoimija :kyselykertaid kyselykertaid})))

(defn hae [kyselykertaid tunnus]
  (-> (db/hae-vastaajatunnus {:kyselykertaid kyselykertaid :tunnus tunnus})
    first
    format-vastaajatunnus))

(defn vastaajatunnus-olemassa? [vastaajatunnus]
  (db/vastaajatunnus-olemassa? {:vastaajatunnus vastaajatunnus}))

(defn find-id [kentta kyselytyyppi-kentat]
  (:id (first (filter #(= kentta (:kentta_id %)) kyselytyyppi-kentat))))

(defn format-taustatiedot [taustatieto-kentat vastaajatunnus]
  (-> vastaajatunnus
    (select-keys taustatieto-kentat)))

(defn hae-kyselytyypin-kentat [kyselytyyppi]
  (map (comp keyword :kentta_id) (kyselytyypit kyselytyyppi)))

(defn hae-kyselykerran-taustatiedot [kyselykertaid]
  (let [kyselytyyppi (keyword (:tyyppi (db/kyselykerran-tyyppi {:kyselykertaid kyselykertaid})))
        kentat (hae-kyselytyypin-kentat kyselytyyppi)]
    (-> kentat
        (cond-> (some #(= :toimipiste %) kentat) (concat [:toimipiste_oid])))))

(defn get-vastaajatunnukset [tunnusten-lkm]
  (->> (luo-satunnaisia-tunnuksia 6)
       (remove vastaajatunnus-olemassa?)
       (take tunnusten-lkm)))

(defn lisaa! [vastaajatunnus]
  {:pre [(pos? (:kohteiden_lkm vastaajatunnus))]}
  (let [kyselytyypin_kentat (hae-kyselykerran-taustatiedot (:kyselykertaid vastaajatunnus))]
    (doall
      (for [tunnus (get-vastaajatunnukset (:tunnusten-lkm vastaajatunnus))]
        (let [base-data (vastaajatunnus-base-data vastaajatunnus tunnus)
              taustatiedot (format-taustatiedot kyselytyypin_kentat vastaajatunnus)
              tallennettava-tunnus (-> base-data
                                       (assoc :taustatiedot taustatiedot)
                                       (assoc :kayttaja (:oid *kayttaja*)))]
          (db/lisaa-vastaajatunnus! tallennettava-tunnus)
          (hae (:kyselykertaid tallennettava-tunnus) tunnus))))))

(def yleinen-vastaajatunnus-kentat [:tunnus, :kyselykertaid, :kohteiden_lkm, :voimassa_alkupvm, :voimassa_loppupvm, :kayttaja_oid, :taustatiedot, :metatiedot])
(def yleinen-vastaajatunnus-defaults (zipmap yleinen-vastaajatunnus-kentat (repeat nil)))

(defn lisaa-vastaajatunnus! [vastaajatunnus]
  (let [tallennettava-tunnus (merge yleinen-vastaajatunnus-defaults vastaajatunnus)]
    (db/lisaa-yleinen-vastaajatunnus! tallennettava-tunnus)))

(defn lisaa-automaattitunnus! [vastaajatunnus]
  (log/info "Lisätään tunnus:" vastaajatunnus)
  (if (:kyselykertaid vastaajatunnus)
    (with-kayttaja integraatio-uid nil nil
      (-> (lisaa! vastaajatunnus)
          first
          (select-keys [:tunnus :voimassa_loppupvm])))
    {:error (:ei-kyselykertaa errors)}))

(defn aseta-lukittu! [kyselykertaid tunnus lukitse]
  (db/lukitse-vastaajatunnus! {:tunnus tunnus :lukittu lukitse})
  (hae kyselykertaid tunnus))

(defn poista! [tunnus]
  (db/poista-vastaajatunnus! {:tunnus tunnus}))

(defn laske-vastaajat [vastaajatunnusid]
  (:count (db/vastaajien-lkm {:vastaajatunnusid vastaajatunnusid})))

(defn tunnus-poistettavissa? [kyselykertaid tunnus]
  (let [tunnus (hae kyselykertaid tunnus)]
    (not (contains? jarjestelma-kayttajat (:luotu_kayttaja tunnus)))))

(defn muokkaa-lukumaaraa!
  [kyselykertaid tunnus lukumaara]
  (db/muokkaa-vastaajien-maaraa! {:tunnus tunnus :vastaajia lukumaara})
  (hae kyselykertaid tunnus))

(defn paivita-nipun-tunnukset [tunnukset]
  (doseq [tunnus tunnukset]
    (db/paivita-taustatiedot! {:vastaajatunnus (:tunnus tunnus) :taustatiedot (select-keys tunnus [:tyopaikkajakson_kesto])})))

(defn niputa-tunnukset [data]
  (jdbc/with-db-transaction [tx *db*]
    (do
      (db/lisaa-nippu! tx data)
      (db/liita-tunnukset-nippuun! tx {:tunniste (:tunniste data) :tunnukset (map :tunnus (:tunnukset data))})
      data)))

(defn hae-niput [kyselykertaid]
  (db/hae-kyselykerran-niput {:kyselykertaid kyselykertaid}))

(defn poista-nippu [tunniste]
  (jdbc/with-db-transaction [tx *db*]
    (do (db/poista-tunnukset-nipusta! {:tunniste tunniste})
        (db/poista-nippu! {:tunniste tunniste}))))
