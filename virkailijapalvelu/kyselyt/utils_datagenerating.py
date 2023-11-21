import random
from datetime import datetime, timedelta
from typing import List

from django.conf import settings

from kyselyt.models import (
    Kyselykerta, Kysely, Kysymysryhma, Organisaatio, Indikaattori, Kayttaja, Kysymys, Scale, TilaEnum,
    KyselyKysymysryhma, Vastaajatunnus)
from kyselyt.utils import create_taustatiedot_data, fetch_vastaajatunnus_list

LOREMS = [
    ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Fusce laoreet rhoncus cursus. Donec pretium, justo non suscipit rutrum, lacus urna feugiat felis, nec sagittis dui turpis euismod dui. Donec nec faucibus lacus. Sed ac eros a neque venenatis aliquam. Aliquam erat volutpat. Proin mauris justo, porttitor sit amet tincidunt ut, euismod vitae mauris. Maecenas lacinia neque id quam ornare, et aliquam diam porttitor. In hac habitasse platea dictumst. In risus justo, laoreet eget accumsan et, vestibulum quis quam. Ut gravida hendrerit ante, et laoreet eros faucibus quis. Vestibulum sollicitudin iaculis nibh, vel bibendum ipsum lacinia sit amet. Proin tristique vulputate elit, vehicula posuere eros condimentum dapibus. Suspendisse ultrices ipsum in eros semper sollicitudin. " * 20).split(" "),
    ("Etiam tincidunt sapien placerat dignissim eleifend. Nullam dictum sapien in enim aliquet, nec bibendum elit fermentum. Duis porttitor tellus at ante condimentum pellentesque. Etiam justo arcu, tempus gravida felis ac, hendrerit ultrices nulla. Donec ac posuere turpis. Vivamus hendrerit vel ligula ac porta. Sed hendrerit eros lacus. Nulla faucibus nunc ut risus dictum laoreet. Phasellus ultrices, velit id volutpat cursus, ligula nisl porttitor nisi, eu sodales orci neque sit amet nunc. Donec sem velit, tincidunt in sollicitudin quis, pellentesque ut arcu. " * 20).split(" "),
    ("Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Aliquam sapien tellus, rhoncus pharetra sapien et, rhoncus ultrices ipsum. Suspendisse faucibus sem in arcu gravida, vitae suscipit sapien dapibus. Sed eu sem volutpat, aliquam nisi vel, vestibulum nunc. Phasellus sit amet quam ipsum. Duis bibendum venenatis nibh vitae lacinia. Nulla luctus ante erat, eu sodales elit pellentesque vitae. Nulla vitae cursus erat, nec pulvinar nibh. Aliquam leo odio, ultrices sed auctor nec, congue vitae arcu. Aliquam pulvinar diam at risus semper auctor. Sed ut dui id sem fermentum lacinia. In nec augue a nisi interdum pellentesque. Integer blandit posuere consequat. Duis imperdiet metus vestibulum odio maximus dignissim. " * 20).split(" "),
    ("Morbi non luctus metus. Aliquam velit erat, finibus at turpis id, varius accumsan velit. Duis lacinia, est vitae elementum venenatis, magna ligula sagittis nibh, sit amet fringilla ligula urna sed eros. Donec tellus mi, dapibus vitae nunc et, posuere luctus quam. Mauris eleifend porttitor orci, at finibus dolor sollicitudin eget. Mauris sed quam metus. Mauris purus est, mollis sit amet felis nec, maximus dapibus dolor. In vel lorem fermentum mi placerat consectetur et ut libero. Maecenas sit amet dui tincidunt ipsum malesuada porttitor. Nulla maximus porta tortor sed congue. Aenean a ipsum malesuada, condimentum ipsum a, varius lacus. Etiam luctus dui id pharetra eleifend. " * 20).split(" "),
    ("Integer nisl purus, ornare vel ipsum quis, scelerisque egestas odio. Curabitur scelerisque egestas vulputate. Nulla quis erat elit. Proin sodales nisl purus, in vestibulum sem convallis vel. Etiam in enim mattis, gravida dui in, suscipit odio. Pellentesque vestibulum, turpis id ullamcorper vehicula, felis ligula pharetra nisi, sit amet volutpat velit erat ut elit. In fringilla nulla ut enim eleifend pulvinar. Curabitur condimentum nisi at est sagittis accumsan. In vestibulum pulvinar feugiat. Aenean tincidunt lorem urna, a aliquam augue vestibulum non. Nullam ut ante quam. " * 20).split(" ")]

