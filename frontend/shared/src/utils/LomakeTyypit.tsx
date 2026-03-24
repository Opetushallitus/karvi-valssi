/*
 * Huom: samat lomaketyypit on määritelty Valssin Arvo-instanssin kyselytyypeiksi.
 * Jos lomaketyyppeihin tehdään muutoksia, pitää samat muutokset tehdä myös Arvo-instanssin.
 */

import {KyselyType} from '@cscfi/shared/services/Data/Data-service';

// Lomaketyyppi code as comment
enum LomakeTyyppi {
    henkilostolomake_prosessitekijat = 'henkilostolomake_prosessitekijat', // 3
    henkilostolomake_rakennetekijat = 'henkilostolomake_rakennetekijat', // 7
    henkilostolomake_palaute = 'henkilostolomake_palaute', // 3P
    henkilostolomake_kansallinen = 'henkilostolomake_kansallinen', // 3K
    huoltajalomake_prosessitekijat = 'huoltajalomake_prosessitekijat', // 4
    huoltajalomake_rakennetekijat = 'huoltajalomake_rakennetekijat', // 8
    taydennyskoulutuslomake_rakennetekijat = 'taydennyskoulutuslomake_rakennetekijat', // 91
    taydennyskoulutuslomake_paakayttaja_rakennetekijat = 'taydennyskoulutuslomake_paakayttaja_rakennetekijat', // 92
    asiantuntijalomake_paivakoti_prosessitekijat = 'asiantuntijalomake_paivakoti_prosessitekijat', // 2
    asiantuntijalomake_paivakoti_rakennetekijat = 'asiantuntijalomake_paivakoti_rakennetekijat', // 61
    asiantuntijalomake_paakayttaja_prosessitekijat = 'asiantuntijalomake_paakayttaja_prosessitekijat', // 1
    asiantuntijalomake_paakayttaja_rakennetekijat = 'asiantuntijalomake_paakayttaja_rakennetekijat', // 62
    asiantuntijalomake_palaute = 'asiantuntijalomake_palaute', // 62P
    asiantuntijalomake_kansallinen = 'asiantuntijalomake_kansallinen', // 62K
    asiantuntijalomake_paivakoti_kansallinen = 'asiantuntijalomake_paivakoti_kansallinen', // 61K
}

export const lomakeTyypitList = [
    LomakeTyyppi.henkilostolomake_prosessitekijat,
    LomakeTyyppi.henkilostolomake_rakennetekijat,
    LomakeTyyppi.henkilostolomake_palaute,
    LomakeTyyppi.henkilostolomake_kansallinen,
    LomakeTyyppi.huoltajalomake_prosessitekijat,
    LomakeTyyppi.huoltajalomake_rakennetekijat,
    LomakeTyyppi.taydennyskoulutuslomake_rakennetekijat,
    LomakeTyyppi.taydennyskoulutuslomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_palaute,
    LomakeTyyppi.asiantuntijalomake_kansallinen,
    LomakeTyyppi.asiantuntijalomake_paivakoti_kansallinen,
];

export const lomakeTyypitProsessitekijaList = [
    LomakeTyyppi.henkilostolomake_prosessitekijat,
    LomakeTyyppi.huoltajalomake_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_prosessitekijat,
];

export const lomakeTyypitRakennetekijaList = [
    LomakeTyyppi.henkilostolomake_rakennetekijat,
    LomakeTyyppi.huoltajalomake_rakennetekijat,
    LomakeTyyppi.taydennyskoulutuslomake_rakennetekijat,
    LomakeTyyppi.taydennyskoulutuslomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_rakennetekijat,
];

export const lomakeTyypitKansallisetList = [
    LomakeTyyppi.henkilostolomake_palaute,
    LomakeTyyppi.henkilostolomake_kansallinen,
    LomakeTyyppi.asiantuntijalomake_palaute,
    LomakeTyyppi.asiantuntijalomake_kansallinen,
    LomakeTyyppi.asiantuntijalomake_paivakoti_kansallinen,
];

export const paakayttajaLomakkeet = [
    LomakeTyyppi.taydennyskoulutuslomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_palaute,
    LomakeTyyppi.asiantuntijalomake_kansallinen,
];

export const huoltajaLomakkeet = [
    LomakeTyyppi.huoltajalomake_rakennetekijat,
    LomakeTyyppi.huoltajalomake_prosessitekijat,
];

export const henkilostoLomakkeet = [
    LomakeTyyppi.henkilostolomake_prosessitekijat,
    LomakeTyyppi.henkilostolomake_rakennetekijat,
    LomakeTyyppi.henkilostolomake_palaute,
    LomakeTyyppi.henkilostolomake_kansallinen,
];

export const taydennyskoulutusLomakkeet = [
    LomakeTyyppi.taydennyskoulutuslomake_rakennetekijat,
];

export const toteuttajanAsiantuntijaLomakkeet = [
    LomakeTyyppi.asiantuntijalomake_paivakoti_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_kansallinen,
];
export const asiantuntijaLomakkeet = [
    LomakeTyyppi.taydennyskoulutuslomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_kansallinen,
];

export const vardaLomakkeet = [
    LomakeTyyppi.henkilostolomake_prosessitekijat,
    LomakeTyyppi.henkilostolomake_rakennetekijat,
    LomakeTyyppi.taydennyskoulutuslomake_rakennetekijat,
    LomakeTyyppi.taydennyskoulutuslomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.henkilostolomake_palaute,
    LomakeTyyppi.henkilostolomake_kansallinen,
];

export const isTypeOf = (listOfTypes: LomakeTyyppi[], valssikysely: KyselyType) =>
    listOfTypes.includes(valssikysely.lomaketyyppi as LomakeTyyppi);

export default LomakeTyyppi;
