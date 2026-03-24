EOS_VALUE_EKR = {
    "fi": "ei koske ryhmääni",
    "sv": "gäller inte min grupp",
    "en": "does not apply to my group",
    "value": 0
}
EOS_VALUE_EKM = {
    "fi": "ei koske minua",
    "sv": "gäller inte mig",
    "en": "does not apply to me",
    "value": 0
}
EOS_VALUE_EOS = {
    "fi": "en osaa sanoa",
    "sv": "jag kan inte säga",
    "en": "I can't say",
    "value": 0
}

TEST_SCALES = [
    {
        "name": "toteutuu-asteikko",
        "order_no": 1,
        "label": {
            "fi": "Toteutuu-asteikko",
            "sv": "Genomförs skala",
            "en": "Is implemented -scale"
        },
        "min_value": 1,
        "max_value": 5,
        "default_value": 3,
        "step_count": 5,
        "scale": [
            {
                "fi": "toteutuu erittäin heikosti",
                "sv": "genomförs mycket dåligt",
                "en": "is implemented very poorly",
                "value": 1
            },
            {
                "fi": "toteutuu heikosti",
                "sv": "genomförs dåligt",
                "en": "is implemented poorly",
                "value": 2
            },
            {
                "fi": "toteutuu kohtalaisesti",
                "sv": "genomförs någorlunda",
                "en": "is implemented moderately",
                "value": 3
            },
            {
                "fi": "toteutuu hyvin",
                "sv": "genomförs väl",
                "en": "is implemented well",
                "value": 4
            },
            {
                "fi": "toteutuu erittäin hyvin",
                "sv": "genomförs mycket väl",
                "en": "is implemented very well",
                "value": 5
            }
        ],
        "eos_value": EOS_VALUE_EKR
    },
    {
        "name": "toteutuu_ekm",
        "order_no": 2,
        "label": {
            "fi": "Toteutuu EKM",
            "sv": "Genomförs GIM",
            "en": "Implemented DNA"
        },
        "min_value": 1,
        "max_value": 5,
        "default_value": 3,
        "step_count": 5,
        "scale": [
            {
                "fi": "toteutuu erittäin heikosti",
                "sv": "genomförs mycket dåligt",
                "en": "is implemented very poorly",
                "value": 1
            },
            {
                "fi": "toteutuu heikosti",
                "sv": "genomförs dåligt",
                "en": "is implemented poorly",
                "value": 2
            },
            {
                "fi": "toteutuu kohtalaisesti",
                "sv": "genomförs någorlunda",
                "en": "is implemented moderately",
                "value": 3
            },
            {
                "fi": "toteutuu hyvin",
                "sv": "genomförs väl",
                "en": "is implemented well",
                "value": 4
            },
            {
                "fi": "toteutuu erittäin hyvin",
                "sv": "genomförs mycket väl",
                "en": "is implemented very well",
                "value": 5
            }
        ],
        "eos_value": EOS_VALUE_EKM
    },
    {
        "name": "toteutuu_eos",
        "order_no": 3,
        "label": {
            "fi": "Toteutuu EOS",
            "sv": "Genomförs KIS",
            "en": "Implemented ICS"
        },
        "min_value": 1,
        "max_value": 5,
        "default_value": 3,
        "step_count": 5,
        "scale": [
            {
                "fi": "toteutuu erittäin heikosti",
                "sv": "genomförs mycket dåligt",
                "en": "is implemented very poorly",
                "value": 1
            },
            {
                "fi": "toteutuu heikosti",
                "sv": "genomförs dåligt",
                "en": "is implemented poorly",
                "value": 2
            },
            {
                "fi": "toteutuu kohtalaisesti",
                "sv": "genomförs någorlunda",
                "en": "is implemented moderately",
                "value": 3
            },
            {
                "fi": "toteutuu hyvin",
                "sv": "genomförs väl",
                "en": "is implemented well",
                "value": 4
            },
            {
                "fi": "toteutuu erittäin hyvin",
                "sv": "genomförs mycket väl",
                "en": "is implemented very well",
                "value": 5
            }
        ],
        "eos_value": EOS_VALUE_EOS
    },
    {
        "name": "kuinka_usein_6",
        "order_no": 4,
        "label": {
            "fi": "Kuinka usein 6",
            "sv": "Hur ofta 6",
            "en": "How often 6"
        },
        "min_value": 1,
        "max_value": 6,
        "default_value": 3,
        "step_count": 6,
        "scale": [
            {
                "fi": "harvemmin kuin kerran kuukaudessa",
                "sv": "mer sällan än en gång i månaden",
                "en": "less than once a month",
                "value": 1
            },
            {
                "fi": "kerran kuukaudessa",
                "sv": "en gång i månaden",
                "en": "once a month",
                "value": 2
            },
            {
                "fi": "2-3 kertaa kuukaudessa",
                "sv": "2-3 gånger i månaden",
                "en": "2-3 times a month",
                "value": 3
            },
            {
                "fi": "kerran viikossa",
                "sv": "en gång i veckan",
                "en": "once a week",
                "value": 4
            },
            {
                "fi": "2-3 kertaa viikossa",
                "sv": "2-3 gånger i veckan",
                "en": "2-3 times a week",
                "value": 5
            },
            {
                "fi": "päivittäin",
                "sv": "dagligen",
                "en": "daily",
                "value": 6
            }
        ],
        "eos_value": EOS_VALUE_EKR
    },
    {
        "name": "kuinka_usein_6_eos",
        "order_no": 5,
        "label": {
            "fi": "Kuinka usein 6 EOS",
            "sv": "Hur ofta 6 KIS",
            "en": "How often 6 ICS"
        },
        "min_value": 1,
        "max_value": 6,
        "default_value": 3,
        "step_count": 6,
        "scale": [
            {
                "fi": "harvemmin kuin kerran kuukaudessa",
                "sv": "mer sällan än en gång i månaden",
                "en": "less than once a month",
                "value": 1
            },
            {
                "fi": "kerran kuukaudessa",
                "sv": "en gång i månaden",
                "en": "once a month",
                "value": 2
            },
            {
                "fi": "2-3 kertaa kuukaudessa",
                "sv": "2-3 gånger i månaden",
                "en": "2-3 times a month",
                "value": 3
            },
            {
                "fi": "kerran viikossa",
                "sv": "en gång i veckan",
                "en": "once a week",
                "value": 4
            },
            {
                "fi": "2-3 kertaa viikossa",
                "sv": "2-3 gånger i veckan",
                "en": "2-3 times a week",
                "value": 5
            },
            {
                "fi": "päivittäin",
                "sv": "dagligen",
                "en": "daily",
                "value": 6
            }
        ],
        "eos_value": EOS_VALUE_EOS
    },
    {
        "name": "kuinka_usein_5",
        "order_no": 6,
        "label": {
            "fi": "Kuinka usein 5",
            "sv": "Hur ofta 5",
            "en": "How often 5"
        },
        "min_value": 1,
        "max_value": 5,
        "default_value": 3,
        "step_count": 5,
        "scale": [
            {
                "fi": "ei koskaan",
                "sv": "aldrig",
                "en": "never",
                "value": 1
            },
            {
                "fi": "harvemmin kuin kerran kuukaudessa",
                "sv": "mer sällan än en gång i månaden",
                "en": "less than once a month",
                "value": 2
            },
            {
                "fi": "kuukausittain",
                "sv": "varje månad",
                "en": "monthly",
                "value": 3
            },
            {
                "fi": "viikoittain",
                "sv": "varje vecka",
                "en": "weekly",
                "value": 4
            },
            {
                "fi": "päivittäin",
                "sv": "dagligen",
                "en": "daily",
                "value": 5
            }
        ],
        "eos_value": EOS_VALUE_EKR
    },
    {
        "name": "kuinka_usein_5_eos",
        "order_no": 7,
        "label": {
            "fi": "Kuinka usein 5 EOS",
            "sv": "Hur ofta 5 KIS",
            "en": "How often 5 ICS"
        },
        "min_value": 1,
        "max_value": 5,
        "default_value": 3,
        "step_count": 5,
        "scale": [
            {
                "fi": "ei koskaan",
                "sv": "aldrig",
                "en": "never",
                "value": 1
            },
            {
                "fi": "harvemmin kuin kerran kuukaudessa",
                "sv": "mer sällan än en gång i månaden",
                "en": "less than once a month",
                "value": 2
            },
            {
                "fi": "kuukausittain",
                "sv": "varje månad",
                "en": "monthly",
                "value": 3
            },
            {
                "fi": "viikoittain",
                "sv": "varje vecka",
                "en": "weekly",
                "value": 4
            },
            {
                "fi": "päivittäin",
                "sv": "dagligen",
                "en": "daily",
                "value": 5
            }
        ],
        "eos_value": EOS_VALUE_EOS
    },
    {
        "name": "kylla_ei_valinta",
        "order_no": 8,
        "label": {
            "fi": "Kyllä-ei",
            "sv": "Ja-nej",
            "en": "Yes-no"
        },
        "min_value": 1,
        "max_value": 2,
        "default_value": 1,
        "step_count": 2,
        "scale": [
            {
                "fi": "ei",
                "sv": "nej",
                "en": "no",
                "value": 1
            },
            {
                "fi": "kyllä",
                "sv": "ja",
                "en": "yes",
                "value": 2
            }
        ],
        "eos_value": EOS_VALUE_EKR
    },
    {
        "name": "kylla_ei_valinta_eos",
        "order_no": 9,
        "label": {
            "fi": "Kyllä-ei EOS",
            "sv": "Ja-nej KIS",
            "en": "Yes-no ICS"
        },
        "min_value": 1,
        "max_value": 2,
        "default_value": 1,
        "step_count": 2,
        "scale": [
            {
                "fi": "ei",
                "sv": "nej",
                "en": "no",
                "value": 1
            },
            {
                "fi": "kyllä",
                "sv": "ja",
                "en": "yes",
                "value": 2
            }
        ],
        "eos_value": EOS_VALUE_EOS
    },
    {
        "name": "olen_lukenut",
        "order_no": 10,
        "label": {
            "fi": "Olen lukenut",
            "sv": "Jag har läst",
            "en": "I have read"
        },
        "min_value": 1,
        "max_value": 3,
        "default_value": 2,
        "step_count": 3,
        "scale": [
            {
                "fi": "en ole lukenut",
                "sv": "jag har inte läst",
                "en": "I have not read",
                "value": 1
            },
            {
                "fi": "olen lukenut osittain",
                "sv": "jag har läst delvis",
                "en": "I have read partly",
                "value": 2
            },
            {
                "fi": "olen lukenut kokonaan",
                "sv": "jag har läst i sin helhet",
                "en": "I have read completely",
                "value": 3
            }
        ],
        "eos_value": EOS_VALUE_EKM
    },
    {
        "name": "olen_lukenut_eos",
        "order_no": 11,
        "label": {
            "fi": "Olen lukenut EOS",
            "sv": "Jag har läst KIS",
            "en": "I have read ICS"
        },
        "min_value": 1,
        "max_value": 3,
        "default_value": 2,
        "step_count": 3,
        "scale": [
            {
                "fi": "en ole lukenut",
                "sv": "jag har inte läst",
                "en": "I have not read",
                "value": 1
            },
            {
                "fi": "olen lukenut osittain",
                "sv": "jag har läst delvis",
                "en": "I have read partly",
                "value": 2
            },
            {
                "fi": "olen lukenut kokonaan",
                "sv": "jag har läst i sin helhet",
                "en": "I have read completely",
                "value": 3
            }
        ],
        "eos_value": EOS_VALUE_EOS
    },
    {
        "name": "likert_asteikko",
        "order_no": 12,
        "label": {
            "fi": "Likert-asteikko",
            "sv": "Likertskala",
            "en": "Likert-scale"
        },
        "min_value": 1,
        "max_value": 5,
        "default_value": 3,
        "step_count": 5,
        "scale": [
            {
                "fi": "täysin eri mieltä",
                "sv": "helt av annan åsikt",
                "en": "strongly disagree",
                "value": 1
            },
            {
                "fi": "jokseenkin eri mieltä",
                "sv": "delvis av annan åsikt",
                "en": "somewhat disagree",
                "value": 2
            },
            {
                "fi": "ei eri eikä samaa mieltä",
                "sv": "varken av annan eller av samma åsikt",
                "en": "neither agree nor disagree",
                "value": 3
            },
            {
                "fi": "jokseenkin samaa mieltä",
                "sv": "delvis av samma åsikt",
                "en": "somewhat agree",
                "value": 4
            },
            {
                "fi": "täysin samaa mieltä",
                "sv": "helt av samma åsikt",
                "en": "strongly agree",
                "value": 5
            }
        ],
        "eos_value": EOS_VALUE_EKR
    },
    {
        "name": "likert_ekm",
        "order_no": 13,
        "label": {
            "fi": "Likert-asteikko EKM",
            "sv": "Likertskala GIM",
            "en": "Likert-scale DNA",
        },
        "min_value": 1,
        "max_value": 5,
        "default_value": 3,
        "step_count": 5,
        "scale": [
            {
                "fi": "täysin eri mieltä",
                "sv": "helt av annan åsikt",
                "en": "strongly disagree",
                "value": 1
            },
            {
                "fi": "jokseenkin eri mieltä",
                "sv": "delvis av annan åsikt",
                "en": "somewhat disagree",
                "value": 2
            },
            {
                "fi": "ei eri eikä samaa mieltä",
                "sv": "varken av annan eller av samma åsikt",
                "en": "neither agree nor disagree",
                "value": 3
            },
            {
                "fi": "jokseenkin samaa mieltä",
                "sv": "delvis av samma åsikt",
                "en": "somewhat agree",
                "value": 4
            },
            {
                "fi": "täysin samaa mieltä",
                "sv": "helt av samma åsikt",
                "en": "strongly agree",
                "value": 5
            }
        ],
        "eos_value": EOS_VALUE_EKM
    },
    {
        "name": "likert_eos",
        "order_no": 14,
        "label": {
            "fi": "Likert-asteikko EOS",
            "sv": "Likertskala KIS",
            "en": "Likert-scale ICS"
        },
        "min_value": 1,
        "max_value": 5,
        "default_value": 3,
        "step_count": 5,
        "scale": [
            {
                "fi": "täysin eri mieltä",
                "sv": "helt av annan åsikt",
                "en": "strongly disagree",
                "value": 1
            },
            {
                "fi": "jokseenkin eri mieltä",
                "sv": "delvis av annan åsikt",
                "en": "somewhat disagree",
                "value": 2
            },
            {
                "fi": "ei eri eikä samaa mieltä",
                "sv": "varken av annan eller av samma åsikt",
                "en": "neither agree nor disagree",
                "value": 3
            },
            {
                "fi": "jokseenkin samaa mieltä",
                "sv": "delvis av samma åsikt",
                "en": "somewhat agree",
                "value": 4
            },
            {
                "fi": "täysin samaa mieltä",
                "sv": "helt av samma åsikt",
                "en": "strongly agree",
                "value": 5
            }
        ],
        "eos_value": EOS_VALUE_EOS
    },
    {
        "name": "toteutuminen",
        "order_no": 15,
        "label": {
            "fi": "Toteutuminen",
            "sv": "Förverkligas",
            "en": "Implementation"
        },
        "min_value": 1,
        "max_value": 4,
        "default_value": 2,
        "step_count": 4,
        "scale": [
            {
                "fi": "ei toteudu",
                "sv": "genomförs inte",
                "en": "not implemented",
                "value": 1
            },
            {
                "fi": "toteutuu osittain",
                "sv": "genomförs delvis",
                "en": "partially implemented",
                "value": 2
            },
            {
                "fi": "toteutuu kokonaan",
                "sv": "genomförs helt",
                "en": "fully implemented",
                "value": 3
            },
            {
                "fi": "ei koske kuntaamme",
                "sv": "gäller inte vår kommun",
                "en": "does not apply to our municipality",
                "value": 4
            }
        ],
        "eos_value": EOS_VALUE_EKR
    },
    {
        "name": "toteutuminen_eos",
        "order_no": 16,
        "label": {
            "fi": "Toteutuminen EOS",
            "sv": "Förverkligas KIS",
            "en": "Implementation ICS"
        },
        "min_value": 1,
        "max_value": 4,
        "default_value": 2,
        "step_count": 4,
        "scale": [
            {
                "fi": "ei toteudu",
                "sv": "genomförs inte",
                "en": "not implemented",
                "value": 1
            },
            {
                "fi": "toteutuu osittain",
                "sv": "genomförs delvis",
                "en": "partially implemented",
                "value": 2
            },
            {
                "fi": "toteutuu kokonaan",
                "sv": "genomförs helt",
                "en": "fully implemented",
                "value": 3
            },
            {
                "fi": "ei koske kuntaamme",
                "sv": "gäller inte vår kommun",
                "en": "does not apply to our municipality",
                "value": 4
            }
        ],
        "eos_value": EOS_VALUE_EOS
    },
    {
        "name": "toteutuminen_3",
        "order_no": 17,
        "label": {
            "fi": "Toteutuminen 3",
            "sv": "Förverkligas 3",
            "en": "Implementation 3"
        },
        "min_value": 1,
        "max_value": 3,
        "default_value": 2,
        "step_count": 3,
        "scale": [
            {
                "fi": "ei toteudu",
                "sv": "genomförs inte",
                "en": "not implemented",
                "value": 1
            },
            {
                "fi": "toteutuu osittain",
                "sv": "genomförs delvis",
                "en": "partially implemented",
                "value": 2
            },
            {
                "fi": "toteutuu kokonaan",
                "sv": "genomförs helt",
                "en": "fully implemented",
                "value": 3
            }
        ],
        "eos_value": EOS_VALUE_EKR
    },
    {
        "name": "toteutuminen_3_eos",
        "order_no": 18,
        "label": {
            "fi": "Toteutuminen 3 EOS",
            "sv": "Förverkligas 3 KIS",
            "en": "Implementation 3 ICS"
        },
        "min_value": 1,
        "max_value": 3,
        "default_value": 2,
        "step_count": 3,
        "scale": [
            {
                "fi": "ei toteudu",
                "sv": "genomförs inte",
                "en": "not implemented",
                "value": 1
            },
            {
                "fi": "toteutuu osittain",
                "sv": "genomförs delvis",
                "en": "partially implemented",
                "value": 2
            },
            {
                "fi": "toteutuu kokonaan",
                "sv": "genomförs helt",
                "en": "fully implemented",
                "value": 3
            }
        ],
        "eos_value": EOS_VALUE_EOS
    },
    {
        "name": "vastuut",
        "order_no": 19,
        "label": {
            "fi": "Vastuut",
            "sv": "Ansvar",
            "en": "Responsibilities"
        },
        "min_value": 1,
        "max_value": 3,
        "default_value": 2,
        "step_count": 3,
        "scale": [
            {
                "fi": "vastuita ei ole määritelty",
                "sv": "ansvaret är inte definierat",
                "en": "responsibilities have not been defined",
                "value": 1
            },
            {
                "fi": "vastuut ovat jossain määrin epäselvät",
                "sv": "ansvaret är något oklart",
                "en": "responsibilities are somewhat unclear",
                "value": 2
            },
            {
                "fi": "vastuut on määritelty",
                "sv": "ansvaret är definierat",
                "en": "responsibilities have been defined",
                "value": 3
            }
        ],
        "eos_value": EOS_VALUE_EKR
    },
    {
        "name": "vastuut_eos",
        "order_no": 20,
        "label": {
            "fi": "Vastuut EOS",
            "sv": "Ansvar KIS",
            "en": "Responsibilities ICS"
        },
        "min_value": 1,
        "max_value": 3,
        "default_value": 2,
        "step_count": 3,
        "scale": [
            {
                "fi": "vastuita ei ole määritelty",
                "sv": "ansvaret är inte definierat",
                "en": "responsibilities have not been defined",
                "value": 1
            },
            {
                "fi": "vastuut ovat jossain määrin epäselvät",
                "sv": "ansvaret är något oklart",
                "en": "responsibilities are somewhat unclear",
                "value": 2
            },
            {
                "fi": "vastuut on määritelty",
                "sv": "ansvaret är definierat",
                "en": "responsibilities have been defined",
                "value": 3
            }
        ],
        "eos_value": EOS_VALUE_EOS
    }
]
