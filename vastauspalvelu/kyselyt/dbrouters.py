from kyselyt.models import (
    Vastaaja, Vastaus, VastausSend, TempVastaus,
    Kyselykerta, Kysely, Kayttaja, Kyselypohja, Vastaajatunnus, Tutkinto, Kysymys,
    Monivalintavaihtoehto, Kysymysryhma, TilaEnum, KyselyKysymysryhma, Organisaatio)


# managed
vastauspalvelu_models = (Vastaaja, Vastaus, VastausSend, TempVastaus)

# unmanaged
valssi_models = (
    Kyselykerta, Kysely, Kayttaja, Kyselypohja, Vastaajatunnus, Tutkinto, Kysymys,
    Monivalintavaihtoehto, Kysymysryhma, TilaEnum, KyselyKysymysryhma, Organisaatio)


class VastauspalveluRouter:
    def db_for_read(self, model, **hints):
        if model in vastauspalvelu_models:
            return "default"
        elif model in valssi_models:
            return "valssi"
        return None

    def db_for_write(self, model, **hints):
        if model in vastauspalvelu_models:
            return "default"
        elif model in valssi_models:
            return "valssi"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
