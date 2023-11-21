(ns arvo.infra.eraajo.automaattikyselyt
  (:require [clojure.java.jdbc :as jdbc]
            [clojure.tools.logging :as log]
            [arvo.arkisto.organisaatio :as organisaatio-arkisto]
            [arvo.db.core :refer [*db*] :as db]
            [arvo.arkisto.kysely :refer [random-hash]])
  (:import (org.quartz Job)))


(defn luo-kysely! [koulutustoimija kuvaus tx]
  (let [kyselyid (:kyselyid (first (db/luo-kysely! tx (merge kuvaus {:tila "julkaistu" :koulutustoimija (:oid koulutustoimija)
                                                                     :kayttaja "JARJESTELMA" :tyyppi (:kyselytyyppi kuvaus)
                                                                     :uudelleenohjaus_url nil
                                                                     :metatiedot (merge (:kysely_metatiedot kuvaus)
                                                                                        {:automatisointi_tunniste (:tunniste kuvaus)
                                                                                         :esikatselu_tunniste (random-hash)})
                                                                     :oppilaitos nil}))))]
    (db/liita-kyselyn-kyselypohja! tx {:kyselyid kyselyid :kyselypohjaid (:kyselypohjaid kuvaus) :kayttaja "JARJESTELMA"})
    (db/liita-kyselyn-kysymykset! tx {:kyselyid kyselyid :kayttaja "JARJESTELMA"})
    (db/luo-kyselykerta! tx {:kyselyid kyselyid :nimi (:kyselykerta_nimi kuvaus) :kayttaja "JARJESTELMA"
                             :automaattinen (format "[%s,%s]" (:automatisointi_voimassa_alkupvm kuvaus)
                                                              (:automatisointi_voimassa_loppupvm kuvaus))
                             :metatiedot (:kyselykerta_metatiedot kuvaus)
                             :voimassa_alkupvm (:voimassa_alkupvm kuvaus)
                             :voimassa_loppupvm (:voimassa_loppupvm kuvaus)})
    kyselyid))

(defn hae-koulutustoimijat [kuvaus]
  (case (:kyselytyyppi kuvaus)
    "rekrykysely" (db/hae-automaattikysely-korkeakoulut kuvaus)
    "tyopaikkaohjaajakysely" (db/hae-ammatilliset-koulutustoimijat kuvaus)
    "tyopaikkakysely" (db/hae-ammatilliset-koulutustoimijat kuvaus)
    "ammatillisen-opiskelijapalaute" (db/hae-ammatilliset-koulutustoimijat kuvaus)
    "amk-uraseuranta" (db/hae-ammattikorkeakoulut kuvaus)
    "yo-uraseuranta" (db/hae-yliopistot kuvaus)
    (db/hae-automaattikysely-koulutustoimijat kuvaus)))

(defn luo-kyselyt! [kuvaus tx]
  (let [koulutustoimijat (hae-koulutustoimijat kuvaus)
        juuriorganisaatio-oid (when (:luo_juuriorganisaatioon kuvaus)
                                (db/hae-automaattikysely-oid {:oid organisaatio-arkisto/root-organisaatio-oid
                                                              :tunniste (:tunniste kuvaus)}))
        luotavat-oidit (concat koulutustoimijat juuriorganisaatio-oid)]
    (when (not-empty luotavat-oidit)
      (log/info "Luodaan automaattikyselyt ("(:tunniste kuvaus)")" (count luotavat-oidit) "koulutustoimijalle"))
    (doseq [k luotavat-oidit]
      (luo-kysely! k kuvaus tx))))

(defn luo-automaattikyselyt! []
  (let [kuvaukset (db/hae-automaattikysely-data)]
    (doseq [kuvaus kuvaukset]
      (jdbc/with-db-transaction [tx *db*]
        (luo-kyselyt! kuvaus tx)))))

(defrecord LuoAutomaattikyselytJob []
  Job
  (execute [this ctx]
    (try
      (do (luo-automaattikyselyt!)
          (log/info "Automaattikyselyiden luonti valmis"))
      (catch Exception e
        (log/error e "Automaattikyselyiden luonti epäonnistui")))))
