import {useState} from 'react';
import {useTranslation} from 'react-i18next';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Link from '@mui/material/Link';
import i18n, {LanguageOptions} from '../../i18n/config';

export default function SelectLanguage() {
    const {t} = useTranslation(['ulkoasu']);

    // Näytettävä kielikoodi (synkassa i18n:n kanssa)
    const [selectedLanguage, setSelectedLanguage] = useState<string>(i18n.language);

    // Ankkuri talteen tilaan – ei ref.current -lukemista renderissä
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);

    const handleOpen = (e: React.MouseEvent<HTMLElement>) => setAnchorEl(e.currentTarget);
    const handleClose = () => setAnchorEl(null);

    const handleSelect = (langCode: string) => {
        i18n.changeLanguage(langCode);
        setSelectedLanguage(langCode);
        setAnchorEl(null);
    };
    if (selectedLanguage !== 'fi' && selectedLanguage !== 'sv') {
        handleSelect('fi');
    }

    return (
        <div>
            {/* Käytetään MUI Linkiä button-tyyppisenä: ei tarvita href="#" eikä a11y-disable-kommenttia */}
            <Link
                component="button"
                type="button"
                onClick={handleOpen}
                variant="inherit"
                underline="hover"
                aria-haspopup="menu"
                aria-controls={open ? 'select-language' : undefined}
                aria-expanded={open ? 'true' : undefined}
            >
                {selectedLanguage.toUpperCase()} | {t('kieli-sprak')}
            </Link>

            <Menu
                id="select-language"
                anchorEl={anchorEl}
                keepMounted
                open={open}
                onClose={handleClose}
            >
                <MenuItem onClick={() => handleSelect(LanguageOptions.fi)}>
                    {t('suomi')}
                </MenuItem>
                <MenuItem onClick={() => handleSelect(LanguageOptions.sv)}>
                    {t('ruotsi')}
                </MenuItem>
            </Menu>
        </div>
    );
}
