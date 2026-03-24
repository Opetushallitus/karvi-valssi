import {MatrixType, TextType} from '@cscfi/shared/services/Data/Data-service';
import Grid from '@mui/material/Grid';
import {useTranslation} from 'react-i18next';
import {Box} from '@mui/material';

interface MatrixEosLabelProps {
    matrixType: MatrixType;
    language?: string;
}

function MatrixEosLabel({matrixType, language}: MatrixEosLabelProps) {
    const {
        i18n: {language: lang},
    } = useTranslation(['form']);
    const langKey = language ? language : (lang as keyof TextType);
    const eos = matrixType.eos_value;
    return (
        <Grid
            container
            sx={{
                margin: '1.2rem 0 0 0',
                alignContent: 'flex-start',
                width: '10%',
            }}
            direction="row"
            display={{
                xs: 'none',
                md: 'grid',
            }}
        >
            <Box
                sx={{
                    justifyContent: 'center',
                    display: 'flex',
                    width: '100%',
                    textAlign: 'center',
                }}
            >
                <span>{eos[langKey]}</span>
            </Box>
        </Grid>
    );
}

export default MatrixEosLabel;
