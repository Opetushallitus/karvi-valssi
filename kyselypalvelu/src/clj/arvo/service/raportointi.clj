(ns arvo.service.raportointi
  (:require [arvo.db.core :refer [*db*] :as db]
            [arvo.util :refer [in?]]
            [arvo.raportti-util :as ru]
            [arvo.translations :refer [translate]]
            [arvo.db.raportti :as r]
            [arvo.infra.kayttaja :refer [*kayttaja*]]
            [arvo.util.paivamaara-util :as pvm]
            [clojure.tools.logging :as log]
            [cheshire.core :as json]
            [arvo.util :refer [in?]]
            [oph.common.util.util :refer [map-values]]))

(def kysymystyyppi->asteikko {"likert_asteikko"         (range 1 6)
                              "arvosana"                (range 1 6)
                              "arvosana6"               (range 1 7)
                              "arvosana7"               (range 1 8)
                              "arvosana4_ja_eos"        (range 5 0 -1)
                              "arvosana6_ja_eos"        (range 0 7)
                              "asteikko5_1"             (range 5 0 -1)
                              "nps"                     (range 0 11)
                              "kylla_ei_valinta"        ["kylla" "ei"]})

(defn- kysymystyyppi->kentta [kysymys]
  (case (:vastaustyyppi kysymys)
    "kylla_ei_valinta" :vaihtoehto
    :numerovalinta))