LOMAKETYYPIT = {
    1: "asiantuntijalomake_paakayttaja_prosessitekijat",
    2: "asiantuntijalomake_paivakoti_prosessitekijat",
    3: "henkilostolomake_prosessitekijat",
    4: "huoltajalomake_prosessitekijat",
    61: "asiantuntijalomake_paivakoti_rakennetekijat",
    62: "asiantuntijalomake_paakayttaja_rakennetekijat",
    7: "henkilostolomake_rakennetekijat",
    8: "huoltajalomake_rakennetekijat",
    91: "taydennyskoulutuslomake_rakennetekijat",
    92: "taydennyskoulutuslomake_paakayttaja_rakennetekijat"
}

DEFAULT_LOMAKETYYPPI = 3  # henkilostolomake_prosessitekijat
DEFAULT_PAAINDIKAATTORI = 1002  # pedagoginen_prosessi


def create_all(
        kayttaja_uid: str,  # YLLAPITAJA-username
        oppilaitos_oids: List[str],
        kysymysryhma_name: str = None,
        lomaketyyppi: int = DEFAULT_LOMAKETYYPPI,
        paaindikaattori_group_id: int = DEFAULT_PAAINDIKAATTORI,
        add_basic_fields: bool = False,
        add_matrix_radiobutton: bool = True,
        add_matrix_sliderscale: bool = False,
        matrix_scale_types: List[str] = [],
        only_basic_matrises: bool = False,
        matrix_count_per_scale_type: int = 1,
        voimassa_alkupvm: str = None,
        voimassa_loppupvm: str = None,
        vastaajatunnus_count: int = 10):
    if settings.PRODUCTION_ENV:
        print("NOT ALLOWED IN PRODUCTION.")
        return 0

    if not isinstance(oppilaitos_oids, list):
        print("Validation error: oppilaitos_oids is not list")
        return 0

    if not isinstance(matrix_scale_types, list):
        print("Validation error: matrix_scale_types is not list")
        return 0

    kysymysryhma_id = create_kysymysryhma_kysymykset(
        kayttaja_uid, kysymysryhma_name, lomaketyyppi, paaindikaattori_group_id, add_basic_fields,
        add_matrix_radiobutton, add_matrix_sliderscale, matrix_scale_types, only_basic_matrises,
        matrix_count_per_scale_type)
    if not kysymysryhma_id:
        return 0
    print("")

    voimassa_alkupvm_default = date_now()
    voimassa_loppupvm_default = date_now_plus_delta(delta_days=30)

    vt_tunnukset_all = []
    kyselykerrat_all = []
    kyselyt_all = []
    for oppilaitos_oid in oppilaitos_oids:
        kyselykerta_id, kysely_id = create_kysely_kyselykerta(
            kysymysryhma_id, oppilaitos_oid, voimassa_alkupvm_default, voimassa_loppupvm_default)
        if not kyselykerta_id:
            return 0
        kyselykerrat_all += [kyselykerta_id]
        kyselyt_all += [kysely_id]
        if vastaajatunnus_count:
            vt_tunnukset = create_vastaajatunnukset(
                kayttaja_uid, kyselykerta_id, vastaajatunnus_count,
                voimassa_alkupvm_default, voimassa_loppupvm_default)
            if not vt_tunnukset:
                return 0
            vt_tunnukset_all += vt_tunnukset
        print("")

    # set voimassa_alkupvm & voimassa_loppupvm to given
    set_voimassa_dates(voimassa_alkupvm, voimassa_loppupvm, kyselykerrat_all, kyselyt_all, vt_tunnukset_all)

    print("Kyselykerrat created:")
    print(kyselykerrat_all)


