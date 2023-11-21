import React, {Dispatch, SetStateAction, useEffect, useMemo} from 'react';
import {useTranslation} from 'react-i18next';
import {Observable} from 'rxjs';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import {debounce} from '@mui/material/utils';
import {
    ArvoKoulutustoimija,
    ArvoImpersonoitava,
} from '@cscfi/shared/services/Arvo-api/Arvo-api-service';

import styles from './AutoComplete.module.css';

function instanceOfArvoKoulutustoimija(object: any): object is ArvoKoulutustoimija {
    return 'nimi_fi' in object;
}

type SearchItem = ArvoImpersonoitava | ArvoKoulutustoimija;

interface ImpersonateSearchProps {
    translationNs: string;
    setOid: Dispatch<SetStateAction<string | null>>;
    fetchFn: (keyword: string) => Observable<SearchItem[]>;
    filterFn?: (obj: any) => boolean;
}

function ImpersonateSearch({
    translationNs = 'impersonointi',
    setOid,
    fetchFn,
    filterFn,
}: ImpersonateSearchProps) {
    const {
        t,
        i18n: {language: lang},
    } = useTranslation([translationNs]);
    const [value, setValue] = React.useState<SearchItem | null>(null);
    const [inputValue, setInputValue] = React.useState('');
    const [options, setOptions] = React.useState<readonly SearchItem[]>([]);
    const koulutustoimijaNimi = `nimi_${lang}` as keyof ArvoKoulutustoimija;

    const fetch = useMemo(
        () =>
            debounce(
                (input: string, callback: (results?: readonly SearchItem[]) => void) => {
                    fetchFn(input).subscribe((res) => callback(res as SearchItem[]));
                },
                400,
            ),
        [fetchFn],
    );

    useEffect(() => {
        let active = true;
        if (inputValue === '') {
            setOptions(value ? [value] : []);
            return undefined;
        }
        fetch(inputValue, (results?: readonly SearchItem[]) => {
            if (active) {
                let newOptions: readonly SearchItem[] = [];

                if (value) {
                    newOptions = [value];
                }
                if (results) {
                    const filtered = filterFn ? results.filter(filterFn) : results;
                    newOptions = [...newOptions, ...filtered];
                }
                setOptions(newOptions);
            }
        });

        return () => {
            active = false;
        };
    }, [value, inputValue, fetch, filterFn]);

    return (
        <Autocomplete
            className={styles['autocomplete-root']}
            id="valssi-autocomplete"
            sx={{width: 600}}
            getOptionLabel={(option) =>
                instanceOfArvoKoulutustoimija(option)
                    ? option[koulutustoimijaNimi]
                    : option.nimi
            }
            filterOptions={(x) => x}
            options={options}
            autoComplete
            includeInputInList
            filterSelectedOptions
            value={value}
            noOptionsText={t('ei-hakutuloksia')}
            onChange={(event: any, newValue: SearchItem | null) => {
                setOptions(newValue ? [newValue, ...options] : options);
                setValue(newValue);
                setOid(newValue?.oid ? newValue.oid : null);
            }}
            onInputChange={(event, newInputValue) => {
                setInputValue(newInputValue);
            }}
            renderInput={(props) => (
                <>
                    <label htmlFor="valssi-autocomplete" className="label-for-inputfield">
                        {t('etsi-label')}
                    </label>
                    {/* eslint-disable-next-line react/jsx-props-no-spreading */}
                    <TextField {...props} placeholder={t('etsi-placeholder')} fullWidth />
                </>
            )}
            renderOption={(props, option) => (
                // eslint-disable-next-line react/jsx-props-no-spreading
                <li {...props}>
                    <Grid container alignItems="center">
                        <Grid item sx={{wordWrap: 'break-word'}}>
                            <Box component="span">
                                {instanceOfArvoKoulutustoimija(option)
                                    ? option[koulutustoimijaNimi]
                                    : option.nimi}
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                                {option.oid}
                            </Typography>
                        </Grid>
                    </Grid>
                </li>
            )}
        />
    );
}

export default ImpersonateSearch;
