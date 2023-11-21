(ns arvo.service.vastaajatunnus
  (:require [arvo.db.core :refer [*db*] :as db]
            [clojure.tools.logging :as log]
            [arvo.arkisto.vastaajatunnus :as arkisto]
            [java-time.api :as jt]
            [arvo.util.paivamaara-util :as pvm-util]
            [arvo.kyselytyypit :as kyselytyypit]
            [arvo.arkisto.oppilaitos :as oppilaitos]
            [arvo.arkisto.tutkinto :as tutkinto]
            [arvo.arkisto.kyselykerta :as kyselykerta]
            [arvo.util.vastaajatunnus :refer [luo-satunnaisia-tunnuksia]]
            [arvo.infra.kayttaja.vakiot :refer [jarjestelma-oid]]
            [arvo.infra.kayttaja :refer [*kayttaja*]]
            [arvo.util :refer [when-let*]]))

(def palaute-voimassaolo (jt/months 6))
(def amispalaute-voimassaolo (jt/days 30))

(defn tunnus-voimassaolo [tyyppi ^java.time.LocalDate alkupvm ^java.time.LocalDate loppupvm]
  (let [voimassa_alkupvm (or alkupvm (jt/local-date))]
    {:voimassa_alkupvm voimassa_alkupvm
     :voimassa_loppupvm (or loppupvm (jt/plus voimassa_alkupvm
                                                (case tyyppi
                                                  :ammatillisen-opiskelijapalaute amispalaute-voimassaolo
                                                  :tyopaikkaohjaajakysely amispalaute-voimassaolo
                                                  palaute-voimassaolo)))}))

(def automaattitunnus-defaults
  {:tunnusten-lkm 1
   :kohteiden_lkm 1})

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

(defn format-vastaajatunnus [data tunnus taustatieto-kentat]
  (let [base-data (vastaajatunnus-base-data data tunnus)
        taustatiedot (select-keys data taustatieto-kentat)]
    (-> base-data
        (assoc :taustatiedot taustatiedot)
        (assoc :kayttaja (or (:oid *kayttaja*) jarjestelma-oid)))))

(defn automaatti-vastaajatunnus [tyyppi tunnus]
  (merge automaattitunnus-defaults
         tunnus
         (tunnus-voimassaolo tyyppi (:voimassa_alkupvm tunnus) (:voimassa_loppupvm tunnus))))


(defn palaute-tunnus
  [{:keys [oppilaitoskoodi koulutus kunta kieli koulutusmuoto kyselytyyppi tarkenne]}]
  (let [ent_oppilaitos (db/hae-organisaatio {:oppilaitoskoodi oppilaitoskoodi :voimassa true})
        ent_tutkinto (tutkinto/hae koulutus)
        _ (log/info "Haetaan automaattikyselykerta:" (:parent_oid ent_oppilaitos) kyselytyyppi tarkenne)
        kyselykerta-id (kyselykerta/hae-automaatti-kyselykerta (:parent_oid ent_oppilaitos) kyselytyyppi tarkenne)
        _ (log/info "Automaattikyselykerta: " kyselykerta-id)]
    (automaatti-vastaajatunnus :palaute
                               {:kieli kieli
                                :toimipiste nil
                                :toimipiste_oid nil
                                :valmistavan_koulutuksen_oppilaitos (:oid ent_oppilaitos)
                                :tutkinto (ent_tutkinto :tutkintotunnus)
                                :kunta kunta
                                :koulutusmuoto koulutusmuoto
                                :kyselykertaid (:kyselykertaid kyselykerta-id)})))


(defn rekry-tunnus [tunnus]
  (let [{henkilonumero :henkilonumero oppilaitos :oppilaitos vuosi :vuosi} tunnus
        kyselykerta-id (kyselykerta/hae-rekrykysely oppilaitos vuosi)]
    (automaatti-vastaajatunnus :rekry
                               {:kyselykertaid (:kyselykertaid kyselykerta-id)
                                :henkilonumero henkilonumero
                                :valmistavan_koulutuksen_oppilaitos (:oid (db/hae-organisaatio {:oppilaitoskoodi oppilaitos :voimassa true}))
                                :kieli "fi"
                                :tutkinto nil})))

