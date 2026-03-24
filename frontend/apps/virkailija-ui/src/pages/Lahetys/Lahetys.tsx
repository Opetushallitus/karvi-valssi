import {Dispatch, SetStateAction, useContext, useEffect, useMemo, useState} from 'react';
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
    Oppilaitos,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {
    FormType,
    HasBeenSentToPeopleType,
    LastKyselysendType,
    virkailijapalveluGetActiveKyselykerta$,
    virkailijapalveluPostSendKyselyList$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import LomakeTyyppi, {
    henkilostoLomakkeet,
    taydennyskoulutusLomakkeet,
    toteuttajanAsiantuntijaLomakkeet,
    isTypeOf,
} from '@cscfi/shared/utils/LomakeTyypit';
import UserContext from '../../Context';
import sendKysely from './SendKysely';
import LahetysForm from './LahetysForm';

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
    const [emailSubjectFn, setEmailSubjectFn] = useState<
        (nameExtender?: number) => TextType
    >(() => ({fi: '', sv: ''}));
    const [startEDate, setStartEDate] = useState<Date | null>(null);
    const [endEDate, setEndEDate] = useState<Date | null>(null);
    const [hasBeenSentToPeople, setHasBeenSentToPeople] = useState<
        HasBeenSentToPeopleType[] | []
    >([]);
    const [numOfUnanswered, setNumOfUnanswered] = useState<number>(0);
    const location = useLocation();
    const oidFromQuery = useMemo(() => getQueryParam(location, 'oid'), [location]);
    const [oid] = useState<string | null>(() => oidFromQuery ?? null);

    const [initialDate] = useState<Date>(() => toDate(Date.now()));

    const [startDateLimit, setStartDateLimit] = useState<Date | undefined>(initialDate);
    const [endDateLimit, setEndDateLimit] = useState<Date | undefined>(undefined);
    const [saateviesti, setSaateviesti] = useState<string>('');
    const [navigateToTiedonkeruu, setNavigateToTiedonkeruu] = useState<boolean>(false);
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

                const valssiKysely = {
                    ...kysymysryhma,
                    oppilaitos: oppilaitosName,
                };

                setKysely(valssiKysely);

                function subjectFn(nameExtender?: number) {
                    return kyselyNameGenerator(
                        valssiKysely,
                        toDate(startEDate || Date.now()),
                        isTypeOf(toteuttajanAsiantuntijaLomakkeet, valssiKysely)
                            ? null
                            : oppilaitosVar && convertOppilaitos(oppilaitosVar),
                        nameExtender,
                    );
                }
                setEmailSubjectFn(() => subjectFn);
                lomaketyypitToTiedonkeruuPage(
                    valssiKysely.lomaketyyppi as LomakeTyyppi,
                    setNavigateToTiedonkeruu,
                );
            });

            arvoGetAllKyselyt$().subscribe((allKyselyt) => {
                const matchedKysely = allKyselyt.find(
                    (a: ArvoKysely) => a.kyselyid === activeKyselyId,
                );

                if (matchedKysely?.metatiedot.valssi_saate)
                    setSaateviesti(matchedKysely.metatiedot.valssi_saate);

                if (matchedKysely?.kyselykerrat[0]) {
                    setNumOfUnanswered(
                        matchedKysely.kyselykerrat[0].aktiivisia_vastaajatunnuksia,
                    );
                }
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

        let org;
        if (!oid) {
            org = userInfo?.rooli.organisaatio;
        } else {
            org = oid;
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
    }, [kysymysryhmaId, location, userInfo, oid]);

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
            (nameExtender?: number) => emailSubjectFn(nameExtender),
        );
    };

    return (
        <LahetysForm
            onSubmit={onSubmit}
            kysely={kysely}
            kyselykertaId={kyselykertaId}
            emailSubjectFn={emailSubjectFn}
            startDateLimit={startDateLimit}
            endDateLimit={endDateLimit}
            saateviesti={saateviesti}
            numOfUnanswered={numOfUnanswered}
            startEDate={startEDate}
            endEDate={endEDate}
            hasBeenSentToPeople={hasBeenSentToPeople}
            lastKyselysend={lastKyselysend}
            oid={oid}
        />
    );
}

export default Lahetys;
