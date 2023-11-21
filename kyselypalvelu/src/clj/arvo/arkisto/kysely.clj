(ns arvo.arkisto.kysely
  (:require [arvo.arkisto.kyselykerta :as kyselykerta]
            [arvo.util.kysely-util :as kysely-util]
            [arvo.infra.kayttaja :refer [yllapitaja? *kayttaja*]]
            [arvo.rest-api.validate-util :as validate-util]
            [arvo.arkisto.kyselykerta :as kyselykerta-arkisto]
            [oph.common.util.util :refer [max-date]]
            [clojure.tools.logging :as log]
            [arvo.util.paivamaara-util :as pvm-util]
            [arvo.db.core :refer [*db*] :as db]
            [clojure.java.jdbc :as jdbc]
            [arvo.toimiala.kayttajaroolit :as kayttajaroolit]
            [arvo.util :refer [add-index]]
            [oph.common.util.util :refer [map-by]])
  (:import (java.security MessageDigest)))

(defn kysely-vastattavissa? [{:keys [kyselytila kyselyvoimassa_alkupvm kyselyvoimassa_loppupvm] :as tiedot}]
  (and (= kyselytila "julkaistu")
       (pvm-util/voimassa-java-date? kyselyvoimassa_alkupvm kyselyvoimassa_loppupvm)))

(defn kyselykerta-vastattavissa? [{:keys [kyselykertalukittu kyselykertavoimassa_alkupvm kyselykertavoimassa_loppupvm] :as tiedot}]
  (and (not kyselykertalukittu)
       (pvm-util/voimassa-java-date? kyselykertavoimassa_alkupvm kyselykertavoimassa_loppupvm)))

(defn vastaajatunnus-vastattavissa? [{:keys [vastaajatunnuslukittu vastaajatunnusvoimassa_alkupvm vastaajatunnusvoimassa_loppupvm]}]
  (and (not vastaajatunnuslukittu)
       (pvm-util/voimassa-java-date? vastaajatunnusvoimassa_alkupvm vastaajatunnusvoimassa_loppupvm)))

(def vastattavissa? (every-pred kysely-vastattavissa?
                                kyselykerta-vastattavissa?
                                vastaajatunnus-vastattavissa?))

(def kysely-kentat [:oppilaitos :nimi_fi :nimi_sv :nimi_en :selite_fi :selite_sv :selite_en :kyselypohjaid :metatiedot :uudelleenohjaus_url :tyyppi])

(def kysely-defaults (zipmap kysely-kentat (repeat nil)))

(defn random-hash []
  (let [algorithm (MessageDigest/getInstance "MD5")
        raw (.digest algorithm (.getBytes (str(rand))))]
    (format "%032x" (BigInteger. 1 raw))))

(defn hae-kyselyt [koulutustoimija oppilaitokset]
  (db/hae-kyselyt {:koulutustoimija koulutustoimija :oppilaitokset oppilaitokset}))

