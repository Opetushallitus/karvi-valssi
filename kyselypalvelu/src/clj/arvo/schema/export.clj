(ns arvo.schema.export
  (:require [schema.core :as s]))

(defonce kysely-tila (s/enum "suljettu" "julkaistu" "luonnos"))

(defonce kysely-tyyppi (s/enum "itsearviointi" "rekrykysely" "amk-uraseuranta" "yo-uraseuranta" "avop"
                               "kandipalaute" "move" "ammatillisen-opiskelijapalaute" "tyopaikkaohjaajakysely" "tyopaikkakysely"))

(s/defschema Kyselykerta
  {:kyselyid s/Int
   :koulutustoimija s/Str
   :tyyppi kysely-tyyppi
   :kysely_fi (s/maybe s/Str)
   :kysely_sv (s/maybe s/Str)
   :kysely_en (s/maybe s/Str)
   :kysely_voimassa_alkupvm s/Str ;muunnetaan kannassa
   :kysely_voimassa_loppupvm (s/maybe s/Str) ;muunnetaan kannassa
   :kysely_tila kysely-tila
   :kyselykertaid s/Int
   :kyselykerta s/Str
   :kyselykerta_vuosi (s/maybe s/Str)
   :kyselypohjaid (s/maybe s/Int)
   :kyselypohja_nimi (s/maybe s/Str)
   :kyselypohja_tarkenne (s/maybe s/Str)
   s/Any s/Any})

(s/defschema Vastaus
  {:vastausid s/Int
   :vastaajatunnusid s/Int
   :vastaajaid s/Int
   :kysymysid s/Int
   :vastausaika s/Str ;muunnetaan kannassa
   :numerovalinta (s/maybe s/Num)
   :vapaateksti (s/maybe s/Str)
   :vaihtoehto (s/maybe (s/enum "kylla" "ei"))
   :koulutustoimija s/Str
   :kyselyid s/Int
   :kyselykertaid s/Int
   :monivalintavaihtoehto_fi (s/maybe s/Str)
   :monivalintavaihtoehto_sv (s/maybe s/Str)
   :monivalintavaihtoehto_en (s/maybe s/Str)
   s/Any s/Any})


(s/defschema Kysymyskategoria
  {(s/optional-key :rahoitusmallikysymys) (s/maybe s/Bool)
   (s/optional-key :taustakysymyksen_tyyppi) (s/maybe s/Str)
   (s/optional-key :min) (s/maybe s/Int)
   (s/optional-key :max) (s/maybe s/Int)
   (s/optional-key :decimals) (s/maybe s/Int)
   (s/optional-key :eos_teksti_sv) (s/maybe s/Str)
   (s/optional-key :eos_teksti_fi) (s/maybe s/Str)
   (s/optional-key :koodisto) (s/maybe s/Str)
   (s/optional-key :teema) (s/maybe s/Str)
   (s/optional-key :ei_vastaus_ensin) (s/maybe s/Bool)
   s/Any s/Any})

(defonce kysymys-vastaustyyppi (s/enum "arvosana"
                                       "arvosana4_ja_eos"
                                       "arvosana6_ja_eos"
                                       "arvosana6"
                                       "asteikko5_1"
                                       "valiotsikko"
                                       "likert_asteikko"
                                       "alasvetovalikko"
                                       "luku"
                                       "arvosana7"
                                       "vapaateksti"
                                       "nps"
                                       "monivalinta"
                                       "kylla_ei_valinta"))

(s/defschema Kysymys
  {:kysymysid s/Int
   :kysymysryhmaid s/Int
   :vastaustyyppi kysymys-vastaustyyppi
   :kysymys_fi (s/maybe s/Str)
   :kysymys_sv (s/maybe s/Str)
   :kysymys_en (s/maybe s/Str)
   :kategoria (s/maybe Kysymyskategoria)
   :jatkokysymys s/Bool
   :jatkokysymys_kysymysid (s/maybe s/Int)
   :kysymysryhma_fi (s/maybe s/Str)
   :kysymysryhma_sv (s/maybe s/Str)
   :kysymysryhma_en (s/maybe s/Str)
   :valtakunnallinen s/Bool
   :jarjestys (s/maybe s/Int)
   s/Any s/Any})

