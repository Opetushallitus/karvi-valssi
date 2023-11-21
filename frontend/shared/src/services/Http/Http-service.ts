import {
    catchError,
    finalize,
    map,
    observeOn,
    retry,
    shareReplay,
    switchMap,
    tap,
} from 'rxjs/operators';
import {asyncScheduler, defer, EMPTY, Observable, Subject, throwError, timer} from 'rxjs';
import {ajax, AjaxError, AjaxRequest} from 'rxjs/ajax';
import Cookies from 'js-cookie';
import {AlertTable} from '@cscfi/shared/services/Alert/Alert-service';
import LoadingService from '../Loading/Loading-service';
import * as ErrorService from '../Error/Error-service';
import {
    arvoHostname,
    currentEnvironment,
    raportointipalveluHostname,
    virkailijapalveluHostname,
} from '../Settings/Settings-service';

type AuthTokens = {
    access?: string;
    refresh?: string;
};

type Hooks = {
    response?: (res) => void;
};

const virkailijapalveluTokens = {} as AuthTokens;
const raportointipalveluTokens = {} as AuthTokens;

export const clearSession = () => {
    Object.keys(Cookies.get()).forEach((cookieKey) => Cookies.remove(cookieKey));
    [virkailijapalveluTokens, raportointipalveluTokens].forEach((token) => {
        token.access = null;
        token.refresh = null;
    });
};

// eslint-disable-next-line prettier/prettier
export const toJson = <T,>(text): T => {
    try {
        return JSON.parse(text);
    } catch (e) {
        return text;
    }
};
const appendUrlWithQueryParams = (url: string, queryParams: {[key: string]: string}) => {
    const separator = url.includes('?') ? '&' : '?';
    const queryString = Object.keys(queryParams)
        .map((key) => `${key}=${queryParams[key]}`)
        .join('&');
    return `${url}${separator}${queryString}`;
};

function renewExpiredArvoSession(requestUrl: string, responseUrl: string) {
    if (
        requestUrl.startsWith(arvoHostname) &&
        responseUrl !== requestUrl &&
        `${responseUrl}/` !== requestUrl
    ) {
        /*
        Handle an expired Arvo-session. Throw and retry the original request.
        Assumed the session is re-established on the background.
        */
        throw new Error();
    }
}

export const logoutFromValssi$ = new Subject<boolean>();

function handleExpiredRefreshToken() {
    /*
    Recursive-request: Refresh-token has expired. User must log in again.
    */
    logoutFromValssi$.next(true);
    return EMPTY;
}

function refreshAccessToken<T>(
    request: AjaxRequest,
    service: 'virkailijapalvelu' | 'raportointipalvelu',
    refreshServiceAccessToken$: {
        (body: RefreshTokenPostType): Observable<any>;
    },
) {
    const localToken =
        service === 'virkailijapalvelu'
            ? virkailijapalveluTokens
            : raportointipalveluTokens;
    const refreshToken = localToken.refresh || Cookies.get(`${service}_refresh_token`);
    const postData = {refresh: refreshToken};
    return refreshServiceAccessToken$(postData).pipe(
        switchMap((res) => {
            Cookies.set(`${service}_access_token`, res.access, {
                path: '/',
            });
            localToken.access = res.access;
            const newRequest = {
                ...request,
                headers: {...request.headers},
            };
            newRequest.headers.Authorization = `Bearer ${res.access}`;
            return ajax<T>(newRequest);
        }),
    );
}

function rerunFailedArvoRequest<T>(request: AjaxRequest) {
    /*
    Arvo renews the session automatically in the background (assuming the main Opintopolku CAS session is still valid).
    However, we need to rerun the failed request again with a refreshed XSRF-Token
    */
    const newRequest = {
        ...request,
        headers: {...request.headers},
    };
    newRequest.headers['x-xsrf-token'] = Cookies.get('XSRF-TOKEN');
    return ajax<T>(newRequest);
}

function catchExpiredSession(error, request) {
    if (error.status === 401) {
        /*
        Refresh JWT access token for Virkailijapalvelu and Raportointipalvelu.
        */
        if (request.url.includes('/virkailijapalvelu/')) {
            if (request.url.includes('/token/refresh/')) {
                return handleExpiredRefreshToken();
            }
            return refreshAccessToken(
                request,
                'virkailijapalvelu',
                refreshVirkailijapalveluAccessToken$,
            );
        }
        if (request.url.includes('/raportointipalvelu/')) {
            if (request.url.includes('/token/refresh/')) {
                return handleExpiredRefreshToken();
            }
            return refreshAccessToken(
                request,
                'raportointipalvelu',
                refreshRaportointipalveluAccessToken$,
            );
        }
        /*
        Handle an expired Arvo-session
        */
        if (request.url.includes('/arvo/')) {
            return rerunFailedArvoRequest(request);
        }
    }
    return throwError(() => error);
}

