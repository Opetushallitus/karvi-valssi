(ns arvo.service.viestinta
  (:require [arvo.db.core :refer [*db*] :as db]
            [selmer.parser :as selmer]
            [clj-http.client :as http]
            [clojure.tools.logging :as log]
            [arvo.config :refer [env]]
            [postal.core :as postal]
            [clojure.string :as s]
            [arvo.util :as au]))

(defn laheta-tekstiviesti [viesti]
  (let [resp (http/post (:host (:sms env))
                        {:content-type "application/x-www-form-urlencoded; charset=utf-8"
                         :form-params {:login (:login (:sms env))
                                       :password (:password (:sms env))
                                       :sender (:lahettaja_nimi viesti)
                                       :msisdn (:puhelinnumero viesti)
                                       :msg (:viesti viesti)}})]
    (if (= 200 (:status resp))
      "SUCCESS"
      "FAILURE")))

(defn laheta-sahkoposti [viesti]
  (let [resp (postal/send-message (:email env)
                                  {:from (:lahettaja_email viesti)
                                   :to (:sahkoposti viesti)
                                   :subject (:otsikko viesti)
                                   :body (:viesti viesti)})]
    (name (:error resp))))

(defn hae-kyselytyypin-vastaanottajat [tunniste lahetyskerta]
  (let [uusintalahetyskerta (:uusintalahetyskerta lahetyskerta)]
      (case (:kyselytyyppi lahetyskerta)
        "amk-uraseuranta" (db/hae-uraseuranta-vastaanottajat {:tunniste tunniste :lahetyskertaid (:id lahetyskerta)
                                                              :kohdejoukko (:kohdejoukko lahetyskerta)})
        "move" (if uusintalahetyskerta
                 (db/hae-move-uusintalahetys-vastaanottajat {:lahetyskertatunniste (str tunniste "/" uusintalahetyskerta) :lahetyskertaid (:id lahetyskerta)})
                 (db/hae-move-vastaanottajat {:tunniste tunniste :lahetyskertaid (:id lahetyskerta)})))))

