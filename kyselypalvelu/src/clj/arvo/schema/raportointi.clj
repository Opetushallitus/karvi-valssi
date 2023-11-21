(ns arvo.schema.raportointi
  (:require [schema.core :as s]))

(defonce kysely-tila (s/enum "suljettu" "julkaistu" "luonnos"))

(defonce kysely-tyyppi (s/enum "itsearviointi" "rekrykysely" "amk-uraseuranta" "yo-uraseuranta" "avop" "ammatillisen-opiskelijapalaute"
                               "kandipalaute" "move" "tyopaikkaohjaajakysely" "tyopaikkakysely"))

(s/defschema Kyselykerta
  {:kyselyid s/Int
   :koulutustoimija s/Str
   :tyyppi kysely-tyyppi
   :kysely_fi (s/maybe s/Str)
   :kysely_sv (s/maybe s/Str)
   :kysely_en (s/maybe s/Str)
   :kysely_voimassa_alkupvm java.time.LocalDate
   :kysely_voimassa_loppupvm (s/maybe java.time.LocalDate)
   :kysely_tila kysely-tila
   :kyselykertaid s/Int
   :kyselykerta s/Str
   :kyselykerta_vuosi (s/maybe s/Str)
   :kyselypohjaid (s/maybe s/Int)
   :kyselypohja_nimi (s/maybe s/Str)
   :kyselypohja_tarkenne (s/maybe s/Str)
   s/Any s/Any})

(s/defschema Raporttidata
  {:jakauma {:vaihtoehto s/Str :lkm s/Int}
   (s/optional-key :nps) s/Num})

(s/defschema Asteikko-entry
  {:jarjestys s/Int
   :arvo s/Any
   :nimi_fi (s/maybe s/Str)
   :nimi_sv (s/maybe s/Str)
   :nimi_en (s/maybe s/Str)})

(s/defschema Monivalintavaihtoehto
  {:jarjestys s/Int
   :vaihtoehto_fi (s/maybe s/Str)
   :vaihtoehto_sv (s/maybe s/Str)
   :vaihtoehto_en (s/maybe s/Str)})

(s/defschema Raportti-kysymys
  {:kysymysid s/Int
   :jarjestys s/Int
   :vastaustyyppi s/Str
   :kysymys_fi (s/maybe s/Str)
   :kysymys_sv (s/maybe s/Str)
   :kysymys_en (s/maybe s/Str)
   (s/optional-key :monivalintavaihtoehdot) (s/maybe [Monivalintavaihtoehto])
   :vastausdata Raporttidata
   :vertailudata Raporttidata})

(s/defschema Raportti-kysymysryhma
  {:kysymysryhmaid s/Int
   :nimi_fi (s/maybe s/Str)
   :nimi_sv (s/maybe s/Str)
   :nimi_en (s/maybe s/Str)
   :kysymykset [Raportti-kysymys]})

(s/defschema Kyselyraportti
  {:kyselyid s/Int
   :nimi_fi (s/maybe s/Str)
   :nimi_sv (s/maybe s/Str)
   :nimi_en (s/maybe s/Str)
   :tyyppi s/Str
   :kysymysryhmat [Raportti-kysymysryhma]
   s/Any s/Any})

(s/defschema Raportti-parametrit
  {:alkupvm s/Str
   :loppupvm s/Str
   :vertailukausi s/Keyword
   ;:vastausaika s/Keyword
   (s/optional-key :tutkinnot)     [s/Str]
   (s/optional-key :suorituskieli) [s/Str]
   s/Any s/Any})
