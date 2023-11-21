(ns arvo.arkisto.kysymysryhma
  (:require
    [arvo.infra.kayttaja :refer [vastuukayttaja? yllapitaja?]]
    [clojure.tools.logging :as log]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [arvo.db.core :refer [*db*] :as db]
    [arvo.service.kysymys :as kysymys]
    [arvo.arkisto.kysely :refer [hae-kysymysryhman-kysymykset]]))

(defn hae-kysymysryhmat
  ([koulutustoimija oppilaitokset vain-voimassaolevat]
   (db/hae-kysymysryhmat {:yllapitaja?         (yllapitaja?)
                          :vain_voimassaolevat vain-voimassaolevat
                          :koulutustoimija     koulutustoimija
                          :oppilaitokset       oppilaitokset}))
  ([koulutustoimija oppilaitokset]
   (hae-kysymysryhmat koulutustoimija oppilaitokset false)))

(defn hae-taustakysymysryhmat []
  (db/hae-taustakysymysryhmat))

(def tyhja-kysymysryhma { :taustakysymykset false
                          :valtakunnallinen false
                          :nimi_fi nil
                          :nimi_sv nil
                          :selite_fi nil
                          :selite_sv nil
                          :koulutustoimija nil
                          :oppilaitos nil
                          :luotuaika nil
                          :muutettuaika nil
                          :tila "luonnos"
                          :kuvaus_fi nil
                          :kuvaus_sv nil
                          :nimi_en nil
                          :selite_en nil
                          :kuvaus_en nil
                          :metatiedot nil})

(defn lisaa-kysymysryhma! [tx kysymysryhma-data]
  (let [kysymysryhma  (merge tyhja-kysymysryhma (assoc kysymysryhma-data :kayttaja (:oid *kayttaja*)))
        kysymysryhma-id (db/lisaa-kysymysryhma! tx kysymysryhma)]
    (first kysymysryhma-id)))

(defn hae-monivalintakysymyksen-vaihtoehdot
  [kysymysid]
  (db/hae-monivalintavaihtoehto {:kysymysid kysymysid}))

(defn taydenna-monivalintakysymys
  [monivalintakysymys]
  (let [kysymysid (:kysymysid monivalintakysymys)]
    (assoc monivalintakysymys :monivalintavaihtoehdot (hae-monivalintakysymyksen-vaihtoehdot kysymysid))))

(def kylla-jatkokysymyksen-kentat
  [:kylla_teksti_fi
   :kylla_teksti_sv
   :kylla_teksti_en
   :kylla_vastaustyyppi])

(def ei-jatkokysymyksen-kentat
  [:ei_teksti_fi
   :ei_teksti_sv
   :ei_teksti_en
   :jatkokysymys_max_vastaus])

(def jatkokysymyksen-kentat
  (into kylla-jatkokysymyksen-kentat ei-jatkokysymyksen-kentat))

(defn onko-jokin-kentista-annettu?
  [m kentat]
  (not-every? nil? (vals (select-keys m kentat))))

(defn kylla-jatkokysymys?
  [kysymys]
  (onko-jokin-kentista-annettu? kysymys [:kylla_teksti_fi :kylla_teksti_sv :kylla_teksti_en]))

(defn ei-jatkokysymys?
  [kysymys]
  (onko-jokin-kentista-annettu? kysymys [:ei_teksti_fi :ei_teksti_sv :ei_teksti_en]))

(defn jatkokysymys?
  [kysymys]
  (or (kylla-jatkokysymys? kysymys) (ei-jatkokysymys? kysymys)))

(defn poista-nil-kentat
  [m]
  (into {} (remove (comp nil? second) m)))

(defn erottele-jatkokysymys
  [kysymys]
  (-> kysymys
    (select-keys jatkokysymyksen-kentat)
    poista-nil-kentat
    (clojure.set/rename-keys {:jatkokysymys_max_vastaus :max_vastaus})
    (assoc :kylla_jatkokysymys (kylla-jatkokysymys? kysymys))
    (assoc :ei_jatkokysymys (ei-jatkokysymys? kysymys))))

(defn taydenna-jatkokysymys
  [kysymys]
  (let [jatkokysymys (erottele-jatkokysymys kysymys)]
    (-> kysymys
        (assoc :jatkokysymys jatkokysymys)
        (as-> kysymys (apply dissoc kysymys jatkokysymyksen-kentat)))))

(defn taydenna-kysymys
  [kysymys]
  (cond-> kysymys
    (= "monivalinta" (:vastaustyyppi kysymys)) taydenna-monivalintakysymys
    (jatkokysymys? kysymys) taydenna-jatkokysymys))

(defn taydenna-kysymysryhman-monivalintakysymykset
  [kysymysryhma]
  (let [kysymykset (for [kysymys (:kysymykset kysymysryhma)]
                     (if (= "monivalinta" (:vastaustyyppi kysymys))
                       (taydenna-monivalintakysymys kysymys)
                       kysymys))]
    (assoc kysymysryhma :kysymykset kysymykset)))

