(ns arvo.util.csv
  (:require [clojure.data.csv :as csv]
            [clojure.java.io :as io]
            [clojure.string :as s]
            [java-time.api :as jt]
            [arvo.util.paivamaara-util :as pvm-util]
            [arvo.config :refer [env]]))

(def valid-chars (apply str (map char (range 256))))

(def default-separator \tab)

(defn clean-str [val]
  (->> (apply str val)
    (filter #(<= 32 (int %) 126))
    (apply str)
    (s/trim)))

(defn read-csv
  ([filename separator]
   (with-open [reader (io/reader filename)]
     (let [file (csv/read-csv reader :separator separator);)
           header-row (map (comp keyword clean-str) (first file))
           data (doall (map #(zipmap header-row %) (rest file)))]
       data)))
  ([filename]
   (read-csv filename default-separator)))

(defn get-header [columns names]
  (let [translation (fn [col] (or (get names col) (name col)))]
    (map translation columns)))

(defn get-rows [header data]
  (map (fn [row]
         (for [k header]
           (get row k))) data))

(defn format-local-date
  "Muuntaa local-datet vastaamaan lähemmäs vanhaa CSV:n formaattia"
  [value]
  (if (jt/local-date? value)
    (str (pvm-util/local-date->instant value))
    value))

(defn format-data [value-map]
  (into {} (for [[key value] value-map] {key (format-local-date value)})))

(defn generate-csv
  ([header data separator names]
   (let [formatted-data (map format-data data)
         headers (get-header header names)
         rows (get-rows header formatted-data)]
     (with-open [writer (java.io.StringWriter.)]
       (csv/write-csv writer (cons headers rows) :separator separator)
       (.toString writer)))))

(defn write-csv
  ([data filename separator]
   (let [columns (keys (first data))
         headers (map name columns)
         rows (mapv #(mapv % columns) data)]
     (with-open [writer (io/writer filename)]
       (csv/write-csv writer (cons headers rows)) :separator separator)))
  ([data filename]
   (write-csv data filename default-separator)))
