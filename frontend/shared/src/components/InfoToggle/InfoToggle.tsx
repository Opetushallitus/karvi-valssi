import {ChangeEventHandler} from 'react';
import Avatar from '@mui/material/Avatar';
import ExpandLessRounded from '@mui/icons-material/ExpandLessRounded';
import InfoOutlined from '@mui/icons-material/InfoOutlined';
import Checkbox from '@mui/material/Checkbox';
import styles from './InfoToggle.module.css';

interface InfoToggleProps {
    isOpen: boolean;
    onChange: ChangeEventHandler<HTMLTextAreaElement | HTMLInputElement>;
}

function InfoToggle({isOpen, onChange}: InfoToggleProps) {
    return (
        <Checkbox
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
