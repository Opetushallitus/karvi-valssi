(ns arvo.service.kysymys
  (:require [arvo.db.core :refer [*db*] :as db]
            [arvo.arkisto.kysymys :as arkisto]
            [arvo.infra.kayttaja :refer [*kayttaja*]]
            [arvo.util :refer [add-index when-let*]]
            [java-time.api :as jt]
            [arvo.util.paivamaara-util :as pvm-util]
            [next.jdbc :as jdbc]
            [arvo.util :as au]
            [clojure.tools.logging :as log]))

(defn add-kysymys-index [kysymys index]
  (let [kysymys (assoc kysymys :jarjestys @index)
        jatkokysymykset (doall (map (fn [[key jatkokysymys]]
                                      (dosync (alter index + 1)
                                              [key (assoc jatkokysymys :jarjestys @index)]))
                                    (:jatkokysymykset kysymys)))
        matriisi-kysymys? (not (empty? (:matriisikysymykset kysymys)))
        matriisi-index (:jarjestys kysymys)
        matriisikysymykset (doall (map-indexed (fn [idx matriisikysymys]
                                                 ; Alkuperäiselle matriisikysymykselle annetaan 0, nämä alkavat siis 1:stä eteenpäin
                                                 (assoc matriisikysymys
                                                        :jarjestys matriisi-index
                                                        :matriisi_jarjestys (inc idx)))
                                               (:matriisikysymykset kysymys)))]
    (dosync(alter index + 1))
    (assoc kysymys
           :jatkokysymykset jatkokysymykset
           :matriisikysymykset matriisikysymykset
           :matriisi_jarjestys (when matriisi-kysymys? 0))))

(defn korjaa-eos-vastaus-sallittu [{:keys [eos_vastaus_sallittu pakollinen vastaustyyppi] :as kysymys}]
  (assoc kysymys :eos_vastaus_sallittu (and eos_vastaus_sallittu
                                            pakollinen
                                            (not= vastaustyyppi "vapaateksti"))))

