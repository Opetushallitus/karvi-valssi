import {useTranslation} from 'react-i18next';
import Grid from '@mui/material/Grid';
// eslint-disable-next-line max-len,import/no-extraneous-dependencies
import {MatrixScaleType} from '@cscfi/shared/services/Data/Data-service';

interface MatrixMobileScaleProps {
    marks: MatrixScaleType[];
}

function MatrixMobileScale({marks}: MatrixMobileScaleProps) {
    const {
        i18n: {language: lang},
    } = useTranslation();
    return (
        <Grid
            item
            container
            sx={{
                margin: '1.2rem 0 0 0',
                width: '100%',
                direction: 'row',
                justifyContent: 'space-between',
                gap: '1rem',
                flexWrap: 'nowrap',
            }}
            display={{
                md: 'none',
            }}
        >
            <Grid
                item
                sx={{
                    width: '50%',
                    textAlign: 'left',
                }}
            >
                {marks[0][lang]}
            </Grid>
            <Grid
                item
                sx={{
                    width: '50%',
                    textAlign: 'right',
                }}
            >
                {marks[marks.length - 1][lang]}
            </Grid>
        </Grid>
    );
}

export default MatrixMobileScale;
