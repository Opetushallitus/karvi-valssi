(ns oph.rest_api.js-log
  (:require
    [clojure.string :as str]
    [ring.util.http-response :as response]
    [clojure.tools.logging :as log]))

;   "max length of message strings from the client side"
(def
  maxlength 1000)

(defn sanitize
  "replaces linefeeds with blanks and limits the length"
  [s]
  {:pre [(clojure.core/string? s)]}
  (let [ln (min (.length s) maxlength)]
    (-> s
      (str/replace "\n" "!")
      (str/replace "\r" "!")
      (.substring 0 ln))))

(defn stacktrace->string [stacktrace]
  (if (sequential? stacktrace)
    (apply str (interpose ".." stacktrace))
    stacktrace))
      
(defn logita
  "Tarkoitus on wrapata tämä sopivaan reittiin"
   [virheenUrl userAgent virheviesti stackTrace cause]
  (let [rivinvaihto "\n"]
    (log/info (str rivinvaihto
                "--- Javascript virhe ---" rivinvaihto
                "Virheen url: " (sanitize virheenUrl) rivinvaihto
                "User agent string: " (sanitize userAgent) rivinvaihto
                "Virheviesti: " (sanitize virheviesti) rivinvaihto
                "Stacktrace: " (sanitize (stacktrace->string stackTrace)) rivinvaihto
                "Aiheuttaja: " (sanitize cause) rivinvaihto
                "------------------------")))
  (response/ok))
