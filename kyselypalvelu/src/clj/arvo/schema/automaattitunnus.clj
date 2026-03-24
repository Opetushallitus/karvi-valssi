(ns arvo.schema.automaattitunnus
  (:require [schema.core :as s]))

(s/defschema Vastaajatunnus-metatiedot
  {(s/optional-key :tila) s/Str})

(def Kieli (s/constrained String #(= 2 (count %))))

(s/defschema Amispalaute-tunnus
  {:vastaamisajan_alkupvm                           java.time.LocalDate ;ISO formaatti
   (s/optional-key :vastaamisajan_loppupvm)         java.time.LocalDate
   :kyselyn_tyyppi                                  s/Str  ;kyselykerran metatieto tarkenne
   :tutkintotunnus                                  s/Str ;6 merkkiä
   :tutkinnon_suorituskieli                         Kieli
   :koulutustoimija_oid                             s/Str ;organisaatio-oid
   (s/optional-key :osaamisala)                     (s/maybe [s/Str])
   (s/optional-key :oppilaitos_oid)                 (s/maybe s/Str) ;organisaatio-oid
   (s/optional-key :toimipiste_oid)                 (s/maybe s/Str) ;organisaatio-oid
   (s/optional-key :hankintakoulutuksen_toteuttaja) (s/maybe s/Str)
   (s/optional-key :heratepvm)                      (s/maybe java.time.LocalDate)
   (s/optional-key :rahoitusryhma)                  s/Str
   :request_id                                      s/Str
   (s/optional-key :metatiedot)                     {(s/optional-key :tila) s/Str}})

(s/defschema Jaksotunnus
  {:koulutustoimija_oid                          s/Str
   :tyonantaja                                 s/Str
   :tyopaikka                                  s/Str
   (s/optional-key :tyopaikka_normalisoitu)    s/Str
   :tutkintotunnus                             s/Str
   (s/optional-key :tutkinnon_osa)             (s/maybe s/Str)
   (s/optional-key :paikallinen_tutkinnon_osa) (s/maybe s/Str)
   :tutkintonimike                             [s/Str]
   :osaamisala                                 [s/Str]
   :tyopaikkajakson_alkupvm                    java.time.LocalDate
   :tyopaikkajakson_loppupvm                   java.time.LocalDate
   :sopimustyyppi                              s/Str
   :vastaamisajan_alkupvm                      java.time.LocalDate
   (s/optional-key :vastaamisajan_loppupvm)    java.time.LocalDate
   (s/optional-key :tyopaikkajakson_kesto)     s/Int
   (s/optional-key :osa_aikaisuus)             (s/maybe s/Int)
   (s/optional-key :oppilaitos_oid)            (s/maybe s/Str)
   (s/optional-key :toimipiste_oid)            (s/maybe s/Str)
   (s/optional-key :oppisopimuksen_perusta)    (s/maybe s/Str)
   (s/optional-key :metatiedot)                (s/maybe {(s/optional-key :tila) s/Str})
   (s/optional-key :rahoitusryhma)             s/Str
   :request_id                                 s/Str})

(s/defschema Jaksotunnus-patch
  {(s/optional-key :oppisopimuksen_perusta)    (s/maybe s/Str)
   (s/optional-key :tyopaikka_normalisoitu)    s/Str})

(s/defschema Niputettava-tunnus
  {:tunnus s/Str :tyopaikkajakson_kesto s/Int})

(s/defschema Nippulinkki
  {:tunniste            s/Str
   :koulutustoimija_oid s/Str
   :tutkintotunnus      s/Str
   :tyonantaja          s/Str
   :tyopaikka           s/Str
   :tunnukset           [Niputettava-tunnus]
   :voimassa_alkupvm    java.time.LocalDate
   :request_id          s/Str})

(s/defschema Nippu-paivitys
  {(s/optional-key :voimassa_loppupvm) java.time.LocalDate
   (s/optional-key :tila)              s/Str})

(s/defschema Tyopaikkakysely-tunnus
  {:koulutustoimija_oid    s/Str
   :tyonantaja             s/Str
   :tyopaikka              s/Str
   :tyopaikka_normalisoitu s/Str
   :tiedonkeruu_alkupvm    java.time.LocalDate
   :tiedonkeruu_loppupvm   java.time.LocalDate
   :vastaamisajan_alkupvm  java.time.LocalDate
   :vastaamisajan_loppupvm java.time.LocalDate
   :request_id             s/Str})

(s/defschema Automaattitunnus
  {:oppilaitos                     s/Str
   :koulutus                       s/Str
   :kunta                          s/Str
   :kieli                          s/Str
   :kyselytyyppi                   s/Str
   (s/optional-key :tarkenne)      s/Str
   (s/optional-key :koulutusmuoto) s/Int})
