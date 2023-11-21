const valssiUiQAHostName = ['qa-valssi.karvi.fi', 'qa-valssivastaus.karvi.fi'];
const valssiUiProdHostNames = ['valssi.karvi.fi', 'valssivastaus.karvi.fi'];

export const currentEnvironment = {
    isDev: process.env.NODE_ENV === 'development',
    isProd:
        process.env.NODE_ENV === 'production' &&
        valssiUiProdHostNames.includes(window.location.host),
    isQA:
        process.env.NODE_ENV === 'production' &&
        valssiUiQAHostName.includes(window.location.host),
    isOtherEnv:
        process.env.NODE_ENV === 'production' &&
        !valssiUiProdHostNames.includes(window.location.host) &&
        !valssiUiQAHostName.includes(window.location.host),
};

export const getEnv = (defaultValue?: string, override?: string): string => {
    const envValue = currentEnvironment.isProd ? override : defaultValue;
    console.assert(envValue, `Undefined environment value ${envValue}`);
    return envValue || '';
};

const getEnvCurrent = (path: string, envValue: string): string =>
    // Use current hostname if not in development, running tests, QA or prod.
    currentEnvironment.isOtherEnv ? window.location.origin + path : envValue;

export const opintopolkuHostname = getEnv(
    process.env.REACT_APP_OPINTOPOLKU_HOSTNAME,
    process.env.REACT_APP_OPINTOPOLKU_HOSTNAME_PROD,
);
export const arvoHostname = getEnvCurrent(
    '/arvo/',
    getEnv(process.env.REACT_APP_ARVO_HOSTNAME, process.env.REACT_APP_ARVO_HOSTNAME_PROD),
);

export const vastauspalveluHostname = getEnvCurrent(
    '/vastauspalvelu/',
    getEnv(
        process.env.REACT_APP_VASTAUSPALVELU_HOSTNAME,
        process.env.REACT_APP_VASTAUSPALVELU_HOSTNAME_PROD,
    ),
);

export const casHostname = getEnvCurrent(
    '/cas/',
    getEnv(process.env.REACT_APP_CAS_HOSTNAME, process.env.REACT_APP_CAS_HOSTNAME_PROD),
);

export const virkailijapalveluHostname = getEnvCurrent(
    '/virkailijapalvelu/',
    getEnv(
        process.env.REACT_APP_VIRKAILIJAPALVELU_HOSTNAME,
        process.env.REACT_APP_VIRKAILIJAPALVELU_HOSTNAME_PROD,
    ),
);

export const raportointipalveluHostname = getEnvCurrent(
    '/raportointipalvelu/',
    getEnv(
        process.env.REACT_APP_RAPORTOINTIPALVELU_HOSTNAME,
        process.env.REACT_APP_RAPORTOINTIPALVELU_HOSTNAME_PROD,
    ),
);

export const raportiointipalveluLoginUrl = `${raportointipalveluHostname}accounts/login`;

export const virkailijapalveluLogin = `${virkailijapalveluHostname}accounts/login`;
