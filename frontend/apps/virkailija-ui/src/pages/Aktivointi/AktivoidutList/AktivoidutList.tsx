import {useMemo} from 'react';
import {useTranslation} from 'react-i18next';
import Grid from '@mui/material/Grid';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import {ArvoOppilaitos} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import styles from './AktivoidutList.module.css';
import {sortOppilaitos} from '../utils';

interface AktivoidutListProps {
    list: ArvoOppilaitos[];
}

function AktivoidutList({list}: AktivoidutListProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['aktivointi']);
    const items = useMemo(() => sortOppilaitos(list, lang), [lang, list]);
    const oppilaitosNimi = `nimi_${lang}` as keyof ArvoOppilaitos;

    return (
        <Grid item className="activated-grid">
            <legend>{t('aktivoidut-title')}</legend>

            <List dense component="div" role="list" className={styles['activated-list']}>
                {items.map((oppilaitos: ArvoOppilaitos) => {
                    const labelId = `transfer-list-all-item-${oppilaitos}-label`;
                    return (
                        <ListItem
                            key={oppilaitos.oid}
                            role="listitem"
                            className={styles['activated-listitem']}
                        >
                            <ListItemText
                                id={labelId}
                                primary={`${oppilaitos[oppilaitosNimi]}`}
                                className={styles['activated-listitem-text']}
                            />
                        </ListItem>
                    );
                })}
                <ListItem />
            </List>
        </Grid>
    );
}

export default AktivoidutList;
