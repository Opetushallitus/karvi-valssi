(ns arvo.kyselytyypit)

(def itsearviointi-taustatiedot
  [{:kentta_id "koulutustoimija"
    :kentta_fi "Koulutuksen järjestäjä"
    :kentta_sv nil
    :kentta_en nil
    :raportointi {:csv {:raportoi true :jarjestys 1}}}])

(def kandipalaute-taustatiedot
  [{:kentta_id "tutkinto"
    :kentta_fi "Tutkinto"
    :kentta_sv "Examen"
    :kentta_en "Degree"
    :raportointi {:csv {:raportoi true :jarjestys 1 :selitteet true}}}
   {:kentta_id "kieli"
    :kentta_fi "Suorituskieli"
    :kentta_sv "Examensspråk"
    :kentta_en "Language of degree"
    :raportointi {:csv {:raportoi false}}}
   {:kentta_id "toimipiste"
    :kentta_fi "Toimipiste"
    :kentta_sv "Verksamhetsställe"
    :kentta_en "Operational unit"
    :raportointi {:csv {:raportoi false}}}
   {:kentta_id "kunta"
    :kentta_fi "Kunta"
    :kentta_sv "Kommun"
    :kentta_en "Region"
    :raportointi {:csv {:raportoi false}}}])

(def avop-taustatiedot
  [{:kentta_id "tutkinto"
    :kentta_fi "Tutkinto"
    :kentta_sv "Examen"
    :kentta_en "Degree"
    :raportointi {:csv {:raportoi true :jarjestys 1 :selitteet true}}}
   {:kentta_id "koulutusmuoto"
    :kentta_fi "Koulutusmuoto"
    :kentta_sv "Utbildningsform"
    :kentta_en "Form of education"
    :raportointi {:csv {:raportoi true :jarjestys 2}}}
   {:kentta_id "kieli"
    :kentta_fi "Suorituskieli"
    :kentta_sv "Examensspråk"
    :kentta_en "Language of degree"
    :raportointi {:csv {:raportoi false}}}
   {:kentta_id "toimipiste"
    :kentta_fi "Toimipiste"
    :kentta_sv "Verksamhetsställe"
    :kentta_en "Operational unit"
    :raportointi {:csv {:raportoi false}}}
   {:kentta_id "kunta"
    :kentta_fi "Kunta"
    :kentta_sv "Kommun"
    :kentta_en "Region"
    :raportointi {:csv {:raportoi false}}}])

(def ammatillisen-opiskelijapalaute-taustatiedot
  [{:kentta_id "hankintakoulutuksen_toteuttaja"
    :kentta_fi "Hankintakoulutuksen toteuttaja "
    :kentta_sv "Anordnaren av anskaffad utbildning"
    :kentta_en "Provider of procured training"
    :raportointi {:csv {:raportoi true :jarjestys 1 :selitteet true}}}
   {:kentta_id "tutkinto"
    :kentta_fi "Tutkinto"
    :kentta_sv "Examen"
    :kentta_en "Degree"
    :raportointi {:csv {:raportoi true :jarjestys 2 :selitteet true}}}
   {:kentta_id "toimipiste"
    :kentta_fi "Toimipiste"
    :kentta_sv "Verksamhetsställe"
    :kentta_en "Operational unit"
    :raportointi {:csv {:raportoi true :jarjestys 3 :selitteet false}}}
   {:kentta_id "toimipiste_oid"
    :kentta_fi "Toimipisteen nimi"
    :kentta_sv "Namn på verksamhetsställe"
    :kentta_en "Name of operational unit"
    :raportointi {:csv {:raportoi true :jarjestys 4 :selitteet false}}}
   {:kentta_id "kieli"
    :kentta_fi "Suorituskieli"
    :kentta_sv "Examensspråk"
    :kentta_en "Language of degree"
    :raportointi {:csv {:raportoi true :jarjestys 5}}}
   {:kentta_id "osaamisala"
    :kentta_fi "Osaamisala" :kentta_sv "Kompetensområde" :kentta_en "Competence area"
    :raportointi nil}
   {:kentta_id "heratepvm"
    :kentta_fi "Herätepäivä" :kentta_sv "" :kentta_en ""
    :raportointi nil}])

