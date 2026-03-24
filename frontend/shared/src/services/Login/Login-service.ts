import {Dispatch, SetStateAction} from 'react';
import {
    catchError,
    distinctUntilChanged,
    filter,
    map,
    mergeMap,
    switchMap,
} from 'rxjs/operators';
import {
    BehaviorSubject,
    combineLatest,
    forkJoin,
    of,
    shareReplay,
    throwError,
} from 'rxjs';
import Cookies from 'js-cookie';
import {virkailijapalveluGetPermission$} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {
    arvoHostname,
    casHostname,
    raportiointipalveluLoginUrl,
    virkailijapalveluLoginUrl,
    raportiointipalveluLogoutUrl,
    virkailijapalveluLogoutUrl,
} from '../Settings/Settings-service';

import {
    arvoHttp,
    commonHttp,
    raportointipalveluHttp,
    virkailijapalveluHttp,
} from '../Http/Http-service';
import {arvoKayttaja$, ArvoRooli} from '../Arvo-api/Arvo-api-service';

import {AlertTable, AlertType} from '../Alert/Alert-service';

type CasLoginInfo = {
    principal: string;
    authenticationDate: string; // iso-date
    ticketGrantingTicketCreationTime: string; // iso-date
    ticketGrantingTicketLastTimeUsed: string; // iso-date
};

export type UserInfoType = {
    nimi: string;
    rooli: ArvoRooli;
    rooliManipuloitu: boolean;
    arvoRoolit: ArvoRooli[];
    arvoAktiivinenRooli: ArvoRooli;
    organisaatio: string;
    uid: string;
    impersonoitu_kayttaja: string;
    vaihdettu_organisaatio: string;
};

interface UserStoreSubjectType {
    impersonated?: ArvoRooli;
}
const userStoreInitialState: UserStoreSubjectType = {
    impersonated: undefined,
};
const userStoreSubject = new BehaviorSubject<UserStoreSubjectType>(userStoreInitialState);

export const userStore = {
    subscribe: (setState: Dispatch<SetStateAction<UserStoreSubjectType>>) =>
        userStoreSubject.subscribe(setState),
    initialState: userStoreInitialState,
};

const initCasSession$ = commonHttp.getWithCache<CasLoginInfo>(
    `${casHostname}actuator/sso`,
    {
        400: {
            severity: 'warning',
            disabled: true,
        },
    } as AlertTable,
);
const initArvoSession$ = arvoHttp.getWithCache<string>(arvoHostname, {
    403: {severity: 'error', disabled: true} as AlertType,
} as AlertTable);

const initVirkailijapalveluSession$ = virkailijapalveluHttp.getWithCache<string>(
    virkailijapalveluLoginUrl,
);

const initRaportointipalveluSession$ = raportointipalveluHttp.getWithCache<string>(
    raportiointipalveluLoginUrl,
);

const virkailijapalveluLogout$ = (token: string) =>
    virkailijapalveluHttp.get<string>(`${virkailijapalveluLogoutUrl}?refresh=${token}`);

const raportointipalveluLogout$ = (token: string) =>
    raportointipalveluHttp.get<string>(
        `${raportiointipalveluLogoutUrl}?refresh=${token}`,
    );

export const expireRefreshTokens = () => {
    const virkailijapalveluRefreshToken = Cookies.get('virkailijapalvelu_refresh_token');
    const raportointipalveluRefreshToken = Cookies.get(
        'raportointipalvelu_refresh_token',
    );
    virkailijapalveluLogout$(virkailijapalveluRefreshToken).subscribe();
    raportointipalveluLogout$(raportointipalveluRefreshToken).subscribe();
};

const isCasSession$ = initCasSession$.pipe(
    map(() => true),
    catchError(() => of(false)),
    shareReplay(),
);

// These init sessions are only for the case user wants to do non GET request with expired session. In this case request
// body gets discarded because of redirect which renews session to the service.
const isArvoSession$ = initArvoSession$.pipe(
    map(() => true),
    distinctUntilChanged(),
);

