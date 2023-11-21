(ns arvo.arkisto.kysymys
  (:require [arvo.db.core :refer [*db*] :as db]))

(defn kysymysryhman-kysymykset-olemassa-count [data]
  (db/kysymysryhman-kysymykset-olemassa-count data))

(defn kysymyksen-matriisi-jarjestys [{:keys [kysymysid1 kysymysid2]}]
  (db/kysymyksen-matriisi-jarjestys {:kysymysidt [kysymysid1 kysymysid2]}))

(defn vaihda-kysymysten-jarjestys! [kysymys-vaihto-data]
  (db/vaihda-kysymysten-jarjestys! kysymys-vaihto-data))

(defn hae-kysymyksen-jatkokysymykset [tx kysymysid]
  (db/hae-kysymyksen-jatkokysymykset tx {:kysymysid kysymysid}))

(defn hae-kysymyksen-matriisikysymykset [tx kysymysid]
  (db/hae-kysymyksen-matriisikysymykset tx {:kysymysid kysymysid}))

(defn poista-monivalintavaihtoehdot! [tx kysymys-idt]
  (db/poista-monivalintavaihtoehdot! tx kysymys-idt))

(defn poista-jatkokysymysliitokset! [tx kysymys-idt]
  (db/poista-jatkokysymysliitokset! tx kysymys-idt))

(defn poista-kysymykset! [tx kysymys-idt]
  (db/poista-kysymykset! tx kysymys-idt))

(defn lisaa-kysymys! [tx kysymys-data]
  (db/lisaa-kysymys! tx kysymys-data))

(defn paivita-matriisi-kysymysid! [tx kysymysid matriisi-kysymysid]
  (db/paivita-matriisi-kysymysid! tx {:kysymysid kysymysid :matriisi_kysymysid matriisi-kysymysid}))

(defn lisaa-monivalintavaihtoehto! [monivalinta-data tx]
  (db/lisaa-monivalintavaihtoehto! tx monivalinta-data))

(defn liita-jatkokysymys! [tx kysymysid jatkokysymysid vastaus]
  (db/liita-jatkokysymys! tx {:kysymysid kysymysid :jatkokysymysid jatkokysymysid :vastaus vastaus}))

(defn hae-kysymysryhman-viimeinen-jarjestys [kysymysryhmaid]
  (-> (db/hae-kysymysryhman-viimeinen-jarjestys {:kysymysryhmaid kysymysryhmaid})
      :max
      (or -1)
      inc
      ref))

(defn hae-matriisinkysymyksen-viimeinen-jarjestys [kysymysid]
  (-> (db/hae-matriisin-viimeinen-jarjestys {:kysymysid kysymysid})
      :max
      (or -1)
      inc))

(defn paivita-kysymys! [kysymys-data tx]
  (db/paivita-kysymys! tx kysymys-data))

(defn hae-kysymys [kysymysid]
  (db/hae-kysymys {:kysymysid kysymysid}))
