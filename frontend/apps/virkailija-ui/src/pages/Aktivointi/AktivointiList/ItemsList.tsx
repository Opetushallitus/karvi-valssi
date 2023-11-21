import {Dispatch, SetStateAction, useMemo} from 'react';
import {useTranslation} from 'react-i18next';
import GenericTextField from '@cscfi/shared/components/GenericTextField/GenericTextField';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';
import Checkbox from '@mui/material/Checkbox';
import CheckIcon from '@mui/icons-material/Check';
import {ArvoOppilaitos} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import styles from './AktivointiList.module.css';
import {filterOppilaitos, sortOppilaitos, not, intersection, union} from '../utils';

interface ItemsListProps {
    isLeft: boolean;
    allItems: ArvoOppilaitos[];
    filter: string;
    setFilter: Dispatch<SetStateAction<string>>;
    checked: ArvoOppilaitos[];
    setChecked: Dispatch<SetStateAction<ArvoOppilaitos[]>>;
}

const oppilaitosItem = (
    oppilaitos: ArvoOppilaitos,
    isChecked: boolean,
    onClick: any,
    lang: string,
) => {
    const labelId = `transfer-list-all-item-${oppilaitos}-label`;
    const oppilaitosNimi = `nimi_${lang}` as keyof ArvoOppilaitos;
    return (
        <ListItem
            key={oppilaitos.oid}
            role="listitem"
            button
            onClick={onClick()}
            className={
                isChecked
                    ? styles['multiselect-listitem-selected']
                    : styles['multiselect-listitem']
            }
        >
            <ListItemText id={labelId} primary={`${oppilaitos[oppilaitosNimi]}`} />
            <ListItemIcon className={styles['multiselect-listitem-icon']}>
                <Checkbox
                    checked={isChecked}
                    tabIndex={-1}
                    disableRipple
                    inputProps={{
                        'aria-labelledby': labelId,
                    }}
                    className={
                        isChecked
                            ? styles['multiselect-listitem-checkbox-selected']
                            : styles['multiselect-listitem-checkbox']
                    }
                    checkedIcon={<CheckIcon />}
                />
            </ListItemIcon>
        </ListItem>
    );
};

function ItemsList({
    isLeft,
    allItems,
    filter,
    setFilter,
    checked,
    setChecked,
}: ItemsListProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['aktivointi']);

    const numberOfChecked = (items: ArvoOppilaitos[]) =>
        intersection(checked, items).length;

    const handleToggle = (value: ArvoOppilaitos) => () => {
        const currentIndex = checked.indexOf(value);
        const newChecked = [...checked];

        if (currentIndex === -1) {
            newChecked.push(value);
        } else {
            newChecked.splice(currentIndex, 1);
        }

        setChecked(newChecked);
    };

    const handleToggleAll = (items: ArvoOppilaitos[]) => () => {
        if (numberOfChecked(items) === items.length) {
            setChecked(not(checked, items));
        } else {
            setChecked(union(checked, items));
        }
    };

    const sorted = useMemo(() => sortOppilaitos(allItems, lang), [allItems, lang]);
    const items = useMemo(
        () => filterOppilaitos(sorted, filter, lang),
        [sorted, filter, lang],
    );
    const indeterminateChecked =
        numberOfChecked(items) !== items.length && numberOfChecked(items) !== 0;
    const allChecked = numberOfChecked(items) === items.length && items.length !== 0;
    const nothingToBeChecked = items.length === 0;
    // `${numberOfChecked(items)}/${items.length}`

    return (
        <fieldset>
            <legend>{isLeft ? t('hae-title-left') : t('hae-title-right')}</legend>

            {isLeft && (
                <>
                    <div className={styles['multiselect-button']}>
                        <button
                            type="button"
                            onClick={handleToggleAll(items)}
                            className={styles['multiselect-selectall-btn']}
                            disabled={nothingToBeChecked}
                        >
                            {indeterminateChecked || !allChecked
                                ? t('valitse-kaikki')
                                : t('poista-kaikki')}
                        </button>
                    </div>
                    <div className={styles['multiselect-search']}>
                        <GenericTextField
                            value={filter}
                            label=""
                            showLabel={false}
                            onChange={setFilter}
                            fullWidth
                            placeholder={
                                isLeft
                                    ? t('hae-placeholder-left')
                                    : t('hae-placeholder-right')
                            }
                            clearButton
                        />
                    </div>
                </>
            )}

            <List
                dense
                component="div"
                role="list"
                className={styles[isLeft ? 'multiselect-list' : 'multiselect-list-right']}
            >
                {items.map((oppilaitos: ArvoOppilaitos) =>
                    oppilaitosItem(
                        oppilaitos,
                        checked.indexOf(oppilaitos) !== -1,
                        () => handleToggle(oppilaitos),
                        lang,
                    ),
                )}
                <ListItem />
            </List>
        </fieldset>
    );
}

export default ItemsList;
