import {useTranslation} from 'react-i18next';
import Grid from '@mui/material/Grid';
import {MatrixScaleType} from '@cscfi/shared/services/Data/Data-service';

interface MatrixMobileScaleProps {
    marks: MatrixScaleType[];
    disabled?: boolean;
}

function MatrixMobileScale({marks, disabled = false}: MatrixMobileScaleProps) {
    const {
        i18n: {language: lang},
    } = useTranslation();
    return (
        <Grid
            container
            className={disabled ? 'mobile-scale-disabled' : ''}
            sx={{
                margin: '1.2rem 0 0 0',
                width: 12,
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
                sx={{
                    width: '50%',
                    textAlign: 'left',
                }}
            >
                {marks[0][lang]}
            </Grid>
            <Grid
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
