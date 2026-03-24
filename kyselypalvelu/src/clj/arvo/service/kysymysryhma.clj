(ns arvo.service.kysymysryhma
    (:require [arvo.db.core :refer [*db*] :as db]
      [arvo.infra.kayttaja :refer [*kayttaja*]]
      [clojure.tools.logging :as log]
      [clojure.java.jdbc :as jdbc]))

(defn kysymysryhma-kayttoraja [kysymysryhmaid-list]
      (db/kayttoraja-ylitetty (merge {:koulutustoimija (:aktiivinen-koulutustoimija *kayttaja*)}
                                     (when-not (or (nil? kysymysryhmaid-list)
                                                   (empty? kysymysryhmaid-list))
                                               {:kysymysryhmaidt kysymysryhmaid-list}))))