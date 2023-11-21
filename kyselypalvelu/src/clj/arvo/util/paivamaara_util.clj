(ns arvo.util.paivamaara-util
  (:require
    [java-time.api :as jt]
    [clojure.tools.logging :as log]))

(defn voimassa-java-date? [^java.time.LocalDate pvm1 ^java.time.LocalDate pvm2]
  (let [nyt (jt/local-date)]
    (and (or (nil? pvm1) (= nyt pvm1) (jt/after? nyt pvm1))
         (or (nil? pvm2) (= nyt pvm2) (jt/before? nyt pvm2)))))

(defn valin-sisalla?
  "Tarkistaa, että pvm2-aikaväli on pvm1-aikavälin sisällä tai jos pvm1-aikavälin jompikumpi pää on nil saa pvm2 vastaava pää olla mitä tahansa."
  [^java.time.LocalDate pvm1-alku ^java.time.LocalDate pvm1-loppu ^java.time.LocalDate pvm2-alku ^java.time.LocalDate pvm2-loppu]
  (and (if (nil? pvm2-alku) (nil? pvm1-alku) true)
       (if (nil? pvm2-loppu) (nil? pvm1-loppu) true)
   (or (nil? pvm1-alku) (= pvm1-alku pvm2-alku) (jt/after? pvm2-alku pvm1-alku))
       (or (nil? pvm1-loppu) (= pvm1-loppu pvm2-loppu) (jt/after? pvm1-loppu pvm2-loppu))))

(defn current-millis []
  (.toEpochMilli (jt/instant)))

(defn pvm-menneisyydessa?
  ([pvm]
  {:pre [(not (nil? pvm))]}
  (let [nytpvm (jt/local-date)]
    (pvm-menneisyydessa? pvm nytpvm)))
  ([pvm vertailu-pvm]
   (jt/after? vertailu-pvm pvm)))

(defn pvm-tanaan-tai-menneisyydessa?
  ([pvm]
  (let [nytpvm (jt/local-date)]
    (pvm-tanaan-tai-menneisyydessa? pvm nytpvm)))
  ([pvm vertailu-pvm]
   (or (= pvm vertailu-pvm)
       (pvm-menneisyydessa? pvm vertailu-pvm))))

(defn pvm-tulevaisuudessa?
  ([pvm]
  {:pre [(not (nil? pvm))]}
  (let [nytpvm (jt/local-date)]
    (pvm-tulevaisuudessa? pvm nytpvm)))
  ([pvm vertailu-pvm]
   (jt/before? vertailu-pvm pvm)))

(defn pvm-tanaan-tai-tulevaisuudessa?
  ([pvm]
  (let [nytpvm (jt/local-date)]
    (pvm-tanaan-tai-tulevaisuudessa? pvm nytpvm)))
  ([pvm vertailu-pvm]
   (or (= pvm vertailu-pvm)
       (pvm-tulevaisuudessa? pvm vertailu-pvm))))

(defn parse-ymd
  "year-month-day->local-date"
  [ymd]
  (some->> ymd (jt/local-date "yyyy-MM-dd")))

(defn format-ymd
  "local-date->year-month-day"
  [local-date]
  (some->> local-date (jt/format "yyyy-MM-dd")))

(defn local-date->instant [local-date]
  (jt/instant (.atStartOfDay local-date) "UTC"))
