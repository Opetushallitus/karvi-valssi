(ns oph.reflect
  (:require  [clojure.test :refer [function?]]))

; Funktio lainattu Tatu Tarvaiselta
(defn- arityt
  "Palauttaa funktion eri arityt. Esim. #{0 1} jos funktio tukee nollan ja yhden parametrin arityjä."
  [f]
  (->> f class .getDeclaredMethods
       (map #(-> % .getParameterTypes alength))
       (into #{})))

(defn no-args?
  "Returns true if f is a var of a function with no arguments. False otherwise."
  [f]
  (cond
    (function? f)
      (= #{0} (arityt f))
    (and
      (seq? f)
      (= 'fn* (first f)))
       (empty? (second f))
    (var? f)
      (= '([]) (:arglists (meta f)))
    :else false))
