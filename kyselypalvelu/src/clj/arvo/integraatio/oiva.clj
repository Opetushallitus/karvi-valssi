(ns arvo.integraatio.oiva
  (:require [clj-http.client :as http]
            [cheshire.core :as json]
            [clojure.walk :refer [keywordize-keys]]
            [arvo.config :refer [env]]))

(defn hae-koulutustoimijoiden-tutkinnot
  "Formaatti: [{
    jarjestajaYtunnus: \"0000000-0\",
    alkupvm: \"2021-01-01\",
    koulutukset: [
    \"111111\",
    \"222222\",
    ],
  }]"
  []
  (let [{url :url
         user :user
         password :password } (:oiva env)]
    (-> (http/get url
                  {:basic-auth [user password]})
        :body
        json/parse-string
        keywordize-keys)))
