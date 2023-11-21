(ns arvo.service.healthcheck
  (:require [arvo.arkisto.healthcheck :as healthcheck]))

(defn check []
  (when (healthcheck/check) "OK"))
