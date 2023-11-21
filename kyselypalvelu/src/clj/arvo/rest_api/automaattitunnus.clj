(ns arvo.rest-api.automaattitunnus
  (:require
    [ring.util.http-status :as status]
    [ring.util.http-response :as response]
    [arvo.util :refer [on-validation-error api-response]]
    [arvo.schema.automaattitunnus :refer :all]
    [arvo.util :as arvo-util]
    [clojure.tools.logging :as log]
    [arvo.db.core :refer [*db*] :as db]
    [arvo.util.paivamaara-util :as pvm-util]
    [schema.core :as s]
    [arvo.config :refer [env]]
    [arvo.service.vastaajatunnus :as vt]
    [arvo.service.vastaajatunnus :as vastaajatunnus]))

(defn handle-error
  ([error request-id]
   (log/error "Virhe vastaajatunnuksen luonnissa: "
              (if request-id (str "request-id " request-id " - ") "")
              (:msg error))
   (response/not-found error))
  ([error]
   (handle-error error nil)))

(defn vastauslinkki-response [luotu-tunnus request-id]
  (if (:tunnus luotu-tunnus)
    (api-response {:kysely_linkki (str (:vastaus-base-url env)"/v/"(:tunnus luotu-tunnus))
                   :voimassa_loppupvm (pvm-util/local-date->instant (:voimassa_loppupvm luotu-tunnus))
                   :tunnus (:tunnus luotu-tunnus)})
    (handle-error (:error luotu-tunnus) request-id)))

(defn vastaajatunnus-response [luotu-tunnus request-id]
  (if (:tunnus luotu-tunnus)
    (do
      (log/info "Luotu vastaajatunnus: " (:tunnus luotu-tunnus))
      (api-response {:tunnus (:tunnus luotu-tunnus)
                     :voimassa_loppupvm (pvm-util/local-date->instant(:voimassa_loppupvm luotu-tunnus))}))
    (handle-error (:error luotu-tunnus) request-id)))

(defn nippulinkki-response [massatunnus]
  (api-response {:nippulinkki (str (:vastaus-base-url env)"/n/"(:tunniste massatunnus))
                 :voimassa_loppupvm (pvm-util/local-date->instant(:voimassa_loppupvm massatunnus))}))

(defn kyselyynohjaus-response [luotu-tunnus]
  (if (:tunnus luotu-tunnus)
    (api-response {:tunnus (:tunnus luotu-tunnus)})
    (handle-error {:error luotu-tunnus})))

(defn kyselyynohjaus-v1 []
  [[""
    {:post {:parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (try
                         (let [vastaajatunnus (vt/lisaa-kyselyynohjaus! body)]
                           (kyselyynohjaus-response vastaajatunnus))
                         (catch java.lang.AssertionError e1
                           (log/error e1 "Mandatory fields missing")
                           (on-validation-error (format "Mandatory fields are missing or not found")))
                         (catch Exception e2
                           (log/error e2 "Unexpected error")
                           (on-validation-error (format "Unexpected error: %s" (.getMessage e2))))))}}]
   ["/rekry"
    {:post {:parameters {:body s/Any}
            :handler (fn [{{:keys [body]} :parameters}]
                       (try
                         (let [vastaajatunnus (vt/lisaa-rekry-tunnus! body)]
                           (kyselyynohjaus-response vastaajatunnus))
                         (catch java.lang.AssertionError e1
                           (log/error e1 "Mandatory fields missing")
                           (on-validation-error (format "Mandatory fields are missing or not found")))
                         (catch Exception e2
                           (log/error e2 "Unexpected error")
                           (on-validation-error (format "Unexpected error: %s" (.getMessage e2))))))}}]])

(defonce sallitut-metatiedot [:tila])

(defn poista-vastaajatunnus [tunnus kyselytyyppi]
  (let [poistettuja (vastaajatunnus/poista-vastaajatunnus! tunnus kyselytyyppi)]
    (if poistettuja
      (api-response "Tunnus poistettu")
      (arvo-util/api-response response/not-found "Tunnus ei ole poistettavissa"))))

