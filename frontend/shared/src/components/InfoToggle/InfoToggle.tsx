import {ChangeEventHandler} from 'react';
import Avatar from '@mui/material/Avatar';
import ExpandLessRounded from '@mui/icons-material/ExpandLessRounded';
import InfoOutlined from '@mui/icons-material/InfoOutlined';
import Checkbox from '@mui/material/Checkbox';
import {useTranslation} from 'react-i18next';
import styles from './InfoToggle.module.css';

interface InfoToggleProps {
    isOpen: boolean;
    onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
    controlId?: string;
    ariaLabelTxt?: string;
}

function InfoToggle({isOpen, onChange, controlId, ariaLabelTxt}: InfoToggleProps) {
    const {t} = useTranslation(['yleiset']);
    return (
        <Checkbox
            inputProps={{
                role: 'button',
                'aria-expanded': isOpen,
                'aria-controls': controlId,
                'aria-label': `${isOpen ? t('sulje-ohje') : t('avaa-ohje')}: ${
                    ariaLabelTxt ?? ''
                }`,
            }}
            checked={isOpen}
            checkedIcon={
                <Avatar className={styles['desc-expand-less-avatar']}>
                    <ExpandLessRounded className={styles['desc-expand-less']} />
                </Avatar>
            }
            icon={<InfoOutlined className={styles['desc-expand-more']} />}
            onChange={onChange}
        />
    );
}

export default InfoToggle;