(defn- yhdista-aktiiviset [kyselykerta aktiiviset-tunnukset]
  (let [aktiivinen-tunnus (first (filter #(= (:kyselykertaid kyselykerta) (:kyselykertaid %)) aktiiviset-tunnukset))]
    (assoc kyselykerta :aktiivisia_vastaajia (get aktiivinen-tunnus :aktiivisia_vastaajia 0)
           :aktiivisia_vastaajatunnuksia (get aktiivinen-tunnus :aktiivisia_vastaajatunnuksia 0))))

(defn ^:private yhdista-kyselykerrat-kyselyihin [kyselyt kyselykerrat aktiiviset-tunnukset]
  (let [kyselyid->kyselykerrat (group-by :kyselyid kyselykerrat)]
    (for [kysely kyselyt
          :let [kyselyn-kyselykerrat (kyselyid->kyselykerrat (:kyselyid kysely))
                kyselyn-kyselykerrat-aktiiviset (map #(yhdista-aktiiviset % aktiiviset-tunnukset) kyselyn-kyselykerrat)
                vastaajia (reduce #(if %2 (+ %1 %2) (+ %1 0)) 0 (map :vastaajia kyselyn-kyselykerrat))]]
      (assoc kysely :kyselykerrat kyselyn-kyselykerrat-aktiiviset
                    :vastaajia vastaajia
                    :poistettavissa (and (not (pos? vastaajia)) (not= (:tila kysely) "julkaistu"))
                    :kaytettavissa (kysely-util/kysely-kaytettavissa? kysely)
                    :vastaajatunnuksia (reduce + (map :vastaajatunnuksia kyselyn-kyselykerrat))
                    :viimeisin_vastaus (reduce max-date nil (map :viimeisin_vastaus kyselyn-kyselykerrat))))))

(defn hae-kysymysten-poistettavuus  [kysymysryhmaid]
  (map #(select-keys % [:kysymysid :poistettava]) (db/hae-kysymysryhman-kysymykset {:kysymysryhmaid kysymysryhmaid})))

(defn- hae-aktiiviset-vastaukset
  "Hakee koulutuksenjärjestäjän kyselykertojen aktiivisten (vastattavissa olevien) vastaajatunnusten ja vastausten
  summan per aktiivinen kyselykerta. Mukaan tulee vain jos kysely, kyselykerta ja vastaajatunnus ovat aktiivisia."
  [koulutustoimija oppilaitokset]
  (->> (db/hae-vastattavissa-tiedot {:koulutustoimija koulutustoimija :oppilaitokset oppilaitokset})
       (filter vastattavissa?)
       (group-by :kyselykertaid)
       (map (fn [[kyselykertaid aktiiviset]]
              {:kyselykertaid kyselykertaid
               :aktiivisia_vastaajatunnuksia (reduce + 0 (map :kohteiden_lkm aktiiviset))
               :aktiivisia_vastaajia (reduce + 0 (map :vastaus_lkm aktiiviset))}))))

(defn hae-kaikki
  [koulutustoimija oppilaitokset]
  (let [kyselyt (hae-kyselyt koulutustoimija oppilaitokset)
        kyselykerrat (kyselykerta/hae-koulutustoimijan-kyselykerrat koulutustoimija oppilaitokset)
        aktiiviset-vastaajatunnukset (hae-aktiiviset-vastaukset koulutustoimija oppilaitokset)]
    (yhdista-kyselykerrat-kyselyihin kyselyt kyselykerrat aktiiviset-vastaajatunnukset)))

(defn hae [kyselyid]
  (db/hae-kysely {:kyselyid kyselyid}))

(defn hae-kyselytyypit []
  (let [kyselytyypit (kayttajaroolit/kaikki-kyselytyypit)
        kayttajan-kyselytyypit (-> *kayttaja* :aktiivinen-rooli :kyselytyypit)]
    (filter #(some #{%} kayttajan-kyselytyypit) kyselytyypit)))

(defn lisaa-kysymysryhma! [tx kyselyid kysymysryhma]
  (db/lisaa-kyselyn-kysymysryhma! tx (merge kysymysryhma {:kyselyid kyselyid :kayttaja (:oid *kayttaja*)}))
  (let [kayttajan-kysymykset (map-by :kysymysid (:kysymykset kysymysryhma))]
    (doseq [kysymys (hae-kysymysten-poistettavuus (:kysymysryhmaid kysymysryhma))]
      (let [kysymysid (:kysymysid kysymys)
            kayttajan-kysymys (get kayttajan-kysymykset kysymysid)
            lisattavissa (not (and (:poistettu kayttajan-kysymys)
                                   (:poistettava kysymys)))]
        (when lisattavissa
          (db/lisaa-kysymys-kyselyyn! tx {:kyselyid kyselyid :kysymysid kysymysid :kayttaja (:oid *kayttaja*)}))))))


(defn format-kysely [kyselydata]
  (let [metatiedot (merge (:metatiedot kyselydata) {:esikatselu_tunniste (random-hash)})]
    (merge kysely-defaults kyselydata {:metatiedot metatiedot :kayttaja (:oid *kayttaja*)})))

(defn samanniminen-kysely?
  "Palauttaa true jos samalla koulutustoimijalla on jo samanniminen kysely."
  [{:keys [koulutustoimija nimi_fi nimi_sv nimi_en] :as kysely}]
  (:exists (db/samanniminen-kysely? {:koulutustoimija koulutustoimija
                                     :nimet_fi [nimi_fi]
                                     :nimet_sv [nimi_sv]
                                     :nimet_en [nimi_en]})))

(defn samanniminen-kysely-massana? [koulutustoimija {:keys [nimet_fi nimet_sv nimet_en] :as kysely-nimet}]
  (:exists (db/samanniminen-kysely? {:koulutustoimija koulutustoimija
                                     :nimet_fi nimet_fi
                                     :nimet_sv nimet_sv
                                     :nimet_en nimet_en})))

(defn validoi-lisaa! [kyselydata]
  (when (samanniminen-kysely? kyselydata) "kysely.samanniminen_kysely"))

(defn lisaa!
  ([kyselydata]
   (jdbc/with-db-transaction [tx *db*]
     (lisaa! tx kyselydata)))
  ([tx kyselydata]
   (let [kysely (first (db/luo-kysely! tx (format-kysely kyselydata)))
         kyselyid (:kyselyid kysely)]
     (doseq [ryhma (add-index :jarjestys (:kysymysryhmat kyselydata))]
       (lisaa-kysymysryhma! tx kyselyid ryhma))
     (doseq [kyselykerta (:kyselykerrat kyselydata)]
       (kyselykerta-arkisto/lisaa! tx kyselyid kyselykerta))
     (assoc kyselydata :kyselyid kyselyid))))

(defn paivita-kysely! [kyselydata]
  (let [kyselyid (:kyselyid kyselydata)
        current-data (hae kyselyid)
        updated-data (if (= "julkaistu" (:tila current-data))
                       (select-keys kyselydata [:selite_fi :selite_sv :selite_en :uudelleenohjaus_url :metatiedot])
                       kyselydata)
        new-data (merge current-data updated-data {:kayttaja (:oid *kayttaja*)})]
    (jdbc/with-db-transaction [tx *db*]
      (db/muokkaa-kyselya! new-data)
      ;TODO smarter way to update questions/groups
      (db/poista-kyselyn-kysymykset! tx {:kyselyid kyselyid})
      (db/poista-kyselyn-kysymysryhmat! tx {:kyselyid kyselyid})
      (doseq [kysymysryhma (add-index :jarjestys (:kysymysryhmat kyselydata))]
        (lisaa-kysymysryhma! tx kyselyid kysymysryhma)))))


(defn julkaise-kysely! [kyselyid]
  (db/muuta-kyselyn-tila! {:kyselyid kyselyid :tila "julkaistu" :kayttaja (:oid *kayttaja*)})
  ;; haetaan kysely, jotta saadaan myös kaytettavissa tieto mukaan paluuarvona
  (-> (hae kyselyid)
      (assoc :sijainti "julkaistu")))

(defn palauta-luonnokseksi! [kyselyid]
  (db/muuta-kyselyn-tila! {:kyselyid kyselyid :tila "luonnos" :kayttaja (:oid *kayttaja*)})
  (-> (hae kyselyid)
      (assoc :sijainti "luonnos")))

(defn sulje-kysely! [kyselyid]
  (db/muuta-kyselyn-tila! {:kyselyid kyselyid :tila "suljettu" :kayttaja (:oid *kayttaja*)})
  (-> (hae kyselyid)
      (assoc :sijainti "suljettu")))

(defn poista-kysely! [kyselyid]
  (jdbc/with-db-transaction [tx *db*]
    (db/poista-kyselyn-kysymykset! tx {:kyselyid kyselyid})
    (db/poista-kyselyn-kysymysryhmat! tx {:kyselyid kyselyid})
    (db/poista-kyselyn-kyselykerrat! tx {:kyselyid kyselyid})
    (db/poista-kysely! tx {:kyselyid kyselyid})))

(defn laske-kysymysryhmat [kyselyid]
  (count (db/hae-kyselyn-kysymysryhmat {:kyselyid kyselyid})))

(defn laske-kyselykerrat [kyselyid]
  (->
    (db/laske-kyselyn-kyselykerrat {:kyselyid kyselyid})
    :lkm))

(defn poista-kysymykset! [kyselyid]
  (db/poista-kyselyn-kysymykset! {:kyselyid kyselyid}))

(defn poista-kysymysryhmat! [kyselyid]
  (db/poista-kyselyn-kysymysryhmat! {:kyselyid kyselyid}))

(defn hae-kyselyn-taustakysymysryhmaid [kyselyid]
  (-> (db/hae-kyselyn-taustakysymysryhmaid {:kyselyid kyselyid})
      first
      :kysymysryhmaid))

(defn aseta-jatkokysymyksen-jarjestys [kysymys kysymykset]
  (if (:jatkokysymys kysymys)
    (let [parent-q (first(filter #(= (:kysymysid %) (:jatkokysymys_kysymysid kysymys)) kysymykset))]
      (assoc kysymys :jarjestys (+ (:jarjestys parent-q) 0.5)))
    kysymys))

(defn aseta-jatkokysymysten-jarjestys [kysymykset]
  (map #(aseta-jatkokysymyksen-jarjestys % kysymykset) kysymykset))

(defn liita-monivalintavaihtoehdot [kysymys]
  (let [monivalintavaihtoehdot (db/hae-monivalintavaihtoehdot kysymys)]
    (assoc kysymys :monivalintavaihtoehdot monivalintavaihtoehdot)))

(defn hae-kysymysryhman-kysymykset [kysymysryhma]
  (->> kysymysryhma
       db/hae-kysymysryhman-kysymykset
       (map liita-monivalintavaihtoehdot)
       ;aseta-jatkokysymysten-jarjestys
       (sort-by :jarjestys)))

(defn hae-kyselyn-kysymykset [kyselyid]
  (->> (db/hae-kyselyn-kysymysryhmat {:kyselyid kyselyid})
       (map hae-kysymysryhman-kysymykset)
       flatten))

(defn kysely-poistettavissa? [kyselyid]
  (-> (hae kyselyid)
      :poistettavissa))

(defn get-kyselyn-pakolliset-kysymysryhmaidt
  "Hakee kyselyn kaikki valtakunnalliset ja taustakysymykset. Näiden muokkausta ei sallita julkaistussa kyselyssä."
  [kyselyid]
  (db/hae-kyselyn-pakolliset-kysymysryhmat {:kyselyid kyselyid}))