(defn ehoks-v1 []
  [[""
    {:post {:summary "Kyselylinkin luominen"
            :description "Päivämäärät ovat ISO-formaatin mukaisia. Suorituskieli on fi, sv tai en. Tutkintotunnus
        on opintopolun koulutus koodiston 6 numeroinen koodi."
            :responses {status/ok {:body {:kysely_linkki s/Str :voimassa_loppupvm java.time.Instant :tunnus s/Str}}
                        status/not-found {:body {:error s/Str :msg s/Str} :description "Kyselykertaa ei ole olemassa"}}
            :parameters {:body Amispalaute-tunnus}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [tunnus (vt/lisaa-amispalaute-tunnus! body)]
                         (vastauslinkki-response tunnus (:request_id body))))}}]
   ["/:tunnus/metatiedot"
    {:conflicting true
     :patch {:summary "Metatietojen päivitys"
             :description "Päivitä vastaajatunnuksen valitut metatiedot. Ei voi käyttää metatietokentän poistamiseen."
             :responses {status/ok {:body {(s/optional-key :tila) s/Str}}
                         status/not-found {:body s/Str :description "Ei vastaajatunnusta integraatiokäyttäjälle"}}
             :parameters {:body {(s/optional-key :tila) s/Str}
                          :path {:tunnus s/Str}}
             :handler (fn [{{:keys [path body]} :parameters}]
                        (let [paivitettavat-metatiedot (select-keys body sallitut-metatiedot)
                              paivitetyt-metatiedot (vt/paivita-metatiedot (:tunnus path) paivitettavat-metatiedot)]
                          (if (not= (:riveja paivitetyt-metatiedot) 0)
                            (api-response (dissoc paivitetyt-metatiedot :riveja))
                            (arvo-util/api-response response/not-found "Ei vastaajatunnusta integraatiokäyttäjälle"))))}}]
   ["/status/:tunnus"
    {:conflicting true
     :get {:summary "Kyselylinkin tila"
           :responses {status/ok {:body (s/maybe {:tunnus s/Str :voimassa_loppupvm (s/maybe java.time.Instant) :vastattu s/Bool})}}
           :parameters {:path {:tunnus s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (let [status (db/vastaajatunnus-status {:tunnus (:tunnus path)})]
                        (if status (api-response (update (select-keys status [:tunnus :voimassa_loppupvm :vastattu]) :voimassa_loppupvm pvm-util/local-date->instant))
                          (arvo-util/api-response response/not-found "Vastaajatunnusta ei löydy"))))}}]
   ["/:tunnus"
    {:delete {:summary "Poista kyselylinkki"
              :responses {status/ok {:body s/Str :description "Tunnus poistettu"}
                          status/not-found {:body s/Str :description "Tunnuksella on jo vastauksia"}}
              :parameters {:path {:tunnus s/Str}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (poista-vastaajatunnus (:tunnus path) "ammatillisen-opiskelijapalaute"))}}]])

