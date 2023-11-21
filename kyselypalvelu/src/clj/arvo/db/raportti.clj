(ns arvo.db.raportti
  (:require [arvo.db.core :refer [*db*] :as db]
            [clojure.java.jdbc :as jdbc]
            [clojure.tools.logging :as log]
            [arvo.util :refer [in?]]
            [arvo.raportti-util :as ru]
            [arvo.service.kysymys :as kysymys-service]
            [arvo.arkisto.kysely :as kysely]))

(defn filter->sqlvec [filter]
  (when (second filter)
    (case (first filter)
      :tutkinto                         (db/cond-snip {:cond ["taustatiedot->>'tutkinto'" "=" (second filter)]})
      :suorituskieli                    (db/cond-snip {:cond ["taustatiedot->>'kieli'" "=" (second filter)]})
      :koulutusala                      (db/koulutusala-snip {:koulutusala (second filter)})
      :koulutusmuoto                    (db/cond-snip {:cond ["taustatiedot->>'koulutusmuoto'" "=" (second filter)]})
      :toimipiste                       (db/cond-snip {:cond ["taustatiedot->>'toimipiste'" "=" (second filter)]})
      :tutkinnon_taso                   (db/cond-snip {:cond ["taustatiedot->>'tutkinnon_taso'" "=" (second filter)]})
      :tutkintonimike                   (db/cond-snip {:cond ["taustatiedot->>'tutkintonimike'" "=" (second filter)]})
      :hankintakoulutuksen_toteuttaja   (db/cond-snip {:cond ["taustatiedot->>'hankintakoulutuksen_toteuttaja'" "=" (second filter)]})
      :osaamisala                       (db/cond-snip {:cond ["taustatiedot->'osaamisala'" "??" (second filter)]})
      :oppilaitos                       (db/cond-snip {:cond ["valmistavan_koulutuksen_oppilaitos" "=" (second filter)]})
      :sopimustyyppi                    (db/cond-snip {:cond ["taustatiedot->>'sopimustyyppi'" "=" (second filter)]})
      :oppisopimuksen_perusta           (db/cond-snip {:cond ["taustatiedot->>'oppisopimuksen_perusta'" "=" (second filter)]})
      :tyonantaja                       (db/cond-snip {:cond ["taustatiedot->>'tyonantaja'" "=" (second filter)]})
      :tehtava_yrityksessa              (db/tehtava-snip {:vaihtoehto (second filter)})
      :kyselykerta                      (db/cond-snip {:cond ["kk.kyselykertaid" "=" (second filter)]})
      ;;TODO: put back CSCARVO-1692 poista rahoitusryhmä
      ;:rahoitusryhma                    (db/cond-snip {:cond ["taustatiedot->>'rahoitusryhma'" "=" (second filter)]})
      :tyopaikkakysely_tutkinto         (db/cond-snip {:cond ["j.taustatiedot->>'tutkinto'" "=" (second filter)]})
      nil)))

(defn laske-kuukauden-vertailudata!
  ([tx kuukausi]
   (log/info "Lasketaan vertailudata välille" (:alkupvm kuukausi) "-" (:loppupvm kuukausi)
     (do
       (db/laske-vertailudata! tx kuukausi)
       (db/laske-vertailu-keskiarvot! tx kuukausi))))
  ([kuukausi]
   (jdbc/with-db-transaction [tx *db*]
     (laske-kuukauden-vertailudata! tx kuukausi))))

(defn paivita-vertailudata! [kuukausi]
  (jdbc/with-db-transaction [tx *db*]
    (db/poista-kuukauden-vertailudata! tx kuukausi)
    (laske-kuukauden-vertailudata! tx kuukausi)))

(defn luo-vertailudata! [kuukaudet tyhjenna]
  (doseq [kk kuukaudet]
    (if tyhjenna
      (paivita-vertailudata! kk)
      (laske-kuukauden-vertailudata! kk))))

(def koulutusmuodot [{:arvo "paivamuoto" :nimi_fi "Päivämuoto" :nimi_sv "Dagstudier" :nimi_en "Full-time studies"}
                     {:arvo "monimuoto" :nimi_fi "Monimuoto" :nimi_sv "Flerformsstudier" :nimi_en "Blended learning studies"}])

(def kielet [{:arvo "fi" :nimi_fi "Suomi" :nimi_sv "Finska" :nimi_en "Finnish"}
             {:arvo "sv" :nimi_fi "Ruotsi" :nimi_sv "Svenska" :nimi_en "Swedish"}
             {:arvo "en" :nimi_fi "Englanti" :nimi_sv "Engelsk" :nimi_en "English"}])