def create_kysymysryhma_kysymykset(
        kayttaja_uid: str,  # YLLAPITAJA-username
        kysymysryhma_name: str = None,
        lomaketyyppi: int = DEFAULT_LOMAKETYYPPI,
        paaindikaattori_group_id: int = DEFAULT_PAAINDIKAATTORI,
        add_basic_fields: bool = True,
        add_matrix_radiobutton: bool = True,
        add_matrix_sliderscale: bool = True,
        matrix_scale_types: List[str] = [],
        only_basic_matrises: bool = False,
        matrix_count_per_scale_type: int = 1):
    if settings.PRODUCTION_ENV:
        print("NOT ALLOWED IN PRODUCTION.")
        return 0

    field_kwargs = dict()
    if not add_basic_fields:
        field_kwargs["add_numberfield"] = False
        field_kwargs["add_textfield"] = False
        field_kwargs["add_textfield_multiline"] = False
        field_kwargs["add_intertitle_field"] = False
        field_kwargs["add_hidden_field"] = False
        field_kwargs["add_multioption_field"] = False

    kysymysryhma_id = create_kysymysryhma(
        kayttaja_uid, kysymysryhma_name, lomaketyyppi, paaindikaattori_group_id)
    if not kysymysryhma_id:
        return 0

    create_kysymykset(
        kysymysryhma_id,
        add_matrix_radiobutton=add_matrix_radiobutton,
        add_matrix_sliderscale=add_matrix_sliderscale,
        matrix_scale_types=matrix_scale_types,
        only_basic_matrises=only_basic_matrises,
        matrix_count_per_scale_type=matrix_count_per_scale_type,
        **field_kwargs)

    return kysymysryhma_id


