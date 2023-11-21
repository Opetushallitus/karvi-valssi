(ns arvo.toimiala.raportti.util
  (:require
    [clojure.tools.logging :as log]
    [java-time.api :as jt]
    [clojure.string :as string]))

(defn- numeroiden-piste-pilkuksi
  "Jos merkkijono on numero, niin muutetaan piste pilkuksi"
  [merkkijono]
  (if (re-matches #"[0-9.]+" merkkijono)
    (clojure.string/replace merkkijono #"\." ",")
    merkkijono))

(defn- muuta-taulut-stringeiksi [taulut]
  (map (fn [taulu] (map #(if (coll? %) (str (string/join ", " %)) %) taulu)) taulut))

(defn muuta-kaikki-stringeiksi [rivit]
  (muuta-taulut-stringeiksi
    (clojure.walk/postwalk (fn [x]
                              (cond
                                (coll? x) x
                                (jt/local-date? x) (str (jt/instant x "UTC"))
                                :else (numeroiden-piste-pilkuksi (str x))))
                           rivit)))
