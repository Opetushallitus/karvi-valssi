(ns arvo.arkisto.healthcheck
  (:require [arvo.db.core :refer [*db*] :as db]))

(defn check []
  (-> (db/healthcheck)
      :count
      some?))
