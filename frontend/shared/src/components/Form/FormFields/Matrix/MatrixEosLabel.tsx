import {MatrixType} from '@cscfi/shared/services/Data/Data-service';
import Grid from '@mui/material/Grid';
import {useTranslation} from 'react-i18next';
import {Box} from '@mui/material';

interface MatrixEosLabelProps {
    matrixType: MatrixType;
}

function MatrixEosLabel({matrixType}: MatrixEosLabelProps) {
    const {
        i18n: {language: lang},
    } = useTranslation(['form']);
    const eos = matrixType.eos_value;
    return (
        <Grid
            item
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
                <span>{eos[lang]}</span>
            </Box>
        </Grid>
    );
}

export default MatrixEosLabel;
