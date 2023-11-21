import {Dispatch, SetStateAction, useEffect, useState, useMemo} from 'react';
import Grid from '@mui/material/Grid';
import Button from '@mui/material/Button';
import ArrowBackIosNewIcon from '@mui/icons-material/ArrowBackIosNew';
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos';
import {ArvoOppilaitos} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';
import ItemsList from './ItemsList';
import {not, intersection} from '../utils';

interface AktivointiListProps {
    left: ArvoOppilaitos[];
    setLeft: Dispatch<SetStateAction<ArvoOppilaitos[]>>;
    right: ArvoOppilaitos[];
    setRight: Dispatch<SetStateAction<ArvoOppilaitos[]>>;
}

function AktivointiList({left, setLeft, right, setRight}: AktivointiListProps) {
    const [checked, setChecked] = useState<ArvoOppilaitos[]>([]);
    const [leftFilter, setLeftFilter] = useState<string>('');
    const [rightFilter, setRightFilter] = useState<string>('');
    const leftChecked = intersection(checked, left);
    const rightChecked = intersection(checked, right);

    const handleCheckedRight = () => {
        setLeftFilter('');
        setRight(right.concat(leftChecked));
        setLeft(not(left, leftChecked));
        setChecked(not(checked, leftChecked));
    };

    const handleCheckedLeft = () => {
        setLeftFilter('');
        setLeft(left.concat(rightChecked));
        setRight(not(right, rightChecked));
        setChecked(not(checked, rightChecked));
    };

    useEffect(() => {
        setChecked([]);
    }, [leftFilter]);

    return (
        <>
            <Grid item>
                {useMemo(
                    () => (
                        <ItemsList
                            isLeft
                            allItems={left}
                            filter={leftFilter}
                            setFilter={setLeftFilter}
                            checked={checked}
                            setChecked={setChecked}
                        />
                    ),
                    [left, leftFilter, setLeftFilter, checked, setChecked],
                )}
            </Grid>
            <Grid item>
                <Grid
                    container
                    direction="column"
                    alignItems="stretch"
                    justifyContent="center"
                    style={{height: '100%'}}
                >
                    <Button
                        sx={{my: 0.5}}
                        size="small"
                        onClick={handleCheckedRight}
                        disabled={leftChecked.length === 0}
                        aria-label="move selected right"
                    >
                        <ArrowForwardIosIcon />
                    </Button>
                    <Button
                        sx={{my: 0.5}}
                        size="small"
                        onClick={handleCheckedLeft}
                        disabled={rightChecked.length === 0}
                        aria-label="move selected left"
                    >
                        <ArrowBackIosNewIcon />
                    </Button>
                </Grid>
            </Grid>
            <Grid item className="selected-grid">
                {useMemo(
                    () => (
                        <ItemsList
                            isLeft={false}
                            allItems={right}
                            filter={rightFilter}
                            setFilter={setRightFilter}
                            checked={checked}
                            setChecked={setChecked}
                        />
                    ),
                    [right, rightFilter, setRightFilter, checked, setChecked],
                )}
            </Grid>
        </>
    );
}

export default AktivointiList;