def create_kysely_kyselykerta(
        kysymysryhma_id: int,
        oppilaitos_oid: str,
        voimassa_alkupvm: str,
        voimassa_loppupvm: str):
    kysymysryhma = Kysymysryhma.objects.filter(pk=kysymysryhma_id).first()
    if not kysymysryhma:
        print("Kysymysryhma not found.")
        return 0

    oppilaitos = Organisaatio.objects.filter(oid=oppilaitos_oid).first()
    if not oppilaitos:
        print("Oppilaitos not found.")
        return 0

    month_year = month_year_now()
    nimi_fi = f"{kysymysryhma.nimi_fi} {month_year} {oppilaitos.nimi_fi}"
    nimi_sv = f"{kysymysryhma.nimi_sv} {month_year} {oppilaitos.nimi_sv}"
    kayttaja = kysymysryhma.luotu_kayttaja
    lomaketyyppi = kysymysryhma.metatiedot["lomaketyyppi"]
    kysely = Kysely.objects.create(
        nimi_fi=nimi_fi, nimi_sv=nimi_sv,
        voimassa_alkupvm=voimassa_alkupvm, voimassa_loppupvm=voimassa_loppupvm,
        koulutustoimija=oppilaitos.parent_oid, oppilaitos=oppilaitos,
        luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja,
        tila=kysymysryhma.tila,
        sivutettu=False,
        tyyppi=lomaketyyppi,
        metatiedot=dict(
            valssi_saate=f"{random_lorem(30, 40)}\n\n{random_lorem(30, 40)}",
            esikatselu_tunniste="00000000" + random_hex(24),
            valssi_kysymysryhma=kysymysryhma.pk))

    KyselyKysymysryhma.objects.create(
        kyselyid=kysely, kysymysryhmaid=kysymysryhma, jarjestys=0,
        luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    taustatiedot = create_taustatiedot_data(None, oppilaitos.parent_oid.oid, oppilaitos_oid, lomaketyyppi)
    kyselykerta = Kyselykerta.objects.create(
        kyselyid=kysely, nimi=nimi_fi, lukittu=False,
        voimassa_alkupvm=voimassa_alkupvm, voimassa_loppupvm=voimassa_loppupvm,
        luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja,
        metatiedot=taustatiedot)

    print("Kysely, KyselyKysymysryhma & Kyselykerta created:")
    print(f"-- Oppilaitos:  {oppilaitos_oid} ({oppilaitos.nimi_fi})")
    print(f"-- Kysely:      {kysely.pk}")
    print(f"-- Kyselykerta: {kyselykerta.pk}")

    return kyselykerta.pk, kysely.pk


def create_vastaajatunnukset(kayttaja_uid: str, kyselykerta_id: int, vastaajatunnus_count: int,
                             voimassa_alkupvm: str, voimassa_loppupvm: str) -> List[str]:
    if settings.PRODUCTION_ENV:
        print("NOT ALLOWED IN PRODUCTION.")
        return 0

    kayttaja = Kayttaja.objects.filter(uid=kayttaja_uid).first()
    if not kayttaja:
        print("Kayttaja not found.")
        return 0

    kyselykerta = Kyselykerta.objects.filter(pk=kyselykerta_id).first()
    if not kyselykerta:
        print("Kyselykerta not found.")
        return 0

    vastaajatunnukset = fetch_vastaajatunnus_list(
        kyselykerta_id, kayttaja.oid, vastaajatunnus_count, 1,
        voimassa_alkupvm, voimassa_loppupvm)
    print(f"Vastaajatunnus list created: {vastaajatunnukset}")

    return vastaajatunnukset


def create_kysymysryhma(
        kayttaja_uid,
        name: str = None,
        lomaketyyppi: int = DEFAULT_LOMAKETYYPPI,
        paaindikaattori_group_id: int = DEFAULT_PAAINDIKAATTORI):
    if settings.PRODUCTION_ENV:
        print("NOT ALLOWED IN PRODUCTION.")
        return 0

    kayttaja = Kayttaja.objects.filter(uid=kayttaja_uid).first()
    if not kayttaja:
        print("Kayttaja not found.")
        return 0

    if lomaketyyppi not in LOMAKETYYPIT.keys():
        print("Lomaketyyppi not found.")
        return 0

    indikaattori = Indikaattori.objects.filter(group_id=paaindikaattori_group_id).first()
    if not indikaattori:
        print("Indikaattori not found.")
        return 0

    # check indikaattori laatutekija and lomaketyyppi matches
    if indikaattori.laatutekija not in LOMAKETYYPIT[lomaketyyppi]:
        print("Indikaattori.laatutekija and lomaketyyppi doesnt match.")
        return 0

    tila_julkaistu = TilaEnum.objects.filter(nimi="julkaistu").first()
    if not tila_julkaistu:
        print("TilaEnum 'julkaistu' not found.")
        return 0

    kysymysryhma_name = f"Lomake {random_lorem(3, 5)}" if name is None else name
    kysymysryhma_name += f" (generated {date_now()} {random_hex()})"

    kysymysryhma = Kysymysryhma.objects.create(
        nimi_fi=kysymysryhma_name, nimi_sv=f"SV {kysymysryhma_name}",
        luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja,
        taustakysymykset=False, valtakunnallinen=True,
        tila=tila_julkaistu,
        metatiedot=dict(
            lomaketyyppi=LOMAKETYYPIT[lomaketyyppi],
            paaIndikaattori=dict(
                key=indikaattori.key,
                group=indikaattori.group_id
            ),
            sekondaariset_indikaattorit=[]
        ))

    print("Kysymysryhma created:")
    print(f"-- Id: {kysymysryhma.pk}")
    print(f"-- Name: {kysymysryhma.nimi_fi}", end="\n\n")

    return kysymysryhma.pk


def create_kysymykset(
        kysymysryhma_id: int,
        add_numberfield: bool = True,
        add_textfield: bool = True,
        add_textfield_multiline: bool = True,
        add_intertitle_field: bool = True,
        add_hidden_field: bool = True,
        add_multioption_field: bool = True,
        add_matrix_radiobutton: bool = True,
        add_matrix_sliderscale: bool = True,
        matrix_scale_types: List[str] = [],
        only_basic_matrises: bool = False,
        matrix_count_per_scale_type: int = 1):
    if settings.PRODUCTION_ENV:
        print("NOT ALLOWED IN PRODUCTION.")
        return 0

    kysymysryhma = Kysymysryhma.objects.filter(pk=kysymysryhma_id).first()
    if not kysymysryhma:
        print("Kysymysryhma not found.")
        return 0

    kayttaja = kysymysryhma.luotu_kayttaja
    kysymys_kwargs = dict(kysymysryhmaid=kysymysryhma, poistettava=False, jatkokysymys=False,
                          raportoitava=True, luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    jarjestys = 0

    jarjestys = create_basic_questions(
        jarjestys, add_numberfield, add_textfield, add_textfield_multiline,
        add_intertitle_field, add_hidden_field, add_multioption_field, kysymys_kwargs)

    jarjestys = create_matrix_questions(
        jarjestys, add_matrix_radiobutton, add_matrix_sliderscale,
        matrix_scale_types, only_basic_matrises, matrix_count_per_scale_type, kysymys_kwargs)

    print("All questions added.")


def create_basic_questions(
        jarjestys: int,
        add_numberfield: bool,
        add_textfield: bool,
        add_textfield_multiline: bool,
        add_intertitle_field: bool,
        add_hidden_field: bool,
        add_multioption_field: bool,
        kysymys_kwargs: dict):
    if add_numberfield:
        jarjestys = create_numberfield_questions(jarjestys, kysymys_kwargs)
        print("Numberfield questions added.")

    if add_textfield:
        jarjestys = create_textfield_questions(jarjestys, kysymys_kwargs)
        print("Textfield questions added.")

    if add_textfield_multiline:
        jarjestys = create_textfield_multiline_questions(jarjestys, kysymys_kwargs)
        print("Multiline textfield questions added.")

    if add_intertitle_field:
        jarjestys = create_intertitle_field(jarjestys, kysymys_kwargs)
        print("Intertitle added.")

    if add_hidden_field:
        jarjestys = create_hidden_field(jarjestys, kysymys_kwargs)
        print("Hidden field added.")

    if add_multioption_field:
        jarjestys = create_multioption_questions(jarjestys, kysymys_kwargs)
        print("Multioption questions added.")

    return jarjestys


def create_matrix_questions(
        jarjestys: int,
        add_matrix_radiobutton: bool,
        add_matrix_sliderscale: bool,
        matrix_scale_types: List[str],
        only_basic_matrises: bool,
        matrix_count_per_scale_type: int,
        kysymys_kwargs: dict):
    scales = get_scales()
    if add_matrix_radiobutton:
        for scale in scales:
            if matrix_scale_types and scale.name not in matrix_scale_types:
                continue
            for i in range(matrix_count_per_scale_type):
                jarjestys = create_matrix_questions_by_type(
                    jarjestys, kysymys_kwargs, scale, "matrix_radiobutton", only_basic_matrises)
        print("Matrix radiobutton questions added.")

    if add_matrix_sliderscale:
        for scale in scales:
            if matrix_scale_types and scale.name not in matrix_scale_types:
                continue
            for i in range(matrix_count_per_scale_type):
                jarjestys = create_matrix_questions_by_type(
                    jarjestys, kysymys_kwargs, scale, "matrix_sliderscale", only_basic_matrises)
        print("Matrix sliderbutton questions added.")

    return jarjestys


def create_numberfield_questions(jarjestys: int, kysymys_kwargs: dict):
    # numberfield question
    kysymys_name = f"Numerokenttä {random_lorem()} ({random_hex()})?"
    description = f"{random_lorem(10, 18)}"
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=False, vastaustyyppi="string",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "string", "numeric": True, "multiline": False,
                    "description": {"fi": description, "sv": f"SV {description}"}})
    jarjestys += 1

    # numberfield question (mandatory)
    kysymys_name = f"Numerokenttä {random_lorem()} ({random_hex()})?"
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=True, vastaustyyppi="string",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "string", "numeric": True, "multiline": False, "description": {"fi": "", "sv": ""}})
    jarjestys += 1

    return jarjestys


