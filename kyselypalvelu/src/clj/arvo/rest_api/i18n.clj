(ns arvo.rest-api.i18n
  (:import (java.util Locale
                      ResourceBundle
                      ResourceBundle$Control))
  (:require
    [schema.core :as schema]
    [clojure.tools.logging :as log]
    [ring.util.http-response :as response]
    [oph.common.util.http-util :refer [response-or-404]]
    [oph.common.util.util :refer [pisteavaimet->puu]]))

(def Kieli (schema/enum "fi" "sv" "en"))

(defn hae-tekstit [kieli]
  (ResourceBundle/clearCache)
  (let [bundle (ResourceBundle/getBundle "i18n/tekstit" (Locale. kieli) (ResourceBundle$Control/getNoFallbackControl ResourceBundle$Control/FORMAT_PROPERTIES))]
   (->> (for [key (.keySet bundle)]
           [(keyword key) (.getString bundle key)])
         (into {})
         pisteavaimet->puu)))

(defn reitit []
  ["/:kieli"
   {:get {:parameters {:path {:kieli Kieli}}
          :kayttooikeus :katselu
          :handler (fn [req]
                     (response/ok (hae-tekstit (get-in req [:path-params :kieli]))))}}])
