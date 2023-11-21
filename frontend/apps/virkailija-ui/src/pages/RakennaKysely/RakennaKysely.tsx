import {useEffect, useState} from 'react';
import {useLocation, useNavigate} from 'react-router-dom';
import {useTranslation} from 'react-i18next';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import EditIcon from '@mui/icons-material/Edit';
import AddIcon from '@mui/icons-material/Add';
import {Box} from '@mui/material';
import {
    arvoGetKysymysryhma$,
    arvoSwapKysymysOrder$,
    arvoUpdateKysymysryhma$,
    convertKysymyksetArvoToValssi,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import {KyselyType, StatusType, TextType} from '@cscfi/shared/services/Data/Data-service';
import Kysely from '@cscfi/shared/components/Kysely/Kysely';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import GenericTextField from '@cscfi/shared/components/GenericTextField/GenericTextField';
import {getQueryParamAsNumber} from '@cscfi/shared/utils/helpers';
import ButtonWithLink from '../../components/ButtonWithLink/ButtonWithLink';
import removeKysely from '../../services/Kysely/RemoveKysely/RemoveKysely-service';
import LuoUusiKysely from './LuoUusiKysely';
import LisaaMuokkaaKysymys from '../../components/LisaaMuokkaaKysymys/LisaaMuokkaaKysymys';
import LisaaMuokkaaTekstia from '../../components/LisaaMuokkaaTekstia/LisaaMuokkaaTekstia';
import styles from './RakennaKysely.module.css';
import FormFieldActions from '../../components/FormFieldActions/FormFieldActions';
import SecondaryIndicators from '../../components/SecondaryIndicators/SecondaryIndicators';

function RakennaKysely() {
    const [kysely, setKysely] = useState<KyselyType | null>(null);
    const [kyselyTopic, setKyselyTopic] = useState<TextType>({fi: '', sv: ''});
    const [showTopicInputField, setShowTopicInputField] = useState(false);
    const navigate = useNavigate();
    const location = useLocation();
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['rakennakysely']);

    useEffect(() => {
        const kyselyId = getQueryParamAsNumber(location, 'id');
        if (kyselyId) {
            arvoGetKysymysryhma$(kyselyId).subscribe((kysymysryhma) => {
                const valssiKysely: KyselyType = {
                    id: kysymysryhma.kysymysryhmaid,
                    topic: {fi: kysymysryhma.nimi_fi, sv: kysymysryhma.nimi_sv || ''},
                    kysymykset: convertKysymyksetArvoToValssi(kysymysryhma.kysymykset),
                    status: kysymysryhma.tila,
                    lomaketyyppi: kysymysryhma.metatiedot?.lomaketyyppi,
                    paaIndikaattori: kysymysryhma.metatiedot?.paaIndikaattori,
                    sekondaariset_indikaattorit:
                        kysymysryhma.metatiedot?.sekondaariset_indikaattorit,
                };
                setKysely(valssiKysely);
                setKyselyTopic(valssiKysely.topic);
            });
        }
    }, [location]);

    if (!kysely) {
        return <LuoUusiKysely handleChange={setKyselyTopic} setKysely={setKysely} />;
    }

    const onClickSaveTopic = () => {
        if (kyselyTopic.fi.trim() !== '') {
            const body = {
                nimi_fi: kyselyTopic.fi,
                nimi_sv: kyselyTopic.sv,
            };
            arvoUpdateKysymysryhma$(kysely.id, body).subscribe((kr) => {
                setKysely((prevKysely) => ({
                    ...prevKysely!,
                    topic: {
                        fi: kr.nimi_fi,
                        sv: kr?.nimi_sv || '',
                    },
                }));
            });
            setShowTopicInputField(false);
        }
    };

    const saveSecondaryIndicators = (selectedIndicators: any) => {
        arvoGetKysymysryhma$(kysely.id).subscribe((kysymysryhma) => {
            arvoUpdateKysymysryhma$(kysely.id, {
                metatiedot: {
                    sekondaariset_indikaattorit: selectedIndicators,
                    lomaketyyppi: kysymysryhma.metatiedot?.lomaketyyppi,
                    paaIndikaattori: kysymysryhma.metatiedot?.paaIndikaattori,
                },
            }).subscribe(() => {
                if (kyselyTopic.fi !== '') {
                    setShowTopicInputField(false);
                }
            });
        });
    };

    const onClickDeleteKysely = () => {
        removeKysely(kysely.id, kysely.topic[lang as keyof TextType]);
        navigate('/indikaattorit');
    };

    /**
     * Swaps order of two questions
     * @param id
     * @param swap
     * @param moveDelta -1 for move up, 1 for move down
     */
    const onClickSwapOrder = (id: number, swap: number, moveDelta: -1 | 1) => {
        arvoSwapKysymysOrder$(kysely.id, id, swap).subscribe(() => {
            const copyKysymykset = [...kysely.kysymykset];
            const indexToMove = copyKysymykset.findIndex((k) => k.id === id);
            const kysymysToMove = {...copyKysymykset[indexToMove]};
            copyKysymykset.splice(indexToMove, 1);
            copyKysymykset.splice(indexToMove + moveDelta, 0, kysymysToMove);
            const newKysely = {...kysely, kysymykset: copyKysymykset};
            setKysely(newKysely);
        });
    };

    const renderFormFieldActions = (id: number, previousid: number, nextid: number) => (
        <FormFieldActions
            kysely={kysely}
            setKysely={setKysely}
            kysymysId={id}
            moveQuestionUp={
                previousid ? () => onClickSwapOrder(id, previousid, -1) : undefined
            }
            moveQuestionDown={nextid ? () => onClickSwapOrder(id, nextid, 1) : undefined}
        />
    );

    const tyyppi = kysely?.lomaketyyppi?.substring(
        kysely.lomaketyyppi.lastIndexOf('_') + 1,
    );

    const rakennaKyselyButtons = () => (
        <div className="button-container">
            <ButtonWithLink
                linkTo="/indikaattorit"
                linkText={t('painike-takaisin', {ns: 'yleiset'})}
                className="secondary"
            />
            {kysely.status !== 'julkaistu' && (
                <ConfirmationDialog
                    title={t('dialogi-otsikko')}
                    confirm={onClickDeleteKysely}
                    content={<div>{t('dialogi-teksti')}</div>}
                >
                    <button type="button" className="warning">
                        {t('painike-poista')}
                    </button>
                </ConfirmationDialog>
            )}
            <ButtonWithLink
                linkTo={`/esikatselu?id=${kysely.id}`}
                linkText={t('painike-esikatselu')}
            />
        </div>
    );

    return (
        <>
            <Box>
                {kysely.status === StatusType.julkaistu ? (
                    <h1>{t('sivun-otsikko-muokkaa-julkaistua')}</h1>
                ) : (
                    <h1>{t('sivun-otsikko-muokkaa')}</h1>
                )}
                {rakennaKyselyButtons()}
                {showTopicInputField && (
                    <div className={styles['topic-container']}>
                        <div className={styles['topic-fields']}>
                            <GenericTextField
                                value={kyselyTopic.fi}
                                fullWidth
                                autoComplete={false}
                                autoFocus
                                label={t('label-lomakkeen-nimi-fi')}
                                required
                                showLabel
                                error={kyselyTopic.fi.trim() === ''}
                                errorMessage={t('pakollinen-tieto', {ns: 'error'})}
                                onChange={(newValue: string) =>
                                    setKyselyTopic((prevState) => ({
                                        ...prevState,
                                        fi: newValue,
                                    }))
                                }
                            />
                            <GenericTextField
                                value={kyselyTopic.sv}
                                fullWidth
                                autoComplete={false}
                                autoFocus
                                label={t('label-lomakkeen-nimi-sv')}
                                showLabel
                                onChange={(newValue: string) =>
                                    setKyselyTopic((prevState) => ({
                                        ...prevState,
                                        sv: newValue,
                                    }))
                                }
                            />
                        </div>
                        <div className={styles['topic-controls']}>
                            <IconButton
                                className="icon-button"
                                aria-label="save topic"
                                component="span"
                                onClick={onClickSaveTopic}
                            >
                                <CheckIcon />
                            </IconButton>

                            <IconButton
                                className="icon-button"
                                aria-label="cancel saving topic"
                                onClick={() => {
                                    setKyselyTopic(kysely?.topic);
                                    setShowTopicInputField(false);
                                }}
                            >
                                <CloseIcon />
                            </IconButton>
                        </div>
                    </div>
                )}
                {!showTopicInputField && (
                    <div className={styles['topic-container']}>
                        <h2 className={styles.topic}>
                            {kyselyTopic[lang as keyof TextType]}
                        </h2>
                        {kysely.status !== StatusType.julkaistu && (
                            <IconButton
                                className="icon-button"
                                aria-label="edit topic"
                                component="span"
                                onClick={() => setShowTopicInputField(true)}
                            >
                                <EditIcon />
                            </IconButton>
                        )}
                    </div>
                )}
                <h3 className={styles.questionnaireType}>
                    {t(kysely.lomaketyyppi, {ns: 'yleiset'})}
                </h3>
                <div className={styles.indicatorWrapper}>
                    <h3>{t('indik:johdanto')}</h3>
                    <p>{t(`indik:desc_${kysely.paaIndikaattori?.key}`)}</p>
                </div>
                <SecondaryIndicators
                    selectedSecondaryIndicators={kysely.sekondaariset_indikaattorit}
                    lomaketyyppi={tyyppi}
                    save={saveSecondaryIndicators}
                    paaIndikaattori={kysely.paaIndikaattori?.key}
                />
                {/* The key prop is needed to force Kysely rendering again when a new
                question is added. Default values need to be initalized. */}
                <Kysely
                    key={`${kysely.id}_${kysely.kysymykset.length}`}
                    selectedKysely={kysely}
                    editable
                    renderFormFieldActions={renderFormFieldActions}
                />
            </Box>

            {/* ”Add question/text” -buttons only if the questionnaire not published. */}
            {kysely.status !== StatusType.julkaistu && (
                <div className="button-container">
                    <LisaaMuokkaaKysymys
                        kysely={kysely}
                        setKysely={setKysely}
                        selectedKysymysId={-1}
                    >
                        {(openDialog) => (
                            <Button
                                className="small"
                                startIcon={<AddIcon />}
                                onClick={openDialog}
                            >
                                {t('painike-lisaa-vaittama')}
                            </Button>
                        )}
                    </LisaaMuokkaaKysymys>
                    <LisaaMuokkaaTekstia
                        kysely={kysely}
                        setKysely={setKysely}
                        selectedKysymysId={-1}
                    >
                        {(openDialog) => (
                            <Button
                                className="small"
                                startIcon={<AddIcon />}
                                onClick={openDialog}
                            >
                                {t('painike-lisaa-tekstia')}
                            </Button>
                        )}
                    </LisaaMuokkaaTekstia>
                </div>
            )}
            {rakennaKyselyButtons()}
        </>
    );
}

export default RakennaKysely;