def create_textfield_questions(jarjestys: int, kysymys_kwargs: dict):
    # textfield question
    kysymys_name = f"Tekstikenttä {random_lorem()} ({random_hex()})?"
    description = f"{random_lorem(10, 18)}"
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=False, vastaustyyppi="string",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "string", "numeric": False, "multiline": False,
                    "description": {"fi": description, "sv": f"SV {description}"}})
    jarjestys += 1

    # textfield question (mandatory)
    kysymys_name = f"Tekstikenttä {random_lorem()} ({random_hex()})?"
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=True, vastaustyyppi="string",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "string", "numeric": False, "multiline": False, "description": {"fi": "", "sv": ""}})
    jarjestys += 1

    return jarjestys


def create_textfield_multiline_questions(jarjestys: int, kysymys_kwargs: dict):
    # textfield multiline question
    kysymys_name = f"Monirivinen tekstikenttä {random_lorem()} ({random_hex()})?"
    description = f"{random_lorem(10, 18)}"
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=False, vastaustyyppi="string",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "string", "numeric": False, "multiline": True,
                    "description": {"fi": description, "sv": f"SV {description}"}})
    jarjestys += 1

    # textfield multiline question (mandatory)
    kysymys_name = f"Monirivinen tekstikenttä {random_lorem()} ({random_hex()})?"
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=True, vastaustyyppi="string",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "string", "numeric": False, "multiline": True, "description": {"fi": "", "sv": ""}})
    jarjestys += 1

    return jarjestys