(defn amispalaute-tunnus [data]
  (let [koulutustoimija (:koulutustoimija_oid data)
        kyselykertaid (:kyselykertaid (kyselykerta/hae-automaatti-kyselykerta koulutustoimija "ammatillisen-opiskelijapalaute" (:kyselyn_tyyppi data)))]
    (automaatti-vastaajatunnus :ammatillisen-opiskelijapalaute
                               {:kyselykertaid kyselykertaid
                                :voimassa_alkupvm (:vastaamisajan_alkupvm data)
                                :voimassa_loppupvm (:vastaamisajan_loppupvm data)
                                :koulutustoimija koulutustoimija
                                :heratepvm (:heratepvm data)
                                :kieli (:tutkinnon_suorituskieli data)
                                :toimipiste (:toimipistekoodi (db/hae-organisaatio {:oid (:toimipiste_oid data)}))
                                :toimipiste_oid (:oid (db/hae-oidilla {:oid (:toimipiste_oid data)}))
                                :valmistavan_koulutuksen_oppilaitos (:oid (db/hae-organisaatio {:oid (:oppilaitos_oid data)}))
                                :tutkinto (:tutkintotunnus data)
                                :osaamisala (:osaamisala data)
                                :hankintakoulutuksen_toteuttaja (:ytunnus (db/hae-organisaatio {:oid (:hankintakoulutuksen_toteuttaja data)}))
                                ;;TODO: put back CSCARVO-1692 poista rahoitusr
                                ;:rahoitusryhma (:rahoitusryhma data)
                                :tarkenne (:kyselyn_tyyppi data)
                                :metatiedot (:metatiedot data)})))

(defn tyopaikkaohjaaja-tunnus [data]
  (let [koulutustoimija (:koulutustoimija_oid data)
        kyselykertaid (:kyselykertaid (kyselykerta/hae-automaatti-kyselykerta koulutustoimija "tyopaikkaohjaajakysely" (:kyselyn_tyyppi data)))]
    (automaatti-vastaajatunnus :tyopaikkaohjaajakysely
                               (merge data
                                 {:kyselykertaid kyselykertaid
                                  :koulutustoimija koulutustoimija
                                  :toimipiste (:toimipistekoodi (db/hae-oidilla {:oid (:toimipiste_oid data)}))
                                  :toimipiste_oid (:oid (db/hae-oidilla {:oid (:toimipiste_oid data)}))
                                  :valmistavan_koulutuksen_oppilaitos (:oid (db/hae-organisaatio {:oid (:oppilaitos_oid data)}))
                                  :tutkinto (:tutkintotunnus data)
                                  :kieli "fi"
                                  :voimassa_alkupvm (:vastaamisajan_alkupvm data)
                                  :voimassa_loppupvm (:vastaamisajan_loppupvm data)}))))

(defn tyopaikkakysely-tunnus [data]
  (let [koulutustoimija (:koulutustoimija_oid data)
        kyselykertaid (:kyselykertaid (kyselykerta/hae-automaatti-kyselykerta koulutustoimija "tyopaikkakysely" nil))]
    (automaatti-vastaajatunnus :tyopaikkakysely
                               (merge {:kyselykertaid kyselykertaid :kieli nil :tutkinto nil :valmistavan_koulutuksen_oppilaitos nil
                                       :voimassa_alkupvm (:vastaamisajan_alkupvm data) :voimassa_loppupvm (:vastaamisajan_loppupvm data)}
                                      (select-keys data [:tyonantaja :tyopaikka :tyopaikka_normalisoitu
                                                         :tyopaikkajakson_alkupvm :tyopaikkajakson_loppupvm
                                                         :tiedonkeruu_alkupvm :tiedonkeruu_loppupvm])))))

(defn nippu [data]
  (log/info "Luodaan nippu tiedoilla " data)
  (let [koulutustoimija (:koulutustoimija_oid data)
        kyselykertaid   (:kyselykertaid (kyselykerta/hae-automaatti-kyselykerta koulutustoimija "tyopaikkaohjaajakysely" nil))
        taustatiedot {:tutkinto (:tutkintotunnus data)
                      :tyonantaja (:tyonantaja data)
                      :tyopaikka (:tyopaikka data)}]
    (merge data {:kyselykertaid kyselykertaid :taustatiedot  taustatiedot :koulutustoimija koulutustoimija}
                (tunnus-voimassaolo :tyopaikkaohjaajakysely (:voimassa_alkupvm data) (:voimassa_loppupvm data)))))

(defn lisaa-tyopaikkaohjaaja-tunnus! [data]
  (log/info "Luodaan työpaikkaohjaajakyselyn tunnus:" data)
  (let [tunnus (tyopaikkaohjaaja-tunnus data)]
    (arkisto/lisaa-automaattitunnus! tunnus)))