(defn rahoitusryhmat []
  (let [koodisto-rr (db/hae-koodiston-koodit {:koodistouri "rahoitusryhma"})]
    (map #(merge (select-keys % [:nimi_fi :nimi_sv :nimi_en]) {:arvo (:koodi_arvo %)}) koodisto-rr)))

(def suodatin->haku
  {:kyselykerta                     (fn [kyselyid] {:type :kyselykerta :values (db/hae-raportin-kyselykerrat {:kyselyid kyselyid})})
   :tutkinto                        (fn [kyselyid] {:type :tutkinto :values (db/hae-kyselyn-tutkinnot {:kyselyid kyselyid})})
   :tutkintonimike                  (fn [kyselyid] {:type :tutkintonimike  :values(db/hae-raportin-tutkintonimikkeet {:kyselyid kyselyid})})
   :koulutusmuoto                   (fn [_] {:type :koulutusmuoto :values koulutusmuodot})
   :hankintakoulutuksen_toteuttaja  (fn [kyselyid] {:type :hankintakoulutuksen_toteuttaja :values (db/hae-raportin-hankintakoulutuksen-toteuttajat {:kyselyid kyselyid})})
   :osaamisala                      (fn [kyselyid] {:type :osaamisala :values (db/hae-raportin-osaamisalat {:kyselyid kyselyid})})
   :oppilaitos                      (fn [kyselyid] {:type :oppilaitos :values (db/hae-raportin-oppilaitokset {:kyselyid kyselyid})})
   :toimipiste                      (fn [kyselyid] {:type :toimipiste :values (db/hae-raportin-toimipisteet {:kyselyid kyselyid})})
   :kieli                           (fn [_] {:type :kieli :values kielet})
   :tutkinnon_taso                  (fn [kyselyid] {:type :tutkinnon_taso :values (db/hae-raportin-tutkinnon-tasot {:kyselyid kyselyid})})
   :tyonantaja                      (fn [kyselyid] {:type :tyonantaja :values (db/hae-raportin-tyonantajat {:kyselyid kyselyid})})
   :sopimustyyppi                   (fn [kyselyid] {:type :sopimustyyppi :values (db/hae-raportin-sopimustyypit {:kyselyid kyselyid})})
   :oppisopimuksen_perusta          (fn [kyselyid] {:type :oppisopimuksen_perusta :values (db/hae-raportin-oppisopimuksen-perustat {:kyselyid kyselyid})})
   :tehtava_yrityksessa             (fn [kyselyid] {:type :tehtava_yrityksessa :values (db/hae-raportin-tehtavat {:kyselyid kyselyid})})
   ;;TODO: put back CSCARVO-1692 poista rahoitusryhmä
   ;:rahoitusryhma                   (fn [_] {:type :rahoitusryhma :values (rahoitusryhmat)})
   :tyopaikkakysely_tutkinto        (fn [kyselyid] {:type :tutkinto :values (db/hae-tyopaikkakyselyn-tutkinnot {:kyselyid kyselyid})})})


(defn hae-suodatin-data [kyselyid suodattimet]
  (let [haku-fn (when (not-empty suodattimet)
                  (->> suodattimet
                       (map #(get suodatin->haku %))
                       (filter some?)
                       (apply juxt)))]
    (if haku-fn (haku-fn kyselyid) [])))


(defn- hae-kaytetty-tutkinto [suodatin-data arvo]
  (let [tutkintodata (:values (first (filter #(= (:type %) :tutkinto) suodatin-data)))
        tutkinto (first (filter #(= (:tutkintotunnus %) arvo) tutkintodata))]
    {:suodatin :tutkinto
     :arvo arvo
     :nimi_fi (:tutkinto_fi tutkinto)
     :nimi_sv (:tutkinto_sv tutkinto)
     :nimi_en (:tutkinto_en tutkinto)}))

(defn- hae-kaytetty-koulutusala [suodatin-data arvo]
  (let [tutkintodata (:values (first (filter #(= (:type %) :tutkinto) suodatin-data)))
        tutkinto (first (filter #(= (:koulutusalatunnus %) arvo) tutkintodata))]
    {:suodatin :koulutusala
     :arvo arvo
     :nimi_fi (:koulutusala_fi tutkinto)
     :nimi_sv (:koulutusala_sv tutkinto)
     :nimi_en (:koulutusala_en tutkinto)}))

(defn- hae-suodatin-arvo [suodatin-data nimi arvo]
  (let [suodattimen-data (:values (first (filter #(= (:type %) nimi) suodatin-data)))
        suodattimen-arvo (first (filter #(= (:arvo %) arvo) suodattimen-data))]
    (assoc suodattimen-arvo :suodatin nimi)))

(defn format-params [kysely params]
  (if (= "tyopaikkakysely" (:tyyppi kysely))
    (-> params
        (clojure.set/rename-keys {:tutkinto :tyopaikkakysely_tutkinto})
        (assoc :koulutustoimija (:koulutustoimija kysely)))
    params))

(defn hae-kaytetyt-suodattimet [kysely suodattimet]
  (let [formatted-params (format-params kysely suodattimet)
        suodatin-data (hae-suodatin-data (:kyselyid kysely) (keys formatted-params))
        kaytetyt-suodattimet (for [[suodatin arvo] (into {} (filter (comp some? val) suodattimet))]
                               (case suodatin
                                 :tutkinto (hae-kaytetty-tutkinto suodatin-data arvo)
                                 :koulutusala (hae-kaytetty-koulutusala suodatin-data arvo)
                                 (hae-suodatin-arvo suodatin-data suodatin arvo)))]
    (filter (comp some? :arvo) kaytetyt-suodattimet)))

(defn raportti-params [kysely params]
  (merge (select-keys params [:alkupvm :loppupvm])
         {:kyselyid (:kyselyid kysely)
          :vastausaika (if (in? ["avop" "kandipalaute"] (:tyyppi kysely))
                         "vs.luotuaika"
                         "vt.voimassa_alkupvm")
          :koulutustoimija (:koulutustoimija kysely)}))

(defn vertailuraportti-params [kysely params]
  (let [vertailukaudet (ru/luo-vertailukaudet (keyword (:tyyppi kysely)))
        kausi (get vertailukaudet (keyword (:vertailukausi params)))]
    {:kyselypohjaid (:kyselypohjaid kysely)
     :alkupvm (str (:alkupvm kausi))
     :loppupvm (str (:loppupvm kausi))
     :vastausaika "vt.voimassa_alkupvm"}))

(defn lisaa-monivalintavaihtoehdot [kysymys]
  (if (= "monivalinta" (:vastaustyyppi kysymys))
    (assoc kysymys :monivalintavaihtoehdot (db/hae-monivalintavaihtoehdot kysymys))
    kysymys))

(defn- taydenna-kysymysryhma [kysymysryhma params kysely]
  (let [kysymykset (db/hae-kysymysryhman-kysymykset (assoc params :kysymysryhmaid (:kysymysryhmaid kysymysryhma)))]
    (assoc kysymysryhma :kysymykset (map lisaa-monivalintavaihtoehdot (filter #(kysymys-service/kysymys-nakyvissa? % (:voimassa_alkupvm kysely)) kysymykset)))))

(defn- hae-kysymysryhmat [kyselyid params kysely]
  (let [kysymysryhmat (db/hae-kyselyn-kysymysryhmat (assoc params :kyselyid kyselyid))]
    (map #(taydenna-kysymysryhma % params kysely) kysymysryhmat)))

(defn hae-kysely [kyselyid & params]
  (let [kysely (db/hae-kysely {:kyselyid kyselyid})
        kysymysryhmat (hae-kysymysryhmat kyselyid (first params) kysely)]
    (assoc kysely :kysymysryhmat kysymysryhmat)))

(defn create-filters [params]
  (->> params
       vec
       (map filter->sqlvec)
       (filter some?)))

(defn hae-vertailudata [kysely params]
  (let [raportti-params (vertailuraportti-params kysely params)
        vertailudata (db/hae-vertailuraportti (vertailuraportti-params kysely params))
        kohteet-tutkinnoittain (db/hae-raportin-kohteet-tutkinnoittain raportti-params)
        kohteet {:tutkinnoittain kohteet-tutkinnoittain
                 :kohteita (->> kohteet-tutkinnoittain (map :kohteita) (reduce +))
                 :vastaajia (->> kohteet-tutkinnoittain (map :vastaajia ) (reduce +))}]

    (assoc kohteet :data vertailudata)))

(defn hae-kyselyraportti [kysely params]
  (if (= "tyopaikkakysely" (:tyyppi kysely))
    (db/hae-tyopaikkakyselyn-raportti params)
    (db/hae-kyselyraportti params)))

(defn vapaatekstikysymysten-raportti [kysely params]
  (if (= "tyopaikkakysely" (:tyyppi kysely))
    (db/hae-tyopaikkakyselyn-vapaatekstikysymysten-raportti params)
    (db/hae-vapaatekstikysymysten-raportti params)))

(defn hae-vastausdata [kysely params]
  (let [filters (create-filters params)
        raportti-params (assoc (raportti-params kysely params) :where filters)
        vastausdata (concat (hae-kyselyraportti kysely raportti-params)
                            (vapaatekstikysymysten-raportti kysely raportti-params))
        kohteet-tutkinnoittain (if (= "tyopaikkakysely" (:tyyppi kysely))
                                 (db/hae-tyopaikkakyselyn-kohteet-tutkinnoittain raportti-params)
                                 (db/hae-raportin-kohteet-tutkinnoittain raportti-params))
        kohteet {:tutkinnoittain kohteet-tutkinnoittain
                 :kohteita (->> (map :kohteita kohteet-tutkinnoittain) (reduce +))
                 :vastaajia (->> (map :vastaajia kohteet-tutkinnoittain) (reduce +))}]
    (assoc kohteet :data vastausdata)))

(defn hae-koodistot [kyselyid]
  (group-by :koodisto_uri (db/hae-kyselyn-koodistot {:kyselyid kyselyid})))

(defn hae-raporttidata [kyselyid params]
  (let [kysely (hae-kysely kyselyid params)
        formatted-params (format-params kysely params)
        vastausdata (hae-vastausdata kysely formatted-params)
        vertailudata (when (not= :ei-vertailudataa (:vertailukausi formatted-params))
                       (hae-vertailudata kysely formatted-params))
        koodistot (hae-koodistot kyselyid)]
    {:kysely kysely
     :koodistot koodistot
     :raporttidata {:vastausdata vastausdata
                    :vertailudata vertailudata}}))