(def rekrykysely-taustatiedot
  [{:kentta_id "henkilonumero"
    :kentta_fi "Henkilönumero"
    :kentta_sv "Anställningsnummer"
    :kentta_en "Employee number"
    :raportointi {:csv {:raportoi true :jarjestys 1}}}
   {:kentta_id "haun_numero"
    :kentta_fi "Haun numero"
    :kentta_sv "Vakans id"
    :kentta_en "Vacancy id"
    :raportointi {:csv {:raportoi true :jarjestys 2}}}])


(def yo-uraseuranta-taustatiedot
  [{:kentta_id "valmistumisvuosi"
    :kentta_fi "Valmistumisvuosi" :kentta_sv "Examensår" :kentta_en "Graduation year"
    :raportointi {:csv {:raportoi true :jarjestys 1}}}
   {:kentta_id "sukupuoli"
    :kentta_fi "Sukupuoli" :kentta_sv "Kön" :kentta_en "Gender"
    :raportointi {:csv {:raportoi true :jarjestys 2}}}
   {:kentta_id "ika_valmistuessa"
    :kentta_fi "Ikä valmistuessa" :kentta_sv "Examensålder" :kentta_en "Graduation age"
    :raportointi {:csv {:raportoi true :jarjestys 3}}}
   {:kentta_id "kansalaisuus"
    :kentta_fi "Kansalaisuus" :kentta_sv "Medborgarskap" :kentta_en "Nationality"
    :raportointi {:csv {:raportoi true :jarjestys 4}}}
   {:kentta_id "aidinkieli"
    :kentta_fi "Äidinkieli" :kentta_sv "Modersmål" :kentta_en "Mother tongue"
    :raportointi {:csv {:raportoi true :jarjestys 5}}}
   {:kentta_id "koulutusalakoodi"
    :kentta_fi "Koulutusalakoodi" :kentta_sv "Utbildningsområde kod" :kentta_en "Field of education code"
    :raportointi {:csv {:raportoi true :jarjestys 6}}}
   {:kentta_id "paaaine"
    :kentta_fi "Pääaine" :kentta_sv "Huvudämne" :kentta_en "Major"
    :raportointi {:csv {:raportoi true :jarjestys 7}}}
   {:kentta_id "tutkinnon_taso"
    :kentta_fi "Tutkinnon taso" :kentta_sv "Examensnivå" :kentta_en "Level of degree"
    :raportointi {:csv {:raportoi true :jarjestys 8}}}
   {:kentta_id "tutkinto"
    :kentta_fi "Tutkinto" :kentta_sv "Examen" :kentta_en "Degree"
    :raportointi {:csv {:raportoi true :jarjestys 9 :selitteet true}}}
   {:kentta_id "laajuus"
    :kentta_fi "Laajuus" :kentta_sv "Omfattning" :kentta_en "Scope"
    :raportointi {:csv {:raportoi true :jarjestys 10}}}
   {:kentta_id "valintavuosi"
    :kentta_fi "Valintavuosi" :kentta_sv "Antagningsår" :kentta_en "Admission year"
    :raportointi {:csv {:raportoi true :jarjestys 11}}}
   {:kentta_id "asuinkunta_koodi"
    :kentta_fi "Asuinkunta" :kentta_sv "Bostadskommun kod" :kentta_en "Municipality of residence"
    :raportointi {:csv {:raportoi true :jarjestys 12}}}
   {:kentta_id "valmistumisajankohta"
    :kentta_fi "Valmistumisajankohta" :kentta_sv "Examenstidpunkt" :kentta_en "Graduation date"
    :raportointi {:csv {:raportoi true :jarjestys 13}}}
   {:kentta_id "opiskelupaikkakunta_koodi"
    :kentta_fi "Opiskelupaikkakunta" :kentta_sv "Utbildningens kommun" :kentta_en "Municipality of education"
    :raportointi {:csv {:raportoi true :jarjestys 14}}}
   {:kentta_id "kirjoilla_olo_kuukausia"
    :kentta_fi "Kirjoilla olo kuukausia" :kentta_sv "Närvaromånader" :kentta_en "Number of months enrolled"
    :raportointi {:csv {:raportoi true :jarjestys 15}}}
   {:kentta_id "lasnaolo_lukukausia"
    :kentta_fi "Läsnäolo lukukausia" :kentta_sv "Närvaroterminer" :kentta_en "Number of terms enrolled as present"
    :raportointi {:csv {:raportoi true :jarjestys 16}}}
   {:kentta_id "koulutuskieli"
    :kentta_fi "Koulutuskieli" :kentta_sv "Utbildningens språk" :kentta_en "Language of education"
    :raportointi {:csv {:raportoi true :jarjestys 17}}}
   {:kentta_id "koulutustyyppi"
    :kentta_fi "Koulutustyyppi" :kentta_sv "Typ av utbildning" :kentta_en "Type of education"
    :raportointi {:csv {:raportoi true :jarjestys 18}}}
   {:kentta_id "arvosana"
    :kentta_fi "Arvosana" :kentta_sv "Vitsord" :kentta_en "Grade"
    :raportointi nil}
   {:kentta_id "asteikko"
    :kentta_fi "Asteikko" :kentta_sv "Vitsordsskala" :kentta_en "Grade scale"
    :raportointi nil}
   {:kentta_id "oppilaitoskoodi"
    :kentta_fi "Oppilaitoskoodi" :kentta_sv "Läroanstalt kod" :kentta_en "Educational institution code"
    :raportointi nil}
   {:kentta_id "koulutusala"
    :kentta_fi "Koulutusala"
    :raportointi {:csv {:raportoi false}}}])

