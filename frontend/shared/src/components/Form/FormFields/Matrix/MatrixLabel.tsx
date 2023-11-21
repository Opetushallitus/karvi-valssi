import {useState} from 'react';
import Collapse from '@mui/material/Collapse';
import {FieldValues} from 'react-hook-form';
import FormLabel from '@mui/material/FormLabel';
import Grid from '@mui/material/Grid';
import InfoToggle from '../../../InfoToggle/InfoToggle';

interface MatrixLabelProps {
    label: string;
    required: boolean;
    description?: string;
    errors?: FieldValues;
    focused?: boolean;
}

function MatrixLabel({
    label,
    required = false,
    description,
    errors,
    focused,
}: MatrixLabelProps) {
    const [descOpen, setDescOpen] = useState<boolean>(false);
    let labelStyles = 'label-for-inputfield';
    if (errors) {
        labelStyles += ' error';
    }
    return (
        <Grid item width={{xs: '100%', md: '25%'}}>
            {label && (
                <FormLabel
                    component="legend"
                    className={labelStyles}
                    focused={focused}
                    style={{fontWeight: 'normal', color: 'inherit'}}
                    required={required}
                >
                    {label}
                    {description && (
                        <InfoToggle
                            isOpen={descOpen}
                            onChange={() => {
                                setDescOpen(!descOpen);
                            }}
                        />
                    )}
                </FormLabel>
            )}
            {description && (
                <Collapse in={descOpen}>
                    <p>{description}</p>
                </Collapse>
            )}
        </Grid>
    );
}

export default MatrixLabel;
