(ns arvo.db.vastaus
  (:require [arvo.db.core :refer [*db*] :as db]
            [clojure.java.jdbc :as jdbc]))

(def vastaus-defaults {:numerovalinta nil :vapaateksti nil :vaihtoehto nil :luku nil :en_osaa_sanoa false})

(defn format-answer [vastaajaid kysymys vastaus]
  (merge vastaus-defaults
    (case (:vastaustyyppi kysymys)
      "kylla_ei_valinta" {:vaihtoehto (name vastaus)}
      "vapaateksti" {:vapaateksti vastaus}
      "luku" {:luku vastaus}
      {:numerovalinta vastaus})
    {:vastaajaid vastaajaid :kysymysid (:kysymysid kysymys)}))

(defn tallenna-monivalinta [tx vastaajaid kysymys vastaukset]
  (doseq [vastaus vastaukset]
    (db/lisaa-vastaus! tx (format-answer vastaajaid kysymys vastaus))))

(defn tallenna-vastaajan-vastaukset [tx kysymykset vastaukset]
  (let [vastaajaid (:vastaajaid (first (db/luo-vastaaja! tx (select-keys vastaukset [:tunnus]))))]
    (doseq [[kysymysid vastaus] (dissoc vastaukset :tunnus)]
      (let [kysymys (first (filter #(= (:kysymysid %) kysymysid) kysymykset))]
        (if (seq? vastaus)
          (tallenna-monivalinta tx vastaajaid kysymys vastaus)
          (db/lisaa-vastaus! tx (format-answer vastaajaid kysymys vastaus)))))))


(defn tallenna-vastaukset [kysymykset vastausdata]
  (jdbc/with-db-transaction [tx *db* {:isolation :read-uncommitted}]
    (doseq [vastaukset vastausdata]
      (tallenna-vastaajan-vastaukset tx kysymykset vastaukset))
    (count vastausdata)))