(def move-taustatiedot
  [{:kentta_id "koulu"
    :kentta_fi "Koulu"
    :kentta_sv "koulu"
    :kentta_en "koulu"
    :raportointi {:vipunen false}}
   {:kentta_id "kunta"
    :kentta_fi "Kunta"
    :kentta_sv "kunta"
    :kentta_en "kunta"
    :raportointi {:vipunen false}}
   {:kentta_id "maakunta"
    :kentta_fi "Maakunta"
    :kentta_sv "maakunta"
    :kentta_en "maakunta"
    :raportointi {:vipunen false}}
   {:kentta_id "maakunta"
    :kentta_fi "Maakunta"
    :kentta_sv "maakunta"
    :kentta_en "maakunta"
    :raportointi {:vipunen false}}])

(def amk-uraseuranta-taustatiedot
  [{:kentta_id "valmistumisvuosi"
    :kentta_fi "Valmistumisvuosi" :kentta_sv "Examensår" :kentta_en "Graduation year"
    :raportointi {:csv {:raportoi true :jarjestys 1}}}
   {:kentta_id "sukupuoli"
    :kentta_fi "Sukupuoli" :kentta_sv "Kön" :kentta_en "Gender"
    :raportointi {:csv {:raportoi true :jarjestys 2}}}
   {:kentta_id "ika_valmistuessa"
    :kentta_fi "Ikä valmistuessa" :kentta_sv "Examensålder" :kentta_en "Graduation age"
    :raportointi {:csv {:raportoi true :jarjestys 3}}}
   {:kentta_id "kansalaisuus"
    :kentta_fi "Kansalaisuus" :kentta_sv "Medborgarskap" :kentta_en "Nationality"
    :raportointi {:csv {:raportoi true :jarjestys 4}}}
   {:kentta_id "aidinkieli"
    :kentta_fi "Äidinkieli" :kentta_sv "Modersmål" :kentta_en "Mother tongue"
    :raportointi {:csv {:raportoi true :jarjestys 5}}}
   {:kentta_id "koulutusalakoodi"
    :kentta_fi "Koulutusalakoodi" :kentta_sv "Utbildningsområde kod" :kentta_en "Field of education code"
    :raportointi {:csv {:raportoi true :jarjestys 6}}}
   {:kentta_id "paaaine"
    :kentta_fi "Pääaine" :kentta_sv "Huvudämne" :kentta_en "Major"
    :raportointi {:csv {:raportoi true :jarjestys 7}}}
   {:kentta_id "tutkinnon_taso"
    :kentta_fi "Tutkinnon taso" :kentta_sv "Examensnivå" :kentta_en "Level of degree"
    :raportointi {:csv {:raportoi true :jarjestys 8}}}
   {:kentta_id "tutkinto"
    :kentta_fi "Tutkinto" :kentta_sv "Examen" :kentta_en "Degree"
    :raportointi {:csv {:raportoi true :jarjestys 9 :selitteet true}}}
   {:kentta_id "laajuus"
    :kentta_fi "Laajuus" :kentta_sv "Omfattning" :kentta_en "Scope"
    :raportointi {:csv {:raportoi true :jarjestys 10}}}
   {:kentta_id "valintavuosi"
    :kentta_fi "Valintavuosi" :kentta_sv "Antagningsår" :kentta_en "Admission year"
    :raportointi {:csv {:raportoi true :jarjestys 11}}}
   {:kentta_id "asuinkunta_koodi"
    :kentta_fi "Asuinkunta" :kentta_sv "Bostadskommun kod" :kentta_en "Municipality of residence"
    :raportointi {:csv {:raportoi true :jarjestys 12}}}
   {:kentta_id "opiskelupaikkakunta_koodi"
    :kentta_fi "Opiskelupaikkakunta" :kentta_sv "Utbildningens_kommun" :kentta_en "Municipality of education"
    :raportointi {:csv {:raportoi true :jarjestys 14}}}
   {:kentta_id "kirjoilla_olo_kuukausia"
    :kentta_fi "Kirjoilla olo kuukausia" :kentta_sv "Närvaromånader" :kentta_en "Number of months enrolled"
    :raportointi {:csv {:raportoi true :jarjestys 15}}}
   {:kentta_id "lasnaolo_lukukausia"
    :kentta_fi "Läsnäolo lukukausia" :kentta_sv "Närvaroterminer" :kentta_en "Number of terms enrolled as present"
    :raportointi {:csv {:raportoi true :jarjestys 16}}}
   {:kentta_id "koulutuskieli"
    :kentta_fi "Koulutuskieli" :kentta_sv "Utbildningens språk" :kentta_en "Language of education"
    :raportointi {:csv {:raportoi true :jarjestys 17}}}
   {:kentta_id "koulutustyyppi"
    :kentta_fi "Koulutustyyppi" :kentta_sv "Typ av utbildning" :kentta_en "Type of education"
    :raportointi {:csv {:raportoi true :jarjestys 18}}}
   {:kentta_id "arvosana"
    :kentta_fi "Arvosana" :kentta_sv "Vitsord" :kentta_en "Grade"
    :raportointi nil}
   {:kentta_id "asteikko"
    :kentta_fi "Asteikko" :kentta_sv "Vitsordsskala" :kentta_en "Grade scale"
    :raportointi nil}])


