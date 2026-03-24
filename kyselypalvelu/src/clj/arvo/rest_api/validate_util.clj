(ns arvo.rest-api.validate-util
  (:require
    [clojure.tools.logging :as log]
    [arvo.arkisto.organisaatio :as org-arkisto]
    [arvo.infra.kayttaja :refer [*kayttaja*]]))

(defn validoi-oppilaitos
  "Olettaa datasta löytyvän :koulutustoimija ja :oppilaitos oideina."
  [data]
  (when (:oppilaitos data)
    (let [oppilaitos (org-arkisto/hae-organisaatio (:oppilaitos data))
          aktiiviset-oppilaitokset (:aktiiviset-oppilaitokset *kayttaja*)]
      [(when (not= (:parent_oid oppilaitos) (:koulutustoimija data))
         "oppilaitos.koulutustoimija_ei_vastaa_oppilaitosta")
       (when (and aktiiviset-oppilaitokset (not-any? #{(:oppilaitos data)} aktiiviset-oppilaitokset))
         "oppilaitos.kayttajalle_tuntematon_oppilaitos")])))

(defn validoi-koulutustoimijan-oppilaitokset [data-lista koulutustoimija]
  (let [oppilaitokset (distinct (filter some? (map :oppilaitos data-lista)))
        oid->oppilaitos (group-by :oid (org-arkisto/hae-organisaatiot oppilaitokset))
        aktiiviset-oppilaitokset (:aktiiviset-oppilaitokset *kayttaja*)]
    (when (not-empty oppilaitokset)
      [(when (not-every? #(= koulutustoimija (:parent_oid (first (get oid->oppilaitos %)))) oppilaitokset)
         "oppilaitos.koulutustoimija_ei_vastaa_oppilaitosta")
       (when (and aktiiviset-oppilaitokset
                  (not-every? #(some #{%} aktiiviset-oppilaitokset) oppilaitokset))
         "oppilaitos.kayttajalle_tuntematon_oppilaitos")])))
