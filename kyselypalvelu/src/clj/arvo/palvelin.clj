(ns arvo.palvelin
  (:gen-class)
  (:require [cheshire.generate :as json-gen]
            [clojure.pprint :refer [pprint]]
            [clojure.tools.logging :as log]
            [clojure.java.io :as io]
            [arvo.util :as arvo-util]
            [ring.util.http-response :as response]
            [clojure.string :as str]
            [org.httpkit.server :as hs]
            [reitit.ring :as ring]
            [reitit.ring.coercion :as rrc]
            [reitit.ring.middleware.exception :as exception]
            [reitit.coercion.schema :as reitit-spec]
            [muuntaja.core :as muuntaja]
            [reitit.ring.middleware.muuntaja :as muuntaja-middleware]
            [reitit.ring.middleware.parameters :refer [parameters-middleware]]
            [ring.util.request :refer [path-info]]
            [ring.middleware.json :refer [wrap-json-params]]
            [ring.middleware.keyword-params :refer [wrap-keyword-params]]
            [ring.middleware.params :refer [wrap-params]]
            [ring.middleware.resource :refer [wrap-resource]]
            [ring.middleware.not-modified :refer [wrap-not-modified]]
            [ring.middleware.session :refer [wrap-session]]
            [reitit.ring.middleware.multipart :as multipart]
            ring.middleware.cors
            [ring.middleware.session.memory :refer [memory-store]]
            [ring.util.request :refer [path-info request-url]]
            [ring.middleware.content-type :refer [wrap-content-type]]
            [ring.middleware.x-headers :refer [wrap-frame-options]]
            [ring.util.response :as resp]
            schema.core

            [arvo.auth.cas-auth-middleware :refer [cas]]
            [arvo.auth.cas-middleware :refer [wrap-cas-single-sign-out]]
            [oph.common.util.cas :refer [cas-login-url]]
            [oph.common.infra.asetukset :refer [konfiguroi-lokitus]]
            [oph.common.infra.anon-auth :as anon-auth]
            [oph.common.infra.print-wrapper :refer [log-request-wrapper]]
            arvo.reitit
            [arvo.infra.kayttaja.middleware :as arvo-middleware]
            [arvo.integraatio.kayttooikeuspalvelu :as kop]
            [arvo.infra.eraajo :as eraajo]
            [arvo.infra.kayttaja.vakiot :refer [default-test-user-uid]]
            [mount.core :as mount]
            [arvo.db.migrations :as migrations]
            [arvo.config :refer [env]]
            [arvo.util :refer [service-path]]))

(schema.core/set-fn-validation! true)

(defn add-dash-suffix [string]
  (cond
    (empty? string) "/"
    (.endsWith string "/") string
    :else (str string "/")))

(defn service-url [env]
  (let [{:keys [base-url port base-path]} (:server env)
        base-url (cond-> base-url
                   (empty? base-url) (str "http://localhost:" port)
                   true add-dash-suffix)
        base-path (cond-> base-path
                    (.startsWith base-path "/") (subs 1))
        url (str base-url base-path)]
    (add-dash-suffix url)))

(defn ajax-request? [request]
  (get-in request [:headers "angular-ajax-request"]))

(defn auth-removeticket
  "Poistaa CAS:n antaman ticket-queryparametrin. Pitää olla auth-middlewaren jälkeen tai aiheuttaa loputtoman loopin."
  [handler asetukset]
  (fn [request]
    (if (get-in request [:query-params "ticket"])
      (resp/redirect (service-url asetukset))
      (handler request))))

