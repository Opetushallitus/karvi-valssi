from kyselyt.models import (
    UserAuthorization, ExternalServices, KyselySend, Indikaattori, Scale, MalfunctionMessage,
    Kyselykerta, Kysely, Kayttaja, Kyselypohja, Vastaajatunnus, Tutkinto, Vastaaja, Kysymys,
    Monivalintavaihtoehto, Kysymysryhma, TilaEnum, KyselyKysymysryhma, Organisaatio, Koodi)


# managed
virkailijapalvelu_models = (UserAuthorization, ExternalServices, KyselySend, Indikaattori, Scale, MalfunctionMessage)

# unmanaged
valssi_models = (
    Kyselykerta, Kysely, Kayttaja, Kyselypohja, Vastaajatunnus, Tutkinto, Vastaaja, Kysymys,
    Monivalintavaihtoehto, Kysymysryhma, TilaEnum, KyselyKysymysryhma, Organisaatio, Koodi)


class VirkailijapalveluRouter:
    def db_for_read(self, model, **hints):
        if model in virkailijapalvelu_models:
            return "default"
        elif model in valssi_models:
            return "valssi"
        return None

    def db_for_write(self, model, **hints):
        if model in virkailijapalvelu_models:
            return "default"
        elif model in valssi_models:
            return "valssi"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