(def jakso-taustatiedot
  [{:kentta_id "toimipiste"
    :kentta_fi "Toimipiste" :kentta_sv "Verksamhetsställe" :kentta_en "Operational unit"
    :raportointi {:csv {:raportoi true :jarjestys 1 :selitteet false}}}
   {:kentta_id "toimipiste_oid"
    :kentta_fi "Toimipisteen nimi"
    :kentta_sv "Namn på verksamhetsställe"
    :kentta_en "Name of operational unit"
    :raportointi {:csv {:raportoi true :jarjestys 2 :selitteet false}}}
   {:kentta_id "tutkinto"
    :kentta_fi "Tutkinto" :kentta_sv "Examen" :kentta_en "Degree"
    :raportointi {:csv {:raportoi true :jarjestys 3 :selitteet true}}}
   {:kentta_id "osaamisala"
    :kentta_fi "Osaamisala" :kentta_sv "Kompetensområde" :kentta_en "Competence area"
    :raportointi {:csv {:raportoi true :jarjestys 4}}}
   {:kentta_id "tutkintonimike"
    :kentta_fi "Tutkintonimike" :kentta_sv "Examensbenämning" :kentta_en "Qualification title"
    :raportointi {:csv {:raportoi true :jarjestys 5}}}
   {:kentta_id "tutkinnon_osa"
    :kentta_fi "Tutkinnon osa" :kentta_sv "Examensdel" :kentta_en "Qualification units"
    :raportointi {:csv {:raportoi true :jarjestys 6 :selitteet true}}}
   {:kentta_id "paikallinen_tutkinnon_osa"
    :kentta_fi "Paikallinen tutkinnon osa" :kentta_sv nil :kentta_en nil
    :raportointi {:csv {:raportoi true :jarjestys 7}}}
   {:kentta_id "sopimustyyppi"
    :kentta_fi "Osaamisen hankkimistapa" :kentta_sv "Sätt att förvärva kunnandet" :kentta_en "Way to achieve competence"
    :raportointi {:csv {:raportoi true :jarjestys 8}}}
   {:kentta_id "tyonantaja"
    :kentta_fi "Työnantaja" :kentta_sv "Arbetsgivare" :kentta_en "Employer"
    :raportointi {:csv {:raportoi true :jarjestys 9}}}
   {:kentta_id "tyopaikka"
    :kentta_fi "Työpaikka" :kentta_sv "Arbetsplats" :kentta_en "Workplace"
    :raportointi {:csv {:raportoi true :jarjestys 10}}}
   {:kentta_id "tyopaikkajakson_alkupvm"
    :kentta_fi "Työelämässä oppimisen alkupvm" :kentta_sv "Startdatum för lärande i arbetslivet" :kentta_en "Work-based learning start date"
    :raportointi {:csv {:raportoi true :jarjestys 11}}}
   {:kentta_id "tyopaikkajakson_loppupvm"
    :kentta_fi "Työelämässä oppimisen loppupvm" :kentta_sv "Slutdatum för lärande i arbetslivet" :kentta_en "Work-based learning end date"
    :raportointi {:csv {:raportoi true :jarjestys 12}}}
   {:kentta_id "osa_aikaisuus"
    :kentta_fi "Työpaikkajakson osa-aikaisuus" :kentta_sv "Deltidsnivå för arbetsplatsperiod" :kentta_en "Part-time rate for work-based learning period"
    :raportointi {:csv {:raportoi true :jarjestys 13}}}
   {:kentta_id "tyopaikkajakson_kesto"
    :kentta_fi "Työpaikkajakson kesto" :kentta_sv "Längd på arbetsplatsperiod" :kentta_en "Duration of work-based learning period"
    :raportointi {:csv {:raportoi true :jarjestys 14}}}
   {:kentta_id "oppisopimuksen_perusta"
    :kentta_fi "Oppisopimuksen perusta" :kentta_sv nil :kentta_en nil
    :raportointi {:csv {:raportoi true :jarjestys 15}}}
   {:kentta_id "tyopaikka_normalisoitu"
    :kentta_fi "Työpaikka" :kentta_sv "Arbetsplats" :kentta_en "Workplace"
    :raportointi nil}])