// This is needed to pick up the virkailijapalvelu_access_token cookie
const isVirkailijapalveluSession$ = initVirkailijapalveluSession$.pipe(
    map((body: string) => !!body?.includes('Login success')),
    distinctUntilChanged(),
);
// This is needed to pick up the raportointipalvelu_access_token cookie
const isRaportointipalveluSession$ = initRaportointipalveluSession$.pipe(
    map((body: string) => !!body?.includes('Login success')),
    distinctUntilChanged(),
);
const loginStack = [
    isArvoSession$,
    isVirkailijapalveluSession$,
    isRaportointipalveluSession$,
];

type LogInType = {
    isLoggedIn?: boolean;
    error?: string;
};

export const isLoggedIn$ = () =>
    isCasSession$.pipe(
        mergeMap((isCasSession) => {
            if (isCasSession) {
                return forkJoin(loginStack).pipe(
                    map(
                        ([
                            isArvoSession,
                            isVirkailijapalveluSession,
                            isRaportointipalveluSession,
                        ]) =>
                            ({
                                isLoggedIn:
                                    isArvoSession &&
                                    isVirkailijapalveluSession &&
                                    isRaportointipalveluSession,
                            }) as LogInType,
                    ),
                    catchError((error) => {
                        if (error?.status === 403) {
                            return of({error: 'ei-oikeuksia'} as LogInType);
                        }
                        return throwError(error);
                    }),
                );
            }

            return of({isLoggedIn: false} as LogInType);
        }),
    );

export const casLoginUrl = (service: string | null) =>
    `${casHostname}login?service=${window.location.origin}/virkailija-ui${
        service || '/login'
    }`;

// this will redirect to `${casHostname}logout`
// in addition, it sets refresh token to blacklist
// so that it is no longer possible to request new access tokens
export const casLogoutUrl = `${casHostname}logout`;

export const userInfo$ = isLoggedIn$().pipe(
    map((login) => login.isLoggedIn),
    filter(Boolean),
    mergeMap(() =>
        forkJoin([arvoKayttaja$]).pipe(
            map(
                ([arvoKayttaja]) =>
                    ({
                        rooli: {
                            ...arvoKayttaja.aktiivinen_rooli,
                            // Vaihda rooli pääkäyttäjäksi
                            kayttooikeus:
                                arvoKayttaja.vaihdettu_organisaatio !== ''
                                    ? 'PAAKAYTTAJA'
                                    : arvoKayttaja.aktiivinen_rooli.kayttooikeus,
                            rooli:
                                arvoKayttaja.vaihdettu_organisaatio !== ''
                                    ? 'VASTUUKAYTTAJA'
                                    : arvoKayttaja.aktiivinen_rooli.rooli,
                        },
                        rooliManipuloitu: false,
                        nimi: `${arvoKayttaja.etunimi} ${arvoKayttaja.sukunimi}`,
                        arvoRoolit: arvoKayttaja.roolit,
                        arvoAktiivinenRooli: arvoKayttaja.aktiivinen_rooli,
                        organisaatio: arvoKayttaja.aktiivinen_rooli.koulutustoimija_fi,
                        uid: arvoKayttaja.uid,
                        impersonoitu_kayttaja: arvoKayttaja.impersonoitu_kayttaja,
                        vaihdettu_organisaatio: arvoKayttaja.vaihdettu_organisaatio,
                    }) as UserInfoType,
            ),
        ),
    ),
);

export type Role = {
    kayttooikeus: string;
    service: string;
};

export const virkailijaPermissionOk$ = combineLatest([isLoggedIn$(), userInfo$]).pipe(
    filter(([login, ui]) => !!login?.isLoggedIn && !!ui?.uid),
    distinctUntilChanged((prev, next) => prev[1]?.uid === next[1]?.uid),
    map(([, ui]) => ui),
    switchMap((ui) =>
        virkailijapalveluGetPermission$(ui).pipe(
            map((resp) => resp === 'OK'),
            catchError((err) => {
                console.error('Permission check failed', err);
                return of(false);
            }),
        ),
    ),
    shareReplay({bufferSize: 1, refCount: true}),
);

