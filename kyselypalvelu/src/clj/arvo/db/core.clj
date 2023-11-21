(ns arvo.db.core
  (:require [hugsql.core :as hugsql]
            [mount.core :as mount]
            [conman.core :as conman]
            [arvo.config :refer [env]]
            [clojure.java.jdbc :as jdbc]
            [cheshire.core :refer [parse-string generate-string]]
            [clojure.java.io :as io]
            [clojure.tools.logging :as log])
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

(def query-resources
  (do
    (map #(str "sql/" %) (.list (io/file "resources/sql")))))

;a version of bind-connection that loads all sql resources
(defmacro bind-connection [conn]
  (let [filenames query-resources
        _ (log/info "Loaded sql resources:" filenames)
        options?  (map? (first filenames))
        options   (if options? (first filenames) {})
        filenames (if options? (rest filenames) filenames)]
    `(let [{snips# :snips fns# :fns :as queries#} (conman.core/load-queries '~filenames ~options)]
       (doseq [[id# {fn# :fn {doc# :doc} :meta}] snips#]
         (intern *ns* (with-meta (symbol (name id#)) {:doc doc#}) fn#))
       (doseq [[id# {fn# :fn {doc# :doc} :meta}] fns#]
         (intern *ns* (with-meta (symbol (name id#)) {:doc doc#})
                 (fn
                   ([] (fn# ~conn {}))
                   ([params#] (fn# ~conn params#))
                   ([conn# params#] (fn# conn# params#))
                   ([conn# params# opts# & command-opts#]
                    (apply fn# conn# params# opts# command-opts#)))))
       queries#)))


(bind-connection *db*)

; clojure jdbc wrapper doesnt pass class to ResultSet.getObject so we get default java.sql.Timestamp and java.sql.Date
; which jdbc 4.2 returns as default for backward compatibility so we need to do this mapping ourselves.
(extend-protocol jdbc/IResultSetReadColumn
  java.sql.Timestamp
  (result-set-read-column [v _ _]
                          (.toInstant v))

  java.sql.Date
  (result-set-read-column [v _ _]
                          (.toLocalDate v))

  PgArray
  (result-set-read-column [v _ _] (vec (.getArray v)))

  PGobject
  (result-set-read-column [pgobj _metadata _index]
    (let [type (.getType pgobj)
          value (.getValue pgobj)]
      (case type
        "json" (parse-string value true)
        "jsonb" (parse-string value true)
        "citext" (str value)
        value))))

(extend-type clojure.lang.IPersistentVector
  jdbc/ISQLParameter
  (set-parameter [v ^java.sql.PreparedStatement stmt ^long idx]
    (let [conn (.getConnection stmt)
          meta (.getParameterMetaData stmt)
          type-name (.getParameterTypeName meta idx)]
      (if-let [elem-type (when (= (first type-name) \_) (apply str (rest type-name)))]
        (.setObject stmt idx (.createArrayOf conn elem-type (to-array v)))
        (.setObject stmt idx v)))))

(defn to-pg-json [value]
  (doto (PGobject.)
    (.setType "jsonb")
    (.setValue (generate-string value))))

(extend-protocol jdbc/ISQLValue
  java.time.Instant
  (sql-value [value] (Timestamp/from value))
  java.time.LocalDate
  (sql-value [value] (Date/valueOf value))
  IPersistentMap
  (sql-value [value] (to-pg-json value))
  IPersistentVector
  (sql-value [value] (to-pg-json value)))
