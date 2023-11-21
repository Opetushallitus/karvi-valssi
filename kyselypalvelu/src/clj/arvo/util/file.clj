(ns arvo.util.file
  (:require [clojure.string :as s]
            [arvo.util.excel :as excel]
            [arvo.util.csv :as csv]
            [clojure.core.match :refer [match]])
  (:import (java.security MessageDigest)
           (javassist.bytecode ByteArray)))


(defn read-bytes [^String path]
  (let [file (java.io.File. path)
        bytearr (byte-array (.length file))
        is (java.io.FileInputStream. file)]
    (.read is bytearr)
    (.close is)
    bytearr))

(defn read-bytes [^String path]
  (let [file (java.io.File. path)
        bytearr (byte-array (.length file))
        is (java.io.FileInputStream. file)]
    (.read is bytearr)
    (.close is)
    bytearr))

(defn md5 [^ByteArray bytes]
  (let [algorithm (MessageDigest/getInstance "MD5")
        raw (.digest algorithm bytes)]
    (format "%032x" (BigInteger. 1 raw))))

(defn checksum [path] (md5 (read-bytes path)))

(defn load-data
  ([file filename password]
   (match [(last (s/split filename #"\."))]
          ["csv"] (csv/read-csv file)
          ["xlsx"] (excel/load-excel file password)))
  ([file filename]
   (load-data file filename "")))