(ns arvo.infra.eraajo.koodistot
  (:require [clojurewerkz.quartzite.jobs :as j
             :refer [defjob]]
            [clojurewerkz.quartzite.conversion :as qc]
            [clojure.tools.logging :as log]
            [arvo.integraatio.koodistopalvelu :as koodisto]
            [arvo.infra.kayttaja.vaihto :refer [with-kayttaja]]
            [arvo.infra.kayttaja.vakiot :refer [integraatio-uid]]))

(defn ^:integration-api paivita-koodistot! [asetukset]
  (with-kayttaja integraatio-uid nil nil
    (koodisto/paivita-koodistot! asetukset)))

;; Cloverage ei tykkää `defrecord`eja generoivista makroista, joten hoidetaan
;; `defjob`:n homma käsin.
(defrecord PaivitaKoodistotJob []
   org.quartz.Job
   (execute [this ctx]
     (try
      (let [{asetukset "asetukset"} (qc/from-job-data ctx)]
        (paivita-koodistot! (clojure.walk/keywordize-keys asetukset)))
      (catch Exception e
        (log/error "Koodistojen päivitys koodistopalvelusta epäonnistui"
                   (map str (.getStackTrace e)))))))
