(ns arvo.service.kysely
  (:require
    [arvo.arkisto.kysely :as kysely-arkisto]
    [arvo.arkisto.kyselykerta :as kyselykerta-arkisto]
    [clojure.tools.logging :as log]
    [arvo.util.paivamaara-util :as pvm-util]
    [arvo.db.core :refer [*db*] :as db]
    [clojure.java.jdbc :as jdbc]
    [arvo.util.excel :as excel]))

(defn- not-blank-keyword? [kw]
  (comp not clojure.string/blank? kw))

(defn- map-not-nil-keyword [kw map-values]
  (filter some? (map kw map-values)))

(defn validoi-lisaa-massana [kyselyt koulutustoimija]
  (let [kysely-nimet {:nimet_fi (map-not-nil-keyword :nimi_fi kyselyt)
                      :nimet_sv (map-not-nil-keyword :nimi_sv kyselyt)
                      :nimet_en (map-not-nil-keyword :nimi_en kyselyt)}
        kyselykerta-nimet (flatten (for [kysely kyselyt
                                         :let [kyselykerrat (:kyselykerrat kysely)]]
                                     (map :nimi kyselykerrat)))]
    [(when (> (count kyselyt) 1000)
       "kysely.massasyotto.maksimi-syottomaara-ylitetty")
     (when (not-every? #((some-fn (not-blank-keyword? :nimi_fi)
                                  (not-blank-keyword? :nimi_sv)
                                  (not-blank-keyword? :nimi_en)) %) kyselyt)
       "kysely.massasyotto.kysely-nimi-puuttuu")
     (when (not-every? #((comp not false?) (some->> % not-empty (apply distinct?))) (vals kysely-nimet))
       "kysely.massasyotto.samanniminen-syote-kysely")
     (when (kysely-arkisto/samanniminen-kysely-massana? koulutustoimija kysely-nimet)
       "kysely.massasyotto.samanniminen-kysely")
     (when (kyselykerta-arkisto/samanniminen-kyselykerta-massa? koulutustoimija kyselykerta-nimet)
       "kysely.massasyotto.samanniminen_kyselykerta")
     (when (some->> kyselykerta-nimet not-empty (apply (comp not distinct?)))
       "kysely.massasyotto.samanniminen-syote-kyselykerta")
     (when (->> kyselyt
                (filter #(not= (:tila %) "julkaistu"))
                (some (comp pos? count :kyselykerrat)))
       "kysely.massasyotto.julkaisematon-kysely-sisaltaa-kyselykertoja")

     (if
       (not-every?
         #(and (not (nil? (:voimassa_alkupvm %))) (not (nil? (:voimassa_loppupvm %)))) kyselyt)
       "kysely.massasyotto.kysely-voimassa-pvm-puuttuu"
       (when
         (not-every?
           #(and
              (pvm-util/pvm-tanaan-tai-tulevaisuudessa? (:voimassa_loppupvm %) (:voimassa_alkupvm %))
              (pvm-util/pvm-tanaan-tai-tulevaisuudessa? (:voimassa_loppupvm %))) kyselyt)
         "kysely.massasyotto.kysely-virheellinen-pvm"))

     (if (not-every? (fn [kysely]
                         (every? #(and
                                    (not (nil? (:voimassa_alkupvm %)))
                                    (not (nil? (:voimassa_loppupvm %)))) (:kyselykerrat kysely)))
                       kyselyt)
       "kysely.massasyotto.kyselykerta-voimassa-pvm-puuttuu"
       (when (not-every? (fn [kysely]
                           (every? #(pvm-util/pvm-tanaan-tai-tulevaisuudessa? (:voimassa_loppupvm %) (:voimassa_alkupvm %)) (:kyselykerrat kysely)))
                         kyselyt)
         "kysely.massasyotto.kyselykerta-virheellinen-pvm"))

     (when (not-every? (fn [kysely]
                         (every?
                          #(pvm-util/valin-sisalla?
                            (:voimassa_alkupvm kysely)
                            (:voimassa_loppupvm kysely)
                            (:voimassa_alkupvm %)
                            (:voimassa_loppupvm %))
                          (:kyselykerrat kysely)))
                       kyselyt)
       "kysely.massasyotto.kyselykerta-kyselyn-sisalla-virheellinen-pvm")]))

(defn- lisaa-massana! [tx kysely koulutustoimija]
  (let [kysely-data (assoc kysely :koulutustoimija koulutustoimija)]
    (kysely-arkisto/lisaa! tx kysely-data)))

(defn lisaa-massana [kyselyt koulutustoimija]
  (jdbc/with-db-transaction
   [tx *db*]
   (->> kyselyt
        (map #(lisaa-massana! tx % koulutustoimija))
        doall
        (map #(select-keys % [:kyselyid])))))
