(ns arvo.util
  (:require [arvo.config :refer [env]]
            [ring.util.http-response :as response]
            [ring.util.http-status :as status]))

(defn in? [coll elem]
  (boolean (some #(= elem %) coll)))

(defn parse-int [number-string]
  (try (Integer/parseInt number-string)
    (catch Exception e nil)))

(defn format-url [base params]
  (str base "?"(->> params
                    (map #(str (name (first %))"=" (second %)))
                    (interpose "&")
                    (apply str))))

(defn service-path [asetukset]
  (let [base-path (get-in asetukset [:server :base-path])]
    (str base-path "/")))

(defn json-string-response
  "Kun käännöstä ei tehdä automaattisesti"
  [response-fn body]
  (-> (str "\"" body "\"") response-fn (response/content-type "application/json; charset=utf-8")))

(defn api-response
  ([body]
    (response/ok body))
  ([response-fn body]
   (response-fn body)))

(defn paginated-response [data key page-length api-url params]
  (let [next-id (when (= page-length (count data)) (-> data last key))
        query-params (into {} (filter second params))
        next-url (format-url (str (-> env :server :base-url) api-url) (merge query-params {:since next-id}))]
    (if (some? data)
      (api-response {:data data
                     :pagination {:next_url (if next-id next-url nil)}})
      {:status status/not-found})))

(defn add-index [key coll]
  (map #(assoc %1 key %2) coll (range)))

(defn on-validation-error [message]
  (let [body {:status status/bad-request
              :detail message}]
    (-> (response/bad-request body))))

(defn update-selected-vals [map vals f]
  (reduce #(update-in % [%2] f) map vals))

(defmacro when-let*
  [bindings & body]
  `(let ~bindings
     (if (and ~@(take-nth 2 bindings))
       (do ~@body))))

(defn falsy? [val]
  (if val false true))