def create_intertitle_field(jarjestys: int, kysymys_kwargs: dict):
    # intertitle (väliotsikko)
    kysymys_name = f"Väliotsikko {random_lorem(4, 8)} ({random_hex()})?"
    description = f"{random_lorem(10, 18)}\n{random_lorem(10, 18)}\n\n{random_lorem(10, 18)}"
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=False, vastaustyyppi="string",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "statictext", "hidden": False,
                    "description": {"fi": description, "sv": f"SV {description}"}})
    jarjestys += 1

    return jarjestys


def create_hidden_field(jarjestys: int, kysymys_kwargs: dict):
    # hidden intertitle (väliotsikko)
    kysymys_name = "TÄMÄ ON PIILOTETTU, EI TULISI NÄKYÄ"
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=False, vastaustyyppi="string",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "statictext", "hidden": True, "description": {"fi": "", "sv": ""}})
    jarjestys += 1

    return jarjestys


def create_multioption_questions(jarjestys: int, kysymys_kwargs: dict):
    # multi-option field (1-choose)
    kysymys_name = f"Monivalinta-1 {random_lorem(4, 8)} ({random_hex()})?"
    description = f"{random_lorem(10, 18)}"
    description_vve = f"{random_lorem(10, 18)}"
    vastausvaihtoehdot = [
        {"id": i, "title": {"fi": f"vaihtoehto {i}", "sv": f"sv vaihtoehto {i}"}, "checked": False,
            "description": {"fi": "", "sv": ""}} for i in range(1, 4)]
    vastausvaihtoehdot[0]["description"] = {"fi": description_vve, "sv": f"SV {description_vve}"}
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=False, vastaustyyppi="monivalinta",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "radiobutton", "hidden": False,
                    "description": {"fi": description, "sv": f"SV {description}"},
                    "vastausvaihtoehdot": vastausvaihtoehdot})
    jarjestys += 1

    # multi-option field (1-choose) (mandatory)
    kysymys_name = f"Monivalinta-1 {random_lorem(4, 8)} ({random_hex()})?"
    vastausvaihtoehdot = [
        {"id": i, "title": {"fi": f"vaihtoehto {i}", "sv": f"sv vaihtoehto {i}"}, "checked": False,
            "description": {"fi": "", "sv": ""}} for i in range(1, 4)]
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=True, vastaustyyppi="monivalinta",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "radiobutton", "hidden": False,
                    "description": {"fi": "", "sv": ""},
                    "vastausvaihtoehdot": vastausvaihtoehdot})
    jarjestys += 1

    # multi-option field (multi-choose)
    kysymys_name = f"Monivalinta-n {random_lorem(4, 8)} ({random_hex()})?"
    description = f"{random_lorem(10, 18)}"
    description_vve = f"{random_lorem(10, 18)}"
    vastausvaihtoehdot = [
        {"id": i, "title": {"fi": f"vaihtoehto {i}", "sv": f"sv vaihtoehto {i}"}, "checked": False,
            "description": {"fi": "", "sv": ""}} for i in range(1, 4)]
    vastausvaihtoehdot[0]["description"] = {"fi": description_vve, "sv": f"SV {description_vve}"}
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=False, vastaustyyppi="monivalinta",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "checkbox", "hidden": False,
                    "description": {"fi": description, "sv": f"SV {description}"},
                    "vastausvaihtoehdot": vastausvaihtoehdot})
    jarjestys += 1

    # multi-option field (multi-choose) (mandatory)
    kysymys_name = f"Monivalinta-n {random_lorem(4, 8)} ({random_hex()})?"
    vastausvaihtoehdot = [
        {"id": i, "title": {"fi": f"vaihtoehto {i}", "sv": f"sv vaihtoehto {i}"}, "checked": False,
            "description": {"fi": "", "sv": ""}} for i in range(1, 4)]
    Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=True, vastaustyyppi="monivalinta",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={"type": "checkbox", "hidden": False,
                    "description": {"fi": "", "sv": ""},
                    "vastausvaihtoehdot": vastausvaihtoehdot})
    jarjestys += 1

    return jarjestys


