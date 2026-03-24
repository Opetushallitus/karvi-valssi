;; Käyttäjän vaihtoon liittyvä koodi on riippuvuussyklien välttämiseksi omassa
;; nimiavaruudessaan, koska se käyttää arkistoja, jotka puolestaan riippuvat
;; nimiavaruudesta arvo.infra.kayttaja.
(ns arvo.infra.kayttaja.vaihto
  (:require [clojure.tools.logging :as log]
            [arvo.config :refer [env]]
            [oph.common.util.util :refer [map-by some-value]]
            [arvo.infra.kayttaja :refer [*kayttaja*]]
            [arvo.infra.kayttaja.vakiot :refer [jarjestelma-oid integraatio-uid]]
            [arvo.toimiala.kayttajaroolit :refer [roolijarjestys]]
            [arvo.arkisto.kayttaja :as kayttaja-arkisto]
            [arvo.arkisto.kayttajaoikeus :as kayttajaoikeus-arkisto]
            [arvo.db.core :refer [*db*] :as db]
            [arvo.arkisto.organisaatio :as organisaatio-arkisto]
            [arvo.integraatio.kayttooikeuspalvelu :as kayttooikeuspalvelu]))

(defn kayttajan-nimi [kayttaja]
  (str (:etunimi kayttaja) " " (:sukunimi kayttaja)))

(declare hae-kayttaja-kayttoikeuspalvelusta)

(defn vaihdettu-rooli [aktiivinen-rooli vaihdettu-organisaatio]
  (if vaihdettu-organisaatio
;    Ylikirjoittaa vain organisaatiotietoa aktiiviseen rooliin
    (let [organisaatio (db/hae-organisaatio {:oid vaihdettu-organisaatio})
          oppilaitos? (not= (:parent_oid organisaatio) organisaatio-arkisto/root-organisaatio-oid)
          parent-organisaatio (when oppilaitos? (db/hae-organisaatio {:oid (:parent_oid organisaatio)}))
          oppilaitos-info (when oppilaitos?
                            [{:oppilaitos_oid (:oid organisaatio)
                              :oppilaitos_fi (:nimi_fi organisaatio)
                              :oppilaitos_sv (:nimi_sv organisaatio)
                              :oppilaitos_en (:nimi_en organisaatio)}])
          koulutustoimija-organisaatio (if oppilaitos? parent-organisaatio organisaatio)]
      (merge aktiivinen-rooli
             {:organisaatio (:oid koulutustoimija-organisaatio)
              :koulutustoimija_fi (:nimi_fi koulutustoimija-organisaatio)
              :koulutustoimija_sv (:nimi_sv koulutustoimija-organisaatio)
              :koulutustoimija_en (:nimi_en koulutustoimija-organisaatio)
              :oppilaitokset oppilaitos-info}))
    aktiivinen-rooli))

(defn- hae-valittu-rooli [valittu-rooli rooli]
  (or
   (some #(= (:rooli_organisaatio_id %) valittu-rooli) (:oppilaitokset rooli))
   (:rooli_organisaatio_id rooli)))

(defn autentikoi-kayttaja [kayttaja impersonoitu-kayttaja-oid vaihdettu-organisaatio valittu-rooli f]
  (let [aktiivinen-rooli (-> (if valittu-rooli
                               (some-value #(= valittu-rooli (hae-valittu-rooli valittu-rooli %)) (:roolit kayttaja))
                               (first (sort-by (comp roolijarjestys :rooli) (:roolit kayttaja))))
                             (vaihdettu-rooli vaihdettu-organisaatio))
        impersonoitu-kayttaja (when impersonoitu-kayttaja-oid
                                (kayttaja-arkisto/hae impersonoitu-kayttaja-oid))]
    (binding [*kayttaja*
              (assoc kayttaja
                     :aktiivinen-oid (or impersonoitu-kayttaja-oid (:oid kayttaja))
                     :aktiiviset-roolit (:roolit kayttaja)
                     :aktiivinen-rooli aktiivinen-rooli
                     :aktiivinen-koulutustoimija (:organisaatio aktiivinen-rooli)
                     :aktiiviset-oppilaitokset (not-empty (map :oppilaitos_oid (:oppilaitokset aktiivinen-rooli)))
                     :nimi (kayttajan-nimi kayttaja)
                     :vaihdettu-organisaatio (or vaihdettu-organisaatio "")
                     :impersonoidun-kayttajan-nimi (if impersonoitu-kayttaja (kayttajan-nimi impersonoitu-kayttaja) ""))]
      (log/info "Käyttäjä autentikoitu:" (pr-str *kayttaja*))
      (f))))

(defn format-oikeudet [kayttooikeudet]
  (for [kayttooikeus kayttooikeudet]
    {:kayttooikeus (:oikeus kayttooikeus)
     :organisaatio (:organisaatioOid kayttooikeus)}))

(defn with-kayttaja* [uid impersonoitu-oid vaihdettu-organisaatio valittu-rooli f]
  (log/debug "Yritetään autentikoida käyttäjä" uid)
  (if-let [kayttaja (db/hae-voimassaoleva-kayttaja {:uid uid :voimassaolo (:kayttooikeus-tarkistusvali env)})]
    (let [aktiivinen-oid (or impersonoitu-oid (:oid kayttaja))
          roolit (kayttajaoikeus-arkisto/hae-roolit aktiivinen-oid)]
      (autentikoi-kayttaja (assoc kayttaja :roolit roolit) impersonoitu-oid vaihdettu-organisaatio valittu-rooli f))
    (autentikoi-kayttaja (hae-kayttaja-kayttoikeuspalvelusta uid impersonoitu-oid) impersonoitu-oid vaihdettu-organisaatio valittu-rooli f)))

(defmacro with-kayttaja [uid impersonointi valittu-rooli & body]
  `(if (map? ~impersonointi)
    (with-kayttaja* ~uid (:kayttaja ~impersonointi) (:organisaatio ~impersonointi) ~valittu-rooli (fn [] ~@body))
    (with-kayttaja* ~uid ~impersonointi nil ~valittu-rooli (fn [] ~@body))))

(defn hae-kayttaja-kayttoikeuspalvelusta [uid impersonoitu-oid]
  (log/info "Yritetään hakea Käyttöoikeuspalvelusta käyttäjä" uid)
  (with-kayttaja integraatio-uid nil nil
    (let [kayttaja (kayttooikeuspalvelu/kayttaja uid)
          roolit (format-oikeudet (:oikeudet kayttaja))
          kayttaja (assoc kayttaja :roolit roolit)]
      (if (:voimassa kayttaja)
        (kayttajaoikeus-arkisto/paivita-kayttaja! kayttaja impersonoitu-oid)
        (do (db/passivoi-kayttaja! {:uid uid})
            (throw (IllegalStateException. (str "Ei voimassaolevaa käyttäjää " uid))))))))