(defn- hae-koodi [koodit idx arvo]
  (let [koodi (first (filter #(= (:koodi_arvo %) arvo) koodit))]
    {:jarjestys idx
     :arvo arvo
     :nimi_fi (:nimi_fi koodi)
     :nimi_sv (:nimi_sv koodi)
     :nimi_en (:nimi_en koodi)}))

(defn- vastausten-koodit [vastaukset]
  (->> vastaukset
       (map :numerovalinta)
       distinct
       (filter some?)
       (map int)
       (map (fn [koodi] (format "%03d" koodi)))
       sort))


(defn- koodisto-selitteet [kysymys vastaukset koodistot]
  (let [koodisto (get-in kysymys [:metatiedot :koodisto])
        koodit (get koodistot koodisto)
        vastaus-koodit (when koodisto (vastausten-koodit vastaukset))]
    (map-indexed (fn [i koodi](hae-koodi koodit i koodi)) vastaus-koodit)))

(defn- monivalinta-selitteet [kysymys]
  (map (fn [mv] {:jarjestys (:jarjestys mv)
                 :arvo (:arvo mv)
                 :nimi_fi (:teksti_fi mv)
                 :nimi_sv (:teksti_sv mv)
                 :nimi_en (:teksti_en mv)})
       (:monivalintavaihtoehdot kysymys)))

(defn- format-asteikko [vastaustyyppi idx arvo]
  {:jarjestys idx
   :arvo arvo
   :nimi_fi (translate [:fi :kysymys (keyword vastaustyyppi) (if (number? arvo) arvo (keyword arvo))])
   :nimi_sv (translate [:sv :kysymys (keyword vastaustyyppi) (if (number? arvo) arvo (keyword arvo))])
   :nimi_en (translate [:en :kysymys (keyword vastaustyyppi) (if (number? arvo) arvo (keyword arvo))])})


(defn asteikko-selitteet [kysymys]
  (let [kysymystyyppi (:vastaustyyppi kysymys)
        asteikko (kysymystyyppi->asteikko kysymystyyppi)]
    (map-indexed (fn [idx arvo] (format-asteikko kysymystyyppi idx arvo)) asteikko)))

(defn kategoria-selitteet [kysymys]
  (let [kategoriat (get-in kysymys [:metatiedot :kategoriat])]
    kategoriat))

(defn- hae-kaannokset [kysymys vastaukset koodistot]
  (case (:vastaustyyppi kysymys)
    "alasvetovalikko" (koodisto-selitteet kysymys (filter #(= (:kysymysid %) (:kysymysid kysymys)) vastaukset) koodistot)
    "monivalinta" (monivalinta-selitteet kysymys)
    "luku" (kategoria-selitteet kysymys)
    (asteikko-selitteet kysymys)))

(defn- lisaa-eos-selite [kysymys selitteet]
  (when (:eos_vastaus_sallittu kysymys)
    (let [kysymystyyppi (keyword (:vastaustyyppi kysymys))
          jarjestys (->> selitteet
                      (map :jarjestys)
                      (apply max)
                      inc)]
      (conj selitteet {:jarjestys jarjestys
                       :arvo :eos
                       :nimi_fi (or (:eos_teksti_fi (:metatiedot kysymys)) (translate [:fi :kysymys kysymystyyppi :eos]))
                       :nimi_sv (or (:eos_teksti_sv (:metatiedot kysymys)) (translate [:sv :kysymys kysymystyyppi :eos]))
                       :nimi_en (or (:eos_teksti_en (:metatiedot kysymys)) (translate [:en :kysymys kysymystyyppi :eos]))})
      selitteet)))

(defn laske-osuus [vastausten-lkm vastauksia-yhteensa]
  (if (and vastausten-lkm (pos? vastauksia-yhteensa))
    (* 100 (/ vastausten-lkm vastauksia-yhteensa)) 0))

(defn- lisaa-eos [kysymys vastauksia vastaukset jakauma]
  (if (:eos_vastaus_sallittu kysymys)
    (let [vastausten-lkm (:vastausten_lkm (first (filter #(= true (:en_osaa_sanoa %)) vastaukset)))]
      (conj jakauma {:vaihtoehto     :eos
                     :vastausten_lkm (or vastausten-lkm 0)
                     :osuus          (laske-osuus vastausten-lkm vastauksia)}))

    jakauma))

(defn- hae-vastaus [vastaukset vastauksia kentta vaihtoehto]
  (let [vastaus (first (filter #(or
                                  (= (get % kentta) vaihtoehto)
                                  (= (str (get % kentta)) vaihtoehto)) ;koska (vastausten-koodit muuttaa intit stringeiks
                               vastaukset))
        vastausten-lkm (or (:vastausten_lkm vastaus) 0)]
    {:vaihtoehto vaihtoehto
     :osuus (if (pos? vastauksia) (* 100 (/ vastausten-lkm vastauksia)) 0)
     :vastausten_lkm vastausten-lkm}))

(defn- luo-jakauma [kysymys data]
  (let [vastaukset (filter #(= (:kysymysid %) (:kysymysid kysymys)) data)
        vastauksia (reduce + (map :vastausten_lkm vastaukset))
        asteikko (case (:vastaustyyppi kysymys)
                   "monivalinta" (map :arvo (sort-by :jarjestys (:monivalintavaihtoehdot kysymys)))
                   "alasvetovalikko" (vastausten-koodit vastaukset)
                   (kysymystyyppi->asteikko (:vastaustyyppi kysymys)))
        kentta (kysymystyyppi->kentta kysymys)
        jakauma (map #(hae-vastaus vastaukset vastauksia kentta %) asteikko)
        jakauma+eos (lisaa-eos kysymys vastauksia vastaukset (sort-by :vaihtoehto jakauma))]
    {:jakauma        jakauma+eos
     :vastaajien_lkm (reduce + (map :vastausten_lkm jakauma+eos))}))

(defn kuuluu-kategoriaan [kategoria vastaus]
  (and (<= (:luku vastaus) (or (:max kategoria) (Integer/MAX_VALUE)))
       (>= (:luku vastaus) (or (:min kategoria) (Integer/MIN_VALUE)))))


(defn hae-kategorian-luvut [vastaukset vastauksia kategoria]
  (let [vastausten-lkm (->> vastaukset
                            (filter (partial kuuluu-kategoriaan kategoria))
                            (map :vastausten_lkm)
                            (reduce +))]
    {:vaihtoehto (:arvo kategoria)
     :vastausten_lkm vastausten-lkm
     :osuus (laske-osuus vastausten-lkm vastauksia)}))


(defn luo-luku-jakauma [base-data kysymys vastausdata]
  (let [vastaukset (filter #(= (:kysymysid %) (:kysymysid kysymys)) vastausdata)
        vastauksia (reduce + (map :vastausten_lkm vastaukset))
        kategoriat (->> kysymys :metatiedot :kategoriat)]
    (update-in base-data [:vastausdata] merge
               {:jakauma (map #(hae-kategorian-luvut vastaukset vastauksia %) kategoriat)
                :vastaajien_lkm vastauksia})))

(defn- luo-jakaumat [base-data kysymys vastausdata vertailudata]
  (let [jakaumat (update-in base-data [:vastausdata] merge (luo-jakauma kysymys vastausdata))]
    (if vertailudata (update-in jakaumat [:vertailudata] merge (luo-jakauma kysymys vertailudata)) jakaumat)))

(defn- jakaumat-summa [jakauma ehto]
  (->> jakauma
       (filter #(some? (:vaihtoehto %)))
       (filter #(ehto (:vaihtoehto %)))
       (map :vastausten_lkm)
       (reduce +)))

(defn- laske-nps-luku [jakauma]
  (when (not-empty jakauma)
    (let [yhteensa (reduce + (map :vastausten_lkm jakauma))
          arvostelijat (jakaumat-summa jakauma #(< % 7))
          suosittelijat (jakaumat-summa jakauma #(> % 8))]
      (when (> yhteensa 0)
        {:nps (Math/round (float (* 100 (- (/ suosittelijat yhteensa) (/ arvostelijat yhteensa)))))
         :suosittelijat suosittelijat
         :arvostelijat arvostelijat}))))

(defn- raportoi-nps [base-data]
  (let [nps (update-in base-data [:vastausdata] merge (laske-nps-luku (:jakauma (:vastausdata base-data))))]
    (if  (:vertailudata base-data) (update-in nps [:vertailudata] merge (laske-nps-luku (:jakuma (:vertailudata base-data)))) nps)))

(def asteikkotyyppi? #{"likert_asteikko" "arvosana" "arvosana6" "arvosana7" "arvosana4_ja_eos" "asteikko5_1" "arvosana6_ja_eos" "luku"})

(defn- luo-vastausprosentti [kysymys data]
  (let [kohteita (or (-> data :kohteita) 0)
        vastauksia (reduce + (map :vastausten_lkm (filter #(= (:kysymysid %) (:kysymysid kysymys)) (:data data))))]
    {:vastausprosentti (if (pos? kohteita) (float (* 100 (/ vastauksia kohteita))) 0)
     :kohteiden_lkm kohteita}))

(defn- luo-vastausprosentit [base-data kysymys vastausdata vertailudata]
  (let [vast (update-in base-data [:vastausdata] merge (luo-vastausprosentti kysymys vastausdata))]
    (if (:data vertailudata) (update-in vast [:vertailudata] merge (luo-vastausprosentti kysymys vertailudata)) vast)))

(defn- luo-ka-hajonta [kysymys data]
  (let [kentta (if (= "luku" (:vastaustyyppi kysymys)) :luku :numerovalinta)
        abs (fn [n] (max n (-' n)))
        vastaukset (filter #(and (= (:kysymysid %) (:kysymysid kysymys))
                                 (some? (kentta %))) data)
        vastauksia (reduce + (map :vastausten_lkm vastaukset))
        yht (reduce + (map #(* (kentta %) (:vastausten_lkm %)) vastaukset))]
    (with-precision 10
      (if (pos? vastauksia)
        {:keskiarvo (/ yht vastauksia)
         :keskihajonta (Math/sqrt (/
                                    (reduce + (map (fn [v] (* (Math/pow (abs (- (/ yht vastauksia) (kentta v))) 2) (:vastausten_lkm v)) ) vastaukset))
                                    vastauksia))}
        {:keskiarvo 0
         :keskihajonta 0}))))


(defn- luo-ka-hajonnat [base-data kysymys vastausdata vertailudata]
  (let [ka (update-in base-data [:vastausdata] merge (luo-ka-hajonta kysymys vastausdata))]
    (if vertailudata (update-in ka [:vertailudata] merge (luo-ka-hajonta kysymys vertailudata)) ka)))

(defn- vapaateksti-data [base-data kysymys vastausdata vertailudata]
  (let [vastaukset (filter #(= (:kysymysid %) (:kysymysid kysymys)) vastausdata)]
    (update-in base-data [:vastausdata] merge
               {:vastaajien_lkm (reduce + (map :vastausten_lkm vastaukset))
                :vastaukset (map :vapaateksti vastaukset)})))

(defn- base-data [vertailu]
  {:vastausdata {}
   :vertailudata (if vertailu {} nil)})

(defn- raportoi-kysymys [{vastausdata :vastausdata vertailudata :vertailudata} koodistot kysymys]
  (let [kaannokset (hae-kaannokset kysymys (:data vastausdata) koodistot)
        vastaustyyppi (:vastaustyyppi kysymys)
        base-data (base-data (:data vertailudata))
        data (case vastaustyyppi
               "vapaateksti" (vapaateksti-data base-data kysymys (:data vastausdata) (:data vertailudata))
               "luku" (luo-luku-jakauma base-data kysymys (:data vastausdata))
               (luo-jakaumat base-data kysymys (:data vastausdata) (:data vertailudata)))
        typpidata (cond
                    (= vastaustyyppi "nps") (raportoi-nps data)
                    (asteikkotyyppi? vastaustyyppi) (luo-ka-hajonnat data kysymys (:data vastausdata) (:data vertailudata))
                    :else data)
        vastauspros (luo-vastausprosentit typpidata kysymys vastausdata vertailudata)]

    (merge (select-keys kysymys [:kysymysid :kysymys_fi :kysymys_sv :kysymys_en :vastaustyyppi :jarjestys :monivalintavaihtoehdot])
           {:selitteet kaannokset}
           vastauspros)))

(defn- raportoi-kysymysryhma [kysymysryhma raporttidata koodistot]
  (let [avovastaukset (in? (:oikeudet (:aktiivinen-rooli *kayttaja*)) :kysely)
        filter-kysymystyypit (if avovastaukset ["valiotsikko"] ["valiotsikko" "vapaateksti"])]
    (merge (select-keys kysymysryhma [:kysymysryhmaid :nimi_fi :nimi_sv :nimi_en :kuvaus_fi :kuvaus_sv :kuvaus_en])
           {:kysymykset (map #(raportoi-kysymys raporttidata koodistot %)
                             (filter #(not (in? filter-kysymystyypit (:vastaustyyppi %))) (:kysymykset kysymysryhma)))})))

(defn raportoi-kysely [{kysely :kysely raporttidata :raporttidata koodistot :koodistot}]
  (let [vastaajia (or (-> raporttidata :vastausdata :vastaajia) 0)
        kohteita (or (-> raporttidata :vastausdata :kohteita) 0)]
    (merge (select-keys kysely [:kyselyid :tyyppi :nimi_fi :nimi_sv :nimi_en])
           {:kohteiden_lkm kohteita
            :vastaajien_lkm vastaajia
            :tutkinnoittain (or (-> raporttidata :vastausdata :tutkinnoittain) nil)
            :rahoitusryhmittain (or (-> raporttidata :vastausdata :rahoitusryhmittain) nil)
            :vastausprosentti (when (pos? kohteita) (float (* 100 (/ vastaajia kohteita))))
            :vertailu_vastausprosentti 0
            :kysymysryhmat (for [kr (:kysymysryhmat kysely)]
                             (raportoi-kysymysryhma kr raporttidata koodistot))})))


(defn luo-kyselyraportti [kyselyid suodattimet]
  (let [raporttidata (r/hae-raporttidata kyselyid suodattimet)
        kaytetyt-suodattimet (r/hae-kaytetyt-suodattimet (:kysely raporttidata) suodattimet)]
    (if (< 5 (-> raporttidata :raporttidata :vastausdata :vastaajia))
      {:yhteenveto {:koulutustoimija (select-keys (:kysely raporttidata) [:koulutustoimija_fi :koulutustoimija_sv :koulutustoimija_en])
                    :suodattimet kaytetyt-suodattimet
                    :luotuaika (pvm/current-millis)}
       :raportti (raportoi-kysely raporttidata)}
      {:error :ei-riittavasti-vastaajia})))

(defn luo-vertailudata! [alkupvm tyhjenna]
  (r/luo-vertailudata! (ru/raportointi-kuukaudet alkupvm) tyhjenna))

(defn paivita-vertailudata! []
  (when (ru/ensimmainen-paiva?) (r/paivita-vertailudata! (ru/edellinen-kuukausi)))
  (r/paivita-vertailudata! (ru/kuluva-kuukausi)))

(defn hae-kyselyt []
  (db/hae-kyselyiden-perustiedot {:koulutustoimija (:aktiivinen-koulutustoimija *kayttaja*)}))

(defn hae-kyselyn-tiedot [kyselyid]
  (let [kysely (db/hae-kysely {:kyselyid kyselyid})
        suodattimet (get ru/kyselytyyppi->suodattimet (keyword (:tyyppi kysely)))]
    (r/hae-suodatin-data kyselyid suodattimet)))
