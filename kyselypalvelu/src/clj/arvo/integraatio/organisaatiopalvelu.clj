(ns arvo.integraatio.organisaatiopalvelu
  (:require [arvo.arkisto.koulutustoimija :as koulutustoimija-arkisto]
            [arvo.arkisto.organisaatio :as organisaatio-arkisto]
            [arvo.util.paivamaara-util :as pvm-util]
            [java-time.api :as jt]
            [cheshire.core :as json]
            [oph.common.util.util :refer [get-json-from-url post-json-from-url map-by some-value muutos]]
            [clojure.tools.logging :as log]
            [arvo.config :refer [env]]))

(defn halutut-kentat [organisaatio]
  (select-keys organisaatio [:nimi :oppilaitosTyyppiUri :postiosoite :yhteystiedot :virastoTunnus :ytunnus :oppilaitosKoodi :toimipistekoodi :oid :tyypit :parentOid :parentOidPath :lakkautusPvm :kotipaikkaUri]))

(defn oppilaitostyyppi [oppilaitostyyppi_uri]
  (if oppilaitostyyppi_uri
    (let [matcher (re-matcher #"\d+" oppilaitostyyppi_uri)]
      (re-find matcher))))

(defn lisaa-oppilaitostyyppi [organisaatio]
  (assoc organisaatio :oppilaitostyyppi (oppilaitostyyppi (:oppilaitosTyyppiUri organisaatio))))

; Käytetyt tyypit: https://github.com/Opetushallitus/organisaatio/blob/84d7f0822a76c802c9de30b1d1fb08b161164115/organisaatio-api/src/main/java/fi/vm/sade/organisaatio/api/model/types/OrganisaatioTyyppi.java
(defn hae-oidit-tyypilla [url tyyppi]
  (get-json-from-url url {:query-params {"searchTerms" (str "type=" tyyppi)}}))

(def organisaatiopalvelu-format "yyyy-MM-dd HH:mm")

; Haetaan minuutin tarkkuudella niin voidaan tarvittaessa hakea useasti päivässä
(defn hae-muuttuneet [url viimeisin-paivitys]
;  Substracting one minute to be sure no data is omitted
  (let [api-url (str url "v4/muutetut")
        paivitys-miinus-1-min (jt/minus viimeisin-paivitys (jt/minutes 1))
        org-aikaleima (jt/format organisaatiopalvelu-format (jt/zoned-date-time paivitys-miinus-1-min "UTC"))]
    (log/info "Haetaan muuttuneet organisaatiot organisaatiopalvelusta" api-url "aikaleimalla" org-aikaleima)
    (map (comp lisaa-oppilaitostyyppi halutut-kentat)
         (get-json-from-url api-url {:query-params {"lastModifiedSince" org-aikaleima}}))))

(defn hae-era [oid-era url]
  (log/info "Haetaan erä " (count oid-era) "kpl")
  (let [body (json/generate-string oid-era)
        full-url (str url "v4/findbyoids")]
    (map (comp lisaa-oppilaitostyyppi halutut-kentat)
         (post-json-from-url full-url {:body body :content-type "application/json"}))))

;; Koodistopalvelun oppilaitostyyppikoodistosta
(def ^:private halutut-tyypit
  #{"oppilaitostyyppi_21" ;; Ammatilliset oppilaitokset
    "oppilaitostyyppi_22" ;; Ammatilliset erityisoppilaitokset
    "oppilaitostyyppi_23" ;; Ammatilliset erikoisoppilaitokset
    "oppilaitostyyppi_24" ;; Ammatilliset aikuiskoulutuskeskukset
    "oppilaitostyyppi_41" ;; Ammattikorkeakoulut
    "oppilaitostyyppi_42" ;; Yliopistot
    "oppilaitostyyppi_43" ;; Sotilaskorkeakoulut
    "oppilaitostyyppi_61" ;; Musiikkioppilaitokset
    "oppilaitostyyppi_62" ;; Liikunnan koulutuskeskukset
    "oppilaitostyyppi_63" ;; Kansanopistot
    "oppilaitostyyppi_65" ;; Opintokeskukset
    "oppilaitostyyppi_93" ;; Muut koulutuksen järjestäjät
    "oppilaitostyyppi_99" ;; Muut oppilaitokset
    "oppilaitostyyppi_xx"}) ;; Tyyppi ei tiedossa

(defn ^:private haluttu-tyyppi? [organisaatio]
  (when-let [tyyppi (:oppilaitosTyyppiUri organisaatio)]
    (contains? halutut-tyypit (subs tyyppi 0 19))))

(defn ^:private kunta [organisaatio]
  (if (:kotipaikkaUri organisaatio)
    (clojure.string/replace (:kotipaikkaUri organisaatio) #"kunta_", "")
    ""))

(defn ^:private nimi [organisaatio]
  ((some-fn :fi :sv :en) (:nimi organisaatio)))

(defn ^:private nimi-sv [organisaatio]
  ((some-fn :sv :fi :en) (:nimi organisaatio)))

(defn ^:private nimi-en [organisaatio]
  ((some-fn :en :fi :sv) (:nimi organisaatio)))

(defn ^:private postinumero [organisaatio]
  (when-let [postinumerokoodi (get-in organisaatio [:postiosoite :postinumeroUri])]
    (when-not (clojure.string/blank? postinumerokoodi)
      (subs postinumerokoodi 6))))

(defn ^:private email [organisaatio]
  (some :email (:yhteystiedot organisaatio)))

(defn ^:private www-osoite [organisaatio]
  (some :www (:yhteystiedot organisaatio)))

(defn ^:private puhelin [organisaatio]
  (:numero (some-value #(= "puhelin" (:tyyppi %)) (:yhteystiedot organisaatio))))

(defn ^:private y-tunnus [organisaatio]
  (or (:ytunnus organisaatio) (:virastoTunnus organisaatio)))

(defn ^:private voimassa? [organisaatio]
  (if-let [lakkautus-pvm (:lakkautusPvm organisaatio)]
    (pvm-util/pvm-tulevaisuudessa? lakkautus-pvm)
    true))

(defn- format-organisaatio [organisaatio]
  {:nimi_fi (nimi organisaatio)
   :nimi_sv (nimi-sv organisaatio)
   :nimi_en (nimi-en organisaatio)
   :oid (:oid organisaatio)
   :sahkoposti (email organisaatio)
   :puhelin (puhelin organisaatio)
   :osoite (get-in organisaatio [:postiosoite :osoite])
   :postinumero (postinumero organisaatio)
   :postitoimipaikka (get-in organisaatio [:postiosoite :postitoimipaikka])
   :www_osoite (www-osoite organisaatio)
   :ytunnus (y-tunnus organisaatio)
   :lakkautuspaiva (:lakkautusPvm organisaatio)
   :voimassa (voimassa? organisaatio)
   :parent_oid (:parentOid organisaatio)
   :oppilaitoskoodi (:oppilaitosKoodi organisaatio)
   :oppilaitostyyppi (:oppilaitostyyppi organisaatio)
   :toimipistekoodi (:toimipistekoodi organisaatio)
   :kunta (kunta organisaatio)
   :tyypit (:tyypit organisaatio)
   :metatiedot (:metatiedot organisaatio)})

(defn- paivita [organisaatio olemassa-olevat-organisaatio-oidit]
  (let [olemassa-oleva? (some #(= (:oid organisaatio) %) olemassa-olevat-organisaatio-oidit)
        formatted-organisaatio (format-organisaatio organisaatio)]
    ;        Pikakorjaus, kannassa pitäisi ehkä sallia pidemmät kuin 200 merkkiä
    (if (some #(> (count ((keyword %) formatted-organisaatio)) 200) [:nimi_fi :nimi_sv :nimi_en])
      (log/warn "Organisaation nimi liian pitkä. Ei voida päivittää " (:oid organisaatio))
      (if olemassa-oleva?
        (organisaatio-arkisto/paivita-organisaatio formatted-organisaatio)
        (organisaatio-arkisto/luo-uusi-organisaatio formatted-organisaatio)))))

(defn ^:integration-api paivita-organisaatiotiedot! [organisaatiot]
  (let [olemassa-olevat-organisaatio-oidit (organisaatio-arkisto/hae-kaikki-oidit)
        ; Otetaan myös lisättävät koska muutosrajapinnan hakua ei tehdä tyyppien mukaan
        kaikki-organisaatio-oidit (concat  olemassa-olevat-organisaatio-oidit(map :oid organisaatiot))
        ; Muuttuneet rajapinta ja kaikkien toimipisteiden haku palauttaa myös filtteröityjen oppilaitosten toimipisteet. Nämä filtteröidään pois.
        tallennettavat-organisaatiot (filter (fn [organisaatio] (some #(= (:parentOid organisaatio) %) kaikki-organisaatio-oidit)) organisaatiot)]
    (doall (map #(paivita % olemassa-olevat-organisaatio-oidit) tallennettavat-organisaatiot))))

(defn ^:integration-api ^:private paivita-haetut-organisaatiot!
  "Lyhyempi parentOidPath tarkoittaa korkeamman tason organisaatiota jotka päivitetään ensin. Joillekin organisaatioille
   on virheellisesti muodostunut pidempiä oideja mutta se ei vaikuta tähän.
   Huom. tämä sallii toimipisteet toimipisteiden alla mikä on myös sallittua organisaatiopalvelussa."
  [muuttuneet-organisaatiot]
  (let [organisaatio-tyypit-v4 (set (-> env :organisaatiopalvelu :organisaatio-tyypit-v4))
        muuttuneet-organisaatiot-format (->> muuttuneet-organisaatiot
                                             (sort-by (comp count :parentOidPath))
                                             (filter #(some organisaatio-tyypit-v4 (:tyypit %)))
                                             (filter #(or (not (:oppilaitosKoodi %)) (haluttu-tyyppi? %))))]
    (log/info "Haettu muuttuneet organisaatiot," (count muuttuneet-organisaatiot-format) "kpl")
    (paivita-organisaatiotiedot! muuttuneet-organisaatiot-format)))

(defn paivita-erassa [oids paivitys-funktio url]
  (let [oid-erat (partition-all 200 oids)]
     (run! (comp #(paivitys-funktio %) #(hae-era % url)) oid-erat)))

(defn hae-ja-paivita-kaikki [url]
  (log/info (str "Haetaan kaikki organisaatiot organisaatiopalvelusta tyypeillä"
                 (-> env :organisaatiopalvelu :organisaatio-tyypit-v1)))
  (organisaatio-arkisto/aseta-kaikki-vanhentuneiksi)
  (doseq [tyyppi (-> env :organisaatiopalvelu :organisaatio-tyypit-v1)]
    (let [organisaatio-oidit (hae-oidit-tyypilla url tyyppi)]
      (paivita-erassa organisaatio-oidit paivita-organisaatiotiedot! url))))

(defn ^:integration-api paivita-organisaatiot!
  [asetukset]
  (log/info "Aloitetaan organisaatioiden päivitys organisaatiopalvelusta")
  (if (:paalla asetukset)
    (let [viimeisin-paivitys (organisaatio-arkisto/hae-viimeisin-paivitys)
          url (:url asetukset)
          nyt (jt/instant)]
      (log/info "Edellinen päivitys:" (str viimeisin-paivitys))
      (if viimeisin-paivitys
        (paivita-haetut-organisaatiot! (hae-muuttuneet url viimeisin-paivitys))
        (hae-ja-paivita-kaikki url))
      (organisaatio-arkisto/tallenna-paivitys! nyt))
    (log/info "Päivitetään vain voimassaolot."))
  (organisaatio-arkisto/paivita-voimassaolot))
