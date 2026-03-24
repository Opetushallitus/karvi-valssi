(ns arvo.translations
  (:require [shadow.resource :as rc]
            [clojure.edn :as edn]))

(def translations {:fi (edn/read-string (rc/inline "i18n/fi.edn"))
                   :sv (edn/read-string (rc/inline "i18n/sv.edn"))
                   :en (edn/read-string (rc/inline "i18n/en.edn"))})

(defn- insert-replacement-values [text & replacements]
  (if (nil? (first replacements))
    text
    (recur (clojure.string/replace-first text #"\{\}" (first replacements)) (rest replacements))))

(defn translate [path & [replacements]]
  (let [translation (get-in translations path)]
    (or (apply insert-replacement-values translation replacements)
        (last path))))

(defn translate-field [obj key lang]
  (let [translated (str (get obj (keyword (str (name key) "_" (name lang)))))]
    (if (not-empty translated)
      translated
      (when (not= :fi lang)
        (translate-field obj key :fi)))))
