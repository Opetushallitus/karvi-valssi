import {ChangeEventHandler} from 'react';
import {useTheme} from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import {MatrixType} from '@cscfi/shared/services/Data/Data-service';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import Grid from '@mui/material/Grid';
import {useTranslation} from 'react-i18next';

interface MatrixEosCheckboxProps {
    id: string;
    onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
    matrixType: MatrixType;
    value: number;
}

function MatrixEosCheckbox({id, onChange, matrixType, value}: MatrixEosCheckboxProps) {
    const {
        i18n: {language: lang},
    } = useTranslation(['form']);
    const eos = matrixType.eos_value;
    const theme = useTheme();
    const lessThanSmall = useMediaQuery(theme.breakpoints.down('md'));
    return (
        <Grid
            item
            width={{xs: '100%', md: '10%'}}
            sx={{
                margin: '0.8rem 0 0 0',
                alignContent: 'center',
            }}
            padding={{md: '0 2rem'}}
        >
            <FormControlLabel
                label={lessThanSmall ? eos[lang] : ''}
                control={
                    <Checkbox
                        checked={value === -1}
                        value={-1}
                        onChange={(event) => {
                            onChange({
                                ...event,
                                currentTarget: {
                                    name: id,
                                    // @ts-ignore
                                    value: event.target.checked ? -1 : undefined,
                                },
                            });
                        }}
                    />
                }
            />
        </Grid>
    );
}

export default MatrixEosCheckbox;
