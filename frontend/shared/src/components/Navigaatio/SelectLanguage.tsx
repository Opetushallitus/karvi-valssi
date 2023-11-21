/* eslint jsx-a11y/anchor-is-valid: 'off' */
import {SyntheticEvent, useRef, useState} from 'react';
import {useTranslation} from 'react-i18next';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import {Link, Typography} from '@mui/material';
import i18n, {LanguageOptions} from '../../i18n/config';

export default function SelectLanguage() {
    const {t} = useTranslation(['ulkoasu']);
    const [selectedLanguage, setSelectedLanguage] = useState<string>(i18n.language);
    const [open, setOpen] = useState(false);
    const anchorRef = useRef(null);

    const handleToggle = () => {
        setOpen(!open);
    };

    const handleClose = () => {
        setOpen(false);
    };

    const handleSelect = (event: SyntheticEvent) => {
        const newLanguage = event.currentTarget.getAttribute('data-language');
        if (newLanguage !== null) {
            i18n.changeLanguage(newLanguage);
            setSelectedLanguage(newLanguage);
        }
        setOpen(false);
    };

    return (
        <div>
            <Typography>
                <Link href="#" onClick={handleToggle} variant="inherit" ref={anchorRef}>
                    {selectedLanguage.toUpperCase()} | {t('kieli-sprak')}
                </Link>
            </Typography>
            <Menu
                id="select-language"
                anchorEl={anchorRef.current}
                keepMounted
                open={open}
                onClose={handleClose}
            >
                <MenuItem data-language={LanguageOptions.fi} onClick={handleSelect}>
                    {t('suomi')}
                </MenuItem>
                <MenuItem data-language={LanguageOptions.sv} onClick={handleSelect}>
                    {t('ruotsi')}
                </MenuItem>
            </Menu>
        </div>
    );
}
