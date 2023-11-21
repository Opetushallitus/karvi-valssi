(ns arvo.service.yllapito
  (:require [arvo.db.core :refer [*db*] :as db]
            [arvo.util.excel :as excel]
            [arvo.config :refer [env]]
            [arvo.infra.eraajo.koodistot :as koodistot]
            [arvo.infra.eraajo.koulutustoimijoiden-tutkinnot :refer [paivita-koulutustoimijoiden-tutkinnot!]]
            [arvo.infra.eraajo.automaattikyselyt :refer [luo-automaattikyselyt!]]))

(defn hae-vastaustiedosto [tunniste]
  (let [tiedonkeruu (db/hae-tiedonkeruu {:tunniste tunniste})
        kysymykset (filter #(not= "valiotsikko" (:vastaustyyppi %)) (flatten (db/hae-kyselypohjan-kysymykset tiedonkeruu)))
        headers [(cons "" (map :kysymysid kysymykset)) (cons "" (map :kysymys_fi kysymykset))]
        tunnukset (db/hae-tiedonkeruun-tunnukset {:tunniste tunniste})]
    (excel/generate-excel headers tunnukset [:tunnus] "Vastaukset")))

(defn kaynnista-eraajo [tyyppi]
  (case tyyppi
    :automaattikyselyt (luo-automaattikyselyt!)
    :oiva (paivita-koulutustoimijoiden-tutkinnot!)
    :koodistot (koodistot/paivita-koodistot! (:koodistopalvelu env))))
