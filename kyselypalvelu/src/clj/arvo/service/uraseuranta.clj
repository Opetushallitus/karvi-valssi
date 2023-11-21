(ns arvo.service.uraseuranta
  (:require [arvo.util.file :refer [load-data]]
            [arvo.util.excel :as excel]
            [arvo.db.core :refer [*db*] :as db]
            [arvo.util.vastaajatunnus :refer [luo-tunnuksia]]
            [arvo.service.vastaajatunnus :as vastaajatunnus]
            [clojure.java.jdbc :as jdbc]
            [clojure.data :refer [diff]]
            [clojure.tools.logging :as log]
            [arvo.kyselytyypit :refer [kyselytyypit]]
            [arvo.util :refer [update-selected-vals]]
            [java-time.api :as jt]
            [arvo.util.paivamaara-util :as pvm-util]))

(defn hae-kyselykerrat [tunniste]
  (db/hae-uraseuranta-kyselykerrat {:tunniste tunniste}))

(defn uraseuranta-tyyppi [vastaaja]
  (case (:tutkinnon_taso vastaaja)
    "7" "tohtorit"
    "4" "maisterit"
    "2" "maisterit"
    "3" "amk"
    "1" "amk"))

(defn luo-tunniste [hetu etunimet sukunimi]
  (let [paiva (subs hetu 0 2)
        kuukausi (subs hetu 2 4)
        vuosi (subs hetu 4 6)]
    (str sukunimi " " etunimet " 19" vuosi kuukausi paiva)))


(defn henkilo-tunniste [virta-data]
  (if (= 11 (count (:henkilotunnus virta-data)))
    (:henkilotunnus virta-data)
    (luo-tunniste (:henkilotunnus virta-data) (:etunimet virta-data) (:sukunimi virta-data))))

(defn format-tunnus [kohde tunnus taustatieto-kentat]
  (-> kohde
      (merge {:tutkinto (:tutkinto_koulutuskoodi kohde)
              :valmistavan_koulutuksen_oppilaitos (:oppilaitos-oid kohde)
              :kieli (:koulutuskieli kohde)
              :paaaine (:aine kohde)
              :kohteiden_lkm 1})
      (vastaajatunnus/format-vastaajatunnus tunnus taustatieto-kentat)
      (assoc :kieli (:koulutuskieli kohde))
      (assoc :opiskelijatunnus (:opiskelijatunnus kohde))
      (assoc :henkilotunnus (:henkilotunnus kohde))
      (assoc :tunniste (henkilo-tunniste kohde))))

(defn lisaa-kyselykerta [kohde kyselykerrat]
  (let [kyselykerta (first (filter #(and (= (:oppilaitoskoodi %) (:oppilaitoskoodi kohde))
                                        (= (:tyyppi %) (uraseuranta-tyyppi kohde))) kyselykerrat))] ;(get kyselykerrat [(:oppilaitoskoodi kohde) (uraseuranta-tyyppi kohde)])]
    (merge kohde {:kyselykertaid (:kyselykertaid kyselykerta)
                  :oppilaitos-oid (:oid kyselykerta)})))