(defn lisaa-tyopaikkakysely-tunnus! [data]
  (log/info "Luodaan työpaikkakyselyn tunnus:" data)
  (let [tunnus (tyopaikkakysely-tunnus data)
        tunnus-olemassa (db/tyopaikkakyselyn-tunnus-olemassa? tunnus)]
    (if-not tunnus-olemassa
      (arkisto/lisaa-automaattitunnus! tunnus)
      {:error {:error "tunnus-olemassa" :msg "Samoilla tiedoilla oleva tunnus on jo olemassa"}})))

(defn lisaa-amispalaute-tunnus! [data]
  (log/info "Luodaan ammatillisen opiskelijapalautteen tunnus tiedoilla" data)
  (let [tunnus (amispalaute-tunnus data)]
    (arkisto/lisaa-automaattitunnus! tunnus)))

(defn lisaa-kyselyynohjaus! [data]
  (log/info "Luodaan avop/kandipalaute tunnus:" data)
  (let [tunnus (palaute-tunnus data)]
    (arkisto/lisaa-automaattitunnus! tunnus)))

(defn lisaa-rekry-tunnus! [data]
  (log/info "Luodaan rekrykyselyn tunnus:" data)
  (let [tunnus (rekry-tunnus data)]
    (arkisto/lisaa-automaattitunnus! tunnus)))

