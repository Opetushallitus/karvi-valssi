(ns oph.common.util.http-util
  (:require
    [java-time.api :as jt]
    [arvo.util :as arvo-util]
    [ring.util.http-response :as response]
    [clojure.tools.logging :as log]
    [schema.core :as s])
  (:import java.io.ByteArrayInputStream))

(defn try-parse-local-date
  [f d]
  (try
    (jt/local-date f d)
    (catch clojure.lang.ExceptionInfo e
      nil)))

(defn try-parse-local-date-with-tz
  "Use Helsinki time zone to adjust time zone, not system default."
  [d]
  (try
;    Käyttöliittymä antaa ajan UTC-ajassa joka jää päiviksi käännettäessä edellisen päivän puolelle esim. "2023-02-28T22:00:00Z"
;    Koska aikavyöhykse ei mene kantaan pitää tämä huomioida local-date käännöksessä
    (jt/local-date (jt/instant d) "Europe/Helsinki")
    (catch clojure.lang.ExceptionInfo e
      nil)))

(defn parse-iso-date
  "Does not support all valid ISO date format presentations: https://en.wikipedia.org/wiki/ISO_8601#Dates"
  [d]
  (when d
    (or
     (try-parse-local-date "yyyy-MM-dd" d)
     (try-parse-local-date "dd.MM.yyyy" d)
      (try-parse-local-date-with-tz d)
      (throw (IllegalArgumentException. (str "Virheellinen pvm formaatti: " d))))))

(defn response-or-404 [data]
   (cond
     (nil? data) (response/not-found)
     :else (response/ok data)))

(defn file-download-response
  ([data filename content-type]
   (file-download-response data filename content-type {}))
  ([data filename content-type options]
   {:status 200
    :body (if-let [charset (:charset options)]
            (ByteArrayInputStream. (.getBytes (str \ufeff data) charset))
            (ByteArrayInputStream. data))
    :headers {"Content-type" content-type
              "Content-Disposition" (str "attachment; filename=\"" filename "\"")}}))

(defn csv-download-response
  [data filename]
  (file-download-response data filename "text/csv" {:charset "UTF-8"}))

(defn file-upload-response
  [data]
  (-> (response-or-404 data)
    (assoc :headers {"Content-Type" "text/html"})))

(defn response-nocache
  [data]
  (-> (response-or-404 data)
    (assoc-in [:headers "Cache-control"] "max-age=0")))

;; https://stackoverflow.com/questions/49547/how-to-control-web-page-caching-across-all-browsers
(defn response-nocache-strict
  [data]
  (-> (response-nocache data)
    (update-in [:headers "Cache-control"] str ", private, no-cache, no-store, must-revalidate")
    (assoc-in [:headers "Pragma"] "no-cache")))

(defn validate-response
  "Ajaa validoinnit ja pitää niitä validointeja epäonnistuneena jotka eivät palauta nil. Olettaa body-fn ja validointi-fn
  saman signaturen. Palauttaa 400 validoinnin epäonnistuessa ja 404 jos body-fn palauttaa nil. Muuten 200."
  [body-fn validation-fns & args]
  (let [validation-results (-> juxt
                               (apply validation-fns)
                               (apply args)
                               flatten)
;        nil pidetään validoinnin onnistumisena
        errors (remove nil? validation-results)]
    (if (empty? errors)
      (response-or-404 (apply body-fn args))
      (response/bad-request errors))))

(defmacro sallittu-jos [ehto & body]
  ;; 403 olisi kuvaavampi koodi, mutta sillä ilmoitetaan myös CAS-istunnon
  ;; puuttumisesta, ja käyttöliittymä lataa sivun uudelleen 403:n saatuaan.
  ;; Speksi sanoo 403:sta "If the server does not wish to make this information
  ;; available to the client, the status code 404 (Not Found) can be used
  ;; instead.", joten käytetään 404:ää.
  `(if ~ehto (do ~@body) {:status 404}))