(s/defschema Taustatiedot
  {(s/optional-key :arvosana) (s/maybe s/Str)
   (s/optional-key :valmistumisvuosi) (s/maybe s/Str)
   (s/optional-key :koulutustyyppi) (s/maybe s/Str)
   (s/optional-key :kirjoilla_olo_kuukausia) (s/maybe s/Str)
   (s/optional-key :valmistumisajankohta) (s/maybe s/Str)
   (s/optional-key :koulutusalakoodi) (s/maybe s/Str)
   (s/optional-key :laajuus) (s/maybe s/Str)
   (s/optional-key :opiskelupaikkakunta_koodi) (s/maybe s/Str)
   (s/optional-key :valintavuosi) (s/maybe s/Str)
   (s/optional-key :sukupuoli) (s/maybe s/Str)
   (s/optional-key :kansalaisuus) (s/maybe s/Str)
   (s/optional-key :koulutuskieli) (s/maybe s/Str)
   (s/optional-key :lasnaolo_lukukausia) (s/maybe s/Str)
   (s/optional-key :asuinkunta_koodi) (s/maybe s/Str)
   (s/optional-key :tutkinnon_taso) (s/maybe s/Str)
   (s/optional-key :toimipaikka) (s/maybe s/Str)
   (s/optional-key :tutkinto) (s/maybe s/Str)
   (s/optional-key :kieli) (s/maybe s/Str)
   (s/optional-key :kunta) (s/maybe s/Str)
   (s/optional-key :koulutusmuoto) (s/maybe s/Str)
   (s/optional-key :hankintakoulutuksen_toteuttaja) (s/maybe s/Str)
   (s/optional-key :henkilonumero) (s/maybe s/Str)
   (s/optional-key :haun_numero) (s/maybe s/Str)
   (s/optional-key :aidinkieli) (s/maybe s/Str)
   (s/optional-key :ika_valmistuessa) (s/maybe s/Str)
   (s/optional-key :asteikko) (s/maybe s/Str)
   (s/optional-key :tutkintomuoto) (s/maybe s/Str)
   (s/optional-key :paaaine) (s/maybe s/Str)
   s/Any s/Any})

(s/defschema Vastaajatunnus
  {(s/optional-key :vastaajaid)       (s/maybe s/Int)
   :vastaajatunnusid s/Int
   :kyselykertaid    s/Int
   :vastaajatunnus   s/Str
   :oppilaitos       (s/maybe s/Str)
   :taustatiedot     (s/maybe Taustatiedot)
   :vastaajatunnus_alkupvm (s/maybe s/Str) ;muunnetaan kannassa
   :vastaajatunnus_loppupvm (s/maybe s/Str) ;muunnetaan kannassa
   s/Any s/Any})

(s/defschema Kysely-kysymysryhma
  {:kyselyid s/Int
   :kysymysryhmaid s/Int
   :jarjestys s/Int})

(s/defschema Opiskeluoikeus
  {:vastaajatunnus s/Str
   :opiskeluoikeus s/Str})

(s/defschema Monivalintavaihtoehto
  {:kysymysid s/Int
   :jarjestys s/Int
   :teksti_fi (s/maybe s/Str)
   :teksti_sv (s/maybe s/Str)
   :teksti_en(s/maybe s/Str)})

(s/defschema Luodut-tunnukset
  {:kyselykertaid s/Int
   :oppilaitoskoodi (s/maybe s/Str)
   :tutkintotunnus (s/maybe s/Str)
   :kuukausi (s/maybe s/Str)
   :tunnuksia s/Int
   :vastauskertoja s/Int})