def create_matrix_questions_by_type(
        jarjestys: int, kysymys_kwargs: dict, scale: Scale, matrix_type: str,
        only_basic_matrix: bool = False) -> int:
    # matrix
    kysymys_name = f"{matrix_type.title()} {random_lorem(4, 8)} ({random_hex()})?"
    description = f"{random_lorem(8, 14)}"
    kysymys_root = Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=False, vastaustyyppi="matrix_root",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        matriisi_jarjestys=0,
        metatiedot={"type": matrix_type,
                    "description": {"fi": description, "sv": f"SV {description}"}})
    Kysymys.objects.filter(pk=kysymys_root.pk).update(matriisi_kysymysid=kysymys_root.pk)
    for i in range(3):
        kysymys_name = f"MS {random_lorem(4, 8)} ({random_hex()})"
        description = f"{random_lorem(8, 14)}"
        Kysymys.objects.create(
            jarjestys=jarjestys,
            pakollinen=False, vastaustyyppi=scale.name,
            kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
            eos_vastaus_sallittu=False, **kysymys_kwargs,
            matriisi_kysymysid=kysymys_root.pk,
            matriisi_jarjestys=i + 1,
            metatiedot={"type": matrix_type,
                        "description": {"fi": description, "sv": f"SV {description}"}})
    jarjestys += 1

    if only_basic_matrix:
        return jarjestys

    # matrix (mandatory)
    kysymys_name = f"{matrix_type.title()} {random_lorem(4, 8)} ({random_hex()})?"
    kysymys_root = Kysymys.objects.create(
        jarjestys=jarjestys,
        pakollinen=True, vastaustyyppi="matrix_root",
        kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
        eos_vastaus_sallittu=False, **kysymys_kwargs,
        matriisi_jarjestys=0,
        metatiedot={"type": matrix_type, "description": {"fi": "", "sv": ""}})
    Kysymys.objects.filter(pk=kysymys_root.pk).update(matriisi_kysymysid=kysymys_root.pk)
    for i in range(3):
        kysymys_name = f"MS {random_lorem(4, 8)} ({random_hex()})"
        Kysymys.objects.create(
            jarjestys=jarjestys,
            pakollinen=True, vastaustyyppi=scale.name,
            kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
            eos_vastaus_sallittu=False, **kysymys_kwargs,
            matriisi_kysymysid=kysymys_root.pk,
            matriisi_jarjestys=i + 1,
            metatiedot={"type": matrix_type, "description": {"fi": "", "sv": ""}})
    jarjestys += 1

    # matrix (eos)
    if scale.eos_allowed:
        kysymys_name = f"{matrix_type.title()} {random_lorem(4, 8)} ({random_hex()})?"
        kysymys_root = Kysymys.objects.create(
            jarjestys=jarjestys,
            pakollinen=True, vastaustyyppi="matrix_root",
            kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
            eos_vastaus_sallittu=True, **kysymys_kwargs,
            matriisi_jarjestys=0,
            metatiedot={"type": matrix_type, "description": {"fi": "", "sv": ""}})
        Kysymys.objects.filter(pk=kysymys_root.pk).update(matriisi_kysymysid=kysymys_root.pk)
        for i in range(3):
            kysymys_name = f"MS {random_lorem(4, 8)} ({random_hex()})"
            Kysymys.objects.create(
                jarjestys=jarjestys,
                pakollinen=True, vastaustyyppi=scale.name,
                kysymys_fi=kysymys_name, kysymys_sv=f"SV {kysymys_name}",
                eos_vastaus_sallittu=True, **kysymys_kwargs,
                matriisi_kysymysid=kysymys_root.pk,
                matriisi_jarjestys=i + 1,
                metatiedot={"type": matrix_type, "description": {"fi": "", "sv": ""}})
        jarjestys += 1

    return jarjestys


