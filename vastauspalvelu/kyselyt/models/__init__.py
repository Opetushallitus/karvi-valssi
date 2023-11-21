from .models_managed import Vastaaja, Vastaus, VastausSend, TempVastaus
from .models_unmanaged import (
    Kyselykerta, Kysely, Kayttaja, Kyselypohja, Vastaajatunnus, Tutkinto,
    Kysymys, Monivalintavaihtoehto, Kysymysryhma, TilaEnum, KyselyKysymysryhma, Organisaatio)


# to avoid pep8/F401 code
(
    Vastaaja, Vastaus, VastausSend, TempVastaus,
    Kyselykerta, Kysely, Kayttaja, Kyselypohja, Vastaajatunnus, Tutkinto, Kysymys, Monivalintavaihtoehto, Kysymysryhma,
    TilaEnum, KyselyKysymysryhma, Organisaatio)
