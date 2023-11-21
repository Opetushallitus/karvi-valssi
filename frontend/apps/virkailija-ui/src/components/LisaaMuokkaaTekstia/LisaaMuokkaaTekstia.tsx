import {Dispatch, SetStateAction, useState} from 'react';
import Dialog from '@mui/material/Dialog';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import {useTranslation} from 'react-i18next';
import {
    KysymysType,
    KyselyType,
    StatusType,
} from '@cscfi/shared/services/Data/Data-service';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import TextField from '@mui/material/TextField';
import {arvoUpdateKysymysryhma$} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import getKysymysFromKysely from '../../services/Kysely/GetKysymys/GetKysymys-service';
import {saveKysymysDb} from '../../services/Kysely/SaveKysymysDb/SaveKysymysDb-service';
import updateOneKysely from '../../services/Kysely/UpdateKysely/UpdateKysely-service';
import styles from './LisaaMuokkaaTekstia.module.css';

interface LisaaMuokkaaTekstiaProps {
    children: (openDialog: () => void) => void;
    kysely: KyselyType;
    setKysely: Dispatch<SetStateAction<KyselyType | null>>;
    selectedKysymysId: number;
}

function LisaaMuokkaaTekstia({
    children,
    kysely,
    setKysely,
    selectedKysymysId,
}: LisaaMuokkaaTekstiaProps) {
    const {t} = useTranslation(['kysely']);
    const initialFildState = {
        title_fi: '',
        title_sv: '',
        description_fi: '',
        description_sv: '',
        hidden: false,
    };
    const [showDialog, setShowDialog] = useState(false);
    const [fieldState, setFieldState] = useState(initialFildState);
    const [existingKysymys, setExistingKysymys] = useState<KysymysType | null>(null);

    const handleChange = (e: any) => {
        setFieldState((state) => ({
            ...state,
            [e.target.id]: e.target.value,
        }));
    };

    const openDialog = () => {
        setFieldState(initialFildState);
        if (selectedKysymysId !== -1) {
            const kysymys = getKysymysFromKysely(kysely, selectedKysymysId);
            setExistingKysymys(kysymys);
            if (kysymys) {
                setFieldState(() => ({
                    title_fi: kysymys.title.fi,
                    title_sv: kysymys.title.sv,
                    description_fi: kysymys.description?.fi || '',
                    description_sv: kysymys.description?.sv || '',
                    hidden: kysymys.hidden || false,
                }));
            } else {
                console.log(`Error: Kysymys not found! Id: ${kysely?.id}`);
            }
        }
        setShowDialog(true);
    };

    const onDialogClose = () => {
        setShowDialog(false);
    };

    const handleSave = () => {
        const updatedKysymys = {
            id: selectedKysymysId,
            inputType: InputTypes.statictext,
            title: {
                fi: fieldState.title_fi,
                sv: fieldState.title_sv,
            },
            description: {
                fi: fieldState.description_fi,
                sv: fieldState.description_sv,
            },
            hidden: fieldState.hidden,
            required: false,
            answerOptions: [],
            matrixQuestions: [],
        };

        saveKysymysDb(kysely.id, updatedKysymys).subscribe((res) => {
            if (selectedKysymysId === -1) {
                // Create a new teksti in DB and receive a unique kysymysId in response
                updatedKysymys.id = res.kysymysid;
            }
            updateOneKysely(kysely, setKysely, updatedKysymys);
            onDialogClose();
        });
        /**
         * This empty patch needs to be sent to synchronize
         * kysymysryhma.muutettuaika with kysymysryhma questions
         */
        if (kysely.status !== StatusType.julkaistu) {
            arvoUpdateKysymysryhma$(kysely.id, {}).subscribe(() => {});
        }
    };

    return (
        <>
            {children(openDialog)}
            {showDialog && (
                <Dialog
                    open
                    maxWidth={false}
                    fullWidth
                    disableRestoreFocus
                    aria-labelledby="lisaamuokkaatekstia_h1"
                >
                    <h1 id="lisaamuokkaatekstia_h1">
                        {existingKysymys ? t('muokkaa-tekstia') : t('lisaa-uusi-teksti')}
                    </h1>
                    <div className="button-container-top">
                        <IconButton
                            className="icon-button"
                            aria-label={t('sulje-dialogi', {ns: 'yleiset'})}
                            onClick={() => onDialogClose()}
                        >
                            <CloseIcon />
                        </IconButton>
                    </div>

                    <div className={styles.tekstit__container}>
                        <div>
                            <div className={styles['kieli-title']}>{t('suomi')}</div>
                            <label htmlFor="title_fi" className="label-for-inputfield">
                                {t('valiotsikko')}
                            </label>
                            <TextField
                                id="title_fi"
                                required
                                fullWidth
                                value={fieldState.title_fi}
                                onChange={handleChange}
                            />
                            <label
                                htmlFor="description_fi"
                                className="label-for-inputfield"
                            >
                                {t('teksti')}
                            </label>
                            <TextField
                                id="description_fi"
                                required
                                fullWidth
                                multiline
                                minRows={3}
                                value={fieldState.description_fi}
                                onChange={handleChange}
                            />
                        </div>
                        <hr />
                        <div>
                            <div className={styles['kieli-title']}>{t('ruotsi')}</div>
                            <label htmlFor="title_sv" className="label-for-inputfield">
                                {t('valiotsikko')}
                            </label>
                            <TextField
                                id="title_sv"
                                required={false}
                                fullWidth
                                value={fieldState.title_sv}
                                onChange={handleChange}
                            />
                            <label
                                htmlFor="description_sv"
                                className="label-for-inputfield"
                            >
                                {t('teksti')}
                            </label>
                            <TextField
                                id="description_sv"
                                required={false}
                                fullWidth
                                multiline
                                minRows={3}
                                value={fieldState.description_sv}
                                onChange={handleChange}
                            />
                        </div>
                    </div>
                    <div className="button-container">
                        <button
                            type="button"
                            className="secondary"
                            onClick={() => onDialogClose()}
                        >
                            {t('peruuta')}
                        </button>
                        <button type="button" onClick={handleSave}>
                            {t('tallenna')}
                        </button>
                    </div>
                </Dialog>
            )}
        </>
    );
}

export default LisaaMuokkaaTekstia;
