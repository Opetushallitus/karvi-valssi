import {useTranslation} from 'react-i18next';
import Box from '@mui/material/Box';
import {visuallyHidden} from '@mui/utils';
import LaunchIcon from '@mui/icons-material/Launch';
import {Typography} from '@mui/material';

interface AlatunnisteLinkProps {
    urlKey: string;
    textKey: string;
}
function AlatunnisteLink({urlKey, textKey}: AlatunnisteLinkProps) {
    const {t} = useTranslation(['ulkoasu']);

    return (
        <Typography>
            <a href={t(urlKey)} target="_blank" rel="noreferrer">
                {t(textKey)}
                <Box component="span" sx={visuallyHidden}>
                    {t('avautuu-uudessa-valilehdessa', {
                        ns: 'saavutettavuus',
                    })}
                </Box>
                <LaunchIcon fontVariant="externalLaunch" />
            </a>
        </Typography>
    );
}

export default AlatunnisteLink;