function httpRequest<T>(
    extraSettings: () => AjaxRequest,
    hooks: Hooks,
    method: string,
    url: string,
    alertTable: AlertTable,
    headers: any,
    body?: any,
    isFetchOnce: boolean = false,
    crossDomain: boolean = false,
    withCredentials: boolean = false,
    retryCount: number = 2,
): Observable<T> {
    const observable = defer(() => {
        const timeoutInMillis = 60 * 1000;
        const retryDelayInMillis = 2000;
        const excludedStatusCodes = [0, 400, 401, 403];
        const async = true;
        const commonSettings: AjaxRequest = {
            url,
            method,
            headers,
            body,
            async,
            crossDomain,
            withCredentials,
            timeout: timeoutInMillis,
            responseType: 'text',
        };
        const request = {...commonSettings, ...extraSettings()};
        LoadingService.startLoading();
        return ajax<T>(request).pipe(
            tap((res) => {
                renewExpiredArvoSession(request.url, res.xhr.responseURL);
            }),
            catchError((error: AjaxError) => catchExpiredSession(error, request)),
            // user session is valid - retry a failed request
            retry({
                delay: (error: AjaxError, index) => {
                    if (
                        index > retryCount ||
                        excludedStatusCodes.find((status) => status === error?.status)
                    ) {
                        console.log(error);
                        ErrorService.addHttpError(error, alertTable);
                        return throwError(() => error).pipe(observeOn(asyncScheduler));
                    }
                    return timer(retryDelayInMillis);
                },
                resetOnSuccess: true,
            }),
            tap((res) => hooks?.response(res)),
            map((res) => toJson<T>(res.response)),
        );
    }).pipe(finalize(() => LoadingService.endLoading()));
    if (isFetchOnce) {
        // Note: shareReplay() will not happen if error is thrown so all subscribers make new http call
        return observable.pipe(shareReplay());
    }
    return observable;
}

function httpRequestFactory(options: (() => AjaxRequest) | AjaxRequest, hooks?: Hooks) {
    const optionsFn = typeof options === 'function' ? options : () => options;
    return <T>(
        ...rest: [
            string,
            string,
            AlertTable?,
            any?,
            any?,
            boolean?,
            boolean?,
            boolean?,
            number?,
        ]
    ) => {
        const extenedArgs: [
            () => AjaxRequest,
            Hooks,
            string,
            string,
            AlertTable?,
            any?,
            any?,
            boolean?,
            boolean?,
            boolean?,
            number?,
        ] = [optionsFn, hooks, ...rest];
        return httpRequest<T>(...extenedArgs);
    };
}

type HttpType = <T>(
    method: string,
    url: string,
    alertTable?: AlertTable,
    headers?: any,
    body?: any,
    isFetchOnce?: boolean | undefined,
    crossDomain?: boolean | undefined,
    withCredentials?: boolean | undefined,
    timeout?: number | undefined,
) => Observable<T>;

const httpServiceFactory = (http: HttpType) => ({
    // Same observable can be used with multiple subscribers to get the same data without extra requests.
    getWithCache<T>(url: string, alertTable?: AlertTable): Observable<T> {
        const isFetchOnce = true;
        const body = null;
        const headers = {'Content-Type': 'application/json'};
        return http<T>('GET', url, alertTable, headers, body, isFetchOnce);
    },
    // Can be only used once by the first subscriber
    get<T>(
        url: string,
        queryParams?: {[key: string]: string},
        alertTable?: AlertTable,
    ): Observable<T> {
        if (queryParams) {
            url = appendUrlWithQueryParams(url, queryParams);
        }
        return http<T>('GET', url, alertTable);
    },
    post<T>(url: string, body?: any, alertTable?: AlertTable): Observable<T> {
        const headers = {'Content-Type': 'application/json'};
        return http<T>('POST', url, alertTable, headers, body);
    },
    put<T>(url: string, body?: any, alertTable?: AlertTable): Observable<T> {
        const headers = {'Content-Type': 'application/json'};
        return http<T>('PUT', url, alertTable, headers, body);
    },
    patch<T>(url: string, body?: any, alertTable?: AlertTable): Observable<T> {
        const headers = {'Content-Type': 'application/json'};
        return http<T>('PATCH', url, alertTable, headers, body);
    },
    delete<T>(url: string, alertTable?: AlertTable): Observable<T> {
        return http<T>('DELETE', url, alertTable);
    },
});

const isAllowCors = currentEnvironment.isDev;

const commonSettings = {
    withCredentials: isAllowCors,
    crossDomain: isAllowCors,
} as AjaxRequest;
export const commonHttp = httpServiceFactory(httpRequestFactory(() => commonSettings));

const arvoSettingsCallback = () =>
    ({
        headers: {
            'x-xsrf-token': Cookies.get('XSRF-TOKEN'),
        } as Readonly<Record<string, any>>, // This only works with common origin and not httpOnly
        withCredentials: true,
        crossDomain: isAllowCors,
    }) as AjaxRequest;
