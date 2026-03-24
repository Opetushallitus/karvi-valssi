(ns arvo.service.csv
  (:require [clojure-csv.core :refer [write-csv]]
            [oph.common.util.http-util :refer [parse-iso-date]]
            [oph.common.util.util :refer [map-by]]
            [clojure.core.match :refer [match]]
            [arvo.toimiala.raportti.util :refer [muuta-kaikki-stringeiksi]]
            [arvo.db.core :as db]
            [arvo.arkisto.kysely :refer [aseta-jatkokysymysten-jarjestys hae-kyselyn-kysymykset]]
            [arvo.arkisto.tutkinto :as tutkinto]
            [arvo.service.kysymys :as kysymys-service]
            [arvo.config :refer [env]]
            [arvo.util :refer [in?]]
            [arvo.integraatio.koodistopalvelu :refer [hae-kunnat hae-osaamisalat hae-tutkintonimikkeet hae-rahoitusryhmat]]
            [clojure.tools.logging :as log]
            [arvo.util.csv :as csv]
            [java-time.api :as jt]
            [arvo.util.paivamaara-util :as pvm-util]
            [arvo.kyselytyypit :refer [kyselytyypit]]
            [clojure.string :as string]
            [arvo.db.raportti :as raportti-db]
            [arvo.translations :refer [translate-field translate]]))

(def default-delimiter \;)

(defn csv-response [kysely lang data]
  (let [koulutustoimija (db/hae-organisaatio {:oid (:koulutustoimija kysely)})]
    {:nimi (translate-field kysely "nimi" lang)
     :koulutustoimija (translate-field koulutustoimija "nimi" lang)
     :date (pvm-util/format-ymd (jt/local-date))
     :csv data}))

(defn vastaajatunnus-url [tunnus]
  (str (:vastaus-base-url env) "/v/" (:tunnus tunnus)))