(defn hae-vastaanottajat [lahetyskerta]
  (assert (au/in? ["vastaajat" "vastanneet"] (:kohdejoukko lahetyskerta)))
  (let [tunniste (:kysely_tunniste lahetyskerta)
        vastaanottajat (hae-kyselytyypin-vastaanottajat tunniste lahetyskerta)]
    (case (:lahetystyyppi lahetyskerta)
      "sms" (filter #(not-empty (:puhelinnumero %)) vastaanottajat)
      "email" (filter #(not-empty (:sahkoposti %)) vastaanottajat))))


(defn hae-viestipohjat [tunniste tyyppi]
  (let [tekstit (db/hae-viesti {:tunniste tunniste :tyyppi tyyppi})]
    (group-by :kieli tekstit)))

(defn hae-lahettaja [vastaanottaja lahetyskerta]
  (let [asiointikieli (or (:asiointikieli vastaanottaja) "fi")
        lahettaja (:lahettaja lahetyskerta)
        kj-lahettaja (get vastaanottaja (keyword (str "lahettaja_" asiointikieli)))]
    (if (and (some? kj-lahettaja) (not-empty (s/trim kj-lahettaja)) (au/falsy? (:ohita_kustomointi lahettaja)))
        kj-lahettaja
        (get lahettaja (keyword (str "nimi_" asiointikieli))))))

(defn format-viesti [vastaanottaja viestipohjat lahetyskerta]
  (let [kieli (or (:asiointikieli vastaanottaja) "fi")
        viestitkieli (->> (get viestipohjat kieli) (sort-by :sisalto_tyyppi) reverse)
        viesti (case (:lahetystyyppi lahetyskerta)
                 "email" (flatten [:alternative
                                   (for [viesti viestitkieli]
                                     {:type (:sisalto_tyyppi viesti) :content (selmer/render (:teksti viesti) vastaanottaja)})])
                 "sms" (selmer/render (:teksti (first viestitkieli)) vastaanottaja))
        lahettaja (hae-lahettaja vastaanottaja lahetyskerta)]
    {:vastaajatunnusid (:vastaajatunnusid vastaanottaja)
     :sahkoposti       (:sahkoposti vastaanottaja)
     :puhelinnumero    (:puhelinnumero vastaanottaja)
     :lahettaja_nimi   lahettaja
     :lahettaja_email  (str lahettaja " <"(get-in lahetyskerta [:lahettaja :email])">")
     :otsikko          (:otsikko (first viestitkieli))
     :viesti           viesti}))


(defn paivita-loki [viesti lahetyskerta status]
  (db/lisaa-lahetystieto! {:vastaajatunnusid (:vastaajatunnusid viesti)
                           :lahetyskertaid (:id lahetyskerta)
                           :status status}))

(defn laheta-viesti [vastaanottaja viestipohjat lahetyskerta]
  (let [viesti (format-viesti vastaanottaja viestipohjat lahetyskerta)]
    (try
      (let [status (case (:lahetystyyppi lahetyskerta)
                     "email" (laheta-sahkoposti viesti)
                     "sms" (laheta-tekstiviesti viesti))]
        (paivita-loki viesti lahetyskerta status))
      (catch Exception e
        (log/error e "Virhe lähetettäessä tunnusta" (:vastaajatunnusid viesti))
        (paivita-loki viesti lahetyskerta "ERROR")))))


(defn- laheta-viestit! [lahetyskertaid]
  (let [lahetyskerta (db/hae-lahetyskerta-by-id {:id lahetyskertaid})
        viestipohjat (hae-viestipohjat (:kysely_tunniste lahetyskerta) (:teksti_tyyppi lahetyskerta))
        vastaanottajat (hae-vastaanottajat lahetyskerta)]
    (log/info "Läheteään viestit, tyyppi: " (:lahetystyyppi lahetyskerta) " vastaanottajia: " (count vastaanottajat))
    (db/paivita-lahetyskerta! {:tila "aloitettu" :id lahetyskertaid})
    (doseq [vastaanottaja vastaanottajat]
      (laheta-viesti vastaanottaja viestipohjat lahetyskerta))
    (log/info "Viestien lähetys valmis")
    (db/paivita-lahetyskerta! {:tila "lahetetty" :id lahetyskertaid})
    (count vastaanottajat)))

(defn laheta-viestit [uusintalahetyskerta]
  (if (get-in env [:ominaisuus :massaviestien-lahetys])
    (laheta-viestit! uusintalahetyskerta)
    (log/warn "Massaviestien lähetys ei ole päällä.")))

(defn laheta-testisahkoposti [lahetyskertaid sahkoposti kieli]
  (let [lahetyskerta (db/hae-lahetyskerta-by-id {:id lahetyskertaid})
        viestipohjat (hae-viestipohjat (:kysely_tunniste lahetyskerta) (:teksti_tyyppi lahetyskerta))
        vastaanottaja {:asiointikieli kieli
                       :tunnus "TEST"
                       :vastaajatunnusid 7357
                       :sahkoposti sahkoposti
                       :oppilaitos_fi "testioppilaitos nimi fi"
                       :oppilaitos_sv "testioppilaitos nimi sv"}]
    (str (laheta-viesti vastaanottaja viestipohjat lahetyskerta)
         "Vastaanottajia:" (count (hae-vastaanottajat lahetyskerta)))))

(defn laheta-testi-sms [lahetyskertaid puhelinnumero kieli]
  (let [lahetyskerta (db/hae-lahetyskerta-by-id {:id lahetyskertaid})
        viestipohjat (hae-viestipohjat (:kysely_tunniste lahetyskerta) (:teksti_tyyppi lahetyskerta))
        vastaanottaja {:asiointikieli kieli
                       :tunnus "TEST"
                       :vastaajatunnusid 7357
                       :puhelinnumero puhelinnumero}]
    (str (laheta-viesti vastaanottaja viestipohjat lahetyskerta))))



(defn hae-seuraava-lahetyskerta [tunniste]
  (let [lahetyskerta (db/hae-lahetyskerta {:tunniste tunniste})
        vastaanottajat (hae-vastaanottajat lahetyskerta)]
    (merge lahetyskerta {:vastaanottajia (count vastaanottajat)})))
