from raportointi.models import (
    ExternalServices, Kyselykerta, Kysely, Kayttaja, Kyselypohja, KyselySend, Vastaus, Vastaaja,
    Vastaajatunnus, Tutkinto, Kysymys, Monivalintavaihtoehto, Kysymysryhma, TilaEnum, KyselyKysymysryhma,
    Organisaatio, ReportingTemplate, ReportingTemplateHelptext, Scale, Koodi, Summary, Result, UserAuthorization,
    Indikaattori)


# unmanaged valssi
valssi_models = (
    Kyselykerta, Kysely, Kayttaja, Kyselypohja, Vastaajatunnus, Tutkinto, Kysymys,
    Monivalintavaihtoehto, Kysymysryhma, TilaEnum, KyselyKysymysryhma, Organisaatio, Koodi)

# unmanaged vastauspalvelu
vastauspalvelu_models = (Vastaus, Vastaaja)

# unmanaged virkailijapalvelu
virkailijapalvelu_models = (KyselySend, Scale, UserAuthorization, Indikaattori)

# managed raportointipalvelu
raportointipalvelu_models = (
    ExternalServices, ReportingTemplate, ReportingTemplateHelptext, Summary, Result)


class RaportointipalveluRouter:
    def db_for_read(self, model, **hints):
        if model in raportointipalvelu_models:
            return "default"
        elif model in valssi_models:
            return "valssi"
        elif model in vastauspalvelu_models:
            return "vastauspalvelu"
        elif model in virkailijapalvelu_models:
            return "virkailijapalvelu"
        return None

    def db_for_write(self, model, **hints):
        if model in raportointipalvelu_models:
            return "default"
        elif model in valssi_models:
            return "valssi"
        elif model in vastauspalvelu_models:
            return "vastauspalvelu"
        elif model in virkailijapalvelu_models:
            return "virkailijapalvelu"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
