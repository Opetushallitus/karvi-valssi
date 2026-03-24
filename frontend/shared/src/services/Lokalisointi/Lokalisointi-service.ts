import {opintopolkuHostname} from '../Settings/Settings-service';
import {opintopolkuHttp} from '../Http/Http-service';

const opintopolkuServiceName = 'lokalisointi';
const opintopolkuLokalisointiBase = `${opintopolkuHostname}${opintopolkuServiceName}/`;
const lokalisointipalveluApiBase = `${opintopolkuLokalisointiBase}cxf/rest/v1/localisation`;

export type LocaleResult = {
    accesscount: number;
    id: number;
    category: string;
    key: string;
    accessed: number;
    created: number;
    createdBy: string;
    modified: number;
    modifiedBy: string;
    force: boolean;
    locale: string;
    value: string;
};
export type OpintopolkuTehtavanimikkeetType = {
    koodiArvo: string;
    koodiUri: string;
    koodisto: KoodistoType;
    metadata: Array<MetadataType>;
    paivittajaOid: string;
    paivitysPvm: string;
    resourceUri: string;
    tila: string;
    versio: number;
    version: number;
    voimassaAlkuPvm: string;
    voimassaLoppuPvm: string | null;
};
export type MetadataType = {
    eiSisallaMerkitysta: string;
    huomioitavaKoodi: string;
    kasite: string;
    kayttoohje: string;
    kieli: string;
    kuvaus: string;
    lyhytNimi: string;
    nimi: string;
    sisaltaaKoodiston: string;
    sisaltaaMerkityksen: string;
};
type KoodistoType = {
    koodistoUri: string;
    koodistoVersios: Array<number>;
    organisaatioOid: string;
};

const getOpintopolkuTranslations$ = (language: string) =>
    opintopolkuHttp.getWithCache<Array<LocaleResult>>(
        `${lokalisointipalveluApiBase}?category=valssi&locale=${language}`,
    );

export default getOpintopolkuTranslations$;
