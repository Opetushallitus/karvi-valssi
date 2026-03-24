(ns arvo.infra.kayttaja.middleware
  (:require
    [arvo.infra.kayttaja.vaihto :refer [with-kayttaja]]
    [arvo.auth.user-rights :as user-rights]
    [reitit.coercion.schema :as reitit-spec]
    [clojure.tools.logging :as log]))

(def unauthorized-virheilmoitus
   (str
      "ARVO-palautejärjestelmän käyttö edellyttää käyttöoikeuksia, jotka sinun käyttäjätunnukseltasi puuttuvat. "
      "Tarvittaessa ota yhteyttä oman organisaatiosi ARVO-koulutustoimijan pääkäyttäjään tai OKM:n ARVO-neuvontaan (arvo@csc.fi).\n\n"
      "Användningen av responssystemet ARVO förutsätter användarrättigheter. I din användarkod finns ej användarrättigheter. "
      "Kontakta vid behov huvudanvändaren för ARVO i din egen organisation eller UBS ARVO-rådgivning (arvo@csc.fi). "))

(defn wrap-kayttaja
  ([handler paasykielletty-virheilmoitus]
   (fn [request]
      ;; CAS-middleware lisää käyttäjätunnuksen :username-avaimen alle
     (let [uid (:username request)
           impersonoitu-oid (get-in request [:session :impersonoitu-oid])
           vaihdettu-organisaatio (get-in request [:session :vaihdettu-organisaatio])
           rooli (get-in request [:session :rooli])]
       (try
         (with-kayttaja uid {:kayttaja impersonoitu-oid :organisaatio vaihdettu-organisaatio} rooli
           (handler request))
         (catch IllegalStateException _
           {:headers {"Content-Type" "text/plain;charset=utf-8"}
            :status 403
            :body paasykielletty-virheilmoitus})))))
  ([handler]
   (wrap-kayttaja handler unauthorized-virheilmoitus)))

(defn- authorisoi [kayttooikeus handler & params]
  (let [[request] params
        [kayttooikeus konteksti-avain] (if (vector? kayttooikeus)
                                         kayttooikeus
                                         [kayttooikeus nil])
        parametrit (merge (:path-params request) (:body-params request))
        konteksti (when konteksti-avain
                    (-> (select-keys parametrit [konteksti-avain])
                        ; path parametrit näyttävät olevan vielä tässä vaiheessa stringejä
                        (update-vals #(Integer/parseInt (str %)))))]
;    Tähän ei pitäisi pystyä päätymään kunhan rajapinnan validointi ei ole ristiriidassa oikeustarkistusten kanssa
    (when (and konteksti-avain (not (konteksti-avain konteksti))
               (throw (ex-info "Pyynnöstä puuttuu pakollinen tieto" {:konteksti-avain konteksti-avain :konteksti konteksti}))))
    (if (user-rights/tarkista-kayttooikeus kayttooikeus konteksti)
      (apply handler params)
      (do
        (log/warn "Käyttöoikeudet eivät riitä. Toiminto estetty.")
        (throw (ex-info "Käyttöoikeudet eivät riitä." {:cause :kayttooikeudet}))))))

(def api-authorisointi-middleware
  "Ei mounttaa reittiin jossa :kayttooikeus tietoa ei ole annettu (palauttaa nil)"
  {:spec ::reitit-spec/kayttooikeus
   :compile (fn [{:keys [kayttooikeus]} opts]
              (when kayttooikeus
                (fn [handler]
                  (fn
                    ([request]
                     (authorisoi kayttooikeus handler request))
                    ([request respond raise]
                     (authorisoi kayttooikeus handler request respond raise))))))})
