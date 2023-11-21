(ns arvo.rest-api.kysymys
  (:require
    [arvo.service.kysymys :as service]
    [ring.util.http-status :as status]
    [schema.core :as s]
    [oph.common.util.http-util :refer [validate-response]]
    [oph.common.util.http-util :refer [response-or-404]]))

(s/defschema Monivalintavaihtoehto
  {(s/optional-key :teksti_fi) s/Str
   (s/optional-key :teksti_sv) s/Str
   (s/optional-key :teksti_en) s/Str})

(s/defschema Jatkokysymys
  {(s/optional-key :kysymys_fi) s/Str
   (s/optional-key :kysymys_sv) s/Str
   (s/optional-key :kysymys_en) s/Str
   (s/optional-key :rajoite) s/Str
   (s/optional-key :max_vastaus) s/Int})

(s/defschema Peruskysymys
  {:pakollinen s/Bool
   (s/optional-key :eos_vastaus_sallittu) s/Bool
   :poistettava s/Bool
   :vastaustyyppi s/Str
   (s/optional-key :kysymys_fi) s/Str
   (s/optional-key :kysymys_sv) s/Str
   (s/optional-key :kysymys_en) s/Str
   (s/optional-key :selite_fi) s/Str
   (s/optional-key :selite_sv) s/Str
   (s/optional-key :selite_en) s/Str
   (s/optional-key :max_vastaus) s/Int
   (s/optional-key :monivalinta_max) s/Int
   (s/optional-key :rajoite) s/Str
   :metatiedot s/Any})

(s/defschema JatkokysymysCreate
  {(s/optional-key :kylla) Jatkokysymys
   (s/optional-key :ei) Jatkokysymys})

(s/defschema KysymysCreateData
  {:pakollinen s/Bool
   (s/optional-key :eos_vastaus_sallittu) s/Bool
   :poistettava s/Bool
   :vastaustyyppi s/Str
   (s/optional-key :kysymys_fi) s/Str
   (s/optional-key :kysymys_sv) s/Str
   (s/optional-key :kysymys_en) s/Str
   (s/optional-key :selite_fi) s/Str
   (s/optional-key :selite_sv) s/Str
   (s/optional-key :selite_en) s/Str
   (s/optional-key :max_vastaus) s/Int
   (s/optional-key :monivalinta_max) s/Int
   (s/optional-key :rajoite) s/Str
   :metatiedot s/Any
   (s/optional-key :jatkokysymykset) JatkokysymysCreate
   (s/optional-key :monivalintavaihtoehdot) [Monivalintavaihtoehto]
   (s/optional-key :matriisikysymykset) [Peruskysymys]})

(s/defschema KysymysUpdateData
  {(s/optional-key :kysymys_fi) s/Str
   (s/optional-key :kysymys_sv) s/Str
   (s/optional-key :kysymys_en) s/Str
   (s/optional-key :selite_fi) s/Str
   (s/optional-key :selite_sv) s/Str
   (s/optional-key :selite_en) s/Str
   (s/optional-key :eos_vastaus_sallittu) s/Bool
   (s/optional-key :pakollinen) s/Bool
   (s/optional-key :poistettava) s/Bool
   (s/optional-key :metatiedot) s/Any
   (s/optional-key :monivalintavaihtoehdot) [Monivalintavaihtoehto]})

(defn reitit []
  [["/kysymysryhma/:kysymysryhmaid"
    {:conflicting true
     :post {:summary "Lisää uusi kysymys kysymysryhmään"
            :description "Järjestys asetetaan aina kysymysryhmän viimeiseksi.
         Jatkokysymyksen voi luoda vain kylla_ei_valinta tyyppiseen kysymykseen ja tyypiksi tulee \"vapaateksti\""
            :kayttooikeus :kysymys
            :parameters {:path {:kysymysryhmaid s/Int}
                         :body KysymysCreateData}
            :responses {status/ok {:body {:kysymysid s/Int :matriisikysymykset [s/Int]}}}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (response-or-404 (service/lisaa! body (:kysymysryhmaid path))))}}]
   ["/:kysymysid/matriisikysymys"
    {:conflicting true
     :post {:summary "Lisää uusi kysymys matriisikysymykseen"
            :description "Järjestys asetetaan aina matriisin viimeiseksi."
            :kayttooikeus :kysymys
            :parameters {:path {:kysymysid s/Int}
                         :body Peruskysymys}
            :responses {status/ok {:body {:kysymysid s/Int}}}
            :handler (fn [{{:keys [path body]} :parameters}]
                       (validate-response service/lisaa-matriisikysymys! [service/validoi-matriisikysymys] body (:kysymysid path)))}}]
   ["/:kysymysid"
    {:patch {:summary "Kysymyksen päivittäminen"
             :description "Päivittää kysymyksen annetuilla tiedoilla. Jos metatiedot annetaan ne korvataan samalla tavalla kuin muissakin kentissä."
             :kayttooikeus :kysymys
             :parameters {:path {:kysymysid s/Int}
                          :body KysymysUpdateData}
             :responses {status/ok {:body s/Str}}
             :handler (fn [{{:keys [path body]} :parameters}]
                        (response-or-404 (service/paivita! (:kysymysid path) body)))}
     :delete {:summary "Poista kysymys"
              :description "Poistaa kysymyksen, tämän jatkokysymyksen ja näiden monivalintavaihtoehdot. Jos poistettava
          kysymys on matriisin pääkysymys (matriisi_jarjestys 0) poistetaan kaikki matriisin kysymykset."
              :kayttooikeus :kysymys
              :parameters {:path {:kysymysid s/Int}}
              :responses {status/ok {:body s/Str}}
              :handler (fn [{{:keys [path]} :parameters}]
                         (response-or-404 (service/poista! (:kysymysid path))))}}]
   ["/vaihda-kysymysten-jarjestys/:kysymysryhmaid"
    {:conflicting true
     :put {:summary "Kysymysten järjestyksen vaihto"
           :description "Vaihtaa kahden kysymyksen järjestyksen kysymysryhmän sisällä."
           :kayttooikeus :kysymys
           :parameters {:path {:kysymysryhmaid s/Int}
                        :body {:kysymysid1 s/Int
                               :kysymysid2 s/Int}}
           :responses {status/ok {:body s/Str}}
           :handler (fn [{{:keys [path body]} :parameters}]
                      (validate-response service/vaihda! [service/validate-vaihda] (:kysymysryhmaid path) body))}}]])
