import i18n, {use} from 'i18next';
import type {BackendModule, Resource} from 'i18next';
import {initReactI18next} from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import BackendAdapter from 'i18next-multiload-backend-adapter';
import {currentEnvironment} from '../services/Settings/Settings-service';
import getOpintopolkuTranslations$, {
    LocaleResult,
} from '../services/Lokalisointi/Lokalisointi-service';

type TranslationResult = {
    [key: string]: string;
};

type NamespacesType = {
    [namespace: string]: TranslationResult;
};

type ResourcesType = {
    [language: string]: NamespacesType;
};

export enum LanguageOptions {
    fi = 'fi',
    sv = 'sv',
}

export const defaultLanguage = LanguageOptions.fi;

function extractTranslationKeys(
    translations: Array<LocaleResult>,
    namespaces: NamespacesType,
) {
    /*
    We get a list of namespaces, but currently Lokalisointipalvelu doesn't use namespaces so we have to fetch
    all keys using the current language.
    */
    translations.forEach((translation: LocaleResult) => {
        const {key} = translation; // key includes namespace, e.g. kyselyt.ei-kyselya
        const {value} = translation;
        const [namespace, actualKey] = key.split('.');
        if (!(namespace in namespaces)) {
            namespaces[namespace] = {};
        }
        namespaces[namespace][actualKey] = value;
    });
    return namespaces;
}

function fetchTranslations(languages: readonly string[]): Resource {
    /*
    Fetch translations from SessionStorage. If not found, fetch from Lokalisointipalvelu.
    */
    const resources: ResourcesType = {};
    languages.forEach((lng) => {
        resources[lng] = {};
        const savedTranslations = sessionStorage.getItem(`translations_${lng}`);
        if (savedTranslations === null) {
            getOpintopolkuTranslations$(lng).subscribe((translations) => {
                sessionStorage.setItem(
                    `translations_${lng}`,
                    JSON.stringify(translations),
                );

                resources[lng] = extractTranslationKeys(translations, resources[lng]);
            });
        } else {
            const translations = JSON.parse(savedTranslations);
            resources[lng] = extractTranslationKeys(translations, resources[lng]);
        }
    });
    return resources;
}

const CustomBackendModule: BackendModule = {
    type: 'backend',
    init: () => null,
    read: () => null,
    create: () => null,
    readMulti: (languages, namespaces, callback) => {
        callback(null, fetchTranslations(languages));
    },
    save: () => null,
};

use(LanguageDetector)
    .use(BackendAdapter)
    .use(initReactI18next)
    .init({
        fallbackLng: defaultLanguage,
        supportedLngs: Object.values(LanguageOptions),
        ns: [
            'datepicker',
            'guard',
            'form',
            'kysely',
            'login',
            'arvtyok',
            'rakennakysely',
            'raporttipohja',
            'raportointi',
            'esikatselu',
            'yleiset',
            'ulkoasu',
            'aktivointi',
            'lahetys',
            'vastaa-kysely',
            'kiitos',
            'etusivu',
            'indik',
            'alert',
            'tiedonkeruun-seuranta',
            'yhteenveto',
            'genericform',
            'impersonointi-avustus',
            'impersonointi-organisaatio',
            'impersonointi-rooli',
            'confirmation',
            'arviointitulokset',
            'saavutettavuus',
        ],
        defaultNS: 'kysely',
        backend: {
            backend: CustomBackendModule,
        },
        load: 'currentOnly',
        lowerCaseLng: true,
        interpolation: {
            escapeValue: false,
        },
        debug: currentEnvironment.isDev,
        react: {
            useSuspense: false,
        },
    });

export default i18n;