(defn taydenna-kysymysryhman-kysymykset
  [kysymysryhma]
  (update-in kysymysryhma [:kysymykset] #(doall (map taydenna-kysymys %))))

(def kysymysryhma-fields [:kysymysryhmaid :tila :nimi_fi :nimi_sv :nimi_en :selite_fi :selite_sv :selite_en :kuvaus_fi :kuvaus_sv :kuvaus_en :taustakysymykset :valtakunnallinen :metatiedot])

(defn liita-erikoiskysymykset [jatkokysymykset-map matriisikysymykset-map kysymys]
  (let [jatkokysymykset (get jatkokysymykset-map (:kysymysid kysymys))
        matriisikysymykset (get matriisikysymykset-map (:kysymysid kysymys))]
    (cond
      jatkokysymykset (reduce #(assoc-in %1 [:jatkokysymykset (:jatkokysymys_vastaus %2)] %2) kysymys jatkokysymykset)
      matriisikysymykset (assoc kysymys :matriisikysymykset matriisikysymykset)
      :else kysymys)))

(defn taydenna-kysymysryhma [kysymysryhma]
  (let [kysymykset (db/hae-kysymysryhman-kysymykset {:kysymysryhmaid (:kysymysryhmaid kysymysryhma)})
        jatkokysymykset (group-by :jatkokysymys_kysymysid (filter :jatkokysymys kysymykset))
        matriisin-sisainen-kysymys? #(when-some [matriisijarjestys (:matriisi_jarjestys %)] (> matriisijarjestys 0))
        matriisikysymykset (group-by :matriisi_kysymysid (filter matriisin-sisainen-kysymys? kysymykset))
        naytettavat-kysymykset (remove #(or (:jatkokysymys %) (matriisin-sisainen-kysymys? %)) kysymykset)
        kys (map #(liita-erikoiskysymykset jatkokysymykset matriisikysymykset %) naytettavat-kysymykset)]
    (assoc kysymysryhma :kysymykset (sort-by :jarjestys kys))))

(defn hae
  ([kysymysryhmaid]
   (hae kysymysryhmaid true))
  ([kysymysryhmaid hae-kysymykset]
   (let [kysymysryhma (db/hae-kysymysryhma {:kysymysryhmaid kysymysryhmaid})]
     (if hae-kysymykset
       (-> kysymysryhma
         (select-keys kysymysryhma-fields)
         taydenna-kysymysryhma
         taydenna-kysymysryhman-kysymykset)
       kysymysryhma))))

(defn kysymysryhma-tilassa? [kysymysryhmaid & tilat]
  (boolean (some #{(:tila (hae kysymysryhmaid false))} (into #{} tilat))))

(defn luonnos? [kysymysryhmaid]
  (kysymysryhma-tilassa? kysymysryhmaid "luonnos"))

(defn julkaistu? [kysymysryhmaid]
  (kysymysryhma-tilassa? kysymysryhmaid "julkaistu"))

(defn julkaistavissa? [kysymysryhmaid]
  (kysymysryhma-tilassa? kysymysryhmaid "luonnos" "suljettu"))

(defn hae-taustakysymysryhma [kysymysryhmaid]
  (hae kysymysryhmaid))

(defn hae-kysymysryhman-kysymyksien-idt [kysymysryhmaid]
  (map :kysymysid (db/hae-kysymysryhman-kysymyksien-idt {:kysymysryhmaid kysymysryhmaid})))

(def kysymysryhma-esikatselu-kentat [:kysymysryhmaid :nimi_fi :nimi_sv :nimi_en :kuvaus_fi :kuvaus_sv :kuvaus_en :tila :valtakunnallinen :taustakysymykset :metatiedot])
(def kysymys-kentat [:kysymysid :kysymys_fi :kysymys_sv :kysymys_en :poistettava :pakollinen :vastaustyyppi :monivalinta_max :eos_vastaus_sallittu :jatkokysymys :jarjestys :kysymysryhmaid :max_vastaus])

(defn hae-esikatselulle
  [kysymysryhmaid]
  (-> (db/hae-kysymysryhma {:kysymysryhmaid kysymysryhmaid})
      (select-keys kysymysryhma-esikatselu-kentat)
      (assoc :kysymykset (map #(select-keys % kysymys-kentat) (db/hae-kysymysryhman-kysymykset {:kysymysryhmaid kysymysryhmaid})))
      taydenna-kysymysryhman-monivalintakysymykset))

(def kyselypohja-esikatselu-kentat [:kysymysryhmaid :nimi_fi :nimi_sv :nimi_en :kuvaus_fi :kuvaus_sv :kuvaus_en :tila :valtakunnallinen :taustakysymykset :metatiedot :jarjestys :kyselypohjaid])
(def kyselypohja-kysymys-kentat [:kysymysid :kysymys_fi :kysymys_sv :kysymys_en :poistettava :pakollinen :vastaustyyppi :monivalinta_max :eos_vastaus_sallittu :jatkokysymys :jarjestys :kysymysryhmaid :max_vastaus :jatkokysymys_kysymysid :jatkokysymys_vastaus])

(defn hae-kyselypohjasta
  "Hakee kyselypohjan kyselyryhmät, jotka ovat lisättävissä kyselyyn"
  [kyselypohjaid]
  (let [kysymysryhmaid->kysymykset (->> (db/hae-kyselypohjan-kysymykset {:kyselypohjaid kyselypohjaid})
                                        (map #(select-keys % kyselypohja-kysymys-kentat))
                                        (group-by :kysymysryhmaid))]
    (->> (db/hae-kysymysryhmatiedot-kyselypohjalla {:kyselypohjaid kyselypohjaid})
        (map #(select-keys % kyselypohja-esikatselu-kentat))
        (map #(assoc % :kysymykset (get kysymysryhmaid->kysymykset (:kysymysryhmaid %))))
        (map taydenna-kysymysryhman-monivalintakysymykset))))

(defn hae-kyselypohjaan-kuuluvat [kyselypohjaid]
  (let [kysymysryhmat (db/hae-kyselypohjan-kysymysryhmat {:kyselypohjaid kyselypohjaid})
        kysymysryhmaidt (map :kysymysryhmaid kysymysryhmat)]
    (map hae kysymysryhmaidt)))

(defn hae-kyselysta
  "Hakee kyselyn kysymysryhmät"
  [kyselyid]
  (let [kysymysryhmaid->kysymykset (->> (db/hae-kyselyn-kysymykset {:kyselyid kyselyid})
                                        (map #(select-keys % (conj kyselypohja-kysymys-kentat :poistettu)))
                                        (group-by :kysymysryhmaid))]
    (->> (db/hae-kyselyn-kysymysryhmat {:kyselyid kyselyid})
         (map #(select-keys % kysymysryhma-esikatselu-kentat))
         (map #(assoc % :kysymykset (get kysymysryhmaid->kysymykset (:kysymysryhmaid %))))
         (map taydenna-kysymysryhman-monivalintakysymykset))))

(def paivitettavat-kysymysryhma-kentat [ :nimi_fi
                                         :nimi_sv
                                         :nimi_en
                                         :selite_fi :selite_sv :selite_en
                                         :kuvaus_fi :kuvaus_sv :kuvaus_en
                                         :valtakunnallinen
                                         :taustakysymykset
                                         :metatiedot])

(defn paivita! [kysymysryhma]
  (let [kysymysryhma-data (assoc (select-keys kysymysryhma paivitettavat-kysymysryhma-kentat)
                                 :kayttaja (:oid *kayttaja*)
                                 :kysymysryhmaid (:kysymysryhmaid kysymysryhma))
         paivitetty-kysymysryhma (db/paivita-kysymysryhma! kysymysryhma-data)]
    (select-keys paivitetty-kysymysryhma (conj paivitettavat-kysymysryhma-kentat :kysymysryhmaid))))

(defn poista! [tx kysymysryhmaid]
  (db/poista-kysymysryhma! tx {:kysymysryhmaid kysymysryhmaid}))

(defn poista-kysymysryhman-kysymykset! [tx kysymysryhmaid]
  (let [kysymykset (db/hae-kysymysryhman-kysymykset tx {:kysymysryhmaid kysymysryhmaid})]
    (doseq [kysymys kysymykset]
      (kysymys/poista! tx (:kysymysid kysymys)))))

(defn ^:private aseta-tila!
  [kysymysryhmaid tila]
  (db/aseta-kysymysryhman-tila! {:kysymysryhmaid kysymysryhmaid :tila tila :kayttaja (:oid *kayttaja*)})
  (hae kysymysryhmaid))

(defn julkaise!
  [kysymysryhmaid]
  (when (julkaistavissa? kysymysryhmaid)
    (aseta-tila! kysymysryhmaid "julkaistu")))

(defn sulje!
  [kysymysryhmaid]
  (aseta-tila! kysymysryhmaid "suljettu"))

(defn palauta-luonnokseksi!
  [kysymysryhmaid]
  (when (julkaistu? kysymysryhmaid)
    (aseta-tila! kysymysryhmaid "luonnos")))

(defn laske-kysymykset [kysymysryhmaid]
  (-> (db/laske-kysymysryhman-kysymykset {:kysymysryhmaid kysymysryhmaid})
      :count))

(defn laske-kyselyt [kysymysryhmaid]
  (-> (db/laske-kysymysryhman-kyselyt {:kysymysryhmaid kysymysryhmaid})
      :count))

(defn laske-kyselypohjat [kysymysryhmaid]
  ((db/laske-kyselypohjan-kysymysryhmat {:kysymysryhmaid kysymysryhmaid})
    :count))

(defn hae-asteikot [koulutustoimija]
  (db/hae-asteikot {:koulutustoimija koulutustoimija}))

(defn tallenna-asteikko [asteikko]
  (db/tallenna-asteikko asteikko)
  asteikko)
