import {Dispatch, SetStateAction, useContext, useEffect, useState} from 'react';
import {parseISO, toDate} from 'date-fns';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {SubmitHandler} from 'react-hook-form';
import {useTranslation} from 'react-i18next';
import {useLocation, useNavigate} from 'react-router-dom';
import {
    convertOppilaitos,
    getQueryParam,
    getQueryParamAsNumber,
    kyselyNameGenerator,
} from '@cscfi/shared/utils/helpers';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysryhma$,
    ArvoKysely,
    convertKysymyksetArvoToValssi,
    Oppilaitos,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    FormType,
    HasBeenSentToPeopleType,
    LastKyselysendType,
    virkailijapalveluGetActiveKyselykerta$,
    virkailijapalveluPostSendKyselyList$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import UserContext from '../../Context';
import sendKysely from './SendKysely';
import LahetysForm from './LahetysForm';
import LomakeTyyppi, {
    henkilostoLomakkeet,
    taydennyskoulutusLomakkeet,
    toteuttajanAsiantuntijaLomakkeet,
} from '../../utils/LomakeTyypit';

export const lomaketyypitToTiedonkeruuPage = (
    lomaketyyppi: LomakeTyyppi,
    setNavigateToTiedonkeruu: Dispatch<SetStateAction<boolean>>,
) => {
    const lomaketyypitTiedonkeruuRedirect = [
        ...henkilostoLomakkeet,
        ...taydennyskoulutusLomakkeet,
        ...toteuttajanAsiantuntijaLomakkeet,
    ];
    if (lomaketyypitTiedonkeruuRedirect.includes(lomaketyyppi)) {
        setNavigateToTiedonkeruu(true);
    }
};

