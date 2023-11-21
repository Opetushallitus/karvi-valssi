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
    convertKysymyksetArvoToValssi,
    Oppilaitos,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import {
    convertOppilaitos,
    kyselyNameGenerator,
    uniqueNumber,
} from '@cscfi/shared/utils/helpers';
import {useObservable} from 'rxjs-hooks';
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
import sendKysely from './SendKysely';
import LahetysForm from './LahetysForm';
import UserContext from '../../Context';
import LomakeTyyppi from '../../utils/LomakeTyypit';
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

    const [kysely, emailSubject] = useObservable(
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
                        id: kysymysryhma.kysymysryhmaid,
                        topic: {
                            fi: kysymysryhma.nimi_fi,
                            sv: kysymysryhma?.nimi_sv || '',
                        },
                        kysymykset: convertKysymyksetArvoToValssi(
                            kysymysryhma.kysymykset,
                        ),
                        status: kysymysryhma.tila,
                        lomaketyyppi: kysymysryhma.metatiedot?.lomaketyyppi,
                        paaIndikaattori: kysymysryhma.metatiedot?.paaIndikaattori,
                        lastKyselysend: kysymysryhma.last_kyselysend,
                        oppilaitos: oppilaitosName,
                    } as KyselyType;

                    const subject = kyselyNameGenerator(
                        valssiKysely,
                        toDate(Date.now()),
                        oppilaitosVar && convertOppilaitos(oppilaitosVar),
                        null,
                    );

                    return [valssiKysely, subject] as [KyselyType | null, TextType];
                }),
            ),
        [null, {fi: '', sv: ''}],
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
                    map(
                        (allKyselyt) =>
                            allKyselyt
                                .find(
                                    (arvoKysely: ArvoKysely) =>
                                        arvoKysely.kyselyid === activeKyselyId,
                                )
                                ?.metatiedot.valssi_saate.toString() || '',
                    ),
                    filter((saate) => !!saate),
                )
                .subscribe((saate) => setSaateviesti(saate));
        }
    }, [activeKyselyId]);

    const [
        kyselykertaId,
        lastKyselysend,
        startDateLimit,
        endDateLimit,
        startEDate,
        endEDate,
    ] = useObservable(
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
        [undefined, null, toDate(Date.now()), undefined, null, null],
    );

    const [peopleListAll, peopleList, hasBeenSentToPeople] = useObservable(
        () =>
            forkJoin([
                getPeople$(userInfo!, oid!),
                getActiveKyselykerta$(userInfo!, kysymysryhmaIdInt, oid!),
            ]).pipe(
                map(([virkailijat, hasBeenSentToPeoples]) => {
                    const virkailijatFiltered = virkailijat.filter(
                        (virkailija) =>
                            !hasBeenSentToPeoples
                                .map((hasBeenSent) => hasBeenSent.tyontekija_id)
                                .includes(virkailija.tyontekija_id || -1),
                    );
                    return [virkailijat, virkailijatFiltered, hasBeenSentToPeoples] as [
                        PeopleType[],
                        PeopleType[],
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
            peopleListAll={peopleListAll}
            peopleList={peopleList}
            hasBeenSentToPeople={hasBeenSentToPeople}
            fromVarda
            oid={oid}
            lastKyselysend={lastKyselysend}
        />
    );
}
export default TyontekijatVardastaLahetys;
