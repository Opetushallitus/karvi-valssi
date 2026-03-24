import {useMemo} from 'react';
import {useTranslation} from 'react-i18next';
import Grid from '@mui/material/Grid';
import {OppilaitosSetType} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {getDefaultEmptySet, sortItems} from '../../utils/helpers';
import ItemsList from './ItemsList';

interface AktivoidutListProps {
    list: OppilaitosSetType;
}

function SelectedList({list}: AktivoidutListProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation(['aktivointi']);
    const items = useMemo(() => sortItems(list, lang), [lang, list]);
    return (
        <Grid alignContent="end">
            <ItemsList
                allItems={items}
                isLeft={false}
                disabled
                label={t('aktivoidut-title')}
                filter=""
                setFilter={(): any => null}
                checked={getDefaultEmptySet()}
                setChecked={(): any => null}
                selectableGroups={false}
            />
        </Grid>
    );
}

export default SelectedList;