(defn validoi-taustatieto [nippu taustatieto tunnukset]
  (if (every? #(= (get-in nippu taustatieto) (get-in % taustatieto)) tunnukset)
    {:valid true}
    {:valid false :error (str "inconsistent info: " taustatieto)}))

(defn validoi-nippu [nippu tunnukset]
  (cons (if (= (count tunnukset) (count (:tunnukset nippu)))
          {:valid true} {:valid false :error "invalid-tunnukset"})
    ((juxt
       #(validoi-taustatieto nippu [:koulutustoimija] %)
       #(validoi-taustatieto nippu [:taustatiedot :tutkinto] %))
     tunnukset)))

(defn niputa-tunnukset! [data]
  (let [nippu (nippu data)
        tunnukset (db/hae-niputettavat-tunnukset {:tunnukset (map :tunnus (:tunnukset data))})
        validation-result (validoi-nippu nippu tunnukset)]
    (if (every? :valid validation-result)
      (do
        (arkisto/paivita-nipun-tunnukset (:tunnukset nippu))
        (arkisto/niputa-tunnukset nippu))
      {:errors (->> validation-result
                    (filter #(not (:valid %)))
                    (map :error))})))

(defn poista-nippu [tunniste]
  (let [tunnukset (db/hae-nipun-tunnukset {:tunniste tunniste})]
    (if (not-any? :vastattu tunnukset)
      (arkisto/poista-nippu tunniste)
      {:error "Nipussa on jo vastauksia"})))

(defn paivita-tila [metatiedot vanhat-metatiedot]
  (if (= (:tila vanhat-metatiedot) "lahetetty")
    (assoc metatiedot :tila "lahetetty")
    metatiedot))

(defn paivita-metatiedot [tunnus metatiedot]
  (let [vanhat-metatiedot (:metatiedot (db/hae-vastaajatunnuksen-tiedot {:tunnus tunnus}))
        paivitettavat-metatiedot (paivita-tila metatiedot vanhat-metatiedot)
        paivitettava-vastaajatunnus {:metatiedot paivitettavat-metatiedot
                                     :tunnus tunnus
                                     :kayttaja arvo.infra.kayttaja.vakiot/integraatio-uid}
        riveja-paivitetty (db/paivita-metatiedot! paivitettava-vastaajatunnus)]
    (assoc paivitettavat-metatiedot :riveja riveja-paivitetty)))

(defn paivita-nipun-metatiedot [tunniste metatiedot]
  (let [vanhat-metatiedot (:metatiedot (db/hae-nippu {:tunniste tunniste}))
        paivitettavat-metatiedot (paivita-tila metatiedot vanhat-metatiedot)
        riveja-paivitetty (db/paivita-nipun-metatiedot! {:tunniste tunniste :metatiedot paivitettavat-metatiedot})]
    (assoc paivitettavat-metatiedot :riveja riveja-paivitetty)))

(defn paivita-nippu! [tunniste data]
  (let [nippu (db/hae-nippu {:tunniste tunniste})
        paivitettavat-metatiedot (paivita-tila {:tila (:tila data)} (:metatiedot nippu))
        riveja-paivitetty (when nippu (db/paivita-nippu! {:tunniste          tunniste
                                                          :voimassa_loppupvm (or (:voimassa_loppupvm data) (:voimassa_loppupvm nippu))
                                                          :metatiedot        paivitettavat-metatiedot}))]
    (assoc data :riveja (or riveja-paivitetty 0))))

(defn poista-vastaajatunnus! [tunnus kyselytyyppi]
  (let [{vastattu :vastattu
         tyyppi :kyselytyyppi} (db/vastaajatunnus-status {:tunnus tunnus})]
    (when (and (not vastattu) (= tyyppi kyselytyyppi))
      (db/poista-vastaajatunnus! {:tunnus tunnus}))))

(defn paivita-taustatiedot [tunnus paivitettavat-tiedot kyselytyyppi]
  (when-let* [vastaajatunnus (db/hae-vastaajatunnuksen-tiedot {:tunnus tunnus})
              _ (= kyselytyyppi (:kyselytyyppi vastaajatunnus))
              sallitut-taustatiedot (map (comp keyword :kentta_id) (kyselytyypit/kyselytyypit (keyword kyselytyyppi)))
              paivitettavat-taustatiedot (select-keys paivitettavat-tiedot sallitut-taustatiedot)
              riveja_paivitetty (db/paivita-taustatiedot! {:vastaajatunnus tunnus :taustatiedot paivitettavat-taustatiedot})]
    (assoc paivitettavat-taustatiedot :riveja (or riveja_paivitetty 0))))

(defn kysely-vastattavissa? [{:keys [kyselytila kyselyvoimassa_alkupvm kyselyvoimassa_loppupvm] :as tiedot}]
  (and (= kyselytila "julkaistu")
       (pvm-util/voimassa-java-date? kyselyvoimassa_alkupvm kyselyvoimassa_loppupvm)))

(defn kyselykerta-vastattavissa? [{:keys [kyselykertalukittu kyselykertavoimassa_alkupvm kyselykertavoimassa_loppupvm] :as tiedot}]
  (and (not kyselykertalukittu)
       (pvm-util/voimassa-java-date? kyselykertavoimassa_alkupvm kyselykertavoimassa_loppupvm)))

(defn validoi-vastaajatunnus [{:keys [voimassa_alkupvm voimassa_loppupvm tunnusten_lkm kohteiden_lkm kyselykertaid kayttaja_oid] :as vastaajatunnus}]
  (let [kyselykerta-vastattavissa-tiedot (db/hae-kyselykerta-vastattavissa-tiedot {:kyselykertaid kyselykertaid})
        kayttaja (db/hae-kayttaja {:kayttajaOid kayttaja_oid})]
    [(when-not (or (nil? voimassa_loppupvm)
                   (= voimassa_alkupvm voimassa_loppupvm)
                   (jt/before? voimassa_alkupvm voimassa_loppupvm))
       "vastaajatunnus.ei-voimassa")
     (when-not (pos-int? tunnusten_lkm)
       "vastaajatunnus.tunnusten-lkm-ei-pos-int")
     (when-not (pos-int? kohteiden_lkm)
       "vastaajatunnus.kohteiden-lkm-ei-pos-int")
     (when (and (> kohteiden_lkm 1) (> tunnusten_lkm 1))
       "vastaajatunnus.useita-ryhmatunnuksia")
     (when-not (kyselykerta-vastattavissa? kyselykerta-vastattavissa-tiedot)
       "vastaajatunnus.kyselykerta-ei-validi")
     (when-not (kysely-vastattavissa? kyselykerta-vastattavissa-tiedot)
       "vastaajatunnus.kysely-ei-validi")
;     Tämä voitaisiin hakea with-kayttaja avulla jolloin myös käyttäjän tiedot päivitettäisiin mutta ei ole nykyisessä käyttötapauksessa tarpeellista
     (when-not (and (some? kayttaja) (:voimassa kayttaja))
       "vastaajatunnus.kayttaja-ei-validi")]))

(defn lisaa-vastaajatunnus! [vastaajatunnus]
  (for [tunnus (arkisto/get-vastaajatunnukset (:tunnusten_lkm vastaajatunnus))
        :let [tallennettava-tunnus (assoc vastaajatunnus :tunnus tunnus)]]
    (arkisto/lisaa-vastaajatunnus! tallennettava-tunnus)))
