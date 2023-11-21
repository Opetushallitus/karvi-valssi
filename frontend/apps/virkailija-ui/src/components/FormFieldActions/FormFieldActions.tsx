import {Dispatch, SetStateAction} from 'react';
import {useTranslation} from 'react-i18next';
import {IconButton} from '@mui/material';
import Grid from '@mui/material/Grid';
import {
    Edit,
    Delete,
    VisibilityOff,
    Visibility,
    ExpandMore,
    ExpandLess,
} from '@mui/icons-material/';
import {
    KyselyType,
    KysymysType,
    StatusType,
} from '@cscfi/shared/services/Data/Data-service';
import InputTypes from '@cscfi/shared/components/InputType/InputTypes';
import ConfirmationDialog from '@cscfi/shared/components/ConfirmationDialog/ConfirmationDialog';
import styles from '@cscfi/shared/components/Form/Form.module.css';
import LisaaMuokkaaKysymys from '../LisaaMuokkaaKysymys/LisaaMuokkaaKysymys';
import LisaaMuokkaaTekstia from '../LisaaMuokkaaTekstia/LisaaMuokkaaTekstia';
import updateOneKysely from '../../services/Kysely/UpdateKysely/UpdateKysely-service';
import getKysymysFromKysely from '../../services/Kysely/GetKysymys/GetKysymys-service';
import {saveKysymysDb} from '../../services/Kysely/SaveKysymysDb/SaveKysymysDb-service';

interface FormFieldActionsProps {
    kysely: KyselyType;
    setKysely: Dispatch<SetStateAction<KyselyType | null>>;
    kysymysId: number;
    moveQuestionUp?: Function;
    moveQuestionDown?: Function;
}

const handleDeleteClick = (
    kysely: KyselyType,
    kysymysId: number,
    setKysely: Dispatch<SetStateAction<KyselyType | null>>,
) => {
    updateOneKysely(kysely, setKysely, undefined, kysymysId, true);
};

const handleHideKysymysClick = (
    kysely: KyselyType,
    setKysely: Dispatch<SetStateAction<KyselyType | null>>,
    kysymys: KysymysType,
    toBeHidden: boolean,
) => {
    kysymys.hidden = toBeHidden;
    if (toBeHidden) kysymys.required = false;
    saveKysymysDb(kysely.id, kysymys).subscribe(() => {
        updateOneKysely(kysely, setKysely, kysymys);
    });
};

function FormFieldActions({
    kysely,
    setKysely,
    kysymysId,
    moveQuestionUp,
    moveQuestionDown,
}: FormFieldActionsProps) {
    const {t} = useTranslation(['kysely']);

    const kysymys = getKysymysFromKysely(kysely, kysymysId);
    const type = kysymys?.inputType;
    const kysymysHidden = kysymys?.hidden;

    let editBtn: JSX.Element;
    switch (type) {
        case InputTypes.statictext:
            editBtn = (
                <LisaaMuokkaaTekstia
                    kysely={kysely}
                    setKysely={setKysely}
                    selectedKysymysId={kysymysId}
                >
                    {(openDialog) => (
                        <IconButton
                            onClick={() => {
                                openDialog();
                            }}
                            aria-label="edit"
                            className="icon-button"
                        >
                            <Edit />
                        </IconButton>
                    )}
                </LisaaMuokkaaTekstia>
            );
            break;
        default:
            editBtn = (
                <LisaaMuokkaaKysymys
                    kysely={kysely}
                    setKysely={setKysely}
                    selectedKysymysId={kysymysId}
                >
                    {(openDialog) => (
                        <IconButton
                            onClick={() => {
                                openDialog();
                            }}
                            aria-label="edit"
                            className="icon-button"
                        >
                            <Edit />
                        </IconButton>
                    )}
                </LisaaMuokkaaKysymys>
            );
    }

    let hideBtn: JSX.Element;
    if (!kysymysHidden && kysymys !== null) {
        if (!kysymys.required) {
            hideBtn = (
                <ConfirmationDialog
                    title={
                        type && type === 'statictext'
                            ? t('piilota-teksti')
                            : t('piilota-vaittama')
                    }
                    confirm={() =>
                        handleHideKysymysClick(kysely, setKysely, kysymys, true)
                    }
                    content={
                        <div>
                            {type && type === 'statictext'
                                ? t('haluatko-varmasti-piilottaa-tekstin')
                                : t('haluatko-varmasti-piilottaa-vaittaman')}
                        </div>
                    }
                >
                    <IconButton aria-label="hide" className="icon-button">
                        <VisibilityOff />
                    </IconButton>
                </ConfirmationDialog>
            );
        } else {
            hideBtn = (
                <IconButton aria-label="hide" className="icon-button" disabled>
                    <VisibilityOff />
                </IconButton>
            );
        }
    } else if (kysymys !== null) {
        hideBtn = (
            <ConfirmationDialog
                title={
                    type && type === 'statictext'
                        ? t('aseta-teksti-nakyvaksi')
                        : t('aseta-vaittama-nakyvaksi')
                }
                confirm={() => handleHideKysymysClick(kysely, setKysely, kysymys, false)}
                content={
                    <div>
                        {type && type === 'statictext'
                            ? t('haluatko-asettaa-tekstin-nakyvaksi')
                            : t('haluatko-asettaa-vaittaman-nakyvaksi')}
                    </div>
                }
            >
                <IconButton aria-label="hide" className="icon-button">
                    <Visibility />
                </IconButton>
            </ConfirmationDialog>
        );
    } else {
        hideBtn = (
            <IconButton aria-label="button does nothing" className="icon-button">
                <ExpandMore />
            </IconButton>
        );
    }

    const delBtn = (
        <ConfirmationDialog
            title={
                type && type === 'statictext' ? t('poista-teksti') : t('poista-vaittama')
            }
            confirm={() => handleDeleteClick(kysely, kysymysId, setKysely)}
            content={
                <div>
                    {type && type === 'statictext'
                        ? t('haluatko-varmasti-poistaa-tekstin')
                        : t('haluatko-varmasti-poistaa-vaittaman')}
                </div>
            }
        >
            <IconButton aria-label="delete" className="icon-button">
                <Delete />
            </IconButton>
        </ConfirmationDialog>
    );

    return (
        <div className={styles['icon-buttons']}>
            <Grid
                container
                sx={{
                    columns: 2,
                    direction: 'row',
                    flexWrap: 'nowrap',
                }}
            >
                <Grid container item direction={{xs: 'column'}}>
                    <Grid item sx={{height: '50px'}}>
                        {moveQuestionUp && (
                            <IconButton
                                className="icon-button"
                                aria-label="move question up"
                                onClick={() => moveQuestionUp()}
                            >
                                <ExpandLess />
                            </IconButton>
                        )}
                    </Grid>
                    <Grid item>
                        {moveQuestionDown && (
                            <IconButton
                                className="icon-button"
                                aria-label="move question down"
                                onClick={() => moveQuestionDown()}
                            >
                                <ExpandMore />
                            </IconButton>
                        )}
                    </Grid>
                </Grid>
                <Grid container item direction={{xs: 'column'}}>
                    <Grid item>{editBtn}</Grid>
                    {kysely.status === StatusType.julkaistu ? (
                        <Grid item>{hideBtn}</Grid>
                    ) : (
                        <Grid item>{delBtn}</Grid>
                    )}
                </Grid>
            </Grid>
        </div>
    );
}

export default FormFieldActions;
