import {useContext, useEffect, useRef, useState} from 'react';
import GenericTextField from '@cscfi/shared/components/GenericTextField/GenericTextField';
import {Controller, SubmitHandler, useForm, UseFormProps} from 'react-hook-form';
import Grid from '@mui/material/Grid';
import WarningIcon from '@mui/icons-material/Warning';
import {useNavigate, useParams} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import {
    AlueFormType,
    OppilaitosSetType,
    virkailijapalveluCreateAlue$,
    virkailijapalveluDeleteAlue,
    virkailijapalveluGetAluejako$,
    virkailijapalveluModifyAlue$,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import AlertService from '@cscfi/shared/services/Alert/Alert-service';
import ButtonWithLink from '../../../components/ButtonWithLink/ButtonWithLink';
import SelectionList from '../../../components/ToimipaikkaSelectionList/SelectionList';
import styles from '../Aluejako.module.css';
import UserContext from '../../../Context';
import {flattenItems, getDefaultEmptySet, itemsNot} from '../../../utils/helpers';

function MuokkaaAluetta() {
    type MuokkaaAluettaParams = {
        alueId: string;
    };
    const params = useParams<MuokkaaAluettaParams>();
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['aluejako']);

    const navigate = useNavigate();
    const submitRef = useRef<any | null>(null);
    const userInfo = useContext(UserContext);

    const [left, setLeft] = useState<OppilaitosSetType>(getDefaultEmptySet());
    const [right, setRight] = useState<OppilaitosSetType>(getDefaultEmptySet());

    const minimumNumOfOrgs = 3;

    const formMethods = useForm<AlueFormType>({
        criteriaMode: 'firstError',
        defaultValues: {
            koulutustoimija: '',
            name_fi: '',
            name_sv: '',
            toimipaikkaList: getDefaultEmptySet(),
        },
    } as UseFormProps<AlueFormType>);

    const {handleSubmit, control, reset, getValues, setValue, formState} = formMethods;

    useEffect(() => {
        setValue('koulutustoimija', userInfo?.arvoAktiivinenRooli.organisaatio || '');
    }, [setValue, userInfo?.arvoAktiivinenRooli.organisaatio]);

    useEffect(() => {
        virkailijapalveluGetAluejako$(userInfo!)(
            userInfo?.arvoAktiivinenRooli.organisaatio || '',
        ).subscribe((alueet) => {
            const newOppilaitos: OppilaitosSetType = {
                grouped: alueet.grouped,
                ungrouped: alueet.ungrouped,
            };

            if (params.alueId) {
                const thisAlue = alueet.grouped.find(
                    (alue) => alue.id?.toString() === params.alueId,
                );
                if (!thisAlue) return;
                const rightItems: OppilaitosSetType = {
                    grouped: [thisAlue],
                    ungrouped: getDefaultEmptySet().ungrouped,
                };
                setRight(rightItems);
                setLeft(itemsNot(newOppilaitos, rightItems));
                reset({
                    ...getValues(),
                    name_fi: thisAlue.name.fi,
                    name_sv: thisAlue.name.sv,
                    toimipaikkaList: rightItems,
                });
            } else {
                setLeft({grouped: [], ungrouped: newOppilaitos.ungrouped});
            }
        });
    }, [getValues, params.alueId, reset, setValue, userInfo]);

    const handleDelete = () => {
        virkailijapalveluDeleteAlue(userInfo!)({
            koulutustoimija: userInfo?.arvoAktiivinenRooli.organisaatio || '',
            id: typeof params.alueId === 'string' ? parseInt(params.alueId, 10) : -1,
        }).subscribe({
            complete: () => {
                AlertService.showAlert({
                    title: {
                        key: 'alert-removing-success-title',
                        ns: 'aluejako',
                    },
                    severity: 'success',
                });
                navigate(`/aluejako`);
            },
            error: (err) => {
                console.error('Error while creating:', err);
                AlertService.showAlert({
                    title: {
                        key: 'alert-removing-error-title',
                        ns: 'aluejako',
                    },
                    severity: 'warning',
                });
            },
        });
    };

    const handleSendAlue = (formData: AlueFormType) => {
        const modifiedData = {
            ...formData,
            id: params.alueId,
            oppilaitos_oids: flattenItems(formData.toimipaikkaList, lang).map(
                (tp) => tp.oid,
            ),
        };
        if (!params.alueId) {
            virkailijapalveluCreateAlue$(userInfo!)(modifiedData).subscribe({
                next: (res) => {
                    virkailijapalveluModifyAlue$(userInfo!)({
                        ...modifiedData,
                        id: res.id,
                    }).subscribe({
                        complete: () => {
                            AlertService.showAlert({
                                title: {
                                    key: 'alert-adding-success-title',
                                    ns: 'aluejako',
                                },
                                severity: 'success',
                            });
                            navigate(`/aluejako`);
                        },
                        error: (err) => {
                            console.warn('Error while removing:', err);
                            AlertService.showAlert({
                                title: {
                                    key: 'alert-modifying-error-title',
                                    ns: 'aluejako',
                                },
                                severity: 'error',
                            });
                        },
                    });
                },
                error: (err) => {
                    console.error('Error while creating:', err);
                    AlertService.showAlert({
                        title: {key: 'alert-creation-error-title', ns: 'aluejako'},
                        severity: 'error',
                    });
                },
            });
        } else {
            virkailijapalveluModifyAlue$(userInfo!)(modifiedData).subscribe({
                complete: () => {
                    AlertService.showAlert({
                        title: {
                            key: 'alert-modifying-success-title',
                            ns: 'aluejako',
                        },
                        severity: 'success',
                    });
                    navigate(`/aluejako`);
                },
                error: (err) => {
                    console.error('Error while modifying:', err);
                    AlertService.showAlert({
                        title: {
                            key: 'alert-modifying-error-title',
                            ns: 'aluejako',
                        },
                        severity: 'error',
                    });
                },
            });
        }
    };

    const onSubmit: SubmitHandler<AlueFormType> = (formData) => {
        handleSendAlue(formData);
    };

    return (
        <>
            <h1>
                {params.alueId
                    ? t('muokkaa-aluetta-otsikko')
                    : t('luo-uusi-sivun-otsikko')}
            </h1>

            <form onSubmit={handleSubmit(onSubmit)}>
                {!params.alueId && (
                    <div className={styles.groupNameFields}>
                        <Controller
                            name="name_fi"
                            control={control}
                            render={({field}) => (
                                <GenericTextField
                                    autoFocus
                                    fullWidth
                                    autoComplete={false}
                                    required
                                    value={field.value}
                                    onChange={field.onChange}
                                    label={t('alueen-nimi-suomeksi')}
                                />
                            )}
                        />
                        <Controller
                            name="name_sv"
                            control={control}
                            render={({field}) => (
                                <GenericTextField
                                    fullWidth
                                    autoComplete={false}
                                    value={field.value}
                                    required
                                    onChange={field.onChange}
                                    label={t('alueen-nimi-ruotsiksi')}
                                />
                            )}
                        />
                    </div>
                )}
                <div>
                    <Controller
                        name="toimipaikkaList"
                        control={control}
                        rules={
                            {
                                validate: (value: OppilaitosSetType) =>
                                    flattenItems(value, lang).length >= minimumNumOfOrgs,
                            } as any
                        }
                        render={({field, fieldState}) => {
                            const {onChange} = field;
                            const {error} = fieldState;
                            return (
                                <>
                                    <Grid container spacing="1rem" rowSpacing="4rem">
                                        <SelectionList
                                            left={left}
                                            setLeft={setLeft}
                                            right={right}
                                            setRight={(uudetValitut) => {
                                                setRight(uudetValitut);
                                                onChange(uudetValitut);
                                            }}
                                            rightGroups={false}
                                            leftLabel={
                                                !params.alueId ? t('toimipaikat') : ''
                                            }
                                            rightLabel={
                                                !params.alueId
                                                    ? t('label-list-uusi-alue')
                                                    : getValues()[
                                                          lang === 'sv'
                                                              ? 'name_sv'
                                                              : 'name_fi'
                                                      ]
                                            }
                                            rightLabelModifiable={!!params.alueId}
                                            selectableGroups={false}
                                            formMethods={formMethods}
                                        />
                                    </Grid>
                                    <div>
                                        {error && (
                                            <p className="error" role="alert">
                                                <WarningIcon />
                                                {t('valitse-ainakin-kolme-toimipaikkaa')}
                                            </p>
                                        )}
                                    </div>
                                </>
                            );
                        }}
                    />
                </div>
                <button type="submit" ref={submitRef} style={{display: 'none'}}>
                    form submit button hiding and waiting to be confirmed
                </button>

                <div className="button-container">
                    {formState.isDirty ? (
                        <ConfirmationDialog
                            title={t('painike-peruuta-title')}
                            confirm={() => navigate('/aluejako')}
                            content={<div>{t('painike-peruuta-content')}</div>}
                            cancelBtnText={t('painike-sulje', {ns: 'yleiset'})}
                            confirmBtnText={t('painike-kylla', {ns: 'yleiset'})}
                        >
                            <button type="button" className="secondary">
                                {t('painike-peruuta', {ns: 'yleiset'})}
                            </button>
                        </ConfirmationDialog>
                    ) : (
                        <ButtonWithLink
                            linkTo="/aluejako"
                            className="secondary"
                            linkText={t('painike-peruuta', {ns: 'yleiset'})}
                        />
                    )}
                    {params.alueId && (
                        <ConfirmationDialog
                            title={t('painike-poista-otsikko')}
                            confirm={() => handleDelete()}
                            content={<div>{t('painike-poista-teksti')}</div>}
                            confirmBtnText={t('painike-kylla', {ns: 'yleiset'})}
                        >
                            <button type="button" className="warning">
                                {t('painike-poista-alue')}
                            </button>
                        </ConfirmationDialog>
                    )}
                    <button
                        type="button"
                        onClick={() => {
                            submitRef.current.click();
                        }}
                    >
                        {params.alueId
                            ? t('painike-tallenna-muutokset')
                            : t('painike-luo-alue')}
                    </button>
                </div>
            </form>
        </>
    );
}

export default MuokkaaAluetta;
