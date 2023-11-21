(ns arvo.rest_api.js-log
  (:require
    [schema.core :as s]
    [oph.rest_api.js-log :as js-log]))

(defn reitit []
  ["/virhe"
   {:post {:kayttooikeus :katselu
           :parameters {:body {:virheenUrl s/Str
                               :userAgent s/Str
                               :virheviesti s/Str
                               :stackTrace s/Any
                               :cause s/Str}}
           :handler (fn [{{:keys [body]} :parameters}]
                      (let [{:keys [virheenUrl userAgent virheviesti stackTrace cause]} body]
                        (js-log/logita virheenUrl userAgent virheviesti stackTrace cause)))}}])