(defn generoi-tunnukset [tunniste data]
  (let [kyselykerrat (hae-kyselykerrat tunniste)
        kyselytyyppi (keyword (:kyselytyyppi (db/hae-tiedonkeruu {:tunniste "yo-uraseuranta-maisterit-2022"})))
        taustatieto-kentat (map (comp keyword :kentta_id) (kyselytyypit kyselytyyppi))
        kohteet (filter #(some? (:kyselykertaid %)) (map #(lisaa-kyselykerta % kyselykerrat) data))
        tunnuksia (:tunnuksia (db/vastaajatunnusten-lkm))
        tunnukset (luo-tunnuksia tunnuksia (count kohteet))]
    (map #(format-tunnus %1 %2 taustatieto-kentat) kohteet tunnukset)))

(defn lisaa-tunnus [tx tunnus]
  (let [vastaajatunnus (db/lisaa-vastaajatunnus! tx tunnus)]
    (db/lisaa-uraseuranta-yhteystieto! tx {:vastaajatunnusid (:vastaajatunnusid (first vastaajatunnus))
                                           :opiskelijatunnus (:opiskelijatunnus tunnus)})))

(defn lisaa-kohteet [tunniste tempfile filename]
  (let [tunnukset (generoi-tunnukset tunniste (load-data tempfile filename))
        lisattavat (filter some? tunnukset)
        lisatyt (jdbc/with-db-transaction [tx *db* {:isolation :read-uncommitted}]
                  (doall
                    (for [tunnus lisattavat]
                       (let [id (:id (first (lisaa-tunnus tx tunnus)))]
                         (assoc tunnus :id id)))))]
    (excel/generate-excel lisatyt [:id :henkilotunnus] "yhteystiedot")))

(defn hae-yhteystiedot [kyselykertaid]
  (let [yhteystiedot (db/hae-yhteystiedot {:kyselykertaid kyselykertaid})]
    (excel/generate-excel yhteystiedot [:id :opiskelijatunnus :sahkoposti :puhelinnumero :asiointikieli] "Yhteystiedot")))

(defn paivita-yhteystiedot [kyselykertaid yhteystiedot]
  (jdbc/with-db-transaction [tx *db*]
    (log/info "Päivitetään" (count yhteystiedot) "yhteystietoa kyselykertaan" kyselykertaid)
    (doseq [yhteystieto yhteystiedot]
      (db/paivita-yhteystieto! tx (assoc yhteystieto :kyselykertaid kyselykertaid)))
    (count yhteystiedot)))


(defn hae-vanhat-yhteystiedot [kyselykertaid]
  (into {}
    (for [[k v] (group-by :id (db/hae-yhteystiedot {:kyselykertaid kyselykertaid}))]
      [k (first v)])))

(defn paivitettavat-yhteystiedot [yhteystiedot kyselykertaid]
  (let [vanhat (hae-vanhat-yhteystiedot kyselykertaid)]
    (filter #(not= % (get vanhat (:id %))) (map #(update % :id int) yhteystiedot))))

(defn lisaa-yhteystiedot [kyselykertaid tempfile filename]
  (let [yhteystiedot (filter #(some? (:id %)) (load-data tempfile filename))
        paivitettavat (paivitettavat-yhteystiedot yhteystiedot kyselykertaid)
        paivitetty (paivita-yhteystiedot kyselykertaid paivitettavat)]
    paivitetty))

(defn lisaa-yo-puhelinnumerot [tiedonkeruu tempfile filename]
  (let [data (load-data tempfile filename)]
    (doseq [puhelinnumero data]
      (db/lisaa-yo-puhelinnumero! (assoc puhelinnumero :tiedonkeruu tiedonkeruu)))
    (count data)))

(defn lisaa-yo-osoitetiedot [tiedonkeruu tempfile filename]
  (let [data (load-data tempfile filename)]
    (doseq [osoite data]
     (db/lisaa-yo-osoitetieto! (assoc osoite :tiedonkeruu tiedonkeruu)))
    (count data)))

(defn lisaa-yo-tunnus [tx tunnus tiedonkeruu]
  (let [vastaajatunnus (db/lisaa-vastaajatunnus! tx tunnus)]
    (db/lisaa-yo-uraseuranta-tunniste! tx {:vastaajatunnusid (:vastaajatunnusid (first vastaajatunnus))
                                           :tunniste (:tunniste tunnus)
                                           :opiskelijatunnus (:opiskelijatunnus tunnus)
                                           :tiedonkeruu tiedonkeruu})))

(defn lisaa-yo-poiminta [tiedonkeruu tempfile filename]
  (let [tunnukset (generoi-tunnukset tiedonkeruu (load-data tempfile filename))
        lisattavat (filter some? tunnukset)]
    (jdbc/with-db-transaction [tx *db* {:isolation :read-uncommitted}]
      (doseq [tunnus lisattavat]
        (let [id (:id (first (lisaa-yo-tunnus tx tunnus tiedonkeruu)))]
          (assoc tunnus :id id)))
      (count lisattavat))))

(def tupa-fields [:tunnus :oppilaitoskoodi :oppilaitos_nimi :valmistumisvuosi :valmistumisajankohta :opiskelijatunnus,
                  :sukupuoli :ika_valmistuessa :kansalaisuus :aidinkieli :koulutusalakoodi :koulutusala :paaaine :tutkinnon_taso :tutkinto_koulutuskoodi :tutkinto_nimi
                  :laajuus :valintavuosi :asuinkunta_koodi :asuinkunta_nimi :kirjoilla_olo_kuukausia :lasnaolo_lukukausia :arvosana :asteikko
                  :sukunimi :etunimet :dvv_sukupuoli :dvv_aidinkieli :lahiosoite :postinumero :postitoimipaikka :kotim_osoitt_muuttopaiva
                  :kotikunta :kotikunnan_nimi :vakinainen_ulkomainen_osoite :ulkomaisen_osoitteen_paikkakunta :ulkomaisen_asuinvaltion_postinimi :asuinvaltio :ulkom_asuinvaltion_nimi :ulkomaille_muuton_pv
                  :matkapuhelin :haltijaliittyma :yritysliittyma])

(def local-date-format "d.M.yyyy")

(defn format-dates [row fields target-format]
  (update-selected-vals row fields
                        (fn [val]
                          (when (some? val)
                            (jt/format target-format (pvm-util/parse-ymd val))))))

(defn format-virta-dates [row]
  (format-dates row [:valmistumisajankohta :valintavuosi] local-date-format))

(defn dvv-to-iso-format [date]
  (let [year (subs date 0 4)
        month (subs date 4 6)
        day (subs date 6 8)]
    (str year "-" month "-" (if (= "00" day) "01" day))))

(defn format-dvv-dates [row]
  (update-selected-vals row [:kotim_osoitt_muuttopaiva :ulkomaille_muuton_pvi]
                        (fn [val]
                          (some->> val
                                   dvv-to-iso-format
                                   pvm-util/parse-ymd
                                   (jt/format local-date-format)))))

(defn format-tupa-tunnus [tunnus]
  (merge (select-keys tunnus tupa-fields)
         (select-keys (:taustatiedot tunnus) tupa-fields)))

(defn hae-tupa-lista [tunniste]
  (let [data (db/hae-tupa-lista {:tunniste tunniste})
        tupa-tiedot (vec (map (comp format-virta-dates format-dvv-dates format-tupa-tunnus) data))]
    (excel/generate-excel tupa-tiedot tupa-fields "Tiedot")))
