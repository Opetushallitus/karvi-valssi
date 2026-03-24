import {ChangeEvent, useState, useId} from 'react';
import {useTranslation} from 'react-i18next';
import AddIcon from '@mui/icons-material/Add';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import {TextType} from '@cscfi/shared/services/Data/Data-service';
import styles from './DescriptionText.module.css';

interface DescriptionTextProps {
    value: TextType;
    onChange: (valueFromInputField: TextType) => void;
    disabled?: boolean;
    showEnglish?: boolean;
    ruotsiVaiEnglantiValittu?: string;
}

function DescriptionText({
    value,
    onChange,
    disabled = false,
    showEnglish,
    ruotsiVaiEnglantiValittu,
}: DescriptionTextProps) {
    const {t} = useTranslation(['kysely']);

    // Kun avataan "Lisää ohjeteksti" -napista ensimmäisen kerran,
    // asetetaan tämä true, jotta kentät näkyvät, vaikka teksti olisi vielä tyhjä.
    const [forceOpen, setForceOpen] = useState(false);
    const [isNew, setIsNew] = useState(false);

    const labelAssociationFi = useId();
    const labelAssociationSv = useId();

    // Johdettu tieto: onko kummassakaan kentässä tekstiä?
    const hasText =
        (value.fi?.trim?.() ?? '') !== '' || (value.sv?.trim?.() ?? '') !== '';

    // Näytetäänkö kuvaustekstikentät?
    const showDescription = forceOpen || hasText;

    const show = () => {
        setForceOpen(true);
        setIsNew(true); // autofocus ensimmäiselle avaukselle
    };

    const handleChange =
        (lang: 'fi' | 'sv' | 'en') =>
        (event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
            if (lang === 'fi') {
                onChange(
                    showEnglish
                        ? {fi: event.target.value, sv: value.sv, en: value.en}
                        : {fi: event.target.value, sv: value.sv},
                );
            } else if (lang === 'sv') {
                onChange(
                    showEnglish
                        ? {fi: value.fi, sv: event.target.value, en: value.en}
                        : {fi: value.fi, sv: event.target.value},
                );
            } else {
                onChange({fi: value.fi, sv: value.sv, en: event.target.value});
            }
        };

    return !showDescription ? (
        <>
            <Button
                className="link-alike"
                startIcon={<AddIcon />}
                onClick={show}
                disabled={disabled}
            >
                {t('lisaa-ohjeteksti')}
            </Button>
            {disabled && (
                <span className={styles['question-hidden-text']}>
                    {t('vaittama-piilotettu')}
                </span>
            )}
        </>
    ) : (
        <>
            <div className="field-row">
                <label
                    htmlFor={labelAssociationFi}
                    className={`label-for-inputfield ${disabled ? 'hidden' : ''}`}
                >
                    {t('ohjeteksti')}
                </label>
                <label
                    htmlFor={labelAssociationSv}
                    className={`label-for-inputfield ${disabled ? 'hidden' : ''}`}
                >
                    {t('ohjeteksti')}
                </label>
            </div>

            <div className="field-row">
                <TextField
                    id={labelAssociationFi}
                    fullWidth
                    multiline
                    autoComplete="off"
                    autoFocus={isNew}
                    minRows={3}
                    value={value.fi}
                    onChange={handleChange('fi')}
                    disabled={disabled}
                />
                {!showEnglish && (
                    <TextField
                        id={labelAssociationSv}
                        fullWidth
                        multiline
                        autoComplete="off"
                        autoFocus={false}
                        minRows={3}
                        value={value.sv}
                        onChange={handleChange('sv')}
                        disabled={disabled}
                    />
                )}
                {showEnglish && ruotsiVaiEnglantiValittu === 'ruotsi' && (
                    <TextField
                        id={labelAssociationSv}
                        fullWidth
                        multiline
                        autoComplete="off"
                        autoFocus={false}
                        minRows={3}
                        value={value.sv}
                        onChange={handleChange('sv')}
                        disabled={disabled}
                    />
                )}
                {showEnglish && ruotsiVaiEnglantiValittu === 'englanti' && (
                    <TextField
                        id={labelAssociationSv}
                        fullWidth
                        multiline
                        autoComplete="off"
                        autoFocus={false}
                        minRows={3}
                        value={value.en}
                        onChange={handleChange('en')}
                        disabled={disabled}
                    />
                )}
            </div>

            {disabled && (
                <div className="field-row">
                    <span className={styles['question-hidden-text']}>
                        {t('vaittama-piilotettu')}
                    </span>
                </div>
            )}
        </>
    );
}

export default DescriptionText;
