(ns arvo.infra.eraajo.raportointi
  (:require [clojure.tools.logging :as log]
            [arvo.service.raportointi :as raportointi]
            [arvo.infra.kayttaja.vaihto :refer [with-kayttaja]]
            [arvo.infra.kayttaja.vakiot :refer [jarjestelma-uid]]))

;; Cloverage ei tykkää `defrecord`eja generoivista makroista, joten hoidetaan
;; `defjob`:n homma käsin.
(defrecord PaivitaNakymatJob []
   org.quartz.Job
   (execute [this ctx]
     (try
       (raportointi/paivita-vertailudata!)
       (catch Exception e
         (log/error "Raportoinnin vertailudatan päivitys"
                    (map str (.getStackTrace e)))))))