def set_voimassa_dates(voimassa_alkupvm, voimassa_loppupvm, kyselykerta_ids, kysely_ids, vt_tunnukset_all):
    if voimassa_alkupvm:
        Kyselykerta.objects.filter(pk__in=kyselykerta_ids).update(voimassa_alkupvm=voimassa_alkupvm)
        Kysely.objects.filter(pk__in=kysely_ids).update(voimassa_alkupvm=voimassa_alkupvm)
        Vastaajatunnus.objects.filter(tunnus__in=vt_tunnukset_all).update(voimassa_alkupvm=voimassa_alkupvm)
    if voimassa_loppupvm:
        Kyselykerta.objects.filter(pk__in=kyselykerta_ids).update(voimassa_loppupvm=voimassa_loppupvm)
        Kysely.objects.filter(pk__in=kysely_ids).update(voimassa_loppupvm=voimassa_loppupvm)
        Vastaajatunnus.objects.filter(tunnus__in=vt_tunnukset_all).update(voimassa_loppupvm=voimassa_loppupvm)


def random_hex(N: int = 4):
    return "".join(random.choices("0123456789abcdef", k=N))


def random_lorem(min_words: int = 4, max_words: int = 12):
    lorem_rnd = random.choice(LOREMS)
    word_count = random.randint(min_words, max_words)
    return " ".join(lorem_rnd[:word_count])


def date_now():
    return datetime.strftime(datetime.now(), "%Y-%m-%d")


def date_now_plus_delta(delta_days: int = 1):
    return datetime.strftime(datetime.now() + timedelta(days=delta_days), "%Y-%m-%d")


def month_year_now():
    return datetime.strftime(datetime.now(), "%-m/%Y")


def get_scales():
    return Scale.objects.filter(is_visible=True).order_by("order_no")
