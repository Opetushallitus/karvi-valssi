import {useContext, useEffect, useMemo, useState} from 'react';
import {filter, forkJoin, map, mergeMap} from 'rxjs';
import {useTranslation} from 'react-i18next';
import {useNavigate, useParams} from 'react-router-dom';
import {parseISO, toDate} from 'date-fns';
import {SubmitHandler} from 'react-hook-form';
import {
    arvoGetAllKyselyt$,
    arvoGetKysymysryhma$,
    ArvoKysely,
    Oppilaitos,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {
    convertOppilaitos,
    kyselyNameGenerator,
    uniqueNumber,
} from '@cscfi/shared/utils/helpers';
import {useObservableState} from 'observable-hooks';
import {
    FormType,
    HasBeenSentToPeopleType,
    LastKyselysendType,
    PeopleType,
    virkailijapalveluGetActiveKyselykerta$,
    virkailijapalveluGetTyontekijaList$,
    virkailijapalveluPostSendKyselyList$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {UserInfoType} from '@cscfi/shared/services/Login/Login-service';
import LomakeTyyppi from '@cscfi/shared/utils/LomakeTyypit';
import sendKysely from './SendKysely';
import LahetysForm, {DuplicateEmailsPeopleType} from './LahetysForm';

import UserContext from '../../Context';
import {lomaketyypitToTiedonkeruuPage} from './Lahetys';

const getActiveKyselykerta$ = (
    userInfo: UserInfoType,
    kysymysryhmaId: number,
    organisaatio: string,
) =>
    virkailijapalveluGetActiveKyselykerta$(userInfo)(kysymysryhmaId, organisaatio).pipe(
        mergeMap((kyselykerrat) =>
            virkailijapalveluPostSendKyselyList$(userInfo)(kyselykerrat[0].kyselykertaid),
        ),
    );

const getPeople$ = (userInfo: UserInfoType, organisaatio: string) =>
    virkailijapalveluGetTyontekijaList$(userInfo)(organisaatio).pipe(
        map((virkailijat) =>
            virkailijat.map(
                (virkailija) =>
                    ({
                        ...virkailija,
                        kokoNimi: `${virkailija.kutsumanimi} ${virkailija.sukunimi}`,
                        checkedElem: {
                            id: uniqueNumber(),
                            checked: false,
                        },
                    }) as PeopleType,
            ),
        ),
    );

type TyontekijatVardastaLahetysParams = {
    kysymysryhmaId: string;
    toimipaikkaOid: string;
};

function TyontekijatVardastaLahetys() {
    const {
        i18n: {language: lang},
    } = useTranslation();
    const userInfo = useContext(UserContext);
    const navigate = useNavigate();
    const [navigateToTiedonkeruu, setNavigateToTiedonkeruu] = useState<boolean>(false);
    const [activeKyselyId, setActiveKyselyId] = useState<number>(-1);
    const [saateviesti, setSaateviesti] = useState<string>('');
    const [numOfUnanswered, setNumOfUnanswered] = useState<number>(0);
    const [initialDate] = useState<Date>(() => toDate(Date.now()));

    const {kysymysryhmaId, toimipaikkaOid} =
        useParams<TyontekijatVardastaLahetysParams>();
    if (!kysymysryhmaId || !toimipaikkaOid) {
        throw Error('kysymysryhmaId or toimipaikkaOid missing');
    }
    const kysymysryhmaIdInt = parseInt(kysymysryhmaId, 10);

    const correctOid = userInfo?.rooli?.oppilaitokset?.find(
        (item: any) => item.oppilaitos_oid === toimipaikkaOid,
    );
    const oid = useMemo(
        () =>
            correctOid?.oppilaitos_oid === toimipaikkaOid
                ? toimipaikkaOid
                : userInfo?.rooli?.oppilaitokset[0]?.oppilaitos_oid,
        [correctOid?.oppilaitos_oid, toimipaikkaOid, userInfo?.rooli?.oppilaitokset],
    );

    const [[kysely, emailSubjectFn]] = useObservableState(
        () =>
            arvoGetKysymysryhma$(kysymysryhmaIdInt).pipe(
                map((kysymysryhma) => {
                    const oppilaitosVar = userInfo?.rooli?.oppilaitokset
                        ?.filter(
                            (oppilaitos) => oppilaitos.oppilaitos_oid === toimipaikkaOid,
                        )
                        .find((opv) => !!opv);
                    const oppilaitosName = oppilaitosVar
                        ? oppilaitosVar[`oppilaitos_${lang}` as keyof Oppilaitos]
                        : '';

                    const valssiKysely: KyselyType = {
                        ...kysymysryhma,
                        oppilaitos: oppilaitosName,
                    };

                    function subjectFn(nameExtender?: number) {
                        return kyselyNameGenerator(
                            valssiKysely,
                            initialDate,
                            oppilaitosVar && convertOppilaitos(oppilaitosVar),
                            nameExtender,
                        );
                    }

                    return [valssiKysely, subjectFn] as [
                        KyselyType | null,
                        (nameExtender?: number) => TextType,
                    ];
                }),
            ),
        [null, () => ({fi: '', sv: ''})],
    );

    useEffect(() => {
        lomaketyypitToTiedonkeruuPage(
            kysely?.lomaketyyppi as LomakeTyyppi,
            setNavigateToTiedonkeruu,
        );
    }, [kysely?.lomaketyyppi]);

    useEffect(() => {
        virkailijapalveluGetActiveKyselykerta$(userInfo!)(
            kysymysryhmaIdInt,
            oid!,
        ).subscribe((x) => setActiveKyselyId(x[0].kyselyid));
    }, [kysymysryhmaIdInt, oid, userInfo]);

    useEffect(() => {
        if (activeKyselyId > 0) {
            arvoGetAllKyselyt$()
                .pipe(
                    map((allKyselyt) => {
                        const matchedKysely = allKyselyt.find(
                            (arvoKysely: ArvoKysely) =>
                                arvoKysely.kyselyid === activeKyselyId,
                        );
                        const matchedKyselykerta = matchedKysely?.kyselykerrat[0];
                        return {
                            saate:
                                matchedKysely?.metatiedot.valssi_saate.toString() || '',
                            numOfUnanswered:
                                matchedKyselykerta?.aktiivisia_vastaajatunnuksia || 0,
                        };
                    }),
                )
                .subscribe((matchedKysely) => {
                    if (matchedKysely.saate) setSaateviesti(matchedKysely.saate);
                    setNumOfUnanswered(matchedKysely.numOfUnanswered);
                });
        }
    }, [activeKyselyId]);

    const [
        [
            kyselykertaId,
            lastKyselysend,
            startDateLimit,
            endDateLimit,
            startEDate,
            endEDate,
        ],
    ] = useObservableState(
        () =>
            virkailijapalveluGetActiveKyselykerta$(userInfo!)(
                kysymysryhmaIdInt,
                oid,
            ).pipe(
                filter((kyselykerrat) => !!kyselykerrat[0]),
                map((kyselykerrat) => kyselykerrat[0]),
                map((kyselykerta) => {
                    const voimassaAlkupvm = parseISO(kyselykerta.voimassa_alkupvm);
                    const voimassaLoppupvm = parseISO(kyselykerta.voimassa_loppupvm);
                    return [
                        kyselykerta.kyselykertaid,
                        kyselykerta.last_kyselysend,
                        voimassaAlkupvm,
                        voimassaLoppupvm,
                        voimassaAlkupvm,
                        voimassaLoppupvm,
                    ] as [
                        number | undefined,
                        LastKyselysendType | null,
                        Date,
                        Date | undefined,
                        Date | null,
                        Date | null,
                    ];
                }),
            ),
        [undefined, null, initialDate, undefined, null, null],
    );

    const [[peopleListAll, peopleList, hasBeenSentToPeople]] = useObservableState(
        () =>
            forkJoin([
                getPeople$(userInfo!, oid!),
                getActiveKyselykerta$(userInfo!, kysymysryhmaIdInt, oid!),
            ]).pipe(
                map(([virkailijat, hasBeenSentToPeoples]) => {
                    // Get a list of duplicate emails and add info to virkailija list.
                    const numOfEmails = virkailijat.reduce((acc, virkailija) => {
                        acc[virkailija.email] = (acc[virkailija.email] || 0) + 1;
                        return acc;
                    }, {});
                    const duplicateEmails = Object.keys(numOfEmails).filter(
                        (email) => numOfEmails[email] > 1,
                    );
                    const virkailijatDuplicateEmails = virkailijat.map((virkailija) => ({
                        ...virkailija,
                        duplicateEmail: duplicateEmails.includes(virkailija.email),
                    }));

                    // Filter virkailijat that kysely is not sent to.
                    const virkailijatFiltered = virkailijatDuplicateEmails.filter(
                        (virkailija) =>
                            !hasBeenSentToPeoples
                                .map((hasBeenSent) => hasBeenSent.tyontekija_id)
                                .includes(virkailija.tyontekija_id || -1),
                    );
                    return [
                        virkailijatDuplicateEmails,
                        virkailijatFiltered,
                        hasBeenSentToPeoples,
                    ] as [
                        DuplicateEmailsPeopleType[],
                        DuplicateEmailsPeopleType[],
                        HasBeenSentToPeopleType[],
                    ];
                }),
            ),
        [[], [], []],
    );

    const onSubmit: SubmitHandler<FormType> = (formData) => {
        sendKysely(
            userInfo!,
            formData,
            kyselykertaId,
            kysely,
            navigate,
            navigateToTiedonkeruu,
            emailSubjectFn,
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
            peopleListAll={peopleListAll}
            peopleList={peopleList}
            fromVarda
        />
    );
}
export default TyontekijatVardastaLahetys;