(defn kyselytyypin-taustatiedot [kyselytyyppi]
  (->> (get kyselytyypit kyselytyyppi)
       (filter #(get-in % [:raportointi :csv :raportoi]))))

(defn format-date [datetime]
  (let [local-date (cond
                     (jt/local-date? datetime) datetime
                     (some? datetime) (jt/local-date datetime "UTC"))]
    (pvm-util/format-ymd local-date)))

(defn replace-control-chars [text]
  (clojure.string/escape text {\newline " " \tab " " default-delimiter \,}))

(defn hae-selitteet [kyselyid]
  {:tutkinnot (db/hae-kyselyn-tutkinnot {:kyselyid kyselyid})
   :toimipisteet (db/hae-kyselyn-toimipaikat {:kyselyid kyselyid})
   :hankintakoulutuksen-toteuttajat (db/hae-kyselyn-hankintakoulutuksen-toteuttajat {:kyselyid kyselyid})
   :koulutustoimijat (db/hae-kyselyn-koulutustoimijat {:kyselyid kyselyid})
   :koulutusalat (db/hae-kyselyn-koulutusalat {:kyselyid kyselyid})
   :kunnat (hae-kunnat (:koodistopalvelu env))
   :tutkinnonosat (tutkinto/hae-tutkinnon-osat)
   :osaamisala (hae-osaamisalat (:koodistopalvelu env))
   :tutkintonimikkeet (hae-tutkintonimikkeet (:koodistopalvelu env))
   :rahoitusryhma (hae-rahoitusryhmat (:koodistopalvelu env))})

(defn hae-koodisto [koodisto]
  {koodisto (db/hae-koodiston-koodit {:koodistouri koodisto})})

(defn hae-koodistot [kysymykset]
  (->> kysymykset
       (map #(get-in % [:kysymys_metatiedot :koodisto]))
       (filter some?)
       (into #{})
       (map hae-koodisto)
       (apply merge)))

(defn format-metatiedot [kyselytyyppi lang metatiedot]
  (let [nippu (:nippu metatiedot)
        tila (or (keyword (:tila metatiedot))
                 (if (and (= kyselytyyppi "tyopaikkaohjaajakysely") (nil? nippu))
                   :odottaa_niputusta
                   :niputettu))]
    (merge metatiedot
      {:tila (translate [lang :vastaajatunnus :tila tila])})))

(defn seq-to-str [xs]
  (apply str (interpose \, xs)))

(defn lisaa-selitteet [data selitteet lang]
  (-> data
      (assoc :tutkinto_selite
             (translate-field (first (filter #(= (:tutkinto data) (:tutkintotunnus %)) (:tutkinnot selitteet))) "tutkinto" lang))
      ;; overwrites default field which contains only id:s for osaamisala
      (assoc :osaamisala
        (seq-to-str (map (fn [osaamisala]
                           (translate-field
                             (first (filter #(= osaamisala (:osaamisalakoodi %)) (:osaamisala selitteet))) "nimi" lang)) (:osaamisala data))))
      ;; overwrites default field which contains only id:s for tutkintonimike
      (assoc :tutkintonimike
        (seq-to-str (map (fn [tutkintonimike]
                           (translate-field
                             (first (filter #(= tutkintonimike (:tutkintonimikekoodi %)) (:tutkintonimikkeet selitteet))) "nimi" lang)) (:tutkintonimike data))))
      (assoc :toimipiste_oid
             (translate-field
               (first (filter #(= (:toimipiste_oid data) (:toimipiste_oid %)) (:toimipisteet selitteet))) "nimi" lang))
      (assoc :hankintakoulutuksen_toteuttaja_selite
             (translate-field
               (first (filter #(= (:hankintakoulutuksen_toteuttaja data) (:ytunnus %)) (:hankintakoulutuksen-toteuttajat selitteet))) "nimi" lang))
      (assoc :koulutustoimija_selite
             (translate-field (first (filter #(= (:koulutustoimija data) (:ytunnus %)) (:koulutustoimijat selitteet))) "nimi" lang))
      (assoc :koulutusalakoodi_selite
             (translate-field
               (first (filter #(= (:koulutusalakoodi data) (:koulutusalatunnus %)) (:koulutusalat selitteet))) "nimi" lang))
      (assoc :asuinkunta_koodi_selite
             (translate-field
               (first (filter #(= (:asuinkunta_koodi data) (:kuntakoodi %)) (:kunnat selitteet))) "nimi" lang))
      (assoc :opiskelupaikkakunta_koodi_selite
             (translate-field
               (first (filter #(= (:opiskelupaikkakunta_koodi data) (:kuntakoodi %)) (:kunnat selitteet))) "nimi" lang))
      (assoc :tutkinnon_osa_selite
             (translate-field
               (first (filter #(= (:tutkinnon_osa data) (:koodi_arvo %)) (:tutkinnonosat selitteet))) "nimi" lang))
      (assoc :rahoitusryhma_selite
             (translate-field
               (first (filter #(= (:rahoitusryhma data) (:rahoitusryhmakoodi %)) (:rahoitusryhma selitteet))) "nimi" lang))))

(defn format-tunnus [tunnus kyselytyyppi selitteet lang]
  (-> tunnus
      (merge (:taustatiedot tunnus))
      (merge (:metatiedot tunnus))
      (dissoc :taustatiedot)
      (assoc :oppilaitos_nimi (translate-field tunnus "oppilaitos_nimi" lang))
      (assoc :vastaajatunnus (:tunnus tunnus))
      (merge (format-metatiedot kyselytyyppi lang (:metatiedot tunnus)))
      (assoc :url (vastaajatunnus-url tunnus))
      (update :voimassa_alkupvm format-date)
      (update :voimassa_loppupvm format-date)
      (update :luotuaika format-date)
      (lisaa-selitteet selitteet lang)))

; Vastaus

(defn hae-monivalintavaihtoehto [choices lang answer]
  (let [arvo (:numerovalinta answer)
        choice (first (filter #(= arvo (:arvo %)) choices))]
    (translate-field choice "teksti" lang)))

(defn numero-tai-eos [answer]
  (match [(some? (:numerovalinta answer)) (some? (:en_osaa_sanoa answer))]
         [true _] (:numerovalinta answer)
         [false true] "eos"
         [false false] ""))

(defn korjaa-vastauksen-koodiarvo
  "Numerovalinta-kenttä on numero joten koodiston alkupään nollat pitää lisätä erikseen vertailuarvoon."
  [vastaus-arvo koodisto]
  (loop [korjattu-arvo vastaus-arvo]
    (if (>= (count korjattu-arvo) (count (:koodi_arvo (first koodisto))))
      korjattu-arvo
      (recur (str "0" korjattu-arvo)))))

(defn alasvetovalikko-vastaus [answers koodistot lang]
  (let [answer (first answers)
        koodisto (get-in koodistot [(:koodisto answer)])
        vastaus-arvo (-> answer
                         :numerovalinta
                         str
                         (korjaa-vastauksen-koodiarvo koodisto))
        koodi (first (filter #(= (:koodi_arvo %) vastaus-arvo) koodisto))]
    (translate-field koodi "nimi" lang)))

(defn get-answer-text [moivalintavaihtoehdot type answers koodistot lang]
  (match [type]
         ["arvosana"] (:numerovalinta (first answers))
         ["arvosana4_ja_eos"] (numero-tai-eos (first answers))
         ["arvosana6_ja_eos"] (numero-tai-eos (first answers))
         ["arvosana6"] (:numerovalinta (first answers))
         ["arvosana7"] (:numerovalinta (first answers))
         ["asteikko5_1"] (:numerovalinta (first answers))
         ["nps"] (:numerovalinta (first answers))
         ["monivalinta"] (->> answers
                              (map #(hae-monivalintavaihtoehto moivalintavaihtoehdot lang %))
                              (clojure.string/join ", "))
         ["likert_asteikko"] (:numerovalinta (first answers))
         ["vapaateksti"] (when (:vapaateksti (first answers))
                           (replace-control-chars (:vapaateksti (first answers))))
         ["kylla_ei_valinta"] (:vaihtoehto (first answers))
         ["luku"] (:luku (first answers))
         ["alasvetovalikko"] (alasvetovalikko-vastaus answers koodistot lang)
         :else ""))

; Käännökset

(defn csv-kaannokset [kysely lang]
  (let [taustatieto-kaannokset (into {}
                                     (for [taustatieto (kyselytyypit (keyword(:tyyppi kysely)))]
                                       [(keyword (:kentta_id taustatieto)) (translate-field taustatieto "kentta" lang)]))
        kysymys-kaannokset (apply merge (flatten
                                          (for [kr (:kysymysryhmat kysely)]
                                            (for [k (:kysymykset kr)]
                                              {(keyword (str (:kysymysid k))) (translate-field k "kysymys" lang)}))))]
    (merge (translate [lang :csv])
           (translate [lang :vastaajatunnus :tila])
           taustatieto-kaannokset kysymys-kaannokset)))


;Filter

(defn poista-valiotsikot [kysymykset]
  (filter #(not= (:vastaustyyppi %) "valiotsikko") kysymykset))

(defn poista-raportoimattomat [kysymykset]
  (filter #(not= false (-> % :metatiedot :raportointi :csv)) kysymykset))

(defn filter-kysymykset [kysely kysymykset]
  (->> kysymykset
       poista-valiotsikot
       poista-raportoimattomat
       (filter #(kysymys-service/kysymys-nakyvissa? % (:voimassa_alkupvm kysely)))))

(defn default-header-fields [kyselytyyppi]
  (case kyselytyyppi
    "ammatillisen-opiskelijapalaute" [:vastaajatunnus :vastausaika :oppilaitos_nimi]
    "tyopaikkaohjaajakysely" [:vastaajatunnus :nippu :vastausaika]
    [:vastaajatunnus :vastausaika]))


(defn luovutuslupa [[_ vastaukset] kysymysid]
  (= 0 (:numerovalinta (first (filter #(= kysymysid (:kysymysid %)) vastaukset)))))

(defn filter-not-allowed [kyselytyyppi kysymykset vastaukset]
  (let [lupakysymys (:kysymysid (first (filter #(= "tietojen_luovutus" (-> % :metatiedot :taustakysymyksen_tyyppi)) kysymykset)))]
    (if (and lupakysymys (some #{"amk-uraseuranta"} #{kyselytyyppi}))
      (filter #(luovutuslupa % lupakysymys) vastaukset)
      vastaukset)))


(defn taustatieto-header [taustatieto]
  (let [kentta-id (:kentta_id taustatieto)]
    (if (get-in taustatieto [:raportointi :csv :selitteet])
      [(keyword kentta-id) (keyword (str kentta-id "_selite"))]
      [(keyword kentta-id)])))

; Vastaajittain

(defn vastaajittain-kysymys-header [kysely]
  (flatten
    (for [kr (:kysymysryhmat kysely)]
      (for [k (sort-by :jarjestys (filter-kysymykset kysely (:kysymykset kr)))]
        (keyword (str (:kysymysid k)))))))

(defn vastaajittain-header [kysely]
  (let [taustatiedot (kyselytyypit (keyword (:tyyppi kysely)))
        csv-taustatiedot (->> taustatiedot
                              (filter #(get-in % [:raportointi :csv :raportoi]))
                              (sort-by #(get-in % [:raportointi :csv :jarjestys]))
                              (map taustatieto-header)
                              flatten)
        kysymys-header (vastaajittain-kysymys-header kysely)]
    (concat (default-header-fields (:tyyppi kysely)) csv-taustatiedot kysymys-header)))

(defn hae-kysymys [kysymykset kysymysid]
  (first (filter #(= (:kysymysid %) kysymysid) kysymykset)))

(defn format-vastaus [[kysymys vastaukset] koodistot lang]
  (merge
    {(keyword (str (:kysymysid kysymys)))
     (get-answer-text (:monivalintavaihtoehdot kysymys)
                      (:vastaustyyppi kysymys)
                      vastaukset
                      koodistot
                      lang)}
    (when false (str (:kysymysid kysymys)"_selite") "Selite tähän")))

(defn format-vastaukset [kysely koodistot lang vastaukset]
  (let [kysymykset (mapcat :kysymykset (:kysymysryhmat kysely))
        kysymyksittain (group-by #(hae-kysymys kysymykset (:kysymysid %)) vastaukset)]
    (apply merge
           (map #(format-vastaus % koodistot lang) kysymyksittain))))

(defn format-vastaaja [kysely tunnukset selitteet koodistot [vastaaja vastaukset] lang]
  (let [tunnus (first (filter #(= (:tunnus %) (:vastaajatunnus vastaaja)) tunnukset))]
    (merge
      {:vastausaika (:vastausaika vastaaja)}
      (format-tunnus tunnus (:tyyppi kysely) selitteet lang)
      (format-vastaukset kysely koodistot lang vastaukset))))


(defn csv-data-vastaajittain [kysely koodistot selitteet lang]
  (let [tunnukset (db/hae-csv-kohteet {:kyselyid (:kyselyid kysely) :vastaamattomat false})
        kysymykset (mapcat :kysymykset (:kysymysryhmat kysely))
        vastaukset (->> (db/hae-vastaukset kysely)
                        (group-by #(select-keys % [:vastaajaid :vastaajatunnus :vastausaika]))
                        (filter-not-allowed (:tyyppi kysely) kysymykset))]
    (map #(format-vastaaja kysely tunnukset selitteet koodistot % lang) vastaukset)))

(defn kysely-csv-vastaajittain [kyselyid lang]
  (let [kysely (raportti-db/hae-kysely kyselyid)
        koodistot (hae-koodistot (mapcat :kysymykset (:kysymysryhmat kysely)))
        selitteet (hae-selitteet kyselyid)
        vastaukset (csv-data-vastaajittain kysely koodistot selitteet lang)
        header (vastaajittain-header kysely)
        translations (csv-kaannokset kysely lang)
        data (csv/generate-csv header vastaukset default-delimiter translations)]
    (csv-response kysely lang data)))

; Vastauksittain

(defn vastauksittain-header [kysely]
  (let [taustatiedot (kyselytyypit (keyword (:tyyppi kysely)))
        csv-taustatiedot (->> taustatiedot
                              (filter #(get-in % [:raportointi :csv :raportoi]))
                              (sort-by #(get-in % [:raportointi :csv :jarjestys]))
                              (map taustatieto-header)
                              flatten)]
    (concat (default-header-fields (:tyyppi kysely)) csv-taustatiedot [:kysymysryhma :kysymys :vastaus])))

(defn format-vastaajan-vastaukset [kysely kysymykset tunnukset selitteet koodistot [vastaaja vastaukset] lang]
  (let [tunnus (first (filter #(= (:tunnus %) (:vastaajatunnus vastaaja)) tunnukset))
        taustatiedot (format-tunnus tunnus (:tyyppi kysely) selitteet lang)]
    (for [kysymys (filter-kysymykset kysely kysymykset)]
      (let [kysymyksen-vastaukset (filter #(= (:kysymysid kysymys) (:kysymysid %)) vastaukset)]
        (merge taustatiedot
          {:kysymys (translate-field kysymys :kysymys lang)
           :kysymysryhma (translate-field kysymys :kysymysryhma lang)
           :vastaus (get-answer-text (:monivalintavaihtoehdot kysymys)
                                     (:vastaustyyppi kysymys)
                                     kysymyksen-vastaukset
                                     koodistot
                                     lang)})))))

(defn lisaa-kysymysryhma [kysymysryhma]
  (map #(merge % (select-keys kysymysryhma [:kysymysryhma_fi :kysymysryhma_en :kysymysryhma_fi])) (:kysymykset kysymysryhma)))

(defn csv-data-vastauksittain [kysely koodistot selitteet lang]
  (let [tunnukset (db/hae-csv-kohteet {:kyselyid (:kyselyid kysely) :vastaamattomat false})

        kysymykset (mapcat lisaa-kysymysryhma (:kysymysryhmat kysely))
        vastaukset (->> (db/hae-vastaukset kysely)
                        (group-by #(select-keys % [:vastaajaid :vastaajatunnus :vastausaika]))
                        (filter-not-allowed (:tyyppi kysely) kysymykset))]
    (flatten (map #(format-vastaajan-vastaukset kysely kysymykset tunnukset selitteet koodistot % lang) vastaukset))))

(defn kysely-csv-vastauksittain [kyselyid lang]
  (let [kysely (raportti-db/hae-kysely kyselyid)
        koodistot (hae-koodistot (mapcat :kysymykset (:kysymysryhmat kysely)))
        selitteet (hae-selitteet kyselyid)
        vastaukset (csv-data-vastauksittain kysely koodistot selitteet lang)
        header (vastauksittain-header kysely)
        data (csv/generate-csv header vastaukset default-delimiter (csv-kaannokset kysely lang))]
    (csv-response kysely lang data)))

; Kohteet

(def kohteet-header
  [:tunnus :nimi :voimassa_alkupvm :kohteiden_lkm :vastaajien_lkm :tutkintotunnus :tutkinto_selite])

(defn kohteet-csv [kyselyid lang]
  (let [kysely (raportti-db/hae-kysely kyselyid)
        kohteet (->> (db/hae-kyselyn-kohteet {:kyselyid kyselyid})
                     (map #(assoc % :tutkinto_selite (translate-field % "tutkinto_selite" lang))))]
    (csv/generate-csv kohteet-header kohteet default-delimiter (csv-kaannokset kysely lang))))

; Vastanneet

(def vastanneet-header
  [:tunnus :nimi :voimassa_alkupvm :vastausaika :tutkintotunnus :tutkinto_selite])

(defn vastanneet-csv [kyselyid lang]
  (let [kysely (raportti-db/hae-kysely kyselyid)
        vastanneet (->> (db/hae-kyselyn-vastaajat {:kyselyid kyselyid})
                        (map #(assoc % :tutkinto_selite (translate-field % "tutkinto_selite" lang))))]
    (csv/generate-csv vastanneet-header vastanneet default-delimiter (csv-kaannokset kysely lang))))


; Vastaajatunnukset

(defn vastaajatunnuksen-metatieto-kentat [kyselytyyppi]
  (case kyselytyyppi
    "ammatillisen-opiskelijapalaute" [:tila]
    "tyopaikkaohjaajakysely" [:tila :nippu]
    []))

(def vastaajatunnus-header-fields [:vastaajatunnus :url :luotuaika :voimassa_alkupvm :voimassa_loppupvm :vastausten_lkm :kohteiden_lkm])

(defn vastaajatunnus-header [kysely]
  (let [taustatiedot (kyselytyypit (keyword (:tyyppi kysely)))
        csv-taustatiedot (->> taustatiedot
                              (filter #(get-in % [:raportointi :csv :raportoi]))
                              (sort-by #(get-in % [:raportointi :csv :jarjestys]))
                              (map taustatieto-header)
                              flatten)]
    (concat vastaajatunnus-header-fields
            csv-taustatiedot
            (vastaajatunnuksen-metatieto-kentat (:tyyppi kysely)))))

(defn muodosta-vastaajatunnukset-csv [kyselykertaid lang]
  (let [kyselyid (:kyselyid (db/hae-kyselykerta {:kyselykertaid kyselykertaid}))
        kysely (raportti-db/hae-kysely kyselyid)
        selitteet (hae-selitteet kyselyid)
        tunnukset (->> (db/hae-vastaajatunnus {:kyselykertaid kyselykertaid})
                       (map #(format-tunnus % (:tyyppi kysely) selitteet lang)))

        header (vastaajatunnus-header kysely)
        translations (csv-kaannokset kysely lang)]
    (csv/generate-csv header tunnukset default-delimiter translations)))


(defn taustatieto-kaannokset [taustatiedot lang]
  (into {} (for [taustatieto taustatiedot]
             {(keyword (:kentta_id taustatieto))
              (get taustatieto (keyword (str "kentta_" (name lang))))})))


(def tyopaikkakysely-header [:tunnus :url :voimassa_alkupvm :voimassa_loppupvm :vastausten_lkm :kohteiden_lkm
                             :tyonantaja :tyopaikka :tutkinnot :tutkinnon_osat :tyopaikkajaksojen_lkm :tyopaikkajaksojen_kesto])

(def tyopaikkaohjaaja-header [:tunnus :luotuaika :voimassa_alkupvm :voimassa_loppupvm :vastausten_lkm :kohteiden_lkm
                              :toimipiste :toimipiste_oid :tutkinto :tutkinto_selite :osaamisala :tutkintonimike
                              :tutkinnon_osa :tutkinnon_osa_selite :paikallinen_tutkinnon_osa :sopimustyyppi :tyonantaja :tyopaikka
                              :tyopaikkajakson_alkupvm :tyopaikkajakson_loppupvm :osa_aikaisuus
                              :tyopaikkajakson_kesto :tila :nippu :tyopaikkakysely_tunnus])



(defn taustatiedot [tunnus taustatiedot]
  (into {}
    (for [taustatieto taustatiedot]
      (let [kentta (keyword (:kentta_id taustatieto))]
        {kentta (get-in tunnus [:taustatiedot kentta])}))))

(defn format-tyopaikkakysely-tunnus [tunnus jaksot tutkinnot kyselytyypin-taustatiedot lang]
  (let [tyopaikan-jaksot (filter #(= (:tyopaikkakysely_tunnus %) (:tunnus tunnus)) jaksot)
        jaksojen-tutkinnot (->> tyopaikan-jaksot
                                (map #(get-in % [:taustatiedot :tutkinto]))
                                (distinct))]
    (-> tunnus
        (assoc :url (vastaajatunnus-url tunnus))
        (update :voimassa_alkupvm format-date)
        (update :voimassa_loppupvm format-date)
        (merge (taustatiedot tunnus kyselytyypin-taustatiedot)
               {:tyopaikkajaksojen_lkm   (count tyopaikan-jaksot)
                :tyopaikkajaksojen_kesto (->> tyopaikan-jaksot
                                              (map #(get-in % [:taustatiedot :tyopaikkajakson_kesto]))
                                              (filter some?)
                                              (reduce +))
                :tutkinnot               (->> jaksojen-tutkinnot
                                              (interpose ",")
                                              (apply str))

                :tutkintonimikkeet       (->> (map (fn [tutkintonimike] (translate-field (first (filter #(= tutkintonimike (:tutkintonimikekoodi %)) tutkinnot)) "nimi" lang)) jaksojen-tutkinnot)
                                              (interpose ", ")
                                              (apply str))

                :tutkinnon_osat          (->> tyopaikan-jaksot
                                              (map #(get-in % [:taustatiedot :tutkinnon_osa]))
                                              (distinct)
                                              (interpose ",")
                                              (apply str))})
        (select-keys tyopaikkakysely-header))))

(defn tyopaikkakysely-tunnukset [kyselykertaid lang]
  (let [tunnukset (db/hae-vastaajatunnus {:kyselykertaid kyselykertaid})
        jaksot (db/hae-tyopaikkakyselyn-jaksot {:kyselykertaid kyselykertaid})
        taustatiedot (kyselytyypin-taustatiedot :tyopaikkakysely)
        tutkinnot (db/hae-tutkinnot)
        translations (merge (translate [lang :csv])
                            (translate [lang :vastaajatunnus :tila])
                            (taustatieto-kaannokset taustatiedot lang))]
    (csv/generate-csv tyopaikkakysely-header
                      (map #(format-tyopaikkakysely-tunnus % jaksot tutkinnot taustatiedot lang) tunnukset)
                      default-delimiter
                      translations)))

(defn format-tyopaikkaohjaaja-tunnus [tunnus selitteet kyselytyypin-taustatiedot lang]
  (-> tunnus
      (update :luotuaika format-date)
      (update :voimassa_alkupvm format-date)
      (update :voimassa_loppupvm format-date)
      (merge (taustatiedot tunnus kyselytyypin-taustatiedot)
             (format-metatiedot "tyopaikkaohjaajakysely" lang (:metatiedot tunnus)))
      (select-keys tyopaikkaohjaaja-header)
      (lisaa-selitteet selitteet lang)))

(defn jaksotunnukset [kyselyid kyselykertaid koulutustoimija lang]
  (let [jaksot (db/hae-tyoelamapalaute-tunnukset {:kyselykertaid kyselykertaid :koulutustoimija koulutustoimija})
        taustatiedot (kyselytyypin-taustatiedot :tyopaikkaohjaajakysely)
        translations (merge (translate [lang :csv])
                            (translate [lang :vastaajatunnus :tila])
                            (taustatieto-kaannokset taustatiedot lang))
        selitteet (hae-selitteet kyselyid)
        rivit (map #(format-tyopaikkaohjaaja-tunnus % selitteet taustatiedot lang) jaksot)]
    (csv/generate-csv tyopaikkaohjaaja-header
                      rivit
                      default-delimiter
                      translations)))

(defn vastaajatunnukset-csv [kyselykertaid lang]
  (let [kyselyid (:kyselyid (db/hae-kyselykerta {:kyselykertaid kyselykertaid}))
        kysely (db/hae-kysely {:kyselyid kyselyid})]
    (case (:tyyppi kysely)
      "tyoelamapalaute" (jaksotunnukset kyselyid kyselykertaid (:koulutustoimija kysely) lang)
      "tyopaikkakysely" (tyopaikkakysely-tunnukset kyselykertaid lang)
      (muodosta-vastaajatunnukset-csv kyselykertaid lang))))