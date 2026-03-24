const valssiUiQAHostName = ['qa-valssi.karvi.fi', 'qa-valssivastaus.karvi.fi'];
const valssiUiProdHostNames = ['valssi.karvi.fi', 'valssivastaus.karvi.fi'];

export const currentEnvironment = {
    isDev: import.meta.env.MODE === 'development',
    isProd:
        import.meta.env.MODE === 'production' &&
        valssiUiProdHostNames.includes(window.location.host),
    isQA:
        import.meta.env.MODE === 'production' &&
        valssiUiQAHostName.includes(window.location.host),
    isOtherEnv:
        import.meta.env.MODE === 'production' &&
        !valssiUiProdHostNames.includes(window.location.host) &&
        !valssiUiQAHostName.includes(window.location.host),
};

export const getEnv = (defaultValue?: string, override?: string): string => {
    const envValue = currentEnvironment.isProd ? override : defaultValue;
    console.assert(!!envValue, `Undefined environment value ${envValue}`);
    return envValue || '';
};

const getEnvCurrent = (path: string, envValue: string): string =>
    // Use current hostname if not in development, running tests, QA or prod.
    currentEnvironment.isOtherEnv ? window.location.origin + path : envValue;

export const opintopolkuHostname = getEnv(
    import.meta.env.VITE_APP_OPINTOPOLKU_HOSTNAME,
    import.meta.env.VITE_APP_OPINTOPOLKU_HOSTNAME_PROD,
);
export const arvoHostname = getEnvCurrent(
    '/arvo/',
    getEnv(
        import.meta.env.VITE_APP_ARVO_HOSTNAME,
        import.meta.env.VITE_APP_ARVO_HOSTNAME_PROD,
    ),
);

export const vastauspalveluHostname =
    import.meta.env.BASE_URL === '/vastaaja-ui/'
        ? getEnvCurrent(
              '/vastauspalvelu/',
              getEnv(
                  import.meta.env.VITE_APP_VASTAUSPALVELU_HOSTNAME,
                  import.meta.env.VITE_APP_VASTAUSPALVELU_HOSTNAME_PROD,
              ),
          )
        : null;

export const casHostname = getEnvCurrent(
    '/cas/',
    getEnv(
        import.meta.env.VITE_APP_CAS_HOSTNAME,
        import.meta.env.VITE_APP_CAS_HOSTNAME_PROD,
    ),
);

export const virkailijapalveluHostname = getEnvCurrent(
    '/virkailijapalvelu/',
    getEnv(
        import.meta.env.VITE_APP_VIRKAILIJAPALVELU_HOSTNAME,
        import.meta.env.VITE_APP_VIRKAILIJAPALVELU_HOSTNAME_PROD,
    ),
);

export const raportointipalveluHostname = getEnvCurrent(
    '/raportointipalvelu/',
    getEnv(
        import.meta.env.VITE_APP_RAPORTOINTIPALVELU_HOSTNAME,
        import.meta.env.VITE_APP_RAPORTOINTIPALVELU_HOSTNAME_PROD,
    ),
);

export const raportiointipalveluLoginUrl = `${raportointipalveluHostname}accounts/login`;

export const virkailijapalveluLoginUrl = `${virkailijapalveluHostname}accounts/login`;

export const raportiointipalveluLogoutUrl = `${raportointipalveluHostname}accounts/logout`;

export const virkailijapalveluLogoutUrl = `${virkailijapalveluHostname}accounts/logout`;
