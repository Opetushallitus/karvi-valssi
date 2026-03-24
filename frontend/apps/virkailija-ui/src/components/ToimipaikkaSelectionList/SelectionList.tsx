import {Dispatch, SetStateAction, useState, useMemo} from 'react';
import Button from '@mui/material/Button';
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import Grid from '@mui/material/Grid';
import {
    AlueFormType,
    OppilaitosSetType,
} from '@cscfi/shared/services/Virkailijapalvelu-api/Virkailijapalvelu-api-service';
import {UseFormReturn} from 'react-hook-form';
import {useTranslation} from 'react-i18next';
import {itemsIntersection, itemsUnion} from './utils';
import styles from './ToimipaikkaSelectionList.module.css';
import ItemsList from './ItemsList';
import {getDefaultEmptySet, itemsLength, itemsNot} from '../../utils/helpers';

interface AktivointiListProps {
    left: OppilaitosSetType;
    setLeft: Dispatch<SetStateAction<OppilaitosSetType>>;
    right: OppilaitosSetType;
    setRight: Dispatch<SetStateAction<OppilaitosSetType>>;
    rightGroups?: boolean;
    leftLabel?: string;
    rightLabel?: string;
    rightLabelModifiable?: boolean;
    selectableGroups: boolean;
    formMethods?: UseFormReturn<AlueFormType, any, undefined>;
}

function SelectionList({
    left,
    setLeft,
    right,
    setRight,
    rightGroups = true,
    leftLabel = '',
    rightLabel = '',
    rightLabelModifiable = false,
    selectableGroups = false,
    formMethods,
}: AktivointiListProps) {
    const {t} = useTranslation(['aluejako']);

    const [checked, setChecked] = useState<OppilaitosSetType>(getDefaultEmptySet());
    const [leftFilter, setLeftFilter] = useState<string>('');
    const [rightFilter, setRightFilter] = useState<string>('');

    // Kun vasenta suodatinta muutetaan, nollaa valinnat heti tässä
    const handleLeftFilterChange = (value: string) => {
        setLeftFilter(value);
        setChecked(getDefaultEmptySet());
    };

    const leftChecked = itemsIntersection(checked, left);
    const rightChecked = itemsIntersection(checked, right);

    // clicking the right arrow, setting checked items from left to right.
    const handleCheckedRight = () => {
        setLeftFilter('');
        setRight(itemsUnion(right, leftChecked));

        setLeft(itemsNot(left, leftChecked));
        setChecked(getDefaultEmptySet());
    };

    // clicking the left arrow, setting checked items from right to left.
    const handleCheckedLeft = () => {
        setLeftFilter('');
        setLeft(itemsUnion(left, rightChecked));
        setRight(itemsNot(right, rightChecked));
        setChecked(getDefaultEmptySet());
    };

    return (
        <>
            <Grid>
                {useMemo(
                    () => (
                        <ItemsList
                            isLeft
                            label={leftLabel || t('alueet-ja-toimipaikat')}
                            allItems={left}
                            filter={leftFilter}
                            setFilter={handleLeftFilterChange} // <- nollaa tässä, ei efektissä
                            checked={checked}
                            setChecked={setChecked}
                            selectableGroups={selectableGroups}
                        />
                    ),
                    [leftLabel, t, left, leftFilter, checked, selectableGroups],
                )}
            </Grid>
            <Grid>
                <Grid
                    container
                    direction="column"
                    alignItems="stretch"
                    justifyContent="center"
                    style={{height: '100%'}}
                >
                    <Button
                        className={styles['selection-arrow-button']}
                        size="small"
                        onClick={handleCheckedRight}
                        disabled={itemsLength(leftChecked) === 0}
                        aria-label="move selected right"
                    >
                        <ArrowForwardIosIcon />
                    </Button>
                    <Button
                        className={styles['selection-arrow-button']}
                        size="small"
                        onClick={handleCheckedLeft}
                        disabled={itemsLength(rightChecked) === 0}
                        aria-label="move selected left"
                    >
                        <ArrowBackIosNewIcon />
                    </Button>
                </Grid>
            </Grid>
            <Grid alignContent="end">
                {useMemo(
                    () => (
                        <ItemsList
                            isLeft={false}
                            allItems={right}
                            filter={rightFilter}
                            setFilter={setRightFilter}
                            checked={checked}
                            setChecked={setChecked}
                            itemsInGroups={rightGroups}
                            label={rightLabel}
                            labelModifiable={rightLabelModifiable}
                            formMethods={formMethods}
                            selectableGroups={selectableGroups}
                        />
                    ),
                    [
                        right,
                        rightFilter,
                        checked,
                        rightGroups,
                        rightLabel,
                        rightLabelModifiable,
                        formMethods,
                        selectableGroups,
                    ],
                )}
            </Grid>
        </>
    );
}

export default SelectionList;
