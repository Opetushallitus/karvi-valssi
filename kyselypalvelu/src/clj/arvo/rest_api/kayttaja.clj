(ns arvo.rest-api.kayttaja
  (:require
    [schema.core :as s]
    [arvo.arkisto.kayttaja :as arkisto]
    [arvo.arkisto.kayttajaoikeus :as kayttajaoikeus-arkisto]
    [arvo.infra.kayttaja :refer [*kayttaja*]]
    [oph.common.util.http-util :refer [response-or-404]]
    [clojure.tools.logging :as log]
    [oph.common.util.cas :as cas]))

(defn reitit []
  [[""
    {:get {:kayttooikeus :katselu
           :handler (fn [req]
                      (let [oikeudet (kayttajaoikeus-arkisto/hae-oikeudet (:aktiivinen-oid *kayttaja*))
                            logout-url (str (cas/cas-login-url) "/logout")]
                        (response-or-404 (assoc oikeudet
                                                :impersonoitu_kayttaja (:impersonoidun-kayttajan-nimi *kayttaja*)
                                                :vaihdettu_organisaatio (:vaihdettu-organisaatio *kayttaja*)
                                                :aktiivinen_rooli (:aktiivinen-rooli *kayttaja*)
                                                :logout-url logout-url))))}}]
   ["/impersonoitava"
    {:get {:kayttooikeus :yllapitaja
           :parameters {:query {:termi s/Str}}
           :handler (fn [{{:keys [query]} :parameters}]
                      (response-or-404 (arkisto/hae-impersonoitava-termilla (:termi query))))}}]
   ["/impersonoi"
    {:post {:kayttooikeus :yllapitaja
            :parameters {:body {:oid s/Str}}
            :handler (fn [{:keys [session parameters] :as req}]
                       {:status 200
                        :body {:oid (-> parameters :body :oid)}
                        :session (assoc session :impersonoitu-oid (-> parameters :body :oid))})}}]
   ["/vaihda-organisaatio"
    {:post {:kayttooikeus :yllapitaja
            :parameters {:body {:oid s/Str}}
            :handler (fn [{:keys [session parameters] :as req}]
                       (log/info "Session:" session)
                       {:status 200
                        :body {:oid  (-> parameters :body :oid)}
                        :session (assoc session :vaihdettu-organisaatio  (-> parameters :body :oid))})}}]
   ["/lopeta-impersonointi"
    {:post {:kayttooikeus :katselu
            :handler (fn [{:keys [session] :as req}]
                       {:status 200
                        :body {:oid nil}
                        :session (apply dissoc session [:impersonoitu-oid :vaihdettu-organisaatio])})}}]
   ["/rooli"
    {:post {:kayttooikeus :katselu
            :parameters {:body {:rooli_organisaatio_id s/Int}}
            :handler (fn [{:keys [session parameters] :as req}]
                       {:status 200
                        :session (assoc session :rooli (-> parameters :body :rooli_organisaatio_id))
                        :body {:rooli_organisaatio_id (-> parameters :body :rooli_organisaatio_id)}})}}]])
