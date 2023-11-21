(ns oph.common.util.cas
  (:require [clj-http.client :as http]
            [again.core :as again]
            [clojure.tools.logging :as log]
            [arvo.config :refer [env]]
            [oph.common.util.util :refer [oletus-header]]))

(def kirjautumistila
  (atom {:cs (clj-http.cookies/cookie-store)
         :tgt nil}))

(defn ^:private hae-ticket-granting-url [url user password unsafe-https]
  (let [{:keys [status headers cookies]} (http/post (str url "/v1/tickets")
                                            (oletus-header {:form-params {:username user
                                                                          :password password}
                                                            :cookie-store (:cs @kirjautumistila)
                                                            :insecure? unsafe-https}))]
    (if (= status 201)
      (headers "location")
      (throw (RuntimeException. "CAS-kirjautuminen epäonnistui")))))

(defn ^:private hae-service-ticket [url palvelu-url unsafe-https]
  (let [{:keys [status body]} (http/post url
                                         (oletus-header {:form-params {:service palvelu-url}
                                                         :cookie-store (:cs @kirjautumistila)
                                                         :insecure? unsafe-https}))]
    (if (= status 200)
      body
      (throw (RuntimeException. "Service ticketin pyytäminen CASilta epäonnistui")))))

(defn uusi-service-ticket [palvelu-url unsafe-https prequel-url status]
  (try
    (let [service-ticket (hae-service-ticket (:tgt @kirjautumistila) (str palvelu-url "/j_spring_cas_security_check") unsafe-https)]
      ; Tyhjennä keksit (sessio keksi saattaa olla rikki) ja hae uusi ST
      (when (not= status 302)
        (do (log/info "Tyhjennetään yhteiset keksit vastauksen statuksella" status)
          (swap! kirjautumistila assoc :cs (clj-http.cookies/cookie-store))))
      ; Lämmittelypyyntö. Ilman tätä muut kuin get-pyynnöt epäonnistuvat (ohjaa kirjautumissivulle)
      (http/get prequel-url (oletus-header {:query-params {"ticket" service-ticket} :cookie-store (:cs @kirjautumistila)})))
    (catch Exception e (str "Ei pystytty hakemaan ST" (.getMessage e)))))

(defmulti tiketit-uusiva-kirjautuminen ::again/status)
(defmethod tiketit-uusiva-kirjautuminen :retry [state]
  (log/info (format "Uudelleenyritys#%s palveluun %s koska %s"
                    (::again/attempts state)
                    (-> state ::again/user-context deref :palvelu)
                    (:cause (Throwable->map (::again/exception state)))))
  (let [{cas-url :url
         unsafe-https :unsafe-https} (:cas-auth-server env)
        {palvelu-url :url
         user :user
         password :password} (get env (-> state ::again/user-context deref :palvelu))
        prequel-url (format "%s/cas/prequel" palvelu-url)
        yritetty-uudestaan? (< 1 (::again/attempts state))
        status (:status (:data (Throwable->map (::again/exception state))))
        _ (when (or (not (:tgt @kirjautumistila)) yritetty-uudestaan?)
            (do
              (log/info "Uusitaan TGT")
              (swap! kirjautumistila assoc :tgt (hae-ticket-granting-url cas-url user password unsafe-https))))]
       (uusi-service-ticket palvelu-url unsafe-https prequel-url status)))
(defmethod tiketit-uusiva-kirjautuminen :success [state])
(defmethod tiketit-uusiva-kirjautuminen :failure [state]
  (log/error "Pyyntö epäonnistui tikettien uusimisesta huolimatta" state))

(defn request-with-cas-auth [palvelu options]
  (log/info "Pyyntö palveluun" palvelu "asetuksilla" options)
  (let [{cas-enabled :enabled} (:cas-auth-server env)]
    (if cas-enabled
      (again/with-retries
       {::again/callback     tiketit-uusiva-kirjautuminen
        ::again/strategy     [100 100]
        ::again/user-context (atom {:palvelu palvelu})}
        ; 302 halutaan tulkita tässä virheeksi (ohjaus kirjautumissivulle). 2xx ja 4xx hyväksytään.
       (http/request (oletus-header (assoc options :cookie-store (:cs @kirjautumistila) :redirect-strategy :none :unexceptional-status #(or (<= 200 % 299) (<= 400 % 499))))))
      (http/request (oletus-header options)))))

(defn get-with-cas-auth
  ([palvelu url]
   (get-with-cas-auth palvelu url {}))
  ([palvelu url options]
   (request-with-cas-auth palvelu (merge options {:method :get
                                                  :url url}))))

(defn post-with-cas-auth
  ([palvelu url]
   (post-with-cas-auth palvelu url {}))
  ([palvelu url options]
   (request-with-cas-auth palvelu (merge options {:method :post
                                                  :url url}))))

(defn cas-login-url []
  (let [cas-config (:cas-auth-server env)
        {:keys [override-login-enabled override-login-url url]} cas-config]
    (if override-login-enabled
      override-login-url
      url)))