function Lahetys() {
    const {
        i18n: {language: lang},
    } = useTranslation();
    const navigate = useNavigate();
    const userInfo = useContext(UserContext);
    const [kyselykertaId, setKyselykertaId] = useState<number | undefined>(undefined);
    const [lastKyselysend, setLastKyselysend] = useState<LastKyselysendType | null>(null);
    const [kysely, setKysely] = useState<KyselyType | null>(null);
    const [activeKyselyId, setActiveKyselyId] = useState<number>(-1);
    const [emailSubject, setEmailSubject] = useState<TextType>({fi: '', sv: ''});
    const [startEDate, setStartEDate] = useState<Date | null>(null);
    const [endEDate, setEndEDate] = useState<Date | null>(null);
    const [hasBeenSentToPeople, setHasBeenSentToPeople] = useState<
        HasBeenSentToPeopleType[] | []
    >([]);
    const [oid, setOid] = useState<string>('');

    const [startDateLimit, setStartDateLimit] = useState<Date | undefined>(
        toDate(Date.now()),
    );
    const [endDateLimit, setEndDateLimit] = useState<Date | undefined>(undefined);
    const [saateviesti, setSaateviesti] = useState<string>('');
    const [navigateToTiedonkeruu, setNavigateToTiedonkeruu] = useState<boolean>(false);
    const location = useLocation();
    const kysymysryhmaId = getQueryParamAsNumber(location, 'id');

    useEffect(() => {
        if (kysymysryhmaId) {
            arvoGetKysymysryhma$(kysymysryhmaId).subscribe((kysymysryhma) => {
                const oppilaitosVar = userInfo?.rooli.oppilaitokset
                    ?.filter(
                        (oppilaitos) =>
                            oppilaitos.oppilaitos_oid === getQueryParam(location, 'oid'),
                    )
                    .find((opv) => !!opv);
                const oppilaitosName = oppilaitosVar
                    ? oppilaitosVar[`oppilaitos_${lang}` as keyof Oppilaitos]
                    : '';

                const valssiKysely: KyselyType = {
                    id: kysymysryhma.kysymysryhmaid,
                    topic: {
                        fi: kysymysryhma.nimi_fi,
                        sv: kysymysryhma?.nimi_sv || '',
                    },
                    kysymykset: convertKysymyksetArvoToValssi(kysymysryhma.kysymykset),
                    status: kysymysryhma.tila,
                    lomaketyyppi: kysymysryhma.metatiedot?.lomaketyyppi,
                    paaIndikaattori: kysymysryhma.metatiedot?.paaIndikaattori,
                    lastKyselysend: kysymysryhma.last_kyselysend,
                    oppilaitos: oppilaitosName,
                };

                setKysely(valssiKysely);

                const subject = kyselyNameGenerator(
                    valssiKysely,
                    toDate(startEDate || Date.now()),
                    toteuttajanAsiantuntijaLomakkeet.includes(
                        kysymysryhma.metatiedot?.lomaketyyppi as LomakeTyyppi,
                    )
                        ? null
                        : oppilaitosVar && convertOppilaitos(oppilaitosVar),
                    null,
                );

                setEmailSubject(subject);
                lomaketyypitToTiedonkeruuPage(
                    kysymysryhma.metatiedot?.lomaketyyppi as LomakeTyyppi,
                    setNavigateToTiedonkeruu,
                );
            });

            arvoGetAllKyselyt$().subscribe((allKyselyt) => {
                const metatieto = allKyselyt
                    .find((a: ArvoKysely) => a.kyselyid === activeKyselyId)
                    ?.metatiedot.valssi_saate.toString();
                if (metatieto) setSaateviesti(metatieto);
            });
        }
    }, [
        activeKyselyId,
        kysymysryhmaId,
        lang,
        location,
        startEDate,
        userInfo?.rooli.oppilaitokset,
    ]);

    useEffect(() => {
        const postHasBeenSendKyselyList = (kyselyKerta: number) =>
            virkailijapalveluPostSendKyselyList$(userInfo!)(kyselyKerta);

        const getActiveKyselykerta = (krId: number, organisaatio: string) =>
            virkailijapalveluGetActiveKyselykerta$(userInfo!)(krId, organisaatio);

        const oidVar = getQueryParam(location, 'oid');
        if (oidVar) {
            setOid(oidVar);
        }

        let org;
        if (!oidVar) {
            org = userInfo?.rooli.organisaatio;
        } else {
            org = oidVar;
        }

        if (org && kysymysryhmaId) {
            getActiveKyselykerta(kysymysryhmaId, org).subscribe((kyselykerta) => {
                if (kyselykerta[0]) {
                    postHasBeenSendKyselyList(kyselykerta[0].kyselykertaid).subscribe(
                        (kyselyPeople: HasBeenSentToPeopleType[]) => {
                            setHasBeenSentToPeople(kyselyPeople);
                        },
                    );
                    setKyselykertaId(kyselykerta[0].kyselykertaid);
                    setActiveKyselyId(kyselykerta[0].kyselyid);
                    setLastKyselysend(kyselykerta[0].last_kyselysend);
                    const eDate = parseISO(kyselykerta[0].voimassa_loppupvm);
                    setEndDateLimit(eDate);
                    setEndEDate(eDate);
                    const eStartDate = parseISO(kyselykerta[0].voimassa_alkupvm);
                    setStartEDate(eStartDate);
                    setStartDateLimit(eStartDate);
                }
            });
        }
    }, [kysymysryhmaId, location, userInfo]);

    if (kysely === null) {
        return null;
    }
    const onSubmit: SubmitHandler<FormType> = (formData) => {
        sendKysely(
            userInfo!,
            formData,
            kyselykertaId,
            kysely,
            navigate,
            navigateToTiedonkeruu,
            emailSubject,
        );
    };

    return (
        <LahetysForm
            onSubmit={onSubmit}
            kysely={kysely}
            emailSubject={emailSubject}
            startDateLimit={startDateLimit}
            endDateLimit={endDateLimit}
            saateviesti={saateviesti}
            startEDate={startEDate}
            endEDate={endEDate}
            hasBeenSentToPeople={hasBeenSentToPeople}
            lastKyselysend={lastKyselysend}
            oid={oid}
        />
    );
}

export default Lahetys;