export const arvoHttp = httpServiceFactory(httpRequestFactory(arvoSettingsCallback));

const opintopolkuSettings = {
    async: false, // i18next intialization requires the resources are already downloaded
    headers: {'Caller-Id': 'csc.Valssi'} as Readonly<Record<string, any>>,
    crossDomain: true,
} as AjaxRequest;
export const opintopolkuHttp = httpServiceFactory(
    httpRequestFactory(opintopolkuSettings),
);

const vastauspalveluSettings = {
    withCredentials: false,
    crossDomain: isAllowCors,
} as AjaxRequest;
export const vastauspalveluHttp = httpServiceFactory(
    httpRequestFactory(vastauspalveluSettings),
);

// TODO: Dependency cycle makes impossible to use UserInfoType
const virkailijapalveluSettingsCallback = (user?: any) => {
    const authToken =
        virkailijapalveluTokens.access || Cookies.get('virkailijapalvelu_access_token');
    return {
        headers: {
            ...(authToken && {
                Authorization: `Bearer ${authToken}`,
            }),

            // Authorization: `Bearer ${authToken}`,
            ...(user?.impersonoitu_kayttaja && {
                'Impersonate-User': user.uid,
            }),
            ...(user?.vaihdettu_organisaatio && {
                'Impersonate-Organization': user.vaihdettu_organisaatio,
            }),
        } as Readonly<Record<string, any>>,
        withCredentials: true,
        crossDomain: isAllowCors,
    } as AjaxRequest;
};

// TODO: Dependency cycle makes impossible to use UserInfoType
const raportointipalveluSettingsCallback = (user?: any) => {
    const authToken =
        raportointipalveluTokens.access || Cookies.get('raportointipalvelu_access_token');
    return {
        headers: {
            ...(authToken && {
                Authorization: `Bearer ${authToken}`,
            }),

            // Authorization: `Bearer ${authToken}`,
            ...(user?.impersonoitu_kayttaja &&
                user.impersonoitu_kayttaja !== '' && {
                    'Impersonate-User': user.uid,
                }),
            ...(user?.vaihdettu_organisaatio &&
                user.vaihdettu_organisaatio !== '' && {
                    'Impersonate-Organization': user.vaihdettu_organisaatio,
                }),
        } as Readonly<Record<string, any>>,
        withCredentials: true,
        crossDomain: isAllowCors,
    } as AjaxRequest;
};

const virkailijapalveluHooks = {
    response: (res) => {
        const accessToken = res.responseHeaders['x-virkailijapalvelu-access-token'];
        if (accessToken) {
            virkailijapalveluTokens.access = accessToken;
        }
        const refreshToken = res.responseHeaders['x-virkailijapalvelu-access-token'];
        if (refreshToken) {
            virkailijapalveluTokens.refresh = refreshToken;
        }
    },
} as Hooks;

/**
 * refresh access token
 */
const raportointipalveluRefreshToken = `${raportointipalveluHostname}api/v1/token/refresh/`;
const virkailijapalveluRefreshToken = `${virkailijapalveluHostname}api/v1/token/refresh/`;

type RefreshTokenPostType = {
    refresh: string;
};

const refreshVirkailijapalveluAccessToken$ = (body: RefreshTokenPostType) =>
    commonHttp.post<any>(virkailijapalveluRefreshToken, body);

const refreshRaportointipalveluAccessToken$ = (body: RefreshTokenPostType) =>
    commonHttp.post<any>(raportointipalveluRefreshToken, body);

const raportointipalveluHooks = {
    response: (res) => {
        const accessRaportointiToken =
            res.responseHeaders['x-raportointipalvelu-access-token'];
        if (accessRaportointiToken) {
            raportointipalveluTokens.access = accessRaportointiToken;
        }
        const refreshRaportointiToken =
            res.responseHeaders['x-raportointipalvelu-refresh-token'];
        if (refreshRaportointiToken) {
            raportointipalveluTokens.refresh = refreshRaportointiToken;
        }
    },
} as Hooks;

// TODO: Dependency cycle makes impossible to use UserInfoType
export const virkailijapalveluHttpImpersonation = (user: any) =>
    httpServiceFactory(
        httpRequestFactory(
            virkailijapalveluSettingsCallback(user),
            virkailijapalveluHooks,
        ),
    );

export const virkailijapalveluHttp = httpServiceFactory(
    httpRequestFactory(virkailijapalveluSettingsCallback, virkailijapalveluHooks),
);

// TODO: Dependency cycle makes impossible to use UserInfoType
export const raportointipalveluHttpImpersonation = (user: any) =>
    httpServiceFactory(
        httpRequestFactory(
            raportointipalveluSettingsCallback(user),
            raportointipalveluHooks,
        ),
    );

export const raportointipalveluHttp = httpServiceFactory(
    httpRequestFactory(raportointipalveluSettingsCallback, raportointipalveluHooks),
);