(def swagger-resources
  "Swagger API resources, not authenticated using CAS"
  #{"/api-docs" "/swagger.json" "/fi/swagger.json"})

(def external-service-api
  #{"/api/vipunen" "/api/export" "/api/vastauslinkki" "/api/admin" "/api/tyoelamapalaute" "/api/yleinen"})

(def public-api
  "Public API methods, not authenticated using CAS"
  #{"/api/public" "/api/healthcheck"})

(defn- full-path [resurssi]
  (map #(str (get-in env [:server :base-path]) %) resurssi))

(defn auth-middleware [handler asetukset]
  (fn [request]
    (let [cas-handler (arvo-middleware/wrap-kayttaja handler)
          auth-handler (cas cas-handler cas-login-url #(service-url asetukset) :no-redirect? ajax-request?)]
      (cond
        (some #(.startsWith (path-info request) %) (full-path external-service-api))
        (do
          (log/info "Vipunen or Export API, only Basic Auth")
          (handler request))

        (some #(.startsWith (path-info request) %) (full-path swagger-resources))
        (do
          (log/info "swagger API docs are public, no auth")
          (handler request))

        (some #(.startsWith (path-info request) %) (full-path public-api))
        (do
          (log/info "public API method, no CAS auth")
          (handler request))

        (and (:development-mode asetukset) (not (:enabled (:cas-auth-server asetukset))))
        (do
          (log/info "development, no CAS")
          (let [anon-auth-handler (anon-auth/auth-cas-user cas-handler default-test-user-uid)]
            (anon-auth-handler request)))

        :else (auth-handler request)))))

(defn sammuta [palvelin]
  ((:sammuta palvelin)))

(defn wrap-expires [handler]
  (fn [request]
    (assoc-in (handler request) [:headers "Expires"] "-1")))

(defn wrap-cors [handler asetukset]
  (if (get-in asetukset [:ominaisuus :allow-cors-requests])
    (ring.middleware.cors/wrap-cors handler
                                    :access-control-allow-origin [#"(http://localhost:3000|https://localhost:3000)"]
                                    :access-control-allow-methods [:get :put :post :delete :patch]
                                    :access-control-allow-credentials true)
    #(handler %)))

(defn wrap-kayttooikeudet-forbidden [handler]
  (fn [request]
    (try
      (handler request)
      (catch clojure.lang.ExceptionInfo e
        (if (= :kayttooikeudet (-> e ex-data :cause))
          {:status 403
           :headers {"Content-Type" "text/plain; charset=utf-8"
                     "X-Kayttooikeudet-Forbidden" "true"}
           :body "yleiset.virhe_kayttoikeudet_eivat_riita"}
          (throw e))))))

(defn wrap-internal-forbidden [handler]
  (fn [request]
    (let [response (handler request)]
      (if (= (:status response) 403)
        (assoc response :headers {"X-Aipal-Error" "true"})
        response))))

(def default-handler (ring/create-default-handler
                      {
                        :not-found (constantly (arvo-util/json-string-response response/not-found "404 - Page not found"))
                        :method-not-allowed (constantly (arvo-util/json-string-response response/method-not-allowed "405 - Not allowed"))
                        :not-acceptable (constantly (arvo-util/json-string-response response/not-acceptable "406 - Not acceptable"))}))

(def resource-handler (ring/create-resource-handler
                       {:path "/resources"}))

(defn wrap-arvo-session [session-store asetukset]
  [wrap-session {:store session-store
                 :cookie-attrs {:http-only true
                                :same-site (if (get-in asetukset [:ominaisuus :allow-cors-requests]) :none :lax)
                                :path (service-path asetukset)
                                :secure true}}])

(def exception-middleware
  (exception/create-exception-middleware
   (merge
    exception/default-handlers
    {;; print stack-traces for all exceptions
      ::exception/wrap (fn [handler e request]
                         (log/error (pr-str (:uri request)) e)
                         (handler e request))})))

(def arvo-muuntaja (muuntaja/create
                    (assoc-in
                     muuntaja/default-options
                     [:http :encode-response-body?]
                     (fn [request {:keys [body] :as response}]
                       (or (coll? body)
;                           Hyväksy json-string body
                           (and
                            (or
                             (some-> (get-in request [:headers "accept"]) (clojure.string/includes? "application/json"))
                             (some-> (get-in request [:headers "accept"]) (clojure.string/includes? "*/*")))
                            (not (get-in response [:headers "Content-type"]))
                            (string? body)))))))

(defn app
  "Ring-wrapperit ja metosin reitit-reitit ilman HTTP-palvelinta"
  [asetukset]

  ;  Ei käytetä normaalisti rajapinnoissa mutta kutsutaan suoraan jossain koodissa
  (json-gen/add-encoder java.time.LocalDateTime
                        (fn [c json-generator]
                          (.writeString json-generator (.toString c))))
  (json-gen/add-encoder java.time.Instant
                        (fn [c json-generator]
                          (.writeString json-generator (.toString c))))
  (json-gen/add-encoder java.time.LocalDate
                        (fn [c json-generator]
                          (.writeString json-generator (.toString c))))

  (let [session-map (atom {})
        session-store (memory-store session-map)]
    (ring/ring-handler
     (ring/router
      (arvo.reitit/reitit asetukset)
      {:data {:coercion reitit-spec/coercion
              :muuntaja arvo-muuntaja
              ;              reitteihin osuvien pyyntöjen middlewaret
              :middleware [muuntaja-middleware/format-middleware  ; content-negotiation/coerce, ei toimi automaattisesti jos content-type asetettu käsin!
                           exception-middleware  ; laajempi kuin rrc/coerce-exceptions-middleware
                           wrap-not-modified
                           wrap-expires
                           wrap-kayttooikeudet-forbidden ;pitää olla ennen wrap-internal-forbidden
                           wrap-internal-forbidden
                           [wrap-cas-single-sign-out session-store session-map]
                           [auth-middleware asetukset]
                           [auth-removeticket asetukset]
                           arvo-middleware/api-authorisointi-middleware
                           rrc/coerce-request-middleware
                           rrc/coerce-response-middleware
                           multipart/multipart-middleware]}})
     (ring/routes (ring/redirect-trailing-slash-handler)
                  resource-handler  ; uuden käyttöliittymän resursseja
                  default-handler)
     ;     globaalit middlewaret
     {:middleware [
                    log-request-wrapper
                    parameters-middleware
                    wrap-content-type  ; pitää olla ennen wrap-resource niin kuvat tulevat oikein
                    [wrap-resource "public/app"]  ; vanha käyttöliittymä
                    [wrap-resource "public"]  ; käyttöliittymän resursseja
                    [wrap-cors asetukset]
                    [wrap-frame-options :deny]
                    (wrap-arvo-session session-store asetukset)]})))

(defn ^:integration-api kaynnista-eraajon-ajastimet! [asetukset]
  (eraajo/kaynnista-ajastimet! asetukset))

(defn ^:integration-api kaynnista! [args]
  (try
    (log/info "Käynnistetään ARVO")
    (let [_ (mount/start)
          _ (konfiguroi-lokitus env)
          sammuta (hs/run-server (app env)
                                 {:port (get-in env [:server :port])})]
      (cond
        (some #{"migrate" "rollback"} args)
        (do (migrations/migrate args) (System/exit 0))
        :else
        (migrations/migrate ["migrate"]))
      (when (or (not (:development-mode env))
                (:eraajo env))
        (kaynnista-eraajon-ajastimet! env))
      (log/info "Palvelin käynnistetty:" (service-url env))
      {:sammuta sammuta})
    (catch Throwable t
      (let [virheviesti "Palvelimen käynnistys epäonnistui"]
        (log/error t virheviesti)
        (binding [*out* *err*]
          (println virheviesti))
        (.printStackTrace t *err*)
        (System/exit 1)))))

(defn -main [& args]
  (kaynnista! args))