export const userInfoToRole = (userInfo: UserInfoType) =>
    [
        {
            kayttooikeus: userInfo.rooli.kayttooikeus,
            service: 'arvo',
        } as Role,
    ] as Role[];

export const userKayttooikeudet$ = userInfo$.pipe(
    map((userInfo) => userInfoToRole(userInfo)),
    /* map((userInfo) =>
        userInfo.arvoRoolit.map(
            (arvoRooli): Role => ({
                kayttooikeus: arvoRooli.kayttooikeus,
                service: 'arvo',
            }),
        ),
    ), */
);

export enum ArvoRoles {
    YLLAPITAJA = 'YLLAPITAJA',
    PAAKAYTTAJA = 'PAAKAYTTAJA',
    TOTEUTTAJA = 'TOTEUTTAJA',
}

export type ArvoRole =
    | ArvoRoles.YLLAPITAJA
    | ArvoRoles.PAAKAYTTAJA
    | ArvoRoles.TOTEUTTAJA;

export type AllowedRole = {[key: string]: ArvoRole[]};

export const hasRequiredRole = (
    allowedRoles: AllowedRole,
    userRoles: Array<Role> | null,
) =>
    userRoles?.some((userRole) =>
        Object.keys(allowedRoles).find(
            (allowedServiceName) =>
                allowedServiceName === userRole.service &&
                allowedRoles[allowedServiceName].some(
                    (allowedRole) => userRole.kayttooikeus === allowedRole,
                ),
        ),
    );

/*
Note:
indikaattorit = arviointityökalut page, it is not visible to toteuttaja role!
rakenna kysely functionality (create new questionnaire) is only for yllapitaja role
*/

export const allowedRoles: {[key: string]: AllowedRole} = {
    etusivu: {arvo: [ArvoRoles.YLLAPITAJA, ArvoRoles.PAAKAYTTAJA, ArvoRoles.TOTEUTTAJA]},
    indikaattorit: {
        arvo: [ArvoRoles.YLLAPITAJA, ArvoRoles.PAAKAYTTAJA, ArvoRoles.TOTEUTTAJA],
    },
    tiedonkeruu: {
        arvo: [ArvoRoles.YLLAPITAJA, ArvoRoles.PAAKAYTTAJA, ArvoRoles.TOTEUTTAJA],
    },
    raportointi: {
        arvo: [ArvoRoles.YLLAPITAJA, ArvoRoles.PAAKAYTTAJA, ArvoRoles.TOTEUTTAJA],
    },
    aluejako: {arvo: [ArvoRoles.PAAKAYTTAJA]},
    raporttipohja: {arvo: [ArvoRoles.YLLAPITAJA]},
    rakennaKysely: {arvo: [ArvoRoles.YLLAPITAJA]},
    kysely: {arvo: [ArvoRoles.YLLAPITAJA, ArvoRoles.PAAKAYTTAJA, ArvoRoles.TOTEUTTAJA]},
    esikatselu: {
        arvo: [ArvoRoles.YLLAPITAJA, ArvoRoles.PAAKAYTTAJA, ArvoRoles.TOTEUTTAJA],
    },
    aktivointi: {arvo: [ArvoRoles.PAAKAYTTAJA]},
    lahetys: {arvo: [ArvoRoles.PAAKAYTTAJA, ArvoRoles.TOTEUTTAJA]},
    yhteenveto: {arvo: [ArvoRoles.TOTEUTTAJA]},
    yhteenvetolist: {arvo: [ArvoRoles.PAAKAYTTAJA]},
    arviointitulokset: {arvo: [ArvoRoles.PAAKAYTTAJA, ArvoRoles.TOTEUTTAJA]},
};
