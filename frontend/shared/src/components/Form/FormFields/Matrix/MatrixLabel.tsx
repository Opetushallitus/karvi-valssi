import {useState, useId} from 'react';
import Collapse from '@mui/material/Collapse';
import {FieldValues} from 'react-hook-form';
import FormLabel from '@mui/material/FormLabel';
import Grid from '@mui/material/Grid';
import {useTranslation} from 'react-i18next';
import InfoToggle from '../../../InfoToggle/InfoToggle';
import styles from '../../Form.module.css';

interface MatrixLabelProps {
    label: string;
    required: boolean;
    description?: string;
    errors?: FieldValues;
    focused?: boolean;
    hidden?: boolean;
}

function MatrixLabel({
    label,
    required = false,
    description,
    errors,
    focused,
    hidden = false,
}: MatrixLabelProps) {
    const {t} = useTranslation(['kysely']);
    const uniqId = useId();
    const [descOpen, setDescOpen] = useState<boolean>(false);
    let labelStyles = 'label-for-inputfield';
    if (errors) labelStyles += ' error';
    if (hidden) labelStyles += ' hidden';
    return (
        <Grid width={{xs: '100%', md: '25%'}}>
            {label && (
                <FormLabel
                    component="legend"
                    className={labelStyles}
                    focused={focused}
                    style={{fontWeight: 'normal'}}
                    required={required}
                    aria-required={required}
                >
                    {label}
                    {description && (
                        <InfoToggle
                            isOpen={descOpen}
                            onChange={() => {
                                setDescOpen(!descOpen);
                            }}
                            controlId={uniqId}
                            ariaLabelTxt={label}
                        />
                    )}
                </FormLabel>
            )}
            {hidden && (
                <span className={styles['hidden-matrix-label']}>
                    {t('vaittama-piilotettu')}
                </span>
            )}
            {description && (
                <Collapse in={descOpen} id={uniqId}>
                    <p>{description}</p>
                </Collapse>
            )}
        </Grid>
    );
}

export default MatrixLabel;