(def tyopaikkakysely-taustatiedot
  [{:kentta_id "tyonantaja"
    :kentta_fi "Työnantaja" :kentta_sv "Arbetsgivare" :kentta_en "Employer"
    :raportointi {:csv {:raportoi true :jarjestys 1}}}
   {:kentta_id "tyopaikka"
    :kentta_fi "Työpaikka" :kentta_sv "Arbetsplats" :kentta_en "Workplace"
    :raportointi {:csv {:raportoi true :jarjestys 2}}}
   {:kentta_id "tyopaikka_normalisoitu"
    :kentta_fi "Työpaikka" :kentta_sv "Arbetsplats" :kentta_en "Workplace"
    :raportointi nil}
   {:kentta_id "tiedonkeruu_alkupvm"
    :kentta_fi "Tiedonkeruun alkupvm" :kentta_sv "" :kentta_en ""
    :raportointi nil}
   {:kentta_id "tiedonkeruu_loppupvm"
    :kentta_fi "Tiedonkeruun päättymispvm" :kentta_sv "" :kentta_en ""
    :raportointi nil}])

(def kyselytyypit {:avop                           avop-taustatiedot
                   :kandipalaute                   kandipalaute-taustatiedot
                   :ammatillisen-opiskelijapalaute ammatillisen-opiskelijapalaute-taustatiedot
                   :tyopaikkaohjaajakysely         jakso-taustatiedot
                   :tyopaikkakysely                tyopaikkakysely-taustatiedot
                   :rekrykysely                    rekrykysely-taustatiedot
                   :move                           move-taustatiedot
                   :amk-uraseuranta                amk-uraseuranta-taustatiedot
                   :yo-uraseuranta                 yo-uraseuranta-taustatiedot
                   :itsearviointi                  itsearviointi-taustatiedot})
