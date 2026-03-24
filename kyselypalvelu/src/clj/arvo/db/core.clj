(ns arvo.db.core
    (:require [hugsql.core :as hugsql]
      [mount.core :as mount]
      [conman.core :as conman]
      [arvo.config :refer [env]]
      [clojure.java.io :as io]
      [clojure.tools.logging :as log]
      [next.jdbc.result-set :as rs]
      [next.jdbc.prepare :as prepare]
      [jsonista.core :as json]
      ;    java-time automatic conversions
      next.jdbc.date-time)
    (:import (org.postgresql.jdbc PgArray)
      (org.postgresql.util PGobject)
      (java.sql Timestamp Date PreparedStatement)
      (clojure.lang IPersistentVector IPersistentMap)))

(defn pool-spec []
      (let [db-conf (:db env)]
           {:jdbc-url (str "jdbc:postgresql://" (:host db-conf)
                           "/"(:name db-conf)"?user="(:user db-conf)"&password=" (:password db-conf))}))

(mount/defstate ^:dynamic *db*
                :start (conman/connect! (pool-spec))
                :stop (conman/disconnect! *db*))

(def query-resources
  (do
    (map #(str "sql/" %) (.list (io/file "resources/sql")))))

(defmacro bind-connection
          "a version of bind-connection that loads all sql resources"
          [conn]
          (log/info "Loaded sql resources:" query-resources)
          `(conman/bind-connection ~conn ~@query-resources))

(bind-connection *db*)

;; SQL-kyselyiden logitus

(def log-sql true)

(defn log-sqlvec [sqlvec]
      (log/info (->> sqlvec
                     (clojure.string/join " ; "))))

(defn log-command-fn [this db sqlvec options]
      (when (-> env :db :log-sql) (log-sqlvec sqlvec))
      (condp contains? (:command options)
             #{:!} (hugsql.adapter/execute this db sqlvec options)
             #{:? :<!} (hugsql.adapter/query this db sqlvec options)))

(defmethod hugsql.core/hugsql-command-fn :! [sym] `log-command-fn)
(defmethod hugsql.core/hugsql-command-fn :<! [sym] `log-command-fn)
(defmethod hugsql.core/hugsql-command-fn :? [sym] `log-command-fn)

;; :decode-key-fn here specifies that JSON-keys will become keywords:
(def mapper (json/object-mapper {:decode-key-fn keyword}))
(def ->json json/write-value-as-string)
(def <-json #(json/read-value % mapper))

(defn ->pgobject
      "Transforms Clojure data to a PGobject that contains the data as
      JSON. PGObject type defaults to `jsonb` but can be changed via
      metadata key `:pgtype`"
      [x]
      (let [pgtype (or (:pgtype (meta x)) "jsonb")]
           (doto (PGobject.)
                 (.setType pgtype)
                 (.setValue (->json x)))))

(defn <-pgobject
      "Transform PGobject containing `json` or `jsonb` value to Clojure
      data."
      [^org.postgresql.util.PGobject v]
      (let [type  (.getType v)
            value (.getValue v)]
           (if (#{"jsonb" "json"} type)
             (when value
                   (with-meta (<-json value) {:pgtype type}))
             value)))

;; if a SQL parameter is a Clojure hash map or vector, it'll be transformed
;; to a PGobject for JSON/JSONB:
(extend-protocol prepare/SettableParameter
                 clojure.lang.IPersistentMap
                 (set-parameter [m ^PreparedStatement s i]
                                (.setObject s i (->pgobject m)))

                 clojure.lang.IPersistentVector
                 (set-parameter [v ^PreparedStatement s i]
                                (let [conn      (.getConnection s)
                                      meta      (.getParameterMetaData s)
                                      type-name (.getParameterTypeName meta i)]
                                     (if-let [elem-type (when (= (first type-name) \_)
                                                              (apply str (rest type-name)))]
                                             (.setObject s i (.createArrayOf conn elem-type (to-array v)))
                                             (.setObject i s v)))))

(extend-protocol rs/ReadableColumn
                 PgArray
                 (read-column-by-label [v _ _] (vec (.getArray v)))
                 (read-column-by-index [v _ _] (vec (.getArray v)))

                 ;; if a row contains a PGobject then we'll convert them to Clojure data
                 ;; while reading (if column is either "json" or "jsonb" type):
                 PGobject
                 (read-column-by-label [^org.postgresql.util.PGobject v _]
                                       (<-pgobject v))
                 (read-column-by-index [^org.postgresql.util.PGobject v _2 _3]
                                       (<-pgobject v))

                 ; conman/hugsql hides typehints we could provide so we get java.sql.Timestamp and java.sql.Date
                 ; which jdbc 4.2 returns as default for backward compatibility so we need to do this mapping ourselves.
                 java.sql.Date
                 (read-column-by-label [^java.sql.Date v _]     (.toLocalDate v))
                 (read-column-by-index [^java.sql.Date v _2 _3] (.toLocalDate v))
                 java.sql.Timestamp
                 (read-column-by-label [^java.sql.Timestamp v _]     (.toInstant v))
                 (read-column-by-index [^java.sql.Timestamp v _2 _3] (.toInstant v)))
