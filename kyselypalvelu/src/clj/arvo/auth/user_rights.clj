(ns arvo.auth.user-rights
  (:require [arvo.infra.kayttaja :as kayttaja :refer [*kayttaja*]]
            [clojure.core.match :refer [match]]
            [arvo.db.core :refer [*db*] :as db]
            [arvo.config :refer [env]]
            [arvo.toimiala.kayttajaroolit :as kayttajaroolit]
            [clojure.tools.logging :as log]))

(defn format-organisaatiotiedot [data]
  (select-keys data [:koulutustoimija :oppilaitos]))

(defn valtakunnallinen-organization [data]
  (if (:valtakunnallinen data)
      {:ei-tarkisteta-organisaatiota true}
    (format-organisaatiotiedot data)))

(defn konteksti->organisaatio [konteksti]
  (match [konteksti]
         [{:kyselypohjaid _}] (valtakunnallinen-organization (db/hae-kyselypohja konteksti))
         [{:kyselykertaid _}] (format-organisaatiotiedot (db/hae-kyselykerran-organisaatio konteksti))
         [{:kyselyid _}] (format-organisaatiotiedot (db/hae-kysely konteksti))
         [{:kysymysryhmaid _}] (valtakunnallinen-organization (db/hae-kysymysryhma konteksti))
         :else {:ei-tarkisteta-organisaatiota true}))

(defn- organisaatio-oikeus-dataan?
  "Aktiivisella oppilaitos käyttäjälä täytyy sekä koulutustoimijan että oppilaitoksen vastata datasta löytyviä vastikkeitaan."
  [vaadittu-organisaatio]
  (let [aktiivinen-koulutustoimija (:organisaatio (:aktiivinen-rooli *kayttaja*))
        koulutustoimijalla-oikeus-dataan? (= (:koulutustoimija vaadittu-organisaatio) aktiivinen-koulutustoimija)
        aktiiviset-oppilaitokset (:aktiiviset-oppilaitokset *kayttaja*)]
    (if (not-empty aktiiviset-oppilaitokset)
      (let [oppilaitoksella-oikeus-dataan? (some #{(:oppilaitos vaadittu-organisaatio)} aktiiviset-oppilaitokset)]
        (and koulutustoimijalla-oikeus-dataan? oppilaitoksella-oikeus-dataan?))
      koulutustoimijalla-oikeus-dataan?)))

(defn tarkista-kayttooikeus
  "Jos datassa on jokin tunnettu id mukana oikeus siihen tarkistetaan täällä. Huom. ei ota kantaa listaus tai luonti tapahtumiin"
  [vaadittu-kayttooikeus konteksti]
  (let [vaadittu-organisaatio (konteksti->organisaatio konteksti)
        kayttooikeudet (when (or (:ei-tarkisteta-organisaatiota vaadittu-organisaatio)
                                 (organisaatio-oikeus-dataan? vaadittu-organisaatio))
                         (kayttajaroolit/oikeudet(:rooli (:aktiivinen-rooli *kayttaja*))))]
    (boolean (some #{vaadittu-kayttooikeus} kayttooikeudet))))

(defmacro authorize [vaadittu-kayttooikeus konteksti & body]
  `(do
     (if (~tarkista-kayttooikeus ~vaadittu-kayttooikeus ~konteksti)
       (do
         ~@body)
       (do
         (log/error "Käyttöoikeudet eivät riitä. Toiminto estetty.")
         (throw (ex-info "Käyttöoikeudet eivät riitä." {:cause :kayttooikeudet}))))))
