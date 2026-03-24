(ns arvo.infra.eraajo.koulutustoimijoiden-tutkinnot
    (:require [clojure.tools.logging :as log]
      [arvo.integraatio.oiva :as oiva]
      [arvo.db.core :refer [*db*] :as db]
      [cheshire.core :as json]
      [arvo.infra.kayttaja.vakiot :refer [integraatio-uid]]
      [next.jdbc :as jdbc]))

(defn paivita-koulutustoimijoiden-tutkinnot! []
      (log/info "Aloitetaan koulutustoimijoiden tutkintojen päivitys Oivasta")
      (let [koulutustoimijoiden-tutkinnot (oiva/hae-koulutustoimijoiden-tutkinnot)]
           (jdbc/with-transaction [tx *db*]
                                  (doseq [koulutustoimija koulutustoimijoiden-tutkinnot
                                          tutkinto (:koulutukset koulutustoimija)]
                                         (db/lisaa-koulutustoimijan-tutkinto! tx {:ytunnus (:jarjestajaYtunnus koulutustoimija)
                                                                                  :tutkintotunnus tutkinto
                                                                                  :alkupvm (:alkupvm koulutustoimija)
                                                                                  :loppupvm (:loppupvm koulutustoimija)
                                                                                  :laaja_oppisopimuskoulutus (= "1" (:laajaOppisopimuskoulutus koulutustoimija))})))

           (log/info "Koulutustoimijoiden tutkintojen päivitys Oivasta valmis")))

;; Cloverage ei tykkää `defrecord`eja generoivista makroista, joten hoidetaan
;; `defjob`:n homma käsin.
(defrecord PaivitaKoulutustoimijoidenTutkinnotJob []
           org.quartz.Job
           (execute [this ctx]
                    (try
                      (paivita-koulutustoimijoiden-tutkinnot!)
                      (catch Exception e
                        (log/error "Koulutustoimijoiden tutkintojen päivitys Oivasta epäonnistui"
                                   (map str (.getStackTrace e)))))))
