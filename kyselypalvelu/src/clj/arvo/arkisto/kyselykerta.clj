(ns arvo.arkisto.kyselykerta
  (:require [arvo.infra.kayttaja :refer [*kayttaja*]]
            [arvo.db.core :refer [*db*] :as db]
            [clojure.tools.logging :as log]
            [arvo.util.kysely-util :as kysely-util]
            [arvo.util.paivamaara-util :as pvm-util]
            [clojure.java.jdbc :as jdbc]))

(defn- yhdista-vastaajatiedot-kyselykertaan [kyselykerta vastaajatiedot]
  (let [kysely-kaytettavissa-tiedot {:voimassa_alkupvm (:kysely_voimassa_alkupvm kyselykerta)
                                     :voimassa_loppupvm (:kysely_voimassa_loppupvm kyselykerta)
                                     :tila (:kysely_tila kyselykerta)}]
    (assoc kyselykerta
           :kaytettavissa (kysely-util/kyselykerta-kaytettavissa? kyselykerta kysely-kaytettavissa-tiedot)
           :vastaajia (or (:vastaajia vastaajatiedot) 0)
           :poistettavissa (or (:poistettavissa vastaajatiedot) 0)
           :viimeisin_vastaus (:viimeisin_vastaus vastaajatiedot))))

(defn hae-koulutustoimijan-kyselykerrat [koulutustoimija oppilaitokset]
  (let [kyselykerrat (db/hae-koulutustoimijan-kyselykerrat {:koulutustoimija koulutustoimija :oppilaitokset oppilaitokset})
        kyselykertaidt (map :kyselykertaid kyselykerrat)
        vastaajatiedot (when-not (empty? kyselykertaidt) (db/hae-kyselykerran-vastaajatiedot {:kyselykerrat kyselykertaidt}))
        kyselykertaid->vastaajatiedot (group-by :kyselykertaid vastaajatiedot)]
    (map #(yhdista-vastaajatiedot-kyselykertaan % (first (get kyselykertaid->vastaajatiedot (:kyselykertaid %)))) kyselykerrat)))

(defn poistettavissa? [id]
  (= 0 (:vastaajia (db/laske-kyselykerran-vastaajat {:kyselykertaid id}))))

(defn kysely-julkaistu?
  ([kyselyid]
   (jdbc/with-db-transaction
     [tx *db*]
    (kysely-julkaistu? tx kyselyid)))
  ([tx kyselyid]
   (boolean (= "julkaistu" (:tila (db/hae-kysely tx {:kyselyid kyselyid}))))))

(defn muokattavissa? [kyselykertaid]
  (let [kyselykerta (db/hae-kyselykerta {:kyselykertaid kyselykertaid})]
    (kysely-julkaistu? (:kyselyid kyselykerta))))

(defn lisaa!
  ([kyselyid kyselykerta-data]
   (jdbc/with-db-transaction
    [tx *db*]
    (lisaa! tx kyselyid kyselykerta-data)))
  ([tx kyselyid kyselykerta-data]
   (when (kysely-julkaistu? tx kyselyid)
     (let [kyselykertaid (db/luo-kyselykerta! tx (merge kyselykerta-data
                                                        {:kyselyid kyselyid
                                                         :kayttaja (:oid *kayttaja*)
                                                         :automaattinen nil
                                                         :metatiedot nil}))]
       (first kyselykertaid)))))

(defn hae-automaatti-kyselykerta [koulutustoimija kyselytyyppi tarkenne]
  (db/hae-automaatti-kyselykerta (merge
                                   {:koulutustoimija koulutustoimija :kyselytyyppi kyselytyyppi}
                                   (when tarkenne {:tarkenne tarkenne}))))

(defn hae-rekrykysely [oppilaitos vuosi]
  (first (db/hae-rekry-kyselykerta {:oppilaitoskoodi oppilaitos :vuosi vuosi})))


(defn hae-yksi [kyselykertaid]
  (db/hae-kyselykerta {:kyselykertaid kyselykertaid}))

(defn paivita! [kyselykertaid kyselykertadata]
  (when (muokattavissa? kyselykertaid)
    (let [kayttaja {:kayttaja (:oid *kayttaja*) :kyselykertaid kyselykertaid}
          data (select-keys kyselykertadata [:nimi :voimassa_alkupvm :voimassa_loppupvm :lukittu])]
      (str (db/paivita-kyselykerta! (merge kayttaja data))))))

(defn aseta-lukittu!
  [kyselykertaid lukitse]
  (db/set-kyselykerta-lukittu! {:kyselykertaid kyselykertaid :lukittu lukitse :kayttaja (:oid *kayttaja*)})
  (hae-yksi kyselykertaid))

(defn poista! [id]
  {:pre [(poistettavissa? id)]}
  (jdbc/with-db-transaction [tx *db*]
    (db/poista-kyselykerran-tunnukset! {:kyselykertaid id})
    (db/poista-kyselykerta! {:kyselykertaid id})))

(defn hae-kyselykerran-oppilaitokset [kyselykertaid]
  (let [oppilaitokset (db/hae-kyselykerran-oppilaitokset {:kyselykertaid kyselykertaid})]
    (when oppilaitokset
      {:oppilaitokset oppilaitokset})))

(defn hae-kyselyn-oppilaitokset [kyselyid]
  (let [oppilaitokset (db/hae-kyselyn-oppilaitokset {:kyselyid kyselyid})]
    (when oppilaitokset
      {:oppilaitokset oppilaitokset})))

(defn samanniminen-kyselykerta?
  ([kyselyid nimi]
   (boolean (seq (db/samanniminen-kyselykerta? {:kyselyid kyselyid :nimi nimi}))))
;  Päivitystä varten
  ([kyselyid nimi kyselykertaid]
   (boolean (seq (db/samanniminen-kyselykerta? {:kyselyid kyselyid :nimi nimi :kyselykertaid kyselykertaid})))))

(defn samanniminen-kyselykerta-massa? [koulutustoimija nimet]
  (if (empty? nimet)
    false
    (:exists (db/samanniminen-kyselykerta-massa? {:koulutustoimija koulutustoimija :nimet nimet}))))
