(ns arvo.toimiala.kayttajaroolit
  (:require [arvo.config :refer [env]]))

(defn kaikki-kyselytyypit []
  (distinct (apply concat (vals (:kyselytyypit env)))))

(defn- haettavan-arvon-avain [[avain arvot] haettava-arvo]
  (when (some #(= haettava-arvo %) arvot)
    avain))

(defn kayttooikeus->rooli [kayttooikeus]
  (some->> (:rooli-kayttooikeus env)
           (some #(haettavan-arvon-avain % kayttooikeus))
           name
           clojure.string/upper-case))

(defn kayttooikeus->kyselytyypit [kayttooikeus]
  (let [kyselytyypit-avain (some->> (:kyselytyyppi-kayttooikeudet env)
                                    (some #(haettavan-arvon-avain % kayttooikeus)))]
    (case kyselytyypit-avain
      :kaikki (kaikki-kyselytyypit)
      (kyselytyypit-avain (:kyselytyypit env)))))

; Sisäisiä rooleja joten ei tarvitse olla konfiguraatiossa
(def roolijarjestys
  "Roolien prioriteettijärjestys, jolla valitaan aktiivinen rooli jos käyttäjä ei ole sitä valinnut"
  {"YLLAPITAJA" 0
   "VASTUUKAYTTAJA" 2
   "KYSELYKERTAKAYTTAJA" 3
   "KAYTTAJA" 4
   "KATSELIJA" 5})

(defn oikeudet [rooli]
  ; Hakee käyttäjän rooliin kuuluvat oikeudet esim. jos rooli on KAYTTAJA => [:vastaajatunnus :katselu]
  ; Because cprops doesn't support keywords in env variables roles need to be in format: {:katselija ["katselu"] ...} => {:katselija [:katselu] ...}
  (let [keyword-roles (clojure.walk/postwalk #(if (string? %) (keyword %) %) (:roolit env))
        ; Format: "YLLAPITAJA" => :yllapitaja
        active-role-keyword (keyword (clojure.string/lower-case rooli))]
    (get keyword-roles active-role-keyword)))
