(ns arvo.service.vastaus
  (:require [arvo.util.file :as file-util]
            [arvo.db.core :refer [*db*] :as db]
            [arvo.db.vastaus :as vdb]
            [clojure.string :as s]
            [clojure.tools.logging :as log]))

(defn parse-monivalinta [vastaus]
  (try (map #(dec (int (Double/parseDouble (s/trim %)))) (filter not-empty (s/split (str vastaus) #",")))
       (catch Exception e nil)))

(defn parse-asteikko [vastaus]
  (when vastaus (int vastaus)))

(defn kysymystyyppi->formatter [kysymys]
  (case (:vastaustyyppi kysymys)
    "monivalinta" parse-monivalinta
    "vapaateksti" identity
    "luku" identity
    "kylla_ei_valinta" (fn [v] (if (= 2 v) "kylla" "ei"))
    parse-asteikko))

(defn format-vastaus [kysymys vastaus]
  (let [formatter (kysymystyyppi->formatter kysymys)]
    (formatter vastaus)))

(defn format-vastaukset [kysymykset vastaukset]
  (into (select-keys vastaukset [:tunnus])
    (for [[kysymysid vastaus] (dissoc vastaukset :tunnus)]
      (let [kysymys (first (filter #(= (:kysymysid %) kysymysid) kysymykset))]
        [kysymysid (format-vastaus kysymys vastaus)]))))

(defn format-vastausdata [kysymykset vastausdata]
  (for [vastaukset vastausdata]
    (format-vastaukset kysymykset vastaukset)))

(defn parse-id [kw]
  (try (int (Double/parseDouble (name kw)))
       (catch Exception e kw)))

(defn tallenna-tiedostosta [tunniste file filename password]
  (let [data (file-util/load-data file filename password)
        tiedonkeruu (db/hae-tiedonkeruu {:tunniste tunniste})
        kysymykset (db/hae-kyselypohjan-kysymykset tiedonkeruu)
        vastausdata (filter #(not-empty (:tunnus %)) (map #(update-keys % parse-id) data))
        _ (log/info "Tallennetaan paperivastauksia: " (count vastausdata) " kpl")]
    (vdb/tallenna-vastaukset
      kysymykset
      (format-vastausdata kysymykset vastausdata))))

