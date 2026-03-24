import {useTranslation} from 'react-i18next';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import {MatrixType, TextType} from '@cscfi/shared/services/Data/Data-service';

interface MatrixDesctopScaleProps {
    id: string;
    matrixType: MatrixType;
    language?: string;
}

function MatrixDesctopScale({id, matrixType, language}: MatrixDesctopScaleProps) {
    const {
        i18n: {language: lang},
    } = useTranslation();
    const langKey = language ? language : (lang as keyof TextType);
    return (
        <Grid
            container
            sx={{
                margin: '1.2rem 0 0 0',
                alignContent: 'flex-start',
                width: '65%',
            }}
            direction="row"
            display={{
                xs: 'none',
                md: 'grid',
            }}
        >
            <Box
                sx={{
                    display: 'flex',
                }}
                gap="1rem"
            >
                {matrixType.scale.map((s) => (
                    <Box
                        key={`matrix_root_scale_labels_${id}_${s.value}`}
                        sx={{
                            justifyContent: 'center',
                            display: 'flex',
                            width: '100%',
                            textAlign: 'center',
                        }}
                    >
                        <span>{s[langKey]}</span>
                    </Box>
                ))}
            </Box>
        </Grid>
    );
}

export default MatrixDesctopScale;
