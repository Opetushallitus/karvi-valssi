(ns arvo.util.excel
  (:require [dk.ative.docjure.spreadsheet :refer :all]
            [clojure.string :as s]
            [clojure.java.io :refer [output-stream]])
  (:import (java.io FileInputStream OutputStream File)
           (org.apache.poi.ss.usermodel WorkbookFactory)
           (org.apache.poi.poifs.filesystem POIFSFileSystem)
           (org.apache.poi.poifs.crypt EncryptionInfo EncryptionMode)
           (org.apache.poi.openxml4j.opc OPCPackage PackageAccess)))

(defn open-workbook-from-stream [^FileInputStream stream ^String password]
  (WorkbookFactory/create stream (str password)))

(defn get-encryptor [^POIFSFileSystem fs ^String password]
  (let [encryptioninfo (EncryptionInfo. EncryptionMode/agile)
        encryptor (.getEncryptor encryptioninfo)]
    (do
      (.confirmPassword encryptor password)
      encryptor)))

(defn encrypt-workbook [^String filename ^String password]
  (let [fs (POIFSFileSystem.)
        enc (get-encryptor fs password)
        opc (OPCPackage/open (File. filename) PackageAccess/READ_WRITE)
        os (.getDataStream enc fs)
        _ (do
            (.save opc os)
            (.close opc))]
    (with-open [fos (output-stream filename)]
      (.writeFilesystem fs fos))))

(defn open-workbook [filename password]
  (with-open [stream (FileInputStream. filename)]
    (open-workbook-from-stream stream password)))

(defn load-sheet [file password]
  (->> (open-workbook file password)
       (select-sheet (fn [x] true))))

(defn int-to-column [val]
  (let [quot (quot val 26)
        char (char (+ 65 (mod val 26)))]
    (str (when (< 0 quot) (int-to-column (dec quot))) char)))

(def column-seq (map (comp keyword int-to-column) (range)))

(def format-key
  (comp
    keyword
    #(s/replace % #"ä|ö|å" {"ä" "a"
                            "ö" "o"
                            "å" "a"})
    #(s/replace % "-" "")
    #(s/replace % "-_" "-")
    #(s/replace % " " "_")
    #(s/replace % #"\n" "_")
    #(.toLowerCase %)
    str))

(defn load-excel [file password]
  (let [sheet (load-sheet file password)
        title-row (first (row-seq sheet))
        keys (map format-key (iterator-seq (.iterator title-row)))
        columns (zipmap column-seq keys)
        rows (select-columns columns sheet)
        empty-row (zipmap keys (repeat nil))]
    (rest (map #(merge empty-row %) rows))))

(defn get-row [keys data]
  (map data keys))

;TODO: Support per-column styles
(defn set-cell-styles [workbook]
  (let [text-style (create-cell-style! workbook {:data-format "@"})
        sheet (select-sheet (fn [_] true) workbook)
        rows (row-seq sheet)]
    (doseq [cell (cell-seq rows)]
      (set-cell-style! cell text-style))))

(defn generate-workbook [headers data data-keys workbook-name]
  (let [rows (map #(get-row data-keys %) data)
        wb (create-workbook workbook-name
             (concat headers rows))
        _ (do (set-cell-styles wb))]
    wb))

(defn generate-excel
  ([headers data data-keys workbook-name]
   (let [wb (generate-workbook headers data data-keys workbook-name)]
     (with-open [bos (java.io.ByteArrayOutputStream.)]
       (do (save-workbook! bos wb)
           (.toByteArray bos)))))
  ([data data-keys workbook-name]
   (generate-excel [(map name data-keys)] data data-keys workbook-name)))

(defn save-excel
  ([data data-keys filename workbook-name password]
   (let [wb (generate-excel data data-keys workbook-name)
         out-file (str filename".xlsx")]
    (save-workbook! out-file wb)
    (when password
      (encrypt-workbook out-file password))
    out-file))
  ([data data-keys filename]
   (save-excel data data-keys filename "Tiedot" nil)))