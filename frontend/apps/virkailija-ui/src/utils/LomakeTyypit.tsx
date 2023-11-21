/*
 * Huom: samat lomaketyypit on määritelty Valssin Arvo-instanssin kyselytyypeiksi.
 * Jos lomaketyyppeihin tehdään muutoksia, pitää samat muutokset tehdä myös Arvo-instanssin.
 */

enum LomakeTyyppi {
    henkilostolomake_prosessitekijat = 'henkilostolomake_prosessitekijat',
    henkilostolomake_rakennetekijat = 'henkilostolomake_rakennetekijat',
    huoltajalomake_prosessitekijat = 'huoltajalomake_prosessitekijat',
    huoltajalomake_rakennetekijat = 'huoltajalomake_rakennetekijat',
    taydennyskoulutuslomake_rakennetekijat = 'taydennyskoulutuslomake_rakennetekijat',
    taydennyskoulutuslomake_paakayttaja_rakennetekijat = 'taydennyskoulutuslomake_paakayttaja_rakennetekijat',
    asiantuntijalomake_paivakoti_prosessitekijat = 'asiantuntijalomake_paivakoti_prosessitekijat',
    asiantuntijalomake_paivakoti_rakennetekijat = 'asiantuntijalomake_paivakoti_rakennetekijat',
    asiantuntijalomake_paakayttaja_prosessitekijat = 'asiantuntijalomake_paakayttaja_prosessitekijat',
    asiantuntijalomake_paakayttaja_rakennetekijat = 'asiantuntijalomake_paakayttaja_rakennetekijat',
}

export const lomakeTyypitList = [
    LomakeTyyppi.henkilostolomake_prosessitekijat,
    LomakeTyyppi.henkilostolomake_rakennetekijat,
    LomakeTyyppi.huoltajalomake_prosessitekijat,
    LomakeTyyppi.huoltajalomake_rakennetekijat,
    LomakeTyyppi.taydennyskoulutuslomake_rakennetekijat,
    LomakeTyyppi.taydennyskoulutuslomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_rakennetekijat,
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

export const paakayttajaLomakkeet = [
    LomakeTyyppi.taydennyskoulutuslomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_rakennetekijat,
];

export const huoltajaLomakkeet = [
    LomakeTyyppi.huoltajalomake_rakennetekijat,
    LomakeTyyppi.huoltajalomake_prosessitekijat,
];

export const henkilostoLomakkeet = [
    LomakeTyyppi.henkilostolomake_prosessitekijat,
    LomakeTyyppi.henkilostolomake_rakennetekijat,
];

export const taydennyskoulutusLomakkeet = [
    LomakeTyyppi.taydennyskoulutuslomake_rakennetekijat,
];

export const toteuttajanAsiantuntijaLomakkeet = [
    LomakeTyyppi.asiantuntijalomake_paivakoti_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat,
];
export const asiantuntijaLomakkeet = [
    LomakeTyyppi.taydennyskoulutuslomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paakayttaja_rakennetekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_prosessitekijat,
    LomakeTyyppi.asiantuntijalomake_paivakoti_rakennetekijat,
];

export default LomakeTyyppi;
