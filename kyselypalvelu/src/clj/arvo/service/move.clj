(ns arvo.service.move
  (:require [arvo.arkisto.vastaajatunnus :refer [get-vastaajatunnukset]]
            [clojure.java.jdbc :as jdbc]
            [arvo.db.core :refer [*db*] :as db]))

(defn luo-tunnukset [tunniste]
  (let [kyselykerta (db/hae-move-kyselykerta {:tunniste tunniste})
        oppilaitokset (db/hae-move-oppilaitokset-ilman-tunnusta kyselykerta)
        tunnukset (get-vastaajatunnukset (count oppilaitokset))
        luotavat-tunnukset (map #(assoc %1 :tunnus %2) oppilaitokset tunnukset)]
    (jdbc/with-db-transaction [tx *db*]
      (doseq [tunnus luotavat-tunnukset]
        (db/lisaa-move-tunnus! tx (merge tunnus kyselykerta)))
      (str "Luotu " (count luotavat-tunnukset) " tunnusta"))))

(defn luo-uudelleenlahetyskerta [lahetyskertaid uusi-viestipohjatyyppi lahetetyt]
  (jdbc/with-db-transaction
   [tx *db*]
   (let [tunnus->email (group-by :tunnus lahetetyt)
         vanha-lahetyskerta (db/hae-lahetyskerta-by-id tx {:id lahetyskertaid})
         uusintalahetyskerta (-> (db/hae-lahetyskerta-max-uusintalahetyskerta tx {:tunniste (:kysely_tunniste vanha-lahetyskerta)})
                                 :uusintalahetyskerta
                                 inc)
         tunnukset (->> (db/hae-move-tunnisteen-tunnukset tx {:tunniste (:kysely_tunniste vanha-lahetyskerta)})
                        (filter #(not= (:sahkoposti %) (:sahkoposti (first (get tunnus->email (:tunnus %)))))))]
     (db/lisaa-lahetyskerta tx (merge vanha-lahetyskerta {:uusintalahetyskerta uusintalahetyskerta
                                                          :teksti_tyyppi       uusi-viestipohjatyyppi
                                                          :tila                nil}))
     (db/move-paivita-lahetyskerta-tunniste tx {:lahetyskertatunniste (str (:kysely_tunniste vanha-lahetyskerta) "/" uusintalahetyskerta)
                                                :tunnukset (map :tunnus tunnukset)}))))
