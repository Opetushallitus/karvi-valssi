import {useEffect, useState} from 'react';
import {useTranslation} from 'react-i18next';
import {forkJoin} from 'rxjs';
import {Box} from '@mui/material';
import Grid from '@mui/material/Grid';
import {useNavigate, useLocation} from 'react-router-dom';
import {KyselyType, TextType} from '@cscfi/shared/services/Data/Data-service';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import DateRangePickerField from '@cscfi/shared/components/DateRangePickerField/DateRangePickerField';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import GenericTextField from '@cscfi/shared/components/GenericTextField/GenericTextField';
import {
    capitalize,
    getQueryParamAsNumber,
    kyselyNameGenerator,
} from '@cscfi/shared/utils/helpers';
import {format, toDate, parseISO, isSameDay, isBefore} from 'date-fns';
import {
    arvoGetKysymysryhma$,
    convertKysymyksetArvoToValssi,
    arvoGetOppilaitos$,
    arvoGetAllKyselyt$,
    ArvoOppilaitos,
    ArvoKysymysryhma,
    ArvoKysely,
    ArvoKyselyPost,
    ArvoKyselyMassPost,
    arvoMassAddKysely$,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import AlertService, {AlertType} from '@cscfi/shared/services/Alert/Alert-service';
import {AjaxError} from 'rxjs/ajax';
import {toJson} from '@cscfi/shared/services/Http/Http-service';
import SinglePanelAccordion from '../../components/SinglePanelAccordion/SinglePanelAccordion';
import AktivointiList from './AktivointiList/AktivointiList';
import AktivoidutList from './AktivoidutList/AktivoidutList';
import {not} from './utils';
import styles from './Aktivointi.module.css';

function Aktivointi() {
    const navigate = useNavigate();
    const location = useLocation();
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['aktivointi']);
    const [kysely, setKysely] = useState<KyselyType | null>(null);
    const [saate, setSaate] = useState<string>('');
    const [startDate, handleStartDateChange] = useState<Date | null>(toDate(Date.now()));
    const [endDate, handleEndDateChange] = useState<Date | null>(null);
    const [valittavat, setValittavat] = useState<ArvoOppilaitos[]>([]);
    const [valitut, setValitut] = useState<ArvoOppilaitos[]>([]);
    const [aktivoidut, setAktivoidut] = useState<ArvoOppilaitos[]>([]);
    const [lahdeKysely, setLahdeKysely] = useState<ArvoKysely>();

    const formDirty =
        valitut.length > 0 || (!lahdeKysely && (saate.trim() !== '' || endDate !== null));

    const formInvalid =
        saate.trim() === '' ||
        !(startDate instanceof Date && !(startDate?.toString() === 'Invalid Date')) ||
        !(endDate instanceof Date && !(endDate?.toString() === 'Invalid Date')) ||
        valitut.length === 0;

    /* just fo debug use */
    // const removeKyselyt = (akt: ArvoKysely[]) => {
    //     akt.forEach((ak) => {
    //         arvoDeleteKysely$(ak.kyselyid).subscribe((k: ArvoKysely) => {
    //             console.log('kysely removed', k.kyselyid);
    //         });
    //     });
    // };

    useEffect(() => {
        const kysymysryhmaId = getQueryParamAsNumber(location, 'id');
        if (kysymysryhmaId) {
            const queries = forkJoin([
                arvoGetKysymysryhma$(kysymysryhmaId),
                arvoGetOppilaitos$(),
                arvoGetAllKyselyt$(),
            ]);

            queries.subscribe(
                ([kysymysryhma, paivakodit, kayttajanKyselyt]: [
                    kysymysryhma: ArvoKysymysryhma,
                    paivakodit: ArvoOppilaitos[],
                    kayttajanKyselyt: ArvoKysely[],
                ]) => {
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
                    };
                    setKysely(valssiKysely);

                    // find existing kysely related to this kysymysryyhma
                    const filteredKyselyt = kayttajanKyselyt.filter((ak: ArvoKysely) => {
                        const loppu = parseISO(ak.voimassa_loppupvm);
                        const nyt = new Date();

                        return (
                            ak.metatiedot.valssi_kysymysryhma === valssiKysely.id &&
                            (isSameDay(nyt, loppu) || isBefore(nyt, loppu))
                        );
                    });

                    // pop first kysely to fill up saate and date fields
                    const existingKysely = filteredKyselyt.find((e) => !!e);
                    if (existingKysely) {
                        setLahdeKysely(existingKysely);
                        handleStartDateChange(parseISO(existingKysely.voimassa_alkupvm));
                        handleEndDateChange(parseISO(existingKysely.voimassa_loppupvm));
                        setSaate(existingKysely.metatiedot.valssi_saate);
                    }

                    // loop trough related kyselyt to find activated toimipaikat
                    const oidList = filteredKyselyt.map((f: ArvoKysely) => f.oppilaitos);
                    const aktivoidutLista = paivakodit.filter((ao: ArvoOppilaitos) =>
                        oidList.includes(ao.oid),
                    );

                    setAktivoidut(aktivoidutLista);
                    setValittavat(not(paivakodit, aktivoidutLista));
                },
            );
        }
    }, [location]);

    if (kysely === null) {
        return null;
    }

    const massaSyottoPost = (
        toimipaikat: ArvoOppilaitos[],
        kysymysryhma: KyselyType,
        nameExtender?: number,
    ): ArvoKyselyMassPost => {
        const alkupvm = format(startDate!, 'yyyy-MM-dd');
        const loppupvm = format(endDate!, 'yyyy-MM-dd');
        return {
            kyselyt: toimipaikat.map((toimipaikka) => {
                const nimi = kyselyNameGenerator(
                    kysymysryhma,
                    startDate,
                    toimipaikka,
                    nameExtender,
                );

                return {
                    tila: 'julkaistu',
                    voimassa_alkupvm: alkupvm,
                    voimassa_loppupvm: loppupvm,
                    nimi_fi: nimi.fi,
                    nimi_sv: nimi.sv,
                    oppilaitos: toimipaikka.oid,
                    tyyppi: kysymysryhma.lomaketyyppi,
                    metatiedot: {
                        valssi_saate: saate,
                        valssi_kysymysryhma: kysymysryhma.id,
                    },
                    kyselykerrat: [
                        {
                            nimi: nimi.fi,
                            voimassa_alkupvm: alkupvm,
                            voimassa_loppupvm: loppupvm,
                        },
                    ],
                    kysymysryhmat: [
                        {
                            kysymysryhmaid: kysymysryhma.id,
                        },
                    ],
                } as ArvoKyselyPost;
            }),
        };
    };

    const handleKayttoonOtto = (retryCounter = 0) => {
        const maxRetry = 2;

        arvoMassAddKysely$(
            massaSyottoPost(
                valitut,
                kysely!,
                retryCounter > 0 ? retryCounter + 1 : undefined,
            ),
        ).subscribe({
            next: (kyselyt) => {
                console.log('kyselyt', kyselyt);
            },
            complete: () => {
                const alert = {
                    title: {key: 'alert-success-title', ns: 'aktivointi'},
                    severity: 'success',
                } as AlertType;
                AlertService.showAlert(alert);
                navigate(`/tiedonkeruu`);
            },
            error: (error: AjaxError) => {
                const errorMsgRaw: string | string[] = toJson(error.response);
                const sameNameError = 'kysely.massasyotto.samanniminen';
                if (
                    Array.isArray(errorMsgRaw)
                        ? errorMsgRaw.some((errorMsg: string) =>
                              errorMsg.startsWith(sameNameError),
                          )
                        : errorMsgRaw.startsWith(sameNameError)
                ) {
                    if (retryCounter < maxRetry) {
                        handleKayttoonOtto(retryCounter + 1);
                    }
                }

                const alert = {
                    title: {key: 'alert-error-title', ns: 'aktivointi'},
                    severity: 'error',
                } as AlertType;
                AlertService.showAlert(alert);
                // navigate(`/tiedonkeruu`);
            },
        });
    };

    return (
        <>
            <h1>{t('sivun-otsikko')}</h1>

            <SinglePanelAccordion
                alignLeft
                alignColumn
                openText={t('esikatselu-avaa', {ns: 'yleiset'})}
                closeText={t('esikatselu-sulje', {ns: 'yleiset'})}
                title={`${kysely ? kysely.topic[lang as keyof TextType] : ''}`}
            >
                <Box sx={{maxWidth: 'md'}}>
                    <Kysely selectedKysely={kysely} />
                </Box>
            </SinglePanelAccordion>

            <div className={styles['section-container']}>
                <GenericTextField
                    value={saate}
                    fullWidth
                    label={t('saateviesti-label')}
                    onChange={setSaate}
                    multiLine
                    multiLineResize
                    disabled={lahdeKysely != null}
                    required
                />
            </div>

            <div className={styles['section-container']}>
                <h3>{capitalize(t('vastausaika', {ns: 'lahetys'}))}</h3>
                <DateRangePickerField
                    labelStart={t('alkupvm')}
                    labelEnd={t('loppupvm')}
                    rangeMin={toDate(Date.now())}
                    dateStart={startDate || undefined}
                    dateEnd={endDate || undefined}
                    onChangeStart={handleStartDateChange}
                    onChangeEnd={handleEndDateChange}
                    disabled={lahdeKysely != null}
                    required
                />
            </div>

            <div className={styles['section-container']}>
                <h3>{capitalize(t('valinta-otsikko'))} *</h3>
                <Grid container spacing={2}>
                    <AktivointiList
                        left={valittavat}
                        setLeft={setValittavat}
                        right={valitut}
                        setRight={setValitut}
                    />
                    {aktivoidut.length > 0 && <AktivoidutList list={aktivoidut} />}
                </Grid>
            </div>

            <p className={styles['required-fields-info']}>
                {t('pakolliset-kentat-info', {ns: 'yleiset'})}
            </p>

            <div className={styles['section-container']}>
                <Grid container spacing={2}>
                    <Grid item>
                        {!formDirty ? (
                            <button
                                className="secondary"
                                type="button"
                                onClick={() => navigate(`/`)}
                            >
                                {t('peruuta')}
                            </button>
                        ) : (
                            <ConfirmationDialog
                                title={t('painike-takaisin-otsikko')}
                                confirmBtnText={t('painike-kylla', {ns: 'yleiset'})}
                                cancelBtnText={t('painike-takaisin-cancel')}
                                confirm={() => navigate(`/`)}
                                content={<p>{t('painike-takaisin-teksti')}</p>}
                            >
                                <button type="button" className="secondary">
                                    {t('painike-takaisin')}
                                </button>
                            </ConfirmationDialog>
                        )}
                    </Grid>
                    <Grid item>
                        <ConfirmationDialog
                            title={t('konfirmaatio-otsikko')}
                            confirm={handleKayttoonOtto}
                            confirmBtnText={t('painike-aktivoi')}
                            content={
                                <>
                                    <p>{t('konfirmaatio-sisalto')}</p>
                                    <ol>
                                        {valitut.map((valittu: ArvoOppilaitos) => {
                                            const oppilaitosNimi =
                                                `nimi_${lang}` as keyof ArvoOppilaitos;
                                            return (
                                                <li key={valittu.oid}>
                                                    {valittu[oppilaitosNimi]}
                                                </li>
                                            );
                                        })}
                                    </ol>
                                </>
                            }
                        >
                            <button type="button" disabled={formInvalid}>
                                {t('painike-aktivoi')}
                            </button>
                        </ConfirmationDialog>
                    </Grid>
                </Grid>
            </div>
        </>
    );
}

export default Aktivointi;
