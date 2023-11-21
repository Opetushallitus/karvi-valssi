(ns arvo.raportti-util
  (:require [tick.core :as t]))

(defn syksy-alkupvm [date]
  (-> date
      (t/with :month-of-year 7)
      (t/with :day-of-month 1)))

(defn kevat-loppupvm [date]
  (-> date
      (t/with :month-of-year 6)
      (t/with :day-of-month 30)))

(defn kevat-alkupvm [date]
  (-> date
    (t/with :month-of-year 1)
    (t/with :day-of-month 1)))

(defn syksy-loppupvm [date]
  (-> date
      (t/with :month-of-year 12)
      (t/with :day-of-month 31)))

(defn dec-year [date]
  (t/<< date (t/new-period 1 :years)))

(defn inc-year [date]
  (t/>> date (t/new-period 1 :years)))

(defn kevat [date]
  {:alkupvm (kevat-alkupvm date) :loppupvm (kevat-loppupvm date)})

(defn syksy [date]
  {:alkupvm (syksy-alkupvm date) :loppupvm (syksy-loppupvm date)})


(defn kuluva-amis-kausi [date]
  (let [previous (t/<< date (t/new-period 1 :years))]
    (if (t/< date (syksy-alkupvm date))
      {:alkupvm (syksy-alkupvm previous) :loppupvm (kevat-loppupvm date)}
      {:alkupvm (syksy-alkupvm date) :loppupvm (kevat-loppupvm (inc-year date))})))

(defn edellinen-amis-kausi [date]
  (-> (kuluva-amis-kausi date)
      (update :alkupvm (fn [pvm] (t/<< pvm (t/new-period 1 :years))))
      (update :loppupvm (fn [pvm] (t/<< pvm (t/new-period 1 :years))))))

(defn kuluva-amis-rahoituskausi [date]
  {:kuluva-rahoituskausi (merge {:jarjestys 1} (kuluva-amis-kausi date))})

(defn edellinen-amis-rahoituskausi [date]
  {:edellinen-rahoituskausi (merge {:jarjestys 2} (edellinen-amis-kausi date))})

(defn kuluva-korkeakoulu-rahoituskausi [date]
  {:kuluva-rahoituskausi {:jarjestys 1 :alkupvm (kevat-alkupvm date) :loppupvm (syksy-loppupvm date)}})

(defn edellinen-korkeakoulu-rahoituskausi [date]
  (let [prev-year (t/<< date (t/new-period 1 :years))]
    {:edellinen-rahoituskausi {:jarjestys 2 :alkupvm (kevat-alkupvm prev-year) :loppupvm (syksy-loppupvm prev-year)}}))

(defn edellinen-kalenterivuosi [date]
  {:edellinen-kalenterivuosi {:jarjestys 5 :alkupvm (kevat-alkupvm (t/<< date (t/new-period 1 :years)))
                              :loppupvm (syksy-loppupvm (t/<< date (t/new-period 1 :years)))}})

(defn edellinen-kevat [date]
  (let [kausi (if (t/> date (kevat-loppupvm date))
                (kevat date)
                (kevat (t/<< date (t/new-period 1 :years))))]
    {:edellinen-kevat (merge {:jarjestys 3} kausi)}))

(defn edellinen-syksy [date]
    {:edellinen-syksy (merge {:jarjestys 4} (syksy (dec-year date)))})

(defn ei-vertailudataa [_]
  {:ei-vertailudataa {:jarjestys 6}})

(def korkeakoulu-kaudet
  (juxt kuluva-korkeakoulu-rahoituskausi edellinen-korkeakoulu-rahoituskausi edellinen-kevat edellinen-syksy edellinen-kalenterivuosi ei-vertailudataa))

(def uraseuranta-kaudet
  (juxt kuluva-korkeakoulu-rahoituskausi edellinen-korkeakoulu-rahoituskausi ei-vertailudataa))

(def amis-kaudet
  (juxt kuluva-amis-rahoituskausi edellinen-amis-rahoituskausi edellinen-kevat edellinen-syksy edellinen-kalenterivuosi ei-vertailudataa))

(def vertailukaudet
  {:avop                           korkeakoulu-kaudet
   :kandipalaute                   korkeakoulu-kaudet
   :ammatillisen-opiskelijapalaute amis-kaudet
   :tyopaikkaohjaajakysely         amis-kaudet
   :tyopaikkakysely                amis-kaudet
   :digikyvykkyys                  (juxt edellinen-kalenterivuosi ei-vertailudataa)
   :rekrykysely                    (juxt edellinen-kalenterivuosi ei-vertailudataa)
   :amk-uraseuranta                uraseuranta-kaudet
   :yo-uraseuranta                 uraseuranta-kaudet
   :move                           (juxt edellinen-kalenterivuosi ei-vertailudataa)})


(defn luo-vertailukaudet [kyselytyyppi]
  (let [kaudet (get vertailukaudet kyselytyyppi)]
    (when kaudet (apply merge (kaudet (t/date))))))

(defn kuukausi
  ([start-date next-date]
   {:alkupvm  (str start-date)
    :loppupvm (str (t/<< next-date (t/new-period 1 :days)))})
  ([start-date]
   (kuukausi start-date (t/>> start-date (t/new-period 1 :months)))))


(defn raportointi-kuukaudet
  ([alkupvm kuukaudet]
   (if (t/> (t/date) alkupvm)
     (let [next-date (t/>> alkupvm (t/new-period 1 :months))]
       (raportointi-kuukaudet next-date (conj kuukaudet (kuukausi alkupvm next-date))))
     kuukaudet))
  ([date-str]
   (raportointi-kuukaudet (t/date date-str) [])))

(defn kuluva-kuukausi []
  (-> (t/date)
      (t/with :day-of-month 1)
      kuukausi))

(defn edellinen-kuukausi []
  (-> (t/date)
      (t/with :day-of-month 1)
      (t/<< (t/new-period 1 :months))
      kuukausi))

(defn ensimmainen-paiva? []
  (= 1 (t/day-of-month (t/date))))

(def kyselytyyppi->suodattimet
  {:avop                           [:kyselykerta :tutkinto :kieli :koulutusmuoto :toimipiste]
   :kandipalaute                   [:kyselykerta :tutkinto :kieli :toimipiste]
   :rekrykysely                    [:kyselykerta]
   :amk-uraseuranta                [:kyselykerta :tutkinto :kieli :tutkinnon_taso :koulutusmuoto :toimipiste]
   :yo-uraseuranta                 [:kyselykerta :tutkinto :tutkinnon_suorituskieli]
   :ammatillisen-opiskelijapalaute [:kyselykerta :tutkinto :kieli :oppilaitos :toimipiste :hankintakoulutuksen_toteuttaja :rahoitusryhma]
   :tyopaikkaohjaajakysely         [:kyselykerta :tutkinto :kieli :oppilaitos :toimipiste :hankintakoulutuksen_toteuttaja :tyonantaja :sopimustyyppi :oppisopimuksen_perusta :rahoitusryhma]
   :tyopaikkakysely                [:kyselykerta :tyonantaja :tehtava_yrityksessa :rahoitusryhma :tyopaikkakysely_tutkinto]
   :itsearviointi                  [:kyselykerta :oppilaitos]
   :move                           [:oppilaitos]})