(defn validate-vaihda [kysymysryhmaid kysymys-vaihto-data]
  (let [kysymykset-loytyvat (when (-> (assoc kysymys-vaihto-data :kysymysryhmaid kysymysryhmaid)
                                      arkisto/kysymysryhman-kysymykset-olemassa-count
                                      :count
                                      (not= 2))
                              "kysymys.vaihto.kysymys-ei-loydy-kysymysryhmasta")
        kysymysten-matriisitiedot (arkisto/kysymyksen-matriisi-jarjestys kysymys-vaihto-data)
        matriisi-jarjestykset (map :matriisi_jarjestys kysymysten-matriisitiedot)
        matriisi-kysymysidt (map :matriisi_kysymysid kysymysten-matriisitiedot)
        matriisi-virheet (cond-> []
                           (and
                            (every? number? matriisi-jarjestykset)
                            (some zero? matriisi-jarjestykset)
                            (some pos? matriisi-jarjestykset))
                           (conj "kysymys.vaihto.matriisi-sisainen-juurikysymyksen-vaihto")
                           (and
                            (some nil? matriisi-jarjestykset)
                            (some #(and (some? %) (pos? %)) matriisi-jarjestykset))
                           (conj "kysymys.vaihto.matriisikysymyksen-vaihto-normaaliin-kysymykseen")
                           (and
                            (every? #(and (some? %) (pos? %)) matriisi-jarjestykset)
                            (not-empty matriisi-kysymysidt)
                            (apply not= matriisi-kysymysidt))
                           (conj "kysymys.vaihto.eri-matriiseja"))]
    [kysymykset-loytyvat matriisi-virheet]))

(defn vaihda! [kysymysryhmaid kysymys-vaihto-data]
    (str (arkisto/vaihda-kysymysten-jarjestys! kysymys-vaihto-data)))

(defn poista!
  "Tämä jättää 'reiän' järjestykseen mutta tämän ei pitäisi haitata kunhan kysymysten keskinen järjestys säilyy."
  ([kysymysid]
  (jdbc/with-transaction
   [tx *db*]
   (poista! tx kysymysid)))
  ([tx kysymysid]
   (let [kysymys-ja-jatkokysymys-idt (-> (map :jatkokysymysid (arkisto/hae-kysymyksen-jatkokysymykset tx kysymysid))
                                         (conj kysymysid)
                                         (concat (map :kysymysid (arkisto/hae-kysymyksen-matriisikysymykset tx kysymysid)))
                                         distinct
                                         (as-> idt {:kysymysidt idt}))
         delete-fn (juxt arkisto/poista-monivalintavaihtoehdot! arkisto/poista-jatkokysymysliitokset! arkisto/poista-kysymykset!)
         delete-count (last (delete-fn tx kysymys-ja-jatkokysymys-idt))]
     (when (< 0 delete-count)
       (str delete-count)))))

(defn valitse-kysymyksen-kentat [kysymys]
  (select-keys kysymys [:pakollinen
                         :eos_vastaus_sallittu
                         :poistettava
                         :vastaustyyppi
                         :kysymys_fi
                         :kysymys_sv
                         :kysymys_en
                         :selite_fi
                         :selite_sv
                         :selite_en
                         :max_vastaus
                         :monivalinta_max
                         :rajoite
                         :jarjestys
                         :matriisi_jarjestys
                         :matriisi_kysymysid
                         :metatiedot]))
(def jatkokysymys-fields [:kysymysryhmaid
                          :kysymys_fi
                          :kysymys_sv
                          :kysymys_en
                          :jarjestys
                          :monivalinta_max
                          :max_vastaus
                          :eos_vastaus_sallittu
                          :vastaustyyppi
                          :jatkokysymys
                          :pakollinen
                          :poistettava
                          :rajoite
                          :matriisi_jarjestys
                          :matriisi_kysymysid
                          :metatiedot])
(def tyhja-kysymys { :kysymysryhmaid nil
                     :pakollinen nil
                     :eos_vastaus_sallittu nil
                     :poistettava nil
                     :vastaustyyppi nil
                     :kysymys_fi nil
                     :kysymys_sv nil
                     :kysymys_en nil
                     :selite_fi nil
                     :selite_sv nil
                     :selite_en nil
                     :max_vastaus nil
                     :monivalinta_max nil
                     :jatkokysymys false
                     :rajoite nil
                     :jarjestys nil
                     :matriisi_jarjestys nil
                     :matriisi_kysymysid nil
                     :metatiedot {}})
(def kysymys-defaults (zipmap jatkokysymys-fields (repeat nil)))

(def jatkokysymys-defaults {:vastaustyyppi "string"
                            :pakollinen false
                            :jatkokysymys true
                            :poistettava false
                            :rajoite nil})
(def vaihtoehto-kentat [:jarjestys
                         :teksti_fi
                         :teksti_sv
                         :teksti_en])
(def vaihtoehto-defaults (zipmap vaihtoehto-kentat (repeat nil)))
(defn valitse-vaihtoehdon-kentat [vaihtoehto]
  (merge vaihtoehto-defaults (select-keys vaihtoehto vaihtoehto-kentat)))

(defn- tallenna-uusi-kysymys! [kysymys-data kysymysryhmaid tx]
  (let [kysymys (assoc (merge tyhja-kysymys kysymys-data) :kayttaja (:oid *kayttaja*))
        kysymysid (arkisto/lisaa-kysymys! tx kysymys)]
    kysymysid))

(defn muodosta-jatkokysymykset [kysymys kysymysryhmaid]
  (when (and ;(= "kylla_ei_valinta" (:vastaustyyppi kysymys))
             (:jatkokysymykset kysymys))
    (let [merge-kys (fn [jk] (assoc (second jk)
                                    :vastaus (name (first jk))
                                    :kysymysryhmaid kysymysryhmaid))]
      (->> (:jatkokysymykset kysymys)
           (map merge-kys)
           (map #(merge jatkokysymys-defaults %))
           (map #(merge kysymys-defaults %))))))

;; function commented out in VAL-1195
;; (defn lisaa-monivalintavaihtoehdot! [tx vaihtoehdot kysymysid]
;;   (when (nil? vaihtoehdot)
;;     (log/error "Kysymyksellä" kysymysid "ei ole monivalintavaihtoehtoja."))
;;   (doseq [vaihtoehto (add-index :jarjestys vaihtoehdot)]
;;     (-> vaihtoehto
;;         valitse-vaihtoehdon-kentat
;;         (assoc :kysymysid kysymysid)
;;         (assoc :kayttaja (:oid *kayttaja*))
;;         (arkisto/lisaa-monivalintavaihtoehto! tx))))

(defn jatkokysymykset-map [tx kysymysid]
  (let [kys-arr (map (fn [liitos]
                       (-> (arkisto/hae-kysymys tx (:jatkokysymysid liitos))
                           (assoc :jatkokysymys_kysymysid (:kysymysid liitos))
                           (assoc :jatkokysymys_vastaus (:vastaus liitos)))
                       ) (arkisto/hae-kysymyksen-jatkokysymykset tx kysymysid))]

    (reduce #(assoc %1 (keyword (:jatkokysymys_vastaus %2)) %2) {} kys-arr)))

(defn lisaa-kysymys!
  ([kysymys kysymysryhmaid]
   (jdbc/with-transaction
    [tx *db*]
    (lisaa-kysymys! tx kysymys kysymysryhmaid)))
  ([tx kysymys kysymysryhmaid]
   (let [kysymysid (-> kysymys
                       valitse-kysymyksen-kentat
                       korjaa-eos-vastaus-sallittu
                       (assoc :kysymysryhmaid kysymysryhmaid)
                       (assoc :luotu_kayttaja (:oid *kayttaja*))
                       (assoc :muutettu_kayttaja (:oid *kayttaja*))
                       (tallenna-uusi-kysymys! kysymysryhmaid tx)
                       first
                       :kysymysid)
         ;TODO: erottele olemassa olevat ja luotavat (VAL-1102)
         jatkokysymykset (muodosta-jatkokysymykset kysymys kysymysryhmaid)
         matriisikysymysidt (doall (map #(lisaa-kysymys! tx (assoc % :matriisi_kysymysid kysymysid)kysymysryhmaid) (:matriisikysymykset kysymys)))]
     (when (= 0 (:matriisi_jarjestys kysymys))
       (arkisto/paivita-matriisi-kysymysid! tx kysymysid kysymysid))

     (doseq [jatkokysymys jatkokysymykset]
       (let [jatkokysymysid (if-let [j-kysymysid (:kysymysid jatkokysymys)]
                              j-kysymysid
                              (-> (select-keys jatkokysymys jatkokysymys-fields)
                                  (tallenna-uusi-kysymys! kysymysryhmaid tx)
                                  first
                                  :kysymysid))
             vastaus (:vastaus jatkokysymys)]
         (arkisto/liita-jatkokysymys! tx kysymysid jatkokysymysid vastaus)))

;; commented out in VAL-1195
;;      (when (= "monivalinta" (:vastaustyyppi kysymys))
;;        (lisaa-monivalintavaihtoehdot! tx (:monivalintavaihtoehdot kysymys) kysymysid))
     {:kysymysid kysymysid
      :matriisikysymykset (map :kysymysid matriisikysymysidt)
      :jatkokysymykset (jatkokysymykset-map tx kysymysid)})))

(defn lisaa!
  "Lisää uusi kysymys kysymysryhmän viimeiseksi."
  [kysymys kysymysryhmaid]
  (let [jarjestys-ref (arkisto/hae-kysymysryhman-viimeinen-jarjestys kysymysryhmaid)
        jarjestetty-kysymys (add-kysymys-index kysymys jarjestys-ref)]
    (lisaa-kysymys! jarjestetty-kysymys kysymysryhmaid)))

(defn validoi-matriisikysymys [kysymys kysymysid]
  (when (-> (arkisto/hae-kysymys kysymysid)
            :matriisi_jarjestys
            (not= 0))
    "kysymys.create.matriisikysymys.epavalidi-matriisi-jarjestys"))

(defn lisaa-matriisikysymys!
  "Lisää uusi kysymys matriisin viimeiseksi."
  [kysymys kysymysid]
  (let [matriisi-kysymys (arkisto/hae-kysymys kysymysid)
        matriisi-jarjestys (arkisto/hae-matriisinkysymyksen-viimeinen-jarjestys kysymysid)
        jarjestetty-kysymys (assoc kysymys
                                   :jarjestys (:jarjestys matriisi-kysymys)
                                   :matriisi_jarjestys matriisi-jarjestys
                                   :matriisi_kysymysid kysymysid)]
    (->(lisaa-kysymys! jarjestetty-kysymys (:kysymysryhmaid matriisi-kysymys))
       (select-keys [:kysymysid]))))

(defn paivita! [kysymysryhmaid kysymysid kysymys-data]
  (when-let [vanha-kysymys (arkisto/hae-kysymys kysymysid)]
    (jdbc/with-transaction
     [tx *db*]

     (let [jatkokysymys-liitokset (arkisto/hae-kysymyksen-jatkokysymykset tx kysymysid)
           uudet-jatkokysymykset (muodosta-jatkokysymykset kysymys-data kysymysryhmaid)]

       ;(log/info "yyy jatkokysymys-liitokset: " (json/generate-string jatkokysymys-liitokset {:pretty true}))

       (if (not (empty? uudet-jatkokysymykset))
         (do
           (doseq [liitos jatkokysymys-liitokset]
             (let [liitos-kys (arkisto/hae-kysymys (:jatkokysymysid liitos))]
               (when (nil? (au/seek #(and (= (:kysymysid %) (:jatkokysymysid liitos))
                                          (= (:vastaus %) (:vastaus liitos)))
                                    uudet-jatkokysymykset))
                 (do
                   (arkisto/poista-jatkokysymysliitos! tx liitos)
                   (when (:jatkokysymys liitos-kys)
                     (poista! tx (:kysymysid liitos-kys)))))))

           (doseq [jatkokysymys uudet-jatkokysymykset]
             (let [jatkokysymysid (if-let [j-kysymysid (:kysymysid jatkokysymys)]
                                    j-kysymysid
                                    (-> (select-keys jatkokysymys jatkokysymys-fields)
                                        (tallenna-uusi-kysymys! kysymysryhmaid tx)
                                        first
                                        :kysymysid))
                   vastaus (:vastaus jatkokysymys)]

               (when (not (arkisto/jatkokysymysliitos-olemassa! tx kysymysid jatkokysymysid vastaus))
                 (arkisto/liita-jatkokysymys! tx kysymysid jatkokysymysid vastaus)))))


         ;else if jos jatkoykysymykset on tyhjä poistetaan kaikki liitokset
         ;        JA haetaan poistettavaksi myös automaattisesti generoidut jatkokysymykset
         (do
           (arkisto/poista-kysymyksen-jatkokysymysliitokset! tx kysymysid)
           (doseq [liitos jatkokysymys-liitokset]
             (let [liitos-kys (arkisto/hae-kysymys (:jatkokysymysid liitos))]
               (when (:jatkokysymys liitos-kys)
                 (poista! tx (:kysymysid liitos-kys))))))))

;; commented out in VAL-1195
;;      (when-let [monivalinnat (:monivalintavaihtoehdot kysymys-data)]
;;        (arkisto/poista-monivalintavaihtoehdot! tx {:kysymysidt [kysymysid]})
;;        (lisaa-monivalintavaihtoehdot! tx monivalinnat kysymysid))
     (-> vanha-kysymys
         (merge kysymys-data)
         (merge {:kayttaja (:oid *kayttaja*)})
         korjaa-eos-vastaus-sallittu
         (arkisto/paivita-kysymys! tx))

     {:kysymysid       kysymysid
      :jatkokysymykset (jatkokysymykset-map tx kysymysid)
      :metatiedot (:metatiedot kysymys-data)})))

(defn kysymys-nakyvissa? [kysymys vertailu-pvm]
  (let [kysymys-piilotettu? (some-> (get-in kysymys [:kysymys_metatiedot :piilotettu])
                                     pvm-util/parse-ymd
                                     (pvm-util/pvm-tanaan-tai-menneisyydessa? vertailu-pvm))]
    (not kysymys-piilotettu?)))
