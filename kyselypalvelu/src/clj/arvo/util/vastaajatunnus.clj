(ns arvo.util.vastaajatunnus
  (:require [arvo.config :refer [env]]
            [clojure.java.jdbc :as jdbc]))

(def allowed-chars "ACEFHJKLMNPRTWXY347")
(def tunnus-length 5)

(def start-val (int (reduce #(+ (Math/pow (count allowed-chars) %2) %1) (range tunnus-length))))

(defn get-nth [a m seed]
  (fn [x] (mod (+ a x seed) m)))

(def closest-prime 2476081)

(defn lazyrange [] (drop 1 (iterate (get-nth 131943 closest-prime (:vastaajatunnus-seed env)) 0)))

(defn -generate-tunnus [val]
  (let [quot (quot val (count allowed-chars))
        char (nth allowed-chars (mod val (count allowed-chars)))]
    (str (when (< 0 quot) (-generate-tunnus (dec quot))) char)))

(defn generate-tunnus [val]
  (-generate-tunnus (+ val start-val)))

(defn luo-tunnuksia [start n]
  (let [lr (lazyrange)]
    (->> lr
         (drop start)
         (take n)
         (map generate-tunnus))))

; vanha arvon tunnusten luonti, ei takaa uniikkiutta
(defn luo-satunnainen-tunnus
  [pituus]
  {:post [(and
            (string? %)
            (= pituus (.length %)))]}
  (apply str (take pituus (repeatedly #(rand-nth allowed-chars)))))

(defn luo-satunnaisia-tunnuksia
  "Luo keskenään uniikkeja satunnaisia määritellyn pituisia tunnuksia."
  [pituus]
  (distinct
    (repeatedly 10000 #(luo-satunnainen-tunnus pituus))))