(defn tyoelamapalaute-v1 []
  [["/vastaajatunnus"
    {:post {:summary "Yksittäisen jakson vastaajatunnuksen luominen"
            :responses {status/ok {:body {:tunnus s/Str :voimassa_loppupvm java.time.Instant}}
                        status/not-found {:body {:error s/Str :msg s/Str}}}
            :parameters {:body Jaksotunnus}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [luotu-tunnus (vt/lisaa-tyopaikkaohjaaja-tunnus! body)]
                         (vastaajatunnus-response luotu-tunnus (:request-id body))))}}]
   ["/vastaajatunnus/:tunnus"
    {:patch {:summary "Jakson taustatietojen päivittäminen"
             :parameters {:body Jaksotunnus-patch
                          :path {:tunnus s/Str}}
             :handler (fn [{{:keys [path body]} :parameters}]
                        (let [paivitetyt-tiedot (vt/paivita-taustatiedot (:tunnus path) body "tyopaikkaohjaajakysely")]
                          (if paivitetyt-tiedot
                            (api-response (dissoc paivitetyt-tiedot :riveja))
                            (arvo-util/api-response response/not-found "Ei tunnusta"))))}
     :delete {:summary "Poista vastaajatunnus"
              :responses {status/ok {:body s/Str :description "Tunnus poistettu"}
                          status/not-found {:body s/Str :description "Tunnuksella on jo vastauksia"}}
              :parameters {:path {:tunnus s/Str}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (poista-vastaajatunnus (:tunnus path) "tyopaikkaohjaajakysely"))}}]
   ["/status/:tunniste"
    {:get {:summary "Kyselylinkin tila"
           :responses {status/ok {:body (s/maybe {:tunniste s/Str :voimassa_loppupvm java.time.Instant :vastattu s/Bool})}}
           :parameters {:path {:tunniste s/Str}}
           :handler (fn [{{:keys [path]} :parameters}]
                      (let [status (db/nippu-status {:tunniste (:tunniste path)})]
                        (if status (api-response (update status :voimassa_loppupvm pvm-util/local-date->instant))
                          (arvo-util/api-response response/not-found "Nippua ei löydy"))))}}]
   ["/nippu"
    {:post {:summary "Yksittäisten linkkien niputus yhdeksi nipputunnukseksi"
            :responses {status/ok {:body {:nippulinkki s/Str :voimassa_loppupvm java.time.Instant}}
                        status/not-found {:body {:errors [s/Str]}}}
            :parameters {:body Nippulinkki}
            :handler (fn [{{:keys [body]} :parameters}]
                       (log/info "Niputetaan tunnukset: " (pr-str body))
                       (let [nippu (vt/niputa-tunnukset! body)]
                         (if-not (:errors nippu)
                           (nippulinkki-response nippu)
                           (do
                             (log/info "Virhe nipun luonnissa: " (:errors nippu) "data:" (pr-str body))
                             (response/not-found {:errors (:errors nippu)})))))}}]
   ["/nippu/:tunniste/metatiedot"
    {:patch {:summary "Nipun metatietojen päivitys"
             :parameters {:body {(s/optional-key :tila) s/Str}
                          :path {:tunniste s/Str}}
             :handler (fn [{{:keys [path body]} :parameters}]
                        (let [paivitettavat-metatiedot (select-keys body sallitut-metatiedot)
                              paivitetyt-metatiedot (vt/paivita-nipun-metatiedot (:tunniste path) paivitettavat-metatiedot)]
                          (if (not= (:riveja paivitetyt-metatiedot) 0)
                            (api-response (dissoc paivitetyt-metatiedot :riveja))
                            (arvo-util/api-response response/not-found "Ei nippua integraatiokäyttäjälle"))))}}]
   ["/nippu/:tunniste"
    {:patch {:summary "Nipun päivitys"
             :parameters {:body Nippu-paivitys
                          :path {:tunniste s/Str}}
             :handler (fn [{{:keys [path body]} :parameters}]
                        (let [paivitetyt-tiedot (vt/paivita-nippu! (:tunniste path) body)]
                          (if (not= (:riveja paivitetyt-tiedot) 0)
                            (api-response (dissoc paivitetyt-tiedot :riveja))
                            (arvo-util/api-response response/not-found "Ei nippua tunnisteelle"))))}
     :delete {:summary "Poista nippu"
              :parameters {:path {:tunniste s/Str}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (let [result (vt/poista-nippu (:tunniste path))]
                           (if-not (:error result)
                             (api-response "Tunnus poistettu")
                             (response/not-found (:error result)))))}}]
   ["/tyopaikkakysely-tunnus"
    {:post {:summary "Työpaikkakyselyn tunnuksen luonti"
            :responses {status/ok {:body {:kysely_linkki s/Str :voimassa_loppupvm java.time.Instant :tunnus s/Str}}
                        status/not-found {:body {:error s/Str :msg s/Str} :description "Kyselykertaa ei ole olemassa"}}
            :parameters {:body Tyopaikkakysely-tunnus}
            :handler (fn [{{:keys [body]} :parameters}]
                       (let [luotu-tunnus (vt/lisaa-tyopaikkakysely-tunnus! body)]
                         (vastauslinkki-response luotu-tunnus (:request-id body))))}}]])
