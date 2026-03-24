import logging


logger = logging.getLogger(__name__)


def create_indicators():
    from kyselyt.migrations.production.prod_indicators import INDICATORS
    from kyselyt.models import Indikaattori

    created_count = 0
    updated_count = 0
    for ind in INDICATORS:
        ind_values = dict(group_id=ind["group_id"], laatutekija=ind["laatutekija"], is_visible=ind["is_visible"])
        indikaattori_obj = Indikaattori.objects.filter(indicator_key=ind["key"])
        # create if key is missing, update if there is changes
        if not indikaattori_obj.exists():
            logger.info(f"Creating indicator: {ind['key']}")
            try:
                Indikaattori.objects.create(indicator_key=ind["key"], **ind_values)
                created_count += 1
            except Exception as e:
                logger.error(f"Error creating indicator: {ind['key']}. Error: {e}")
        elif not Indikaattori.objects.filter(indicator_key=ind["key"], **ind_values).exists():
            logger.info(f"Updating indicator: {ind['key']}")
            indikaattori_obj.update(**ind_values)
            updated_count += 1

    logger.info(f"Indicators created: {created_count}, updated: {updated_count}")


def create_scales():
    from kyselyt.migrations.production.prod_scales import SCALES
    from kyselyt.models import Scale

    created_count = 0
    updated_count = 0
    for scale in SCALES:
        scale_values = dict(
            order_no=scale["order_no"],
            label=scale["label"],
            min_value=scale["min_value"],
            max_value=scale["max_value"],
            default_value=scale["default_value"],
            step_count=scale["step_count"],
            scale=scale["scale"],
            eos_value=scale["eos_value"],
        )
        scale_obj = Scale.objects.filter(name=scale["name"])
        # create if name is missing, update if there is changes
        if not scale_obj.exists():
            Scale.objects.create(name=scale["name"], **scale_values)
            created_count += 1
        elif not scale_obj.filter(**scale_values).exists():
            scale_obj.update(**scale_values)
            updated_count += 1

    logger.info(f"Scales created: {created_count}, updated: {updated_count}")


def create_malfunction_messages():
    from kyselyt.models import MalfunctionMessage

    malf_messages = [
        # Virkailijapalvelu messages
        {"service": "virkailijapalvelu", "code": 1,
         "message": "Järjestelmässä on tilapäinen häiriö. / Det finns ett tillfälligt fel i systemet."},

        # Vastauspalvelu messages
        {"service": "vastauspalvelu", "code": 51,
         "message": "Järjestelmässä on tilapäinen häiriö. / Det finns ett tillfälligt fel i systemet."}
    ]

    created_count = 0
    updated_count = 0
    for malf_message in malf_messages:
        obj = MalfunctionMessage.objects.filter(code=malf_message["code"])
        # create if code is missing, update if there is changes
        if not obj.exists():
            MalfunctionMessage.objects.create(**malf_message)
            created_count += 1
        elif not MalfunctionMessage.objects.filter(**malf_message).exists():
            obj.update(**malf_message)
            updated_count += 1

    logger.info(f"MalfunctionMessages created: {created_count}, updated: {updated_count}")
