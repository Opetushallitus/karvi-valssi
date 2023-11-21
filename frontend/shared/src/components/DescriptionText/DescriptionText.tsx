import {ChangeEvent, useState, useId, useEffect} from 'react';
import {useTranslation} from 'react-i18next';
import AddIcon from '@mui/icons-material/Add';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import {TextType} from '@cscfi/shared/services/Data/Data-service';

interface DescriptionTextProps {
    value: TextType;
    onChange: (valueFromInputField: TextType) => void;
}

function DescriptionText({value, onChange}: DescriptionTextProps) {
    const {t} = useTranslation(['kysely']);
    const [isNew, setIsNew] = useState(false);
    const [showDescription, setShowDescription] = useState(false);
    const labelAssociationFi = useId();
    const labelAssociationSv = useId();

    const show = () => {
        setShowDescription(true);
        setIsNew(true); // for setting the focus when opening
    };

    const handleChange =
        (lang) => (event: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>) => {
            if (lang === 'fi') {
                onChange({fi: event.target.value, sv: value.sv});
            } else {
                onChange({fi: value.fi, sv: event.target.value});
            }
        };

    useEffect(() => {
        if (value.fi === '' && value.sv === '') {
            setShowDescription(false);
        } else if (value.fi !== '' || value.sv !== '') {
            setShowDescription(true);
        }
    }, [value]);

    return !showDescription ? (
        <Button className="link-alike" startIcon={<AddIcon />} onClick={show}>
            {t('lisaa-ohjeteksti')}
        </Button>
    ) : (
        <>
            <div className="field-row">
                <label htmlFor={labelAssociationFi} className="label-for-inputfield">
                    {t('ohjeteksti')}
                </label>
                <label htmlFor={labelAssociationSv} className="label-for-inputfield">
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
                />
                <TextField
                    id={labelAssociationSv}
                    fullWidth
                    multiline
                    autoComplete="off"
                    autoFocus={isNew}
                    minRows={3}
                    value={value.sv}
                    onChange={handleChange('sv')}
                />
            </div>
        </>
    );
}

export default DescriptionText